"""High-level client for sending AT commands and parsing modem replies."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from app.core.exceptions import ATCommandError, ATCommandTimeoutError, SerialTransportError
from app.core.logger import get_logger
from app.modem.transport import SerialTransport


@dataclass(slots=True, frozen=True)
class ATResponse:
    """Parsed response of an AT command."""

    command: str
    raw: str
    lines: list[str]
    status: str  # "OK", "ERROR", "TIMEOUT", or a vendor-specific error

    @property
    def ok(self) -> bool:
        return self.status == "OK"


_TERMINATORS = (b"\r\nOK\r\n", b"\r\nERROR\r\n", b"+CME ERROR", b"+CMS ERROR", b"\r\n> ")


class ATClient:
    """Wraps a :class:`SerialTransport` to provide AT-style request/response."""

    def __init__(
        self,
        transport: SerialTransport,
        *,
        default_timeout: float = 10.0,
        retries: int = 2,
        logger: logging.Logger | None = None,
    ) -> None:
        self.transport = transport
        self.default_timeout = default_timeout
        self.retries = max(0, retries)
        self._logger = logger or get_logger(f"at.{transport.port}")

    # ── Public API ────────────────────────────────────────────────────────────
    async def execute(
        self,
        command: str,
        *,
        timeout: float | None = None,
        expect_prompt: bool = False,
    ) -> ATResponse:
        """Send *command* and wait for an OK/ERROR (or ``>`` prompt) terminator.

        Retries on timeout / transport errors up to :attr:`retries` times.
        """
        timeout = timeout if timeout is not None else self.default_timeout
        attempts = self.retries + 1
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                response = await self._send_once(
                    command, timeout=timeout, expect_prompt=expect_prompt
                )
            except SerialTransportError as exc:
                last_error = exc
                self._logger.warning(
                    "AT %s transport error (attempt %d/%d): %s",
                    command,
                    attempt,
                    attempts,
                    exc,
                )
            except ATCommandTimeoutError as exc:
                last_error = exc
                self._logger.warning("AT %s timed out (attempt %d/%d)", command, attempt, attempts)
            else:
                return response
            if attempt < attempts:
                await asyncio.sleep(0.25 * attempt)

        assert last_error is not None
        raise last_error

    async def execute_raw_then_read(
        self,
        prompt_command: str,
        body: bytes,
        *,
        timeout: float = 30.0,
    ) -> ATResponse:
        """Send a command that returns ``>``, then push *body* and wait for OK.

        Used by SMS submission (``AT+CMGS``) where the modem prompts for the
        message body after the initial command.
        """
        prompt_response = await self.execute(prompt_command, timeout=10.0, expect_prompt=True)
        if "> " not in prompt_response.raw:
            raise ATCommandError(
                f"Modem did not prompt for body after {prompt_command}",
                details={"raw": prompt_response.raw},
            )
        async with self.transport.lock():
            await self.transport.write(body)
            data = await self.transport.read_until(
                (b"\r\nOK\r\n", b"\r\nERROR\r\n", b"+CMS ERROR"),
                timeout=timeout,
            )
        raw = data.decode("utf-8", errors="ignore")
        return _parse(prompt_command, raw)

    async def execute_optional(
        self,
        command: str,
        *,
        timeout: float | None = None,
    ) -> ATResponse | None:
        """Like :meth:`execute` but returns ``None`` instead of raising."""
        try:
            return await self.execute(command, timeout=timeout)
        except (ATCommandError, SerialTransportError) as exc:
            self._logger.debug("Optional command %s failed: %s", command, exc)
            return None

    # ── Internals ─────────────────────────────────────────────────────────────
    async def _send_once(
        self,
        command: str,
        *,
        timeout: float,
        expect_prompt: bool,
    ) -> ATResponse:
        terminators = _TERMINATORS if not expect_prompt else (*_TERMINATORS, b"\r\n> ")
        async with self.transport.lock():
            await self.transport.reset_input()
            await self.transport.write(f"{command}\r\n".encode())
            data = await self.transport.read_until(terminators, timeout=timeout)
        raw = data.decode("utf-8", errors="ignore")
        if not raw:
            raise ATCommandTimeoutError(
                f"AT command {command!r} timed out after {timeout:.1f}s",
                details={"command": command, "timeout": timeout},
            )
        response = _parse(command, raw)
        if response.status not in {"OK"} and not (expect_prompt and "> " in raw):
            if response.status == "TIMEOUT":
                raise ATCommandTimeoutError(
                    f"AT command {command!r} returned no terminator",
                    details={"command": command, "timeout": timeout, "raw": raw},
                )
            raise ATCommandError(
                f"AT command {command!r} failed: {response.status}",
                details={"command": command, "raw": raw, "status": response.status},
            )
        return response


def _parse(command: str, raw: str) -> ATResponse:
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    status = "TIMEOUT"
    for line in lines:
        if line == "OK":
            status = "OK"
            break
        if line == "ERROR":
            status = "ERROR"
            break
        if line.startswith("+CME ERROR") or line.startswith("+CMS ERROR"):
            status = line
            break
    return ATResponse(command=command, raw=raw, lines=lines, status=status)
