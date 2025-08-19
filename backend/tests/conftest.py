"""
Test configuration and fixtures for the Multi-Modem SIM Card Management System.

This module provides pytest configuration, fixtures, and test utilities
for the multi-modem system testing.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from core.logger import SimManagerLogger
from core.exceptions import SimManagerException
from config import get_settings
from models.models import (
    ModemStatus, SimInfo, SmsMessage, UssdResponse, NetworkType, SmsStatus,
    ModemInfo, MultiModemStatus, ModemDetectionResponse
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings():
    """Provide test settings."""
    return get_settings()


@pytest.fixture
def logger(settings):
    """Provide test logger."""
    return SimManagerLogger(settings)


@pytest.fixture
def mock_modem_status():
    """Provide a mock modem status."""
    return ModemStatus(
        connected=True,
        modem_id="huawei_COM1",
        port="COM1",
        model="E3531s",
        firmware="1.0.0",
        signal_strength=75,
        network_type=NetworkType.LTE,
        operator="Ooredoo Algeria"
    )


@pytest.fixture
def mock_sim_info():
    """Provide a mock SIM info."""
    return SimInfo(
        modem_id="huawei_COM1",
        imsi="603021234567890",
        iccid="8921302123456789012",
        imei="123456789012345",
        msisdn="0555123456",
        operator_name="Ooredoo Algeria",
        signal_strength=75,
        network_type=NetworkType.LTE,
        roaming=False
    )


@pytest.fixture
def mock_sms_message():
    """Provide a mock SMS message."""
    return SmsMessage(
        id=1,
        modem_id="huawei_COM1",
        status=SmsStatus.UNREAD,
        phone_number="+213555123456",
        message="Test SMS message",
        timestamp="2024-01-01T12:00:00Z"
    )


@pytest.fixture
def mock_ussd_response():
    """Provide a mock USSD response."""
    return UssdResponse(
        command="*223#",
        modem_id="huawei_COM1",
        response="Your balance is 100 DZD",
        success=True,
        timestamp="2024-01-01T12:00:00Z"
    )


@pytest.fixture
def mock_modem_info():
    """Provide a mock modem info."""
    return ModemInfo(
        modem_id="huawei_COM1",
        port="COM1",
        connected_at="2024-01-01T12:00:00Z",
        last_activity="2024-01-01T12:05:00Z"
    )


@pytest.fixture
def mock_multi_modem_status(mock_modem_status):
    """Provide a mock multi-modem status."""
    return MultiModemStatus(
        total_modems=2,
        connected_modems=1,
        modems={
            "huawei_COM1": mock_modem_status,
            "huawei_COM2": ModemStatus(
                connected=False,
                modem_id="huawei_COM2",
                port="COM2",
                error="Not connected"
            )
        }
    )


@pytest.fixture
def mock_modem_detection_response():
    """Provide a mock modem detection response."""
    return ModemDetectionResponse(
        detected_modems=["huawei_COM1", "huawei_COM2"],
        connected_modems=["huawei_COM1"],
        total_detected=2,
        total_connected=1
    )


@pytest.fixture
def mock_serial_port():
    """Provide a mock serial port."""
    mock_port = Mock()
    mock_port.device = "COM1"
    mock_port.description = "Huawei E3531s"
    mock_port.vid = 0x12d1
    mock_port.pid = 0x1f01
    return mock_port


@pytest.fixture
def mock_serial_connection():
    """Provide a mock serial connection."""
    mock_conn = Mock()
    mock_conn.is_open = True
    mock_conn.in_waiting = 0
    mock_conn.reset_input_buffer = Mock()
    mock_conn.write = Mock()
    mock_conn.readline = Mock()
    mock_conn.close = Mock()
    return mock_conn


@pytest.fixture
def mock_modem_manager():
    """Provide a mock modem manager."""
    mock_manager = Mock()
    mock_manager.is_initialized = True
    mock_manager.port = "COM1"
    mock_manager.model = "E3531s"
    mock_manager.firmware = "1.0.0"
    mock_manager.imei = "123456789012345"
    
    # Mock async methods
    mock_manager.get_status = AsyncMock()
    mock_manager.get_sim_info = AsyncMock()
    mock_manager.get_sms_messages = AsyncMock()
    mock_manager.send_sms = AsyncMock()
    mock_manager.delete_sms = AsyncMock()
    mock_manager.send_ussd = AsyncMock()
    mock_manager.get_balance = AsyncMock()
    mock_manager.close = Mock()
    
    return mock_manager


@pytest.fixture
def mock_multi_modem_manager():
    """Provide a mock multi-modem manager."""
    mock_manager = Mock()
    
    # Mock properties
    mock_manager.modems = {}
    mock_manager.modem_info = {}
    mock_manager.active_modem_ids = []
    
    # Mock async methods
    mock_manager.detect_modems = AsyncMock()
    mock_manager.connect_modem = AsyncMock()
    mock_manager.disconnect_modem = AsyncMock()
    mock_manager.get_all_modems_status = AsyncMock()
    mock_manager.get_modem_status = AsyncMock()
    mock_manager.get_modem_sim_info = AsyncMock()
    mock_manager.get_modem_sms = AsyncMock()
    mock_manager.send_modem_sms = AsyncMock()
    mock_manager.delete_modem_sms = AsyncMock()
    mock_manager.send_modem_ussd = AsyncMock()
    mock_manager.get_modem_balance = AsyncMock()
    mock_manager.cleanup = AsyncMock()
    
    # Mock sync methods
    mock_manager.get_connected_modems = Mock()
    mock_manager.get_modem_info = Mock()
    mock_manager.get_performance_stats = Mock()
    
    return mock_manager


@pytest.fixture
def mock_operator_manager():
    """Provide a mock operator manager."""
    mock_manager = Mock()
    
    # Mock properties
    mock_manager.operators = {}
    
    # Mock methods
    mock_manager.detect_operator = Mock()
    mock_manager.get_operator_by_name = Mock()
    mock_manager.get_operator_by_mcc_mnc = Mock()
    mock_manager.get_operators_by_country = Mock()
    mock_manager.get_supported_operators = Mock()
    mock_manager.get_ussd_code = Mock()
    mock_manager.get_apn_settings = Mock()
    mock_manager.add_operator = Mock()
    mock_manager.remove_operator = Mock()
    mock_manager.update_operator = Mock()
    mock_manager.get_statistics = Mock()
    mock_manager.validate_operator_profile = Mock()
    
    return mock_manager


@pytest.fixture
def mock_websocket():
    """Provide a mock WebSocket connection."""
    mock_ws = Mock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.receive_text = AsyncMock()
    return mock_ws


@pytest.fixture
def test_settings():
    """Provide test-specific settings."""
    return {
        "HOST": "127.0.0.1",
        "PORT": 8000,
        "DEBUG": True,
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE": "test.log",
        "LOG_MAX_SIZE": 1024 * 1024,
        "LOG_BACKUP_COUNT": 3,
        "MODEM_BAUDRATE": 115200,
        "MODEM_TIMEOUT": 5,
        "MODEM_OPERATION_TIMEOUT": 10,
        "MAX_CONCURRENT_MODEMS": 5,
        "API_TITLE": "Test Multi-Modem SIM Card Management System",
        "API_VERSION": "1.0.0",
        "API_DESCRIPTION": "Test API for multi-modem management",
        "WS_HEARTBEAT_INTERVAL": 30
    }


@pytest.fixture
def mock_exception():
    """Provide a mock exception."""
    return SimManagerException(
        message="Test error message",
        error_code="TEST_ERROR",
        details={"test": "data"}
    )


@pytest.fixture
def mock_validation_error():
    """Provide a mock validation error."""
    from pydantic import ValidationError
    
    mock_error = Mock(spec=ValidationError)
    mock_error.errors = lambda: [{"loc": ("field",), "msg": "Validation error", "type": "value_error"}]
    return mock_error


@pytest.fixture
def mock_request():
    """Provide a mock FastAPI request."""
    mock_req = Mock()
    mock_req.url = Mock()
    mock_req.url.path = "/api/test"
    mock_req.method = "GET"
    mock_req.headers = {"user-agent": "test-agent"}
    return mock_req


@pytest.fixture
def test_data():
    """Provide test data for various scenarios."""
    return {
        "valid_phone_numbers": [
            "+213555123456",
            "0555123456",
            "213555123456",
            "555123456"
        ],
        "invalid_phone_numbers": [
            "123",
            "abcdef",
            "+1234567890123456",  # Too long
            ""
        ],
        "valid_ussd_commands": [
            "*223#",
            "*100*123456#",
            "*101*2#"
        ],
        "invalid_ussd_commands": [
            "223",
            "*223",
            "223#",
            "abc"
        ],
        "valid_imsi": [
            "603021234567890",
            "603031234567890"
        ],
        "invalid_imsi": [
            "123",
            "abcdef",
            "60302123456789",  # Too short
            "6030212345678901"  # Too long
        ],
        "valid_iccid": [
            "8921302123456789012",
            "8921303123456789012"
        ],
        "invalid_iccid": [
            "123",
            "abcdef",
            "892130212345678901",  # Too short
            "89213021234567890123"  # Too long
        ]
    }


@pytest.fixture
def mock_performance_metrics():
    """Provide mock performance metrics."""
    return {
        "operation_count": 100,
        "success_rate": 0.95,
        "average_response_time": 0.5,
        "total_modems": 2,
        "connected_modems": 1,
        "active_websocket_connections": 3
    }


@pytest.fixture
def mock_log_data():
    """Provide mock log data."""
    return {
        "level": "INFO",
        "message": "Test log message",
        "component": "test_component",
        "operation": "test_operation",
        "duration": 0.1,
        "success": True,
        "error": None
    }


@pytest.fixture
def mock_config_data():
    """Provide mock configuration data."""
    return {
        "api": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "Test API description"
        },
        "modem": {
            "baudrate": 115200,
            "timeout": 5,
            "max_concurrent": 5
        },
        "logging": {
            "level": "DEBUG",
            "file": "test.log",
            "max_size": 1024 * 1024,
            "backup_count": 3
        }
    }


@pytest.fixture
def mock_error_response():
    """Provide a mock error response."""
    return {
        "success": False,
        "error": "Test error message",
        "error_code": "TEST_ERROR",
        "details": {"test": "data"}
    }


@pytest.fixture
def mock_success_response():
    """Provide a mock success response."""
    return {
        "success": True,
        "message": "Test success message",
        "data": {"test": "data"}
    }


@pytest.fixture
def mock_api_endpoints():
    """Provide mock API endpoints data."""
    return {
        "multi_modem": [
            "/api/modems/detect",
            "/api/modems/connect",
            "/api/modems/disconnect",
            "/api/modems/status",
            "/api/modems/{modem_id}/status",
            "/api/modems/{modem_id}/sim-info",
            "/api/modems/{modem_id}/sms",
            "/api/modems/{modem_id}/sms/send",
            "/api/modems/{modem_id}/sms/{message_id}",
            "/api/modems/{modem_id}/ussd",
            "/api/modems/{modem_id}/balance"
        ],
        "legacy": [
            "/api/status",
            "/api/sim-info",
            "/api/sms",
            "/api/sms/send",
            "/api/sms/{message_id}",
            "/api/ussd",
            "/api/balance"
        ],
        "system": [
            "/api/health",
            "/api/performance",
            "/ws"
        ]
    }


@pytest.fixture
def mock_operator_profiles():
    """Provide mock operator profiles."""
    return {
        "ooredoo_algeria": {
        "name": "Ooredoo Algeria",
        "country": "Algeria",
        "mcc": "603",
            "mnc": ["01"],
            "imsi_prefix": ["60301"],
            "iccid_prefix": ["8921301"],
        "balance_ussd": "*223#",
            "data_balance_ussd": "*223*2#",
            "recharge_ussd": "*100*{code}#"
        },
        "djezzy_algeria": {
            "name": "Djezzy Algeria",
            "country": "Algeria",
            "mcc": "603",
            "mnc": ["03"],
            "imsi_prefix": ["60303"],
            "iccid_prefix": ["8921303"],
            "balance_ussd": "*100#",
            "data_balance_ussd": "*100*2#",
            "recharge_ussd": "*100*{code}#"
        },
        "mobilis_algeria": {
            "name": "Mobilis Algeria",
            "country": "Algeria",
            "mcc": "603",
            "mnc": ["02"],
            "imsi_prefix": ["60302"],
            "iccid_prefix": ["8921302"],
            "balance_ussd": "*101#",
            "data_balance_ussd": "*101*2#",
            "recharge_ussd": "*101*{code}#"
        }
    }


@pytest.fixture
def mock_at_commands():
    """Provide mock AT commands and responses."""
    return {
        "AT": "OK",
        "AT+CGMM": "E3531s\nOK",
        "AT+CGMR": "1.0.0\nOK",
        "AT+CGSN": "123456789012345\nOK",
        "AT+CPIN?": "READY\nOK",
        "AT+CIMI": "603021234567890\nOK",
        "AT+CCID": "8921302123456789012\nOK",
        "AT+CSQ": "CSQ: 25,99\nOK",
        "AT+COPS?": "COPS: 0,0,\"Ooredoo Algeria\"\nOK",
        "AT+CREG?": "CREG: 0,1\nOK",
        "AT+CMGF=1": "OK",
        "AT+CMGL=\"ALL\"": "+CMGL: 1,\"REC UNREAD\",\"+213555123456\",\"\",\"24/01/01,12:00:00+00\"\nTest message\nOK",
        "AT+CMGS=\"+213555123456\"": ">",
        "AT+CMGD=1": "OK",
        "AT+CUSD=1,\"*223#\",15": "OK",
        "+CUSD: 0,\"Your balance is 100 DZD\",15": "Your balance is 100 DZD"
    }


@pytest.fixture
def mock_serial_ports():
    """Provide mock serial ports."""
    return [
        Mock(device="COM1", description="Huawei E3531s", vid=0x12d1, pid=0x1f01),
        Mock(device="COM2", description="Huawei E3131", vid=0x12d1, pid=0x14db),
        Mock(device="COM3", description="USB Serial Device", vid=0x0403, pid=0x6001),
        Mock(device="COM4", description="Huawei E5573", vid=0x12d1, pid=0x1506)
    ]


@pytest.fixture
def mock_websocket_messages():
    """Provide mock WebSocket messages."""
    return {
        "modem_connected": {
            "type": "modem_connected",
            "modem_id": "huawei_COM1",
            "timestamp": 1704067200.0
        },
        "modem_disconnected": {
            "type": "modem_disconnected",
            "modem_id": "huawei_COM1",
            "timestamp": 1704067200.0
        },
        "sms_sent": {
            "type": "sms_sent",
            "modem_id": "huawei_COM1",
            "number": "+213555123456",
            "timestamp": 1704067200.0
        },
        "status_update": {
            "type": "status_update",
            "data": {
                "total_modems": 2,
                "connected_modems": 1,
                "modems": {
                    "huawei_COM1": {
                        "connected": True,
                        "port": "COM1",
                        "signal_strength": 75
                    }
                }
            }
        }
    }
