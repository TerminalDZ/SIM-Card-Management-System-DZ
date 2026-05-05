"""HTTP-level smoke tests using the real FastAPI app + ASGI transport."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok(app_client: AsyncClient) -> None:
    response = await app_client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint_returns_metadata(app_client: AsyncClient) -> None:
    response = await app_client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "name" in body and "version" in body and body["docs"] == "/docs"


@pytest.mark.asyncio
async def test_operators_endpoint_lists_all_operators(app_client: AsyncClient) -> None:
    response = await app_client.get("/api/operators")
    assert response.status_code == 200
    body = response.json()
    ids = {item["id"] for item in body}
    assert {"ooredoo_dz", "djezzy_dz", "mobilis_dz"} <= ids


@pytest.mark.asyncio
async def test_operator_lookup_404s_for_missing(app_client: AsyncClient) -> None:
    response = await app_client.get("/api/operators/unknown")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_legacy_endpoints_require_connected_modem(app_client: AsyncClient) -> None:
    response = await app_client.get("/api/status")
    # No modem connected by default → MODEM_NOT_FOUND (404)
    assert response.status_code == 404
    body = response.json()
    assert body["error_code"] == "MODEM_NOT_FOUND"


@pytest.mark.asyncio
async def test_performance_endpoint_returns_counters(app_client: AsyncClient) -> None:
    response = await app_client.get("/api/performance")
    assert response.status_code == 200
    body = response.json()
    assert body["connected_modems"] == 0
    assert body["websocket_clients"] == 0
    assert body["max_concurrent_modems"] >= 1
