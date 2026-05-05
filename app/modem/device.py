"""High-level operations on a single modem device.

This is the only place the rest of the system needs to know about. It
composes a transport, an AT client and the operator repository to expose a
clean ``ModemDevice`` API.

The class is deliberately *thin*: each public method maps to a single user
intent (status, SIM info, send SMS, run USSD…). Parsing helpers and AT
configuration sequences are kept as private methods to keep the surface
focused.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import re
from datetime import datetime, timezone
from typing import Final

from app.config import Settings
from app.core.exceptions import (
    ATCommandError,
    ModemNotConnectedError,
    SimCardNotReadyError,
    SmsDeleteError,
    SmsReadError,
    SmsSendError,
    UssdError,
)
from app.core.logger import get_logger, timed_operation
from app.modem.at_client import ATClient, ATResponse
from app.modem.encoders import from_hex_septets, from_ucs2_hex, sanitize_ussd, to_hex_septets
from app.modem.transport import SerialTransport
from app.operators.repository import OperatorRepository
from app.schemas.enums import NetworkType, SmsStorageStatus
from app.schemas.modem import ModemHealth, ModemStatus
from app.schemas.sim import SimInfo
from app.schemas.sms import SmsMessage
from app.schemas.ussd import UssdResponse

# ── Configuration applied once after connect ─────────────────────────────────
_CONFIG_SEQUENCE: Final[tuple[tuple[str, str], ...]] = (
    ("ATZ", "Soft reset"),
    ("ATE0", "Disable echo"),
    ("AT+CMEE=2", "Verbose error reporting"),
    ("AT+CMGF=1", "SMS text mode"),
    ('AT+CSCS="UCS2"', "Use UCS-2 encoding for SMS"),
    ("AT+CNMI=2,1,0,0,0", "Configure SMS notifications"),
    ('AT+CPMS="SM","SM","SM"', "Use SIM storage for SMS"),
)


# Regex helpers
_RE_CSQ = re.compile(r"\+CSQ:\s*(\d+),(\d+)")
_RE_COPS = re.compile(r'\+COPS:\s*(\d+),(\d+),"([^"]*)"(?:,(\d+))?')
_RE_CREG = re.compile(r"\+C(?:E|G)?REG:\s*\d+,(\d+)(?:,.*?)?(?:,(\d+))?")
_RE_CMGL_HEADER = re.compile(r'\+CMGL:\s*(\d+),"([^"]+)","([^"]+)",("[^"]*")?,"([^"]*)"')


class ModemDevice:
    """A connected modem with its identity, status, SMS and USSD capabilities."""

    def __init__(
        self,
        modem_id: str,
        port: str,
        *,
        settings: Settings,
        operators: OperatorRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self.modem_id = modem_id
        self.port = port
        self._settings = settings
        self._operators = operators
        self._logger = logger or get_logger(f"device.{modem_id}")

        self._transport = SerialTransport(
            port=port,
            baudrate=settings.modem_baudrate,
            open_timeout=settings.modem_open_timeout,
            read_timeout=0.05,
            logger=self._logger,
        )
        self._client = ATClient(
            self._transport,
            default_timeout=settings.modem_read_timeout,
            retries=settings.modem_command_retries,
            logger=self._logger,
        )

        # Identity (filled at connect time)
        self.model: str | None = None
        self.firmware: str | None = None
        self.imei: str | None = None
        self.connected_at: datetime | None = None
        self.last_activity: datetime | None = None
        self.last_error: str | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    @property
    def connected(self) -> bool:
        return self._transport.is_open

    async def connect(self) -> None:
        if self.connected:
            return
        with timed_operation(self._logger, "modem.connect", port=self.port):
            await self._transport.open()
            try:
                await self._client.execute("AT", timeout=3.0)
                await self._configure()
                await self._read_identity()
                self.connected_at = datetime.now(timezone.utc)
                self.last_activity = self.connected_at
                self.last_error = None
            except Exception:
                await self._transport.close()
                raise

    async def disconnect(self) -> None:
        if not self.connected:
            return
        await self._transport.close()
        self.connected_at = None

    # ── Status ───────────────────────────────────────────────────────────────
    async def status(self) -> ModemStatus:
        self._ensure_connected()
        with timed_operation(self._logger, "modem.status"):
            health = await self._read_health()
            self._touch()
            return ModemStatus(
                modem_id=self.modem_id,
                port=self.port,
                connected=True,
                model=self.model,
                firmware=self.firmware,
                imei=self.imei,
                health=health,
                connected_at=self.connected_at,
                last_activity=self.last_activity,
                last_error=self.last_error,
            )

    # ── SIM info ─────────────────────────────────────────────────────────────
    async def sim_info(self) -> SimInfo:
        self._ensure_connected()
        with timed_operation(self._logger, "modem.sim_info"):
            await self._ensure_sim_ready()

            imsi = await self._first_payload("AT+CIMI")
            iccid = await self._first_payload("AT+CCID") or await self._first_payload(
                "AT+CRSM=176,12258,0,0,10"
            )
            imei = await self._first_payload("AT+CGSN") or self.imei

            msisdn: str | None = None
            cnum = await self._client.execute_optional("AT+CNUM")
            if cnum is not None:
                for line in cnum.lines:
                    match = re.search(r'\+CNUM:\s*"[^"]*","([^"]+)"', line)
                    if match:
                        msisdn = match.group(1)
                        break

            health = await self._read_health()
            operator = self._operators.match(imsi=imsi, iccid=iccid)

            self._touch()
            return SimInfo(
                modem_id=self.modem_id,
                imsi=imsi,
                iccid=iccid,
                imei=imei,
                msisdn=msisdn,
                operator_id=operator.id if operator else None,
                operator_name=operator.name if operator else health.operator,
                network_operator=health.operator,
                signal_strength=health.signal_strength,
                network_type=health.network_type,
                roaming=health.roaming,
            )

    # ── SMS ──────────────────────────────────────────────────────────────────
    async def list_sms(self) -> list[SmsMessage]:
        self._ensure_connected()
        with timed_operation(self._logger, "modem.list_sms"):
            await self._client.execute("AT+CMGF=1")
            await self._client.execute('AT+CSCS="UCS2"')
            try:
                response = await self._client.execute('AT+CMGL="ALL"', timeout=20.0)
            except ATCommandError as exc:
                raise SmsReadError(f"Failed to read SMS storage: {exc.message}") from exc
            self._touch()
            return list(_parse_cmgl(response, modem_id=self.modem_id))

    async def send_sms(self, number: str, message: str) -> bool:
        self._ensure_connected()
        with timed_operation(self._logger, "modem.send_sms", recipient=number):
            await self._ensure_sim_ready()
            await self._client.execute("AT+CMGF=1")
            await self._client.execute('AT+CSCS="UCS2"')

            recipient_hex = to_ucs2_hex(_normalize_msisdn(number))
            body_hex = to_ucs2_hex(message)

            # When sending in UCS2 we must announce the data coding scheme
            await self._client.execute("AT+CSMP=17,167,0,8")
            try:
                response = await self._client.execute_raw_then_read(
                    f'AT+CMGS="{recipient_hex}"',
                    body_hex.encode("ascii") + b"\x1a",
                    timeout=45.0,
                )
            except ATCommandError as exc:
                raise SmsSendError(f"SMS send failed: {exc.message}", details=exc.details) from exc
            if not response.ok:
                raise SmsSendError(
                    f"Modem rejected SMS send: {response.status}",
                    details={"raw": response.raw},
                )
            self._touch()
            return True

    async def delete_sms(self, message_id: int) -> bool:
        self._ensure_connected()
        with timed_operation(self._logger, "modem.delete_sms", id=message_id):
            try:
                await self._client.execute(f"AT+CMGD={message_id}")
            except ATCommandError as exc:
                raise SmsDeleteError(f"Failed to delete SMS {message_id}: {exc.message}") from exc
            self._touch()
            return True

    # ── USSD ─────────────────────────────────────────────────────────────────
    async def send_ussd(self, command: str) -> UssdResponse:
        self._ensure_connected()
        with timed_operation(self._logger, "modem.send_ussd", command=command):
            sanitized = sanitize_ussd(command)
            if not sanitized:
                raise UssdError("Empty USSD command")
            with contextlib.suppress(ATCommandError):
                await self._client.execute('AT+CSCS="GSM"')
            encoded = to_hex_septets(sanitized)
            try:
                response = await self._client.execute(
                    f'AT+CUSD=1,"{encoded}",15',
                    timeout=30.0,
                )
            except ATCommandError as exc:
                raise UssdError(f"USSD failed: {exc.message}", details=exc.details) from exc
            text = _extract_cusd(response)
            if text is None:
                raise UssdError(
                    "Modem did not return a +CUSD response", details={"raw": response.raw}
                )
            self._touch()
            return UssdResponse(
                command=command,
                modem_id=self.modem_id,
                response=text,
                raw_response=response.raw,
                success=True,
            )

    async def get_balance(self) -> UssdResponse:
        """Run the operator-specific balance USSD and return the result."""
        sim = await self.sim_info()
        operator = None
        if sim.operator_id:
            operator = self._operators.get(sim.operator_id)
        if operator is None:
            operator = self._operators.match(imsi=sim.imsi, iccid=sim.iccid)
        if operator is None:
            raise UssdError(
                "No operator profile matched this SIM — cannot resolve balance USSD",
                details={"imsi": sim.imsi, "iccid": sim.iccid},
            )
        return await self.send_ussd(operator.ussd.balance)

    # ── Internals ────────────────────────────────────────────────────────────
    async def _configure(self) -> None:
        for command, label in _CONFIG_SEQUENCE:
            self._logger.debug("Configure: %s (%s)", command, label)
            await self._client.execute_optional(command, timeout=5.0)
        # APN — best effort, only if not already set
        apn_command = f'AT+CGDCONT=1,"IP","{self._settings.modem_default_apn}"'
        await self._client.execute_optional(apn_command, timeout=5.0)

    async def _read_identity(self) -> None:
        async def first_line(command: str) -> str | None:
            return await self._first_payload(command)

        self.model, self.firmware, self.imei = await asyncio.gather(
            first_line("AT+CGMM"),
            first_line("AT+CGMR"),
            first_line("AT+CGSN"),
        )

    async def _read_health(self) -> ModemHealth:
        signal: int | None = None
        rssi: int | None = None
        operator: str | None = None
        registered = False
        roaming = False
        network = NetworkType.UNKNOWN

        csq = await self._client.execute_optional("AT+CSQ", timeout=3.0)
        if csq is not None:
            match = _search_lines(_RE_CSQ, csq.lines)
            if match is not None:
                rssi_raw = int(match.group(1))
                if rssi_raw != 99:
                    signal = min(100, int((rssi_raw / 31.0) * 100))
                    rssi = -113 + 2 * rssi_raw

        cops = await self._client.execute_optional("AT+COPS?", timeout=3.0)
        if cops is not None:
            match = _search_lines(_RE_COPS, cops.lines)
            if match is not None:
                roaming = match.group(1) == "2"
                operator = match.group(3)
                act = match.group(4)
                network = _map_act(act)

        creg = await self._client.execute_optional("AT+CREG?", timeout=3.0)
        if creg is not None:
            match = _search_lines(_RE_CREG, creg.lines)
            if match is not None:
                stat = int(match.group(1))
                registered = stat in {1, 5}
                if not roaming:
                    roaming = stat == 5

        return ModemHealth(
            signal_strength=signal,
            rssi_dbm=rssi,
            network_type=network,
            operator=operator,
            registered=registered,
            roaming=roaming,
        )

    async def _ensure_sim_ready(self) -> None:
        cpin = await self._client.execute_optional("AT+CPIN?", timeout=5.0)
        if cpin is None:
            raise SimCardNotReadyError("Could not query SIM state")
        if not any("READY" in line for line in cpin.lines):
            raise SimCardNotReadyError(
                "SIM card not READY",
                details={"raw": cpin.raw},
            )

    async def _first_payload(self, command: str) -> str | None:
        response = await self._client.execute_optional(command, timeout=5.0)
        if response is None:
            return None
        for line in response.lines:
            if line in {"OK", "ERROR", command}:
                continue
            if line.startswith("+CME") or line.startswith("+CMS"):
                continue
            if line.startswith("+CCID:"):
                return line.split(":", 1)[1].strip().strip('"')
            if line.startswith("AT"):
                continue
            return line.strip().strip('"')
        return None

    def _ensure_connected(self) -> None:
        if not self.connected:
            raise ModemNotConnectedError(
                f"Modem {self.modem_id} is not connected",
                details={"modem_id": self.modem_id},
            )

    def _touch(self) -> None:
        self.last_activity = datetime.now(timezone.utc)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _search_lines(pattern: re.Pattern[str], lines: list[str]) -> re.Match[str] | None:
    for line in lines:
        match = pattern.search(line)
        if match is not None:
            return match
    return None


def _map_act(act: str | None) -> NetworkType:
    """Map ``AT+COPS?`` access-technology codes to our enum."""
    if act is None:
        return NetworkType.UNKNOWN
    return {
        "0": NetworkType.GSM,
        "1": NetworkType.GSM,
        "2": NetworkType.UMTS,
        "3": NetworkType.UMTS,
        "4": NetworkType.UMTS,
        "5": NetworkType.UMTS,
        "6": NetworkType.UMTS,
        "7": NetworkType.LTE,
        "8": NetworkType.LTE,
        "12": NetworkType.NR,
        "13": NetworkType.NR,
    }.get(act, NetworkType.UNKNOWN)


def _normalize_msisdn(number: str) -> str:
    return number.strip().replace(" ", "")


def to_ucs2_hex(text: str) -> str:
    return text.encode("utf-16-be").hex().upper()


def _extract_cusd(response: ATResponse) -> str | None:
    for line in response.lines:
        if not line.startswith("+CUSD:"):
            continue
        # Two formats: status,"<text>",dcs   OR   status
        match = re.match(r'\+CUSD:\s*(\d+)(?:,"([^"]*)"(?:,(\d+))?)?', line)
        if match is None:
            continue
        text = match.group(2) or ""
        dcs_raw = match.group(3)
        dcs = int(dcs_raw) if dcs_raw is not None and dcs_raw.isdigit() else 0
        if not text:
            return ""
        # Heuristic: UCS-2 if alphabet bits 2-3 of DCS are 01 (i.e. dcs & 0x0C == 0x08)
        if (dcs & 0x0C) == 0x08:
            return from_ucs2_hex(text)
        # Otherwise, decode hex septets if the text is hex
        if re.fullmatch(r"[0-9A-Fa-f]+", text):
            return from_hex_septets(text)
        return text
    return None


def _parse_cmgl(response: ATResponse, *, modem_id: str):
    """Yield :class:`SmsMessage` from a ``+CMGL`` response in text/UCS2 mode."""
    lines = response.lines
    i = 0
    while i < len(lines):
        line = lines[i]
        match = _RE_CMGL_HEADER.search(line)
        if match is None:
            i += 1
            continue
        try:
            msg_id = int(match.group(1))
            status = SmsStorageStatus(match.group(2))
        except (ValueError, KeyError):
            i += 1
            continue

        sender_raw = match.group(3)
        sender = from_ucs2_hex(sender_raw) if _looks_hex(sender_raw) else sender_raw
        ts_raw = match.group(5)
        timestamp = _parse_timestamp(ts_raw)

        body_raw = lines[i + 1] if i + 1 < len(lines) else ""
        body = from_ucs2_hex(body_raw) if _looks_hex(body_raw) else body_raw
        yield SmsMessage(
            id=msg_id,
            modem_id=modem_id,
            status=status,
            phone_number=sender,
            message=body,
            timestamp=timestamp,
            raw_header=line,
        )
        i += 2


def _looks_hex(value: str) -> bool:
    return bool(value) and len(value) % 2 == 0 and all(c in "0123456789ABCDEFabcdef" for c in value)


def _parse_timestamp(value: str) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.strptime(value, "%y/%m/%d,%H:%M:%S%z")
    except ValueError:
        try:
            return datetime.strptime(value[:17], "%y/%m/%d,%H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return datetime.now(timezone.utc)
