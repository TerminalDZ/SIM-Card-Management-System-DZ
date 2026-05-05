"""SIM card information schema."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.enums import NetworkType


class SimInfo(BaseModel):
    """Information read from the inserted SIM card."""

    model_config = ConfigDict(use_enum_values=True)

    modem_id: str | None = None
    imsi: str | None = None
    iccid: str | None = None
    imei: str | None = None
    msisdn: str | None = None
    operator_id: str | None = Field(default=None, description="Resolved operator profile id")
    operator_name: str | None = None
    network_operator: str | None = None
    signal_strength: int | None = Field(default=None, ge=0, le=100)
    network_type: NetworkType = NetworkType.UNKNOWN
    roaming: bool = False

    @field_validator("imsi")
    @classmethod
    def _validate_imsi(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.isdigit() or len(value) != 15:
            raise ValueError("IMSI must be 15 digits")
        return value

    @field_validator("iccid")
    @classmethod
    def _validate_iccid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.isdigit() or not (18 <= len(value) <= 22):
            raise ValueError("ICCID must be 18-22 digits")
        return value

    @field_validator("imei")
    @classmethod
    def _validate_imei(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.isdigit() or len(value) not in (14, 15, 16):
            raise ValueError("IMEI must be 14-16 digits")
        return value
