"""FastAPI application factory.

Wires together settings, logging, the operator repository, the modem pool
and the WebSocket manager. Each component has its own module so this file
stays small and easy to follow.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api import legacy as legacy_api
from app.api import modems as modems_api
from app.api import operators as operators_api
from app.api import system as system_api
from app.api import ws as ws_api
from app.config import Settings, get_settings
from app.core.exceptions import SimManagerError
from app.core.logger import configure_logging, get_logger
from app.modem.pool import ModemPool
from app.operators.repository import OperatorRepository
from app.ws.manager import WebSocketManager


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure a :class:`FastAPI` instance."""
    settings = settings or get_settings()
    logger = configure_logging(settings)

    operators = OperatorRepository.from_file(settings.operators_file)
    pool = ModemPool(settings, operators)
    ws_manager = WebSocketManager(pool, broadcast_interval=settings.ws_broadcast_interval)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info(
            "Starting %s v%s on %s:%d",
            settings.title,
            settings.version,
            settings.host,
            settings.port,
        )
        if settings.auto_detect_on_startup:
            try:
                detection = await pool.discover()
                logger.info("Detected %d modem(s) at startup", detection.total_detected)
            except Exception as exc:
                logger.warning("Modem auto-detection failed: %s", exc)
        await ws_manager.start()
        try:
            yield
        finally:
            logger.info("Shutting down")
            await ws_manager.stop()
            await pool.shutdown()

    app = FastAPI(
        title=settings.title,
        version=settings.version,
        description=settings.description,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.state.settings = settings
    app.state.operators = operators
    app.state.pool = pool
    app.state.ws_manager = ws_manager

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _install_exception_handlers(app)

    app.include_router(system_api.router)
    app.include_router(operators_api.router)
    app.include_router(modems_api.router)
    app.include_router(legacy_api.router)
    app.include_router(ws_api.router)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "name": settings.title,
            "version": settings.version,
            "docs": "/docs",
        }

    return app


def _install_exception_handlers(app: FastAPI) -> None:
    logger = get_logger("api")

    @app.exception_handler(SimManagerError)
    async def domain_error_handler(_: Request, exc: SimManagerError) -> JSONResponse:
        return JSONResponse(status_code=exc.http_status, content=exc.to_payload())

    @app.exception_handler(ValidationError)
    async def validation_handler(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "details": {"errors": exc.errors()},
            },
        )

    @app.exception_handler(Exception)
    async def unexpected_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "details": {"exception": exc.__class__.__name__},
            },
        )


# Eager singleton for `uvicorn app.main:app`
app = create_app()
