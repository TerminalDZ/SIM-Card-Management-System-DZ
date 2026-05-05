"""Legacy endpoints kept for backward compatibility.

They all act on the *first* connected modem so that pre-3.x clients keep
working. No new logic should land here — point new integrations to the
``/api/modems/...`` family instead.
"""

from __future__ import annotations

from fastapi import APIRouter, Path

from app.api.deps import PoolDep
from app.schemas.modem import ModemStatus
from app.schemas.response import SuccessResponse
from app.schemas.sim import SimInfo
from app.schemas.sms import SmsMessage, SmsSendRequest
from app.schemas.ussd import UssdRequest, UssdResponse

router = APIRouter(prefix="/api", tags=["Legacy"])


@router.get("/status", response_model=ModemStatus)
async def status(pool: PoolDep) -> ModemStatus:
    device = pool.first_connected()
    return await device.status()


@router.get("/sim-info", response_model=SimInfo)
async def sim_info(pool: PoolDep) -> SimInfo:
    device = pool.first_connected()
    return await device.sim_info()


@router.get("/sms", response_model=list[SmsMessage])
async def sms_list(pool: PoolDep) -> list[SmsMessage]:
    device = pool.first_connected()
    return await device.list_sms()


@router.post("/sms/send", response_model=SuccessResponse)
async def sms_send(payload: SmsSendRequest, pool: PoolDep) -> SuccessResponse:
    device = pool.first_connected()
    await device.send_sms(payload.number, payload.message)
    return SuccessResponse(
        message=f"SMS sent from {device.modem_id}",
        data={"modem_id": device.modem_id, "recipient": payload.number},
    )


@router.delete("/sms/{message_id}", response_model=SuccessResponse)
async def sms_delete(
    pool: PoolDep,
    message_id: int = Path(..., ge=0),
) -> SuccessResponse:
    device = pool.first_connected()
    await device.delete_sms(message_id)
    return SuccessResponse(
        message=f"SMS {message_id} deleted",
        data={"modem_id": device.modem_id, "message_id": message_id},
    )


@router.post("/ussd", response_model=UssdResponse)
async def ussd(payload: UssdRequest, pool: PoolDep) -> UssdResponse:
    device = pool.first_connected()
    return await device.send_ussd(payload.command)


@router.get("/balance", response_model=UssdResponse)
async def balance(pool: PoolDep) -> UssdResponse:
    device = pool.first_connected()
    return await device.get_balance()
