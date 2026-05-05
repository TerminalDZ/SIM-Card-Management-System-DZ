"""USSD schemas."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class UssdRequest(BaseModel):
    """Payload for executing a USSD command."""

    command: str = Field(min_length=2, max_length=64)

    @field_validator("command")
    @classmethod
    def _validate_command(cls, value: str) -> str:
        stripped = value.strip()
        if not (stripped.startswith("*") or stripped.startswith("#")):
            raise ValueError("USSD command must start with '*' or '#'")
        if not stripped.endswith("#"):
            raise ValueError("USSD command must end with '#'")
        return stripped


class UssdResponse(BaseModel):
    """Result of a USSD execution."""

    command: str
    modem_id: str | None = None
    response: str
    raw_response: str | None = None
    success: bool
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
