"""SMS schemas: stored messages and outbound send request."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.enums import SmsStorageStatus


class SmsMessage(BaseModel):
    """A single SMS message returned by the modem."""

    model_config = ConfigDict(use_enum_values=True)

    id: int = Field(ge=0)
    modem_id: str | None = None
    status: SmsStorageStatus
    phone_number: str
    message: str
    timestamp: datetime
    raw_header: str | None = None


class SmsSendRequest(BaseModel):
    """Payload to send an SMS through a specific modem."""

    number: str = Field(min_length=3, max_length=20, description="Recipient phone number.")
    message: str = Field(min_length=1, max_length=1530, description="Body in plain text.")

    @field_validator("number")
    @classmethod
    def _validate_number(cls, value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        if not 6 <= len(digits) <= 15:
            raise ValueError("Phone number must contain between 6 and 15 digits")
        return value.strip()
