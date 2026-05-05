"""Domain exceptions mapped to HTTP status codes.

A flat taxonomy is enough for this project — going deeper would add ceremony
without clearer error handling. Each exception carries a stable error code so
clients can switch on it instead of parsing free-form messages.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any


class SimManagerError(Exception):
    """Base class for all domain errors."""

    code: str = "SIM_MANAGER_ERROR"
    http_status: int = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, Any] = details or {}

    def to_payload(self) -> dict[str, Any]:
        return {
            "success": False,
            "error": self.message,
            "error_code": self.code,
            "details": self.details,
        }


# ── Hardware / transport ───────────────────────────────────────────────────────
class ModemDetectionError(SimManagerError):
    code = "MODEM_DETECTION_FAILED"
    http_status = HTTPStatus.SERVICE_UNAVAILABLE


class ModemNotFoundError(SimManagerError):
    code = "MODEM_NOT_FOUND"
    http_status = HTTPStatus.NOT_FOUND


class ModemAlreadyConnectedError(SimManagerError):
    code = "MODEM_ALREADY_CONNECTED"
    http_status = HTTPStatus.CONFLICT


class ModemNotConnectedError(SimManagerError):
    code = "MODEM_NOT_CONNECTED"
    http_status = HTTPStatus.SERVICE_UNAVAILABLE


class ModemLimitExceededError(SimManagerError):
    code = "MODEM_LIMIT_EXCEEDED"
    http_status = HTTPStatus.TOO_MANY_REQUESTS


class SerialTransportError(SimManagerError):
    code = "SERIAL_TRANSPORT_ERROR"
    http_status = HTTPStatus.SERVICE_UNAVAILABLE


# ── AT commands ───────────────────────────────────────────────────────────────
class ATCommandError(SimManagerError):
    code = "AT_COMMAND_FAILED"
    http_status = HTTPStatus.SERVICE_UNAVAILABLE


class ATCommandTimeoutError(ATCommandError):
    code = "AT_COMMAND_TIMEOUT"
    http_status = HTTPStatus.REQUEST_TIMEOUT


# ── SIM ────────────────────────────────────────────────────────────────────────
class SimCardError(SimManagerError):
    code = "SIM_CARD_ERROR"
    http_status = HTTPStatus.SERVICE_UNAVAILABLE


class SimCardNotReadyError(SimCardError):
    code = "SIM_CARD_NOT_READY"


# ── SMS ────────────────────────────────────────────────────────────────────────
class SmsError(SimManagerError):
    code = "SMS_ERROR"
    http_status = HTTPStatus.SERVICE_UNAVAILABLE


class SmsSendError(SmsError):
    code = "SMS_SEND_FAILED"


class SmsReadError(SmsError):
    code = "SMS_READ_FAILED"


class SmsDeleteError(SmsError):
    code = "SMS_DELETE_FAILED"


# ── USSD ───────────────────────────────────────────────────────────────────────
class UssdError(SimManagerError):
    code = "USSD_ERROR"
    http_status = HTTPStatus.SERVICE_UNAVAILABLE


class UssdTimeoutError(UssdError):
    code = "USSD_TIMEOUT"
    http_status = HTTPStatus.REQUEST_TIMEOUT


# ── Operator data ─────────────────────────────────────────────────────────────
class OperatorError(SimManagerError):
    code = "OPERATOR_ERROR"
    http_status = HTTPStatus.SERVICE_UNAVAILABLE


class OperatorNotFoundError(OperatorError):
    code = "OPERATOR_NOT_FOUND"
    http_status = HTTPStatus.NOT_FOUND


class OperatorRepositoryError(OperatorError):
    code = "OPERATOR_REPOSITORY_ERROR"
    http_status = HTTPStatus.INTERNAL_SERVER_ERROR


# ── Configuration ──────────────────────────────────────────────────────────────
class ConfigurationError(SimManagerError):
    code = "CONFIGURATION_ERROR"
    http_status = HTTPStatus.INTERNAL_SERVER_ERROR
