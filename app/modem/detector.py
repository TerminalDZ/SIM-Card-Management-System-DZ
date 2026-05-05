"""Discovery of Huawei (and compatible) USB modems on the system bus.

Detection has two phases:

1. **Catalog phase** — list every serial port whose USB descriptors look
   like a Huawei modem (VID 0x12D1, 0x19D2, 0x1C9E or a known model name).
2. **Probe phase** — open each candidate briefly, send ``AT``/``ATI`` and
   check for an ``OK`` reply. The probe is *informational*: a candidate
   that fails the probe is still returned, with ``responsive=False``, so
   callers can decide whether to attempt a connection anyway. Some Huawei
   modems expose multiple COM ports where only one accepts AT — the others
   would otherwise disappear from the list.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from dataclasses import dataclass

import serial
from serial.tools import list_ports
from serial.tools.list_ports_common import ListPortInfo

from app.core.logger import get_logger
from app.schemas.modem import DetectedModem

# Vendor IDs that ship modems supported by this project.
HUAWEI_VENDOR_IDS: frozenset[int] = frozenset({0x12D1, 0x19D2, 0x1C9E})

# Known model names — used as a soft fallback when VID is missing on a system.
_HUAWEI_KEYWORDS: tuple[str, ...] = (
    "huawei",
    "e3531",
    "e3372",
    "e3131",
    "e173",
    "e398",
    "e5573",
    "e5785",
    "k3520",
    "hilink",
    "mobile connect",
)


@dataclass(slots=True, frozen=True)
class DetectedPort:
    """A serial port that looks like a Huawei modem."""

    port: str
    description: str | None
    vendor_id: int | None
    product_id: int | None
    responsive: bool = False

    @property
    def modem_id(self) -> str:
        # Prefix differs for hardware vs network-attached "modems" so URL
        # routing stays unambiguous and IDs remain path-safe.
        if "://" in self.port:
            scheme, _, rest = self.port.partition("://")
            safe = rest.replace("/", "_").replace("\\", "_").replace(":", "_")
            return f"net_{scheme}_{safe}"
        safe = self.port.replace("/", "_").replace("\\", "_")
        return f"huawei_{safe}"

    def to_schema(self) -> DetectedModem:
        return DetectedModem(
            modem_id=self.modem_id,
            port=self.port,
            description=self.description,
            vendor_id=f"{self.vendor_id:04X}" if self.vendor_id is not None else None,
            product_id=f"{self.product_id:04X}" if self.product_id is not None else None,
            responsive=self.responsive,
        )


class ModemDetector:
    """Probe serial ports for Huawei-class modems."""

    def __init__(
        self,
        *,
        baudrate: int,
        probe_timeout: float = 2.0,
    ) -> None:
        self._baudrate = baudrate
        self._probe_timeout = probe_timeout
        self._logger = get_logger("detector")

    async def discover(self) -> list[DetectedPort]:
        """Return every Huawei-class port, marked with the AT probe result."""
        candidates = self._candidates()
        self._logger.info(
            "Detector found %d candidate port(s): %s",
            len(candidates),
            [c.port for c in candidates],
        )
        results: list[DetectedPort] = []
        for candidate in candidates:
            responsive = await self._probe(candidate.port)
            self._logger.info(
                "Probe %s: %s",
                candidate.port,
                "responsive" if responsive else "no AT reply",
            )
            results.append(
                DetectedPort(
                    port=candidate.port,
                    description=candidate.description,
                    vendor_id=candidate.vendor_id,
                    product_id=candidate.product_id,
                    responsive=responsive,
                )
            )
        return results

    # ── Internals ─────────────────────────────────────────────────────────────
    def _candidates(self) -> list[DetectedPort]:
        ports: list[DetectedPort] = []
        for info in list_ports.comports():
            if not self._looks_like_huawei(info):
                continue
            ports.append(
                DetectedPort(
                    port=info.device,
                    description=info.description,
                    vendor_id=info.vid,
                    product_id=info.pid,
                )
            )
        return ports

    @staticmethod
    def _looks_like_huawei(info: ListPortInfo) -> bool:
        if info.vid in HUAWEI_VENDOR_IDS:
            return True
        haystack = " ".join(
            x or "" for x in (info.description, info.manufacturer, info.product, info.hwid)
        ).lower()
        return any(keyword in haystack for keyword in _HUAWEI_KEYWORDS)

    async def _probe(self, port: str) -> bool:
        """Open *port* briefly and check whether it answers ``AT``."""
        try:
            return await asyncio.to_thread(
                _probe_blocking, port, self._baudrate, self._probe_timeout
            )
        except Exception as exc:
            self._logger.debug("Probe failed for %s: %s", port, exc)
            return False


def _probe_blocking(port: str, baudrate: int, timeout: float) -> bool:
    """Run a single AT probe against *port*. Returns True if OK was seen."""
    try:
        conn = serial.Serial(
            port,
            baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,
            write_timeout=timeout,
        )
    except (serial.SerialException, OSError):
        return False

    try:
        with contextlib.suppress(serial.SerialException, OSError):
            conn.dtr = True
            conn.rts = True
        with contextlib.suppress(serial.SerialException, OSError):
            conn.reset_input_buffer()

        # Give the modem a heartbeat to wake from any standby state
        time.sleep(0.05)
        for command in (b"AT\r", b"AT\r\n", b"ATI\r\n"):
            try:
                conn.write(command)
                conn.flush()
            except (serial.SerialException, OSError):
                return False
            buffer = bytearray()
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    chunk = conn.read(256)
                except (serial.SerialException, OSError):
                    return False
                if chunk:
                    buffer.extend(chunk)
                    if b"OK" in buffer or b"+CME ERROR" in buffer or b"+CMS ERROR" in buffer:
                        return True
                    if b"ERROR" in buffer:
                        break
        return False
    finally:
        with contextlib.suppress(serial.SerialException, OSError):
            conn.close()
