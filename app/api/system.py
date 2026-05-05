"""System-level endpoints: health and metrics."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import PoolDep, SettingsDep, WsManagerDep
from app.schemas.response import SuccessResponse

router = APIRouter(prefix="/api", tags=["System"])


@router.get("/health", response_model=SuccessResponse)
async def health(pool: PoolDep, settings: SettingsDep) -> SuccessResponse:
    """Lightweight health probe — used by Docker, Kubernetes and CI."""
    return SuccessResponse(
        message="ok",
        data={
            "status": "healthy",
            "version": settings.version,
            "connected_modems": len(pool.connected_ids()),
        },
    )


@router.get("/performance")
async def performance(pool: PoolDep, ws_manager: WsManagerDep, settings: SettingsDep) -> dict:
    """Snapshot of runtime counters for monitoring."""
    return {
        "version": settings.version,
        "connected_modems": len(pool.connected_ids()),
        "known_modems": len(pool.known_ports()),
        "websocket_clients": ws_manager.client_count,
        "max_concurrent_modems": settings.max_concurrent_modems,
    }
