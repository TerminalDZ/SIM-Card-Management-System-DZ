"""Unit tests for :class:`ATClient` against an in-memory transport."""

from __future__ import annotations

import pytest

from app.core.exceptions import ATCommandError, ATCommandTimeoutError
from app.modem.at_client import ATClient
from tests.conftest import FakeTransport


@pytest.mark.asyncio
async def test_execute_returns_parsed_ok_response(
    at_client: ATClient, fake_transport: FakeTransport
) -> None:
    fake_transport.script = [b"AT\r\n\r\nOK\r\n"]
    await fake_transport.open()
    response = await at_client.execute("AT")
    assert response.ok
    assert response.status == "OK"
    assert "OK" in response.lines


@pytest.mark.asyncio
async def test_execute_raises_on_modem_error(fake_transport: FakeTransport) -> None:
    client = ATClient(fake_transport, default_timeout=1.0, retries=0)
    fake_transport.script = [b"\r\n+CME ERROR: 13\r\n"]
    await fake_transport.open()
    with pytest.raises(ATCommandError) as exc:
        await client.execute("AT+CPIN?")
    assert "13" in str(exc.value)


@pytest.mark.asyncio
async def test_execute_raises_timeout_when_buffer_empty(fake_transport: FakeTransport) -> None:
    client = ATClient(fake_transport, default_timeout=0.1, retries=0)
    fake_transport.script = [b""]
    await fake_transport.open()
    with pytest.raises(ATCommandTimeoutError):
        await client.execute("AT")


@pytest.mark.asyncio
async def test_execute_optional_returns_none_on_failure(fake_transport: FakeTransport) -> None:
    client = ATClient(fake_transport, default_timeout=0.1, retries=0)
    fake_transport.script = [b"\r\nERROR\r\n"]
    await fake_transport.open()
    assert await client.execute_optional("AT+UNKNOWN") is None


@pytest.mark.asyncio
async def test_execute_retries_until_success(fake_transport: FakeTransport) -> None:
    client = ATClient(fake_transport, default_timeout=0.1, retries=1)
    fake_transport.script = [b"", b"\r\nOK\r\n"]
    await fake_transport.open()
    response = await client.execute("AT")
    assert response.ok
