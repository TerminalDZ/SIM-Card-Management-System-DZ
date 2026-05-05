"""Shared enumerations used across multiple schemas."""

from __future__ import annotations

from enum import Enum


class NetworkType(str, Enum):
    """Cellular network technology, as advertised by the modem."""

    GSM = "2G"
    UMTS = "3G"
    LTE = "4G"
    NR = "5G"
    UNKNOWN = "Unknown"


class SmsStorageStatus(str, Enum):
    """SMS message status as returned by ``AT+CMGL``."""

    UNREAD = "REC UNREAD"
    READ = "REC READ"
    STORED_UNSENT = "STO UNSENT"
    STORED_SENT = "STO SENT"
