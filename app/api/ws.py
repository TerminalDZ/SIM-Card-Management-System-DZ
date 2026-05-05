"""WebSocket endpoint for real-time updates."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    # FastAPI's HTTP-style ``Depends(...)`` doesn't bind ``Request`` for
    # WebSocket routes, so resolve the WebSocket manager from app state
    # directly. Keeps the rest of the deps module HTTP-only.
    manager = websocket.app.state.ws_manager
    await manager.serve(websocket)
