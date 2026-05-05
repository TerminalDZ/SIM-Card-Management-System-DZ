"""Modem-related response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import NetworkType


class ModemHealth(BaseModel):
    """Last-known signal/network quality for a modem."""

    model_config = ConfigDict(use_enum_values=True)

    signal_strength: int | None = Field(default=None, ge=0, le=100)
    rssi_dbm: int | None = Field(default=None)
    network_type: NetworkType = NetworkType.UNKNOWN
    operator: str | None = None
    registered: bool = False
    roaming: bool = False


class ModemStatus(BaseModel):
    """Operational state of a single modem."""

    model_config = ConfigDict(use_enum_values=True)

    modem_id: str
    port: str
    connected: bool
    model: str | None = None
    firmware: str | None = None
    imei: str | None = None
    health: ModemHealth = Field(default_factory=ModemHealth)
    connected_at: datetime | None = None
    last_activity: datetime | None = None
    last_error: str | None = None


class DetectedModem(BaseModel):
    """A modem found on the system bus, regardless of connection state."""

    modem_id: str
    port: str
    description: str | None = None
    vendor_id: str | None = None
    product_id: str | None = None
    responsive: bool = Field(
        default=False,
        description="True when the AT probe got an OK during detection.",
    )


class ModemDetectionResponse(BaseModel):
    detected: list[DetectedModem]
    connected_ids: list[str]
    total_detected: int = Field(ge=0)
    total_connected: int = Field(ge=0)


class MultiModemStatus(BaseModel):
    total: int = Field(ge=0)
    connected: int = Field(ge=0)
    modems: dict[str, ModemStatus]
