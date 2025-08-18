"""
Test configuration and fixtures for backend tests
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from core.modem_manager import ModemManager
from core.operator_manager import OperatorManager
from models.models import ModemStatus, SimInfo, SmsMessage, OperatorProfile

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def mock_modem_manager():
    """Mock ModemManager for testing"""
    mock = Mock(spec=ModemManager)
    mock.is_connected = Mock(return_value=True)
    mock.initialize = AsyncMock()
    mock.get_status = AsyncMock(return_value=ModemStatus(
        connected=True,
        port="COM3",
        model="E3531s",
        firmware="1.0.0",
        signal_strength=75,
        network_type="LTE",
        operator="Ooredoo Algeria"
    ))
    mock.get_sim_info = AsyncMock(return_value=SimInfo(
        imsi="60302123456789",
        iccid="8921302123456789012",
        imei="123456789012345",
        msisdn="0555123456",
        signal_strength=75,
        network_type="LTE",
        network_operator="Ooredoo Algeria"
    ))
    mock.get_sms_messages = AsyncMock(return_value=[])
    mock.send_sms = AsyncMock(return_value=True)
    mock.delete_sms = AsyncMock(return_value=True)
    mock.send_ussd = AsyncMock(return_value="Your balance is 100 DZD")
    return mock

@pytest.fixture
def mock_operator_manager():
    """Mock OperatorManager for testing"""
    mock = Mock(spec=OperatorManager)
    mock.detect_operator = Mock(return_value={
        "name": "Ooredoo Algeria",
        "country": "Algeria",
        "mcc": "603",
        "mnc": ["02"],
        "balance_ussd": "*223#",
        "data_balance_ussd": "*223*2#"
    })
    mock.get_all_operators = Mock(return_value=[
        {
            "name": "Ooredoo Algeria",
            "country": "Algeria",
            "mcc": "603",
            "mnc": ["02"],
            "balance_ussd": "*223#"
        }
    ])
    return mock

@pytest.fixture
def sample_sms_message():
    """Sample SMS message for testing"""
    return SmsMessage(
        id=1,
        status="REC UNREAD",
        phone_number="0555123456",
        message="Test message",
        timestamp="2024-01-01T12:00:00"
    )

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
