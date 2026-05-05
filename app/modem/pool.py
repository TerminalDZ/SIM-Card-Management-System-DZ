"""Manages a collection of :class:`ModemDevice` objects.

Responsibilities:

* Maintain the registry of detected ports.
* Connect / disconnect modems on demand, enforcing a configurable cap.
* Aggregate status across devices for monitoring.
* Tear everything down cleanly on shutdown.

The pool is the only mutable state outside individual devices, so all
mutations go through an :class:`asyncio.Lock`.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from datetime import datetime, timezone

from app.config import Settings
from app.core.exceptions import (
    ModemAlreadyConnectedError,
    ModemDetectionError,
    ModemLimitExceededError,
    ModemNotFoundError,
)
from app.core.logger import get_logger, timed_operation
from app.modem.detector import DetectedPort, ModemDetector
from app.modem.device import ModemDevice
from app.operators.repository import OperatorRepository
from app.schemas.modem import (
    DetectedModem,
    ModemDetectionResponse,
    ModemStatus,
    MultiModemStatus,
)


class ModemPool:
    """Concurrent registry + lifecycle manager for modem devices."""

    def __init__(
        self,
        settings: Settings,
        operators: OperatorRepository,
        detector: ModemDetector | None = None,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self._operators = operators
        self._detector = detector or ModemDetector(baudrate=settings.modem_baudrate)
        self._logger = logger or get_logger("pool")
        self._lock = asyncio.Lock()
        self._known: dict[str, DetectedPort] = {}
        self._devices: dict[str, ModemDevice] = {}

    # ── Detection ────────────────────────────────────────────────────────────
    async def discover(self) -> ModemDetectionResponse:
        with timed_operation(self._logger, "pool.discover"):
            try:
                detected = await self._detector.discover()
            except Exception as exc:  # pragma: no cover — depends on hardware
                raise ModemDetectionError(f"Detection failed: {exc}") from exc
            manual = self._manual_ports()
            combined = [*detected, *manual]
            async with self._lock:
                self._known = {port.modem_id: port for port in combined}
                # Drop devices whose ports vanished
                stale = [mid for mid in self._devices if mid not in self._known]
                for modem_id in stale:
                    self._logger.warning("Removing stale device %s (port disappeared)", modem_id)
                    await self._safely_disconnect(modem_id)
            return ModemDetectionResponse(
                detected=[port.to_schema() for port in combined],
                connected_ids=list(self._devices),
                total_detected=len(combined),
                total_connected=len(self._devices),
            )

    def _manual_ports(self) -> list[DetectedPort]:
        """Build :class:`DetectedPort` entries for every URL in the manual list."""
        ports: list[DetectedPort] = []
        for entry in self._settings.manual_modems:
            cleaned = entry.strip()
            if not cleaned:
                continue
            ports.append(
                DetectedPort(
                    port=cleaned,
                    description=f"Manually registered ({cleaned})",
                    vendor_id=None,
                    product_id=None,
                    responsive=True,
                )
            )
        return ports

    def known_ports(self) -> list[DetectedModem]:
        return [port.to_schema() for port in self._known.values()]

    # ── Connection lifecycle ─────────────────────────────────────────────────
    async def connect(self, modem_id: str) -> ModemDevice:
        async with self._lock:
            if modem_id in self._devices:
                raise ModemAlreadyConnectedError(
                    f"Modem {modem_id} is already connected",
                    details={"modem_id": modem_id},
                )
            if len(self._devices) >= self._settings.max_concurrent_modems:
                raise ModemLimitExceededError(
                    f"Cannot connect: limit of {self._settings.max_concurrent_modems} reached",
                    details={"limit": self._settings.max_concurrent_modems},
                )
            port = self._known.get(modem_id)
            if port is None:
                raise ModemNotFoundError(
                    f"Modem {modem_id} was not detected — run discovery first",
                    details={"modem_id": modem_id},
                )
            device = ModemDevice(
                modem_id=modem_id,
                port=port.port,
                settings=self._settings,
                operators=self._operators,
            )
            try:
                await device.connect()
            except Exception:
                await device.disconnect()
                raise
            self._devices[modem_id] = device
            return device

    async def disconnect(self, modem_id: str) -> None:
        async with self._lock:
            await self._safely_disconnect(modem_id)

    async def get(self, modem_id: str, *, auto_connect: bool = False) -> ModemDevice:
        device = self._devices.get(modem_id)
        if device is not None:
            return device
        if not auto_connect:
            raise ModemNotFoundError(
                f"Modem {modem_id} is not connected",
                details={"modem_id": modem_id},
            )
        # Auto-connect on first use — trigger detection if we have no record.
        if modem_id not in self._known:
            await self.discover()
        return await self.connect(modem_id)

    def connected_ids(self) -> list[str]:
        return list(self._devices)

    def first_connected(self) -> ModemDevice:
        if not self._devices:
            raise ModemNotFoundError("No modems are currently connected")
        # ``dict`` preserves insertion order in CPython 3.7+
        first_id = next(iter(self._devices))
        return self._devices[first_id]

    # ── Aggregate status ─────────────────────────────────────────────────────
    async def all_status(self) -> MultiModemStatus:
        snapshots = await asyncio.gather(
            *(self._safe_status(device) for device in self._devices.values()),
            return_exceptions=False,
        )
        modems = {
            device.modem_id: status
            for device, status in zip(self._devices.values(), snapshots, strict=True)
        }
        return MultiModemStatus(
            total=len(self._known),
            connected=len(self._devices),
            modems=modems,
        )

    async def shutdown(self) -> None:
        with timed_operation(self._logger, "pool.shutdown"):
            async with self._lock:
                for modem_id in list(self._devices):
                    await self._safely_disconnect(modem_id)

    # ── Internals ────────────────────────────────────────────────────────────
    async def _safely_disconnect(self, modem_id: str) -> None:
        device = self._devices.pop(modem_id, None)
        if device is None:
            return
        try:
            await device.disconnect()
        except Exception as exc:
            self._logger.warning("Disconnect of %s raised: %s", modem_id, exc)

    async def _safe_status(self, device: ModemDevice) -> ModemStatus:
        try:
            return await device.status()
        except Exception as exc:
            self._logger.warning("Status for %s failed: %s", device.modem_id, exc)
            return ModemStatus(
                modem_id=device.modem_id,
                port=device.port,
                connected=False,
                connected_at=device.connected_at,
                last_activity=device.last_activity or datetime.now(timezone.utc),
                last_error=str(exc),
            )

    @property
    def known(self) -> Iterable[DetectedPort]:
        return self._known.values()
