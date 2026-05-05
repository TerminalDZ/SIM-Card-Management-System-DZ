"""Async wrapper around a blocking :mod:`pyserial` connection.

``pyserial`` is synchronous, so we run its ``read``/``write`` calls in a thread
executor. A single :class:`asyncio.Lock` per transport ensures full-duplex
safety: only one coroutine talks to the modem at a time, and binary in/out is
always paired with the right reader.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import TracebackType
from typing import Self

import serial

from app.core.exceptions import SerialTransportError
from app.core.logger import get_logger


class SerialTransport:
    """Owns a single serial port and offers async read/write primitives."""

    def __init__(
        self,
        port: str,
        *,
        baudrate: int = 115200,
        open_timeout: float = 2.0,
        read_timeout: float = 0.05,
        logger: logging.Logger | None = None,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self._open_timeout = open_timeout
        self._read_timeout = read_timeout
        self._logger = logger or get_logger(f"transport.{port}")
        self._serial: serial.Serial | None = None
        self._io_lock = asyncio.Lock()

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    @property
    def is_open(self) -> bool:
        return self._serial is not None and self._serial.is_open

    @property
    def is_url(self) -> bool:
        """True when the configured ``port`` is a pyserial URL (e.g. socket://host:port)."""
        return "://" in self.port

    async def open(self) -> None:
        if self.is_open:
            return
        try:
            self._serial = await asyncio.to_thread(self._open_blocking)
        except (serial.SerialException, OSError) as exc:
            raise SerialTransportError(
                f"Could not open serial port {self.port}",
                details={"port": self.port, "reason": str(exc)},
            ) from exc

        # DTR/RTS handshake + buffer reset apply only to physical ports —
        # a TCP/RFC2217 URL has no modem control lines.
        if not self.is_url:
            try:
                self._serial.dtr = True
                self._serial.rts = True
                self._serial.reset_input_buffer()
                self._serial.reset_output_buffer()
            except (serial.SerialException, OSError) as exc:
                self._logger.debug("DTR/RTS handshake failed on %s: %s", self.port, exc)

        # Give the device a moment to settle after opening — physical Huawei
        # sticks often need ~150ms before they accept their first AT command.
        await asyncio.sleep(0.15)

        self._logger.debug("Serial port %s opened @ %d baud", self.port, self.baudrate)

    def _open_blocking(self) -> serial.SerialBase:
        """Open the configured port. Used both for plain ports and URLs."""
        if self.is_url:
            conn = serial.serial_for_url(
                self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self._read_timeout,
                write_timeout=self._open_timeout,
                do_not_open=False,
            )
            return conn
        return serial.Serial(
            self.port,
            self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self._read_timeout,
            write_timeout=self._open_timeout,
        )

    async def close(self) -> None:
        if self._serial is None:
            return
        try:
            await asyncio.to_thread(self._serial.close)
        except (serial.SerialException, OSError) as exc:
            self._logger.debug("Closing %s raised %s", self.port, exc)
        finally:
            self._serial = None

    async def __aenter__(self) -> Self:
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    # ── I/O primitives ────────────────────────────────────────────────────────
    @asynccontextmanager
    async def lock(self) -> AsyncIterator[None]:
        """Reserve exclusive access to the underlying port."""
        async with self._io_lock:
            yield

    async def write(self, data: bytes) -> None:
        if self._serial is None:
            raise SerialTransportError("Serial port is not open", details={"port": self.port})
        try:
            await asyncio.to_thread(self._serial.write, data)
            await asyncio.to_thread(self._serial.flush)
        except (serial.SerialException, OSError) as exc:
            raise SerialTransportError(
                f"Write failed on {self.port}",
                details={"port": self.port, "reason": str(exc)},
            ) from exc

    async def reset_input(self) -> None:
        if self._serial is None:
            return
        with contextlib.suppress(serial.SerialException, OSError):
            await asyncio.to_thread(self._serial.reset_input_buffer)

    async def read_until(
        self,
        terminators: tuple[bytes, ...],
        *,
        timeout: float,
    ) -> bytes:
        """Read bytes until *any* of the given terminators is seen, or timeout.

        The caller decides what success / error markers to look for so we do
        not couple the transport to AT-specific semantics.
        """
        if self._serial is None:
            raise SerialTransportError("Serial port is not open", details={"port": self.port})
        deadline = time.monotonic() + timeout
        buffer = bytearray()

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return bytes(buffer)
            try:
                chunk = await asyncio.to_thread(self._serial.read, 4096)
            except (serial.SerialException, OSError) as exc:
                raise SerialTransportError(
                    f"Read failed on {self.port}",
                    details={"port": self.port, "reason": str(exc)},
                ) from exc

            if chunk:
                buffer.extend(chunk)
                if any(term in buffer for term in terminators):
                    return bytes(buffer)
            else:
                # Yield control briefly so siblings make progress
                await asyncio.sleep(0.02)
