"""Generic API response envelopes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_code: str | None = None
    details: dict[str, Any] | None = Field(default=None)
