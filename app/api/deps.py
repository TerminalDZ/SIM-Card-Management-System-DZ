"""FastAPI dependency providers — kept thin so handlers stay testable."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.config import Settings
from app.modem.pool import ModemPool
from app.operators.repository import OperatorRepository
from app.ws.manager import WebSocketManager


def get_pool(request: Request) -> ModemPool:
    return request.app.state.pool  # type: ignore[no-any-return]


def get_operators(request: Request) -> OperatorRepository:
    return request.app.state.operators  # type: ignore[no-any-return]


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings  # type: ignore[no-any-return]


def get_ws_manager(request: Request) -> WebSocketManager:
    return request.app.state.ws_manager  # type: ignore[no-any-return]


PoolDep = Annotated[ModemPool, Depends(get_pool)]
OperatorsDep = Annotated[OperatorRepository, Depends(get_operators)]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
WsManagerDep = Annotated[WebSocketManager, Depends(get_ws_manager)]
