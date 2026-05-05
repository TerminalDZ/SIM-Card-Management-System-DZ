"""WebSocket connection manager and periodic broadcaster."""

from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from app.core.logger import get_logger
from app.modem.pool import ModemPool


class WebSocketManager:
    """Multiplex broadcasts to every connected websocket client."""

    def __init__(self, pool: ModemPool, *, broadcast_interval: int = 15) -> None:
        self._pool = pool
        self._broadcast_interval = broadcast_interval
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._broadcast_task: asyncio.Task[None] | None = None
        self._logger = get_logger("ws")

    @property
    def client_count(self) -> int:
        return len(self._connections)

    # ── Lifecycle ───────────────────────────────────────────────────────────
    async def start(self) -> None:
        if self._broadcast_task is None or self._broadcast_task.done():
            self._broadcast_task = asyncio.create_task(self._broadcast_loop(), name="ws-broadcast")

    async def stop(self) -> None:
        if self._broadcast_task is not None:
            self._broadcast_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._broadcast_task
            self._broadcast_task = None
        async with self._lock:
            for ws in list(self._connections):
                with contextlib.suppress(Exception):
                    await ws.close()
            self._connections.clear()

    # ── Connections ─────────────────────────────────────────────────────────
    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        self._logger.info("WebSocket connected (%d total)", len(self._connections))
        await self._send(
            websocket,
            {
                "type": "hello",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {"connected_clients": len(self._connections)},
            },
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        self._logger.info("WebSocket disconnected (%d remaining)", len(self._connections))

    async def serve(self, websocket: WebSocket) -> None:
        """Run the receive loop for *websocket*, returning on disconnect."""
        await self.connect(websocket)
        try:
            while True:
                # Treat any incoming text as a ping; reply pong.
                message = await websocket.receive_text()
                if message:
                    await self._send(websocket, {"type": "pong", "echo": message})
        except WebSocketDisconnect:
            pass
        finally:
            await self.disconnect(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        if not self._connections:
            return
        async with self._lock:
            recipients = list(self._connections)
        await asyncio.gather(
            *(self._send(ws, message) for ws in recipients),
            return_exceptions=True,
        )

    # ── Internals ───────────────────────────────────────────────────────────
    async def _broadcast_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self._broadcast_interval)
                if not self._connections:
                    continue
                try:
                    status = await self._pool.all_status()
                    await self.broadcast(
                        {
                            "type": "status_update",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "payload": status.model_dump(mode="json"),
                        }
                    )
                except Exception as exc:
                    self._logger.warning("Broadcast loop iteration failed: %s", exc)
        except asyncio.CancelledError:
            raise

    async def _send(self, websocket: WebSocket, payload: dict[str, Any]) -> None:
        try:
            await websocket.send_json(payload)
        except Exception as exc:
            self._logger.debug("Send to client failed, dropping: %s", exc)
            await self.disconnect(websocket)
