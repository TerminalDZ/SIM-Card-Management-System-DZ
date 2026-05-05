"""Operator profile schema — mirrors the JSON registry."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OperatorUssdCodes(BaseModel):
    """Service-specific USSD codes for an operator.

    ``balance`` is required because every supported operator can serve a
    balance query. Other services are optional.
    """

    balance: str
    data_balance: str | None = None
    recharge: str | None = None
    my_number: str | None = None
    call_forward: str | None = None
    call_forward_cancel: str | None = None


class OperatorApn(BaseModel):
    name: str
    apn: str
    username: str = ""
    password: str = ""
    auth_type: str = "none"


class OperatorProfile(BaseModel):
    """Mobile operator metadata used for detection and operations."""

    id: str
    name: str
    country: str
    country_code: str = Field(min_length=2, max_length=3)
    mcc: str = Field(min_length=3, max_length=3, pattern=r"^\d{3}$")
    mnc: list[str]
    imsi_prefixes: list[str]
    iccid_prefixes: list[str] = Field(default_factory=list)
    ussd: OperatorUssdCodes
    apn: OperatorApn

    def matches_imsi(self, imsi: str | None) -> bool:
        if not imsi:
            return False
        return any(imsi.startswith(prefix) for prefix in self.imsi_prefixes)

    def matches_iccid(self, iccid: str | None) -> bool:
        if not iccid:
            return False
        return any(iccid.startswith(prefix) for prefix in self.iccid_prefixes)
