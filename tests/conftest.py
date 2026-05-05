"""Shared pytest fixtures and helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.core.logger import configure_logging
from app.modem.at_client import ATClient
from app.modem.transport import SerialTransport
from app.operators.repository import OperatorRepository

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        host="127.0.0.1",
        port=18000,
        debug=True,
        log_level="WARNING",
        log_file=None,
        operators_file=PROJECT_ROOT / "data" / "operators.json",
        auto_detect_on_startup=False,
        modem_read_timeout=1.0,
        modem_open_timeout=1.0,
        modem_command_retries=0,
        max_concurrent_modems=4,
    )


@pytest.fixture
def operators() -> OperatorRepository:
    return OperatorRepository.from_file(PROJECT_ROOT / "data" / "operators.json")


@pytest.fixture(autouse=True)
def _configure_logging(settings: Settings) -> None:
    configure_logging(settings)


# ── Fakes used in unit tests ────────────────────────────────────────────────
class FakeTransport(SerialTransport):
    """In-memory transport used by AT client / device tests."""

    def __init__(self, *, port: str = "FAKE", baudrate: int = 115200) -> None:
        super().__init__(port=port, baudrate=baudrate)
        self._opened = False
        self.script: list[bytes] = []
        self.last_writes: list[bytes] = []

    @property
    def is_open(self) -> bool:
        return self._opened

    async def open(self) -> None:
        self._opened = True

    async def close(self) -> None:
        self._opened = False

    async def write(self, data: bytes) -> None:
        if not self._opened:
            raise RuntimeError("Transport not open")
        self.last_writes.append(data)

    async def reset_input(self) -> None:
        return None

    async def read_until(self, terminators: tuple[bytes, ...], *, timeout: float) -> bytes:
        if not self.script:
            return b""
        return self.script.pop(0)


@pytest.fixture
def fake_transport() -> FakeTransport:
    return FakeTransport()


@pytest.fixture
def at_client(fake_transport: FakeTransport) -> ATClient:
    return ATClient(fake_transport, default_timeout=1.0, retries=0)


@pytest.fixture
async def app_client(settings: Settings) -> AsyncIterator[AsyncClient]:
    """Spin up the FastAPI app with mocked pool/operators for HTTP tests."""
    from app.main import create_app

    app = create_app(settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
