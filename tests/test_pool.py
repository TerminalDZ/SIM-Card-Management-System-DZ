"""Tests for :class:`ModemPool` using fake detector + device factories."""

from __future__ import annotations

from typing import Any

import pytest

from app.config import Settings
from app.core.exceptions import ModemAlreadyConnectedError, ModemNotFoundError
from app.modem.detector import DetectedPort
from app.modem.pool import ModemPool
from app.operators.repository import OperatorRepository


class _FakeDetector:
    def __init__(self, detected: list[DetectedPort]) -> None:
        self._detected = detected
        self.calls = 0

    async def discover(self) -> list[DetectedPort]:
        self.calls += 1
        return list(self._detected)


class _FakeDevice:
    """Minimal stand-in for :class:`ModemDevice` to test the pool plumbing."""

    def __init__(self, modem_id: str, port: str) -> None:
        self.modem_id = modem_id
        self.port = port
        self.connected = False
        self.connected_at = None
        self.last_activity = None

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    async def status(self) -> Any:
        from app.schemas.modem import ModemStatus

        return ModemStatus(
            modem_id=self.modem_id,
            port=self.port,
            connected=self.connected,
        )


@pytest.fixture
def detected() -> list[DetectedPort]:
    return [
        DetectedPort(port="COM3", description="Huawei E3531", vendor_id=0x12D1, product_id=0x1F01),
        DetectedPort(port="COM4", description="Huawei E3372", vendor_id=0x12D1, product_id=0x14DC),
    ]


@pytest.fixture
def pool(
    settings: Settings,
    operators: OperatorRepository,
    detected: list[DetectedPort],
    monkeypatch: pytest.MonkeyPatch,
) -> ModemPool:
    pool = ModemPool(settings, operators, detector=_FakeDetector(detected))

    # Replace the real ModemDevice factory with a fake to avoid hardware.
    def _fake_device_factory(modem_id: str, port: str, **_: Any) -> _FakeDevice:
        return _FakeDevice(modem_id, port)

    from app.modem import pool as pool_module

    monkeypatch.setattr(pool_module, "ModemDevice", _fake_device_factory)
    return pool


@pytest.mark.asyncio
async def test_discover_populates_known_ports(
    pool: ModemPool, detected: list[DetectedPort]
) -> None:
    response = await pool.discover()
    assert response.total_detected == 2
    assert {m.port for m in response.detected} == {p.port for p in detected}


@pytest.mark.asyncio
async def test_connect_requires_prior_discovery(pool: ModemPool) -> None:
    with pytest.raises(ModemNotFoundError):
        await pool.connect("huawei_COM3")


@pytest.mark.asyncio
async def test_connect_returns_connected_device(pool: ModemPool) -> None:
    await pool.discover()
    device = await pool.connect("huawei_COM3")
    assert device.connected is True
    assert pool.connected_ids() == ["huawei_COM3"]


@pytest.mark.asyncio
async def test_double_connect_raises_conflict(pool: ModemPool) -> None:
    await pool.discover()
    await pool.connect("huawei_COM3")
    with pytest.raises(ModemAlreadyConnectedError):
        await pool.connect("huawei_COM3")


@pytest.mark.asyncio
async def test_disconnect_releases_device(pool: ModemPool) -> None:
    await pool.discover()
    await pool.connect("huawei_COM3")
    await pool.disconnect("huawei_COM3")
    assert pool.connected_ids() == []


@pytest.mark.asyncio
async def test_get_first_connected_returns_oldest(pool: ModemPool) -> None:
    await pool.discover()
    await pool.connect("huawei_COM3")
    await pool.connect("huawei_COM4")
    assert pool.first_connected().modem_id == "huawei_COM3"


@pytest.mark.asyncio
async def test_shutdown_clears_connections(pool: ModemPool) -> None:
    await pool.discover()
    await pool.connect("huawei_COM3")
    await pool.shutdown()
    assert pool.connected_ids() == []
