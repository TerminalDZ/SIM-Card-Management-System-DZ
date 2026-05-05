"""Modem hardware layer.

The modem package is organised around clear, single-responsibility units:

* :mod:`encoders`  — GSM 7-bit / hex encoding helpers (pure functions).
* :mod:`transport` — async wrapper over a :class:`pyserial` connection.
* :mod:`at_client` — request/response semantics for AT commands.
* :mod:`detector`  — discovers Huawei modems on the system bus.
* :mod:`device`    — high-level operations on a single modem (status, SMS, USSD).
* :mod:`pool`      — manages many devices concurrently.
"""

from app.modem.detector import DetectedPort, ModemDetector
from app.modem.device import ModemDevice
from app.modem.pool import ModemPool

__all__ = ["DetectedPort", "ModemDetector", "ModemDevice", "ModemPool"]
