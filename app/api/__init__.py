"""HTTP routers wired into the FastAPI application."""

from app.api import legacy, modems, operators, system, ws

__all__ = ["legacy", "modems", "operators", "system", "ws"]
