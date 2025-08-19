"""
Data models for the Multi-Modem SIM Card Management System.

This module defines all Pydantic models used throughout the system, providing
type safety, validation, and serialization for API requests and responses.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class NetworkType(str, Enum):
    """Network technology types supported by modems."""
    GSM = "2G"
    UMTS = "3G"
    LTE = "4G"
    NR = "5G"
    UNKNOWN = "Unknown"


class SmsStatus(str, Enum):
    """SMS message status types."""
    UNREAD = "REC UNREAD"
    READ = "REC READ"
    STORED_UNSENT = "STO UNSENT"
    STORED_SENT = "STO SENT"


class ModemStatus(BaseModel):
    """
    Status information for a modem connection.
    
    Provides comprehensive status information including connection state,
    hardware details, network information, and error conditions.
    """
    
    connected: bool = Field(..., description="Whether the modem is connected")
    modem_id: Optional[str] = Field(None, description="Unique identifier for the modem")
    port: Optional[str] = Field(None, description="Serial port used for connection")
    model: Optional[str] = Field(None, description="Modem model name")
    firmware: Optional[str] = Field(None, description="Modem firmware version")
    signal_strength: Optional[int] = Field(None, ge=0, le=100, description="Signal strength percentage")
    network_type: Optional[NetworkType] = Field(None, description="Current network technology")
    operator: Optional[str] = Field(None, description="Network operator name")
    error: Optional[str] = Field(None, description="Error message if connection failed")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        schema_extra = {
            "example": {
                "connected": True,
                "modem_id": "huawei_COM1",
                "port": "COM1",
                "model": "E3531s",
                "firmware": "1.0.0",
                "signal_strength": 75,
                "network_type": "LTE",
                "operator": "Ooredoo Algeria"
            }
        }


class SimInfo(BaseModel):
    """
    SIM card information and details.
    
    Contains all relevant SIM card information including identifiers,
    network details, and signal quality metrics.
    """
    
    modem_id: Optional[str] = Field(None, description="Modem identifier")
    imsi: Optional[str] = Field(None, description="International Mobile Subscriber Identity")
    iccid: Optional[str] = Field(None, description="Integrated Circuit Card Identifier")
    imei: Optional[str] = Field(None, description="International Mobile Equipment Identity")
    msisdn: Optional[str] = Field(None, description="Mobile Station International Subscriber Directory Number")
    operator_name: Optional[str] = Field(None, description="SIM operator name")
    signal_strength: Optional[int] = Field(None, ge=0, le=100, description="Signal strength percentage")
    signal_quality: Optional[int] = Field(None, ge=0, le=100, description="Signal quality percentage")
    rssi: Optional[int] = Field(None, description="Received Signal Strength Indicator")
    network_type: Optional[NetworkType] = Field(None, description="Current network technology")
    network_operator: Optional[str] = Field(None, description="Network operator name")
    roaming: Optional[bool] = Field(None, description="Whether the SIM is roaming")
    
    @validator('imsi')
    def validate_imsi(cls, v):
        """Validate IMSI format."""
        if v and not v.isdigit():
            raise ValueError('IMSI must contain only digits')
        if v and len(v) != 15:
            raise ValueError('IMSI must be exactly 15 digits')
        return v
    
    @validator('iccid')
    def validate_iccid(cls, v):
        """Validate ICCID format."""
        if v and not v.isdigit():
            raise ValueError('ICCID must contain only digits')
        if v and len(v) != 19 and len(v) != 20:
            raise ValueError('ICCID must be 19 or 20 digits')
        return v
    
    @validator('imei')
    def validate_imei(cls, v):
        """Validate IMEI format."""
        if v and not v.isdigit():
            raise ValueError('IMEI must contain only digits')
        if v and len(v) != 15:
            raise ValueError('IMEI must be exactly 15 digits')
        return v
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        schema_extra = {
            "example": {
                "modem_id": "huawei_COM1",
                "imsi": "603021234567890",
                "iccid": "8921302123456789012",
                "imei": "123456789012345",
                "msisdn": "0555123456",
                "operator_name": "Ooredoo Algeria",
                "signal_strength": 75,
                "network_type": "LTE",
                "roaming": False
            }
        }


class SmsMessage(BaseModel):
    """
    SMS message representation.
    
    Contains all details about an SMS message including content,
    metadata, and status information.
    """
    
    id: int = Field(..., description="Unique message identifier")
    modem_id: Optional[str] = Field(None, description="Modem that received/sent the message")
    status: SmsStatus = Field(..., description="Message status")
    phone_number: str = Field(..., description="Phone number of sender/recipient")
    message: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    pdu_type: Optional[str] = Field(None, description="PDU type for SMS")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format."""
        # Remove any non-digit characters for validation
        digits = ''.join(filter(str.isdigit, v))
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError('Phone number must be between 10 and 15 digits')
        return v
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        schema_extra = {
            "example": {
                "id": 1,
                "modem_id": "huawei_COM1",
                "status": "REC UNREAD",
                "phone_number": "+213555123456",
                "message": "Hello World",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class UssdResponse(BaseModel):
    """
    USSD command response.
    
    Contains the response from a USSD command execution including
    success status, response content, and timing information.
    """
    
    command: str = Field(..., description="USSD command that was executed")
    modem_id: Optional[str] = Field(None, description="Modem that executed the command")
    response: str = Field(..., description="Response from the USSD command")
    raw_response: Optional[str] = Field(None, description="Raw response from the modem")
    success: bool = Field(..., description="Whether the command was successful")
    timestamp: datetime = Field(default_factory=datetime.now, description="Command execution timestamp")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "command": "*223#",
                "modem_id": "huawei_COM1",
                "response": "Your balance is 100 DZD",
                "raw_response": "AT+CUSD=1,\"*223#\",15\r\n+CUSD: 1,\"Your balance is 100 DZD\",15\r\nOK\r\n",
                "success": True,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class OperatorProfile(BaseModel):
    """
    Mobile operator profile and configuration.
    
    Contains all operator-specific information including USSD codes,
    APN settings, and service configurations.
    """
    
    name: str = Field(..., description="Operator name")
    country: str = Field(..., description="Country where operator operates")
    mcc: str = Field(..., description="Mobile Country Code")
    mnc: List[str] = Field(..., description="Mobile Network Codes")
    imsi_prefix: List[str] = Field(..., description="IMSI prefixes for this operator")
    iccid_prefix: List[str] = Field(..., description="ICCID prefixes for this operator")
    balance_ussd: Optional[str] = Field(None, description="USSD code for balance check")
    data_balance_ussd: Optional[str] = Field(None, description="USSD code for data balance check")
    recharge_ussd: Optional[str] = Field(None, description="USSD code for recharge")
    apn_settings: Optional[Dict[str, Any]] = Field(None, description="APN configuration")
    common_services: Optional[Dict[str, str]] = Field(None, description="Common USSD services")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "name": "Ooredoo Algeria",
                "country": "Algeria",
                "mcc": "603",
                "mnc": ["02"],
                "imsi_prefix": ["60302"],
                "iccid_prefix": ["8921302"],
                "balance_ussd": "*223#",
                "data_balance_ussd": "*223*2#",
                "recharge_ussd": "*100*{code}#"
            }
        }


class ATCommand(BaseModel):
    """
    AT command configuration.
    
    Defines an AT command with its expected response and retry configuration.
    """
    
    command: str = Field(..., description="AT command to execute")
    expected_response: Optional[str] = Field("OK", description="Expected response from command")
    timeout: Optional[int] = Field(5, ge=1, le=60, description="Command timeout in seconds")
    retries: Optional[int] = Field(3, ge=0, le=10, description="Number of retry attempts")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "command": "AT+CIMI",
                "expected_response": "OK",
                "timeout": 5,
                "retries": 3
            }
        }


# Multi-Modem Support Models

class ModemInfo(BaseModel):
    """
    Detailed information about a specific modem.
    
    Contains comprehensive information about a modem including connection
    details, status, and activity tracking.
    """
    
    modem_id: str = Field(..., description="Unique modem identifier")
    port: str = Field(..., description="Serial port used by the modem")
    connected_at: datetime = Field(..., description="When the modem was connected")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    status: Optional[ModemStatus] = Field(None, description="Current modem status")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "modem_id": "huawei_COM1",
                "port": "COM1",
                "connected_at": "2024-01-01T12:00:00Z",
                "last_activity": "2024-01-01T12:05:00Z"
            }
        }


class MultiModemStatus(BaseModel):
    """
    Status of all connected modems.
    
    Provides an overview of all modems in the system including
    connection counts and individual status information.
    """
    
    total_modems: int = Field(..., ge=0, description="Total number of modems")
    connected_modems: int = Field(..., ge=0, description="Number of connected modems")
    modems: Dict[str, ModemStatus] = Field(..., description="Status of each modem")
    
    @validator('connected_modems')
    def validate_connected_count(cls, v, values):
        """Validate connected modems count."""
        if 'total_modems' in values and v > values['total_modems']:
            raise ValueError('Connected modems cannot exceed total modems')
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
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


# API Request/Response Models

class ModemConnectionRequest(BaseModel):
    """Request to connect to a specific modem."""
    
    modem_id: str = Field(..., description="Modem identifier to connect to")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "modem_id": "huawei_COM1"
            }
        }


class ModemDisconnectionRequest(BaseModel):
    """Request to disconnect from a specific modem."""
    
    modem_id: str = Field(..., description="Modem identifier to disconnect from")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "modem_id": "huawei_COM1"
            }
        }


class SmsRequest(BaseModel):
    """SMS request with modem specification."""
    
    modem_id: str = Field(..., description="Modem to use for SMS")
    number: str = Field(..., description="Phone number to send SMS to")
    message: str = Field(..., min_length=1, max_length=160, description="SMS message content")
    
    @validator('number')
    def validate_phone_number(cls, v):
        """Validate phone number format."""
        digits = ''.join(filter(str.isdigit, v))
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError('Phone number must be between 10 and 15 digits')
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "modem_id": "huawei_COM1",
                "number": "+213555123456",
                "message": "Hello from multi-modem system"
            }
        }


class UssdRequest(BaseModel):
    """USSD request with modem specification."""
    
    modem_id: str = Field(..., description="Modem to use for USSD")
    command: str = Field(..., min_length=1, description="USSD command to execute")
    
    @validator('command')
    def validate_ussd_command(cls, v):
        """Validate USSD command format."""
        if not v.startswith('*') or not v.endswith('#'):
            raise ValueError('USSD command must start with * and end with #')
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "modem_id": "huawei_COM1",
                "command": "*223#"
            }
        }


class ModemDetectionResponse(BaseModel):
    """Response for modem detection operation."""
    
    detected_modems: List[str] = Field(..., description="List of detected modem IDs")
    connected_modems: List[str] = Field(..., description="List of connected modem IDs")
    total_detected: int = Field(..., ge=0, description="Total number of detected modems")
    total_connected: int = Field(..., ge=0, description="Total number of connected modems")
    
    @validator('total_connected')
    def validate_connected_count(cls, v, values):
        """Validate connected count."""
        if 'total_detected' in values and v > values['total_detected']:
            raise ValueError('Connected count cannot exceed detected count')
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "detected_modems": ["huawei_COM1", "huawei_COM2"],
                "connected_modems": ["huawei_COM1"],
                "total_detected": 2,
                "total_connected": 1
            }
        }


# API Response Models

class SuccessResponse(BaseModel):
    """Standard success response for API operations."""
    
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"modem_id": "huawei_COM1"}
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response for API operations."""
    
    success: bool = Field(False, description="Operation success status")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code for programmatic handling")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "success": False,
                "error": "Modem not found",
                "error_code": "MODEM_NOT_FOUND",
                "details": {"modem_id": "huawei_COM1"}
            }
        }
