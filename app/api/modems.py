"""Modem-centric endpoints — discovery, lifecycle, and per-modem operations."""

from __future__ import annotations

from fastapi import APIRouter, Path, status
from pydantic import BaseModel, Field

from app.api.deps import PoolDep
from app.schemas.modem import ModemDetectionResponse, ModemStatus, MultiModemStatus
from app.schemas.response import SuccessResponse
from app.schemas.sim import SimInfo
from app.schemas.sms import SmsMessage, SmsSendRequest
from app.schemas.ussd import UssdRequest, UssdResponse

router = APIRouter(prefix="/api/modems", tags=["Multi-Modem"])


class ModemIdRequest(BaseModel):
    modem_id: str = Field(min_length=1, examples=["huawei_COM3"])


# ── Discovery / lifecycle ─────────────────────────────────────────────────────
@router.post(
    "/detect",
    response_model=ModemDetectionResponse,
    summary="Detect every Huawei modem currently attached",
)
async def detect(pool: PoolDep) -> ModemDetectionResponse:
    return await pool.discover()


@router.post(
    "/connect",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Connect and configure a specific modem",
)
async def connect_modem(payload: ModemIdRequest, pool: PoolDep) -> SuccessResponse:
    device = await pool.connect(payload.modem_id)
    return SuccessResponse(
        message=f"Connected to modem {payload.modem_id}",
        data={
            "modem_id": device.modem_id,
            "port": device.port,
            "model": device.model,
            "imei": device.imei,
            "connected_modems": len(pool.connected_ids()),
        },
    )


@router.post(
    "/disconnect",
    response_model=SuccessResponse,
    summary="Release the connection to a modem",
)
async def disconnect_modem(payload: ModemIdRequest, pool: PoolDep) -> SuccessResponse:
    await pool.disconnect(payload.modem_id)
    return SuccessResponse(
        message=f"Disconnected modem {payload.modem_id}",
        data={"connected_modems": len(pool.connected_ids())},
    )


@router.get("/status", response_model=MultiModemStatus, summary="Aggregate status of all modems")
async def all_status(pool: PoolDep) -> MultiModemStatus:
    return await pool.all_status()


# ── Per-modem operations ──────────────────────────────────────────────────────
ModemId = Path(..., min_length=1, description="Modem identifier as returned by /detect")


@router.get("/{modem_id}/status", response_model=ModemStatus)
async def modem_status(modem_id: str = ModemId, *, pool: PoolDep) -> ModemStatus:
    device = await pool.get(modem_id, auto_connect=True)
    return await device.status()


@router.get("/{modem_id}/sim-info", response_model=SimInfo)
async def modem_sim_info(modem_id: str = ModemId, *, pool: PoolDep) -> SimInfo:
    device = await pool.get(modem_id, auto_connect=True)
    return await device.sim_info()


@router.get("/{modem_id}/sms", response_model=list[SmsMessage])
async def modem_sms_list(modem_id: str = ModemId, *, pool: PoolDep) -> list[SmsMessage]:
    device = await pool.get(modem_id, auto_connect=True)
    return await device.list_sms()


@router.post("/{modem_id}/sms/send", response_model=SuccessResponse)
async def modem_sms_send(
    payload: SmsSendRequest,
    modem_id: str = ModemId,
    *,
    pool: PoolDep,
) -> SuccessResponse:
    device = await pool.get(modem_id, auto_connect=True)
    await device.send_sms(payload.number, payload.message)
    return SuccessResponse(
        message=f"SMS sent from {modem_id}",
        data={"modem_id": modem_id, "recipient": payload.number},
    )


@router.delete("/{modem_id}/sms/{message_id}", response_model=SuccessResponse)
async def modem_sms_delete(
    modem_id: str = ModemId,
    message_id: int = Path(..., ge=0),
    *,
    pool: PoolDep,
) -> SuccessResponse:
    device = await pool.get(modem_id, auto_connect=True)
    await device.delete_sms(message_id)
    return SuccessResponse(
        message=f"SMS {message_id} deleted from {modem_id}",
        data={"modem_id": modem_id, "message_id": message_id},
    )


@router.post("/{modem_id}/ussd", response_model=UssdResponse)
async def modem_ussd(
    payload: UssdRequest,
    modem_id: str = ModemId,
    *,
    pool: PoolDep,
) -> UssdResponse:
    device = await pool.get(modem_id, auto_connect=True)
    return await device.send_ussd(payload.command)


@router.get("/{modem_id}/balance", response_model=UssdResponse)
async def modem_balance(modem_id: str = ModemId, *, pool: PoolDep) -> UssdResponse:
    device = await pool.get(modem_id, auto_connect=True)
    return await device.get_balance()
