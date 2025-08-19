"""
Custom exceptions for the Multi-Modem SIM Card Management System.

This module defines a comprehensive exception hierarchy for all system components,
providing clear error categorization and detailed error information for better
debugging and error handling.
"""

from typing import Optional, Dict, Any


class SimManagerException(Exception):
    """
    Base exception for all SIM Manager errors.
    
    All custom exceptions in this system inherit from this base class,
    providing a common interface for error handling and categorization.
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the base exception.
        
        Args:
            message: Human-readable error message
            error_code: Optional error code for programmatic handling
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        """Return formatted error message."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "exception_type": self.__class__.__name__
        }


# Hardware and Connection Exceptions
class ModemNotConnectedException(SimManagerException):
    """Raised when attempting to use a modem that is not connected."""
    
    def __init__(self, modem_id: Optional[str] = None, message: Optional[str] = None):
        msg = message or f"Modem {modem_id} is not connected" if modem_id else "Modem is not connected"
        super().__init__(msg, "MODEM_NOT_CONNECTED", {"modem_id": modem_id})


class ModemDetectionException(SimManagerException):
    """Raised when modem detection fails."""
    
    def __init__(self, message: str, port: Optional[str] = None):
        super().__init__(message, "MODEM_DETECTION_FAILED", {"port": port})


class SerialPortException(SimManagerException):
    """Raised when serial port operations fail."""
    
    def __init__(self, message: str, port: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message, "SERIAL_PORT_ERROR", {
            "port": port,
            "operation": operation
        })


# AT Command Exceptions
class ATCommandException(SimManagerException):
    """Raised when AT command execution fails."""
    
    def __init__(self, message: str, command: Optional[str] = None, response: Optional[str] = None):
        super().__init__(message, "AT_COMMAND_FAILED", {
            "command": command,
            "response": response
        })


class ATCommandTimeoutException(ATCommandException):
    """Raised when AT command times out."""
    
    def __init__(self, command: str, timeout: int):
        message = f"AT command '{command}' timed out after {timeout} seconds"
        super().__init__(message, "AT_COMMAND_TIMEOUT", {
            "command": command,
            "timeout": timeout
        })


# SMS Exceptions
class SmsException(SimManagerException):
    """Base exception for SMS-related errors."""
    
    def __init__(self, message: str, operation: Optional[str] = None, phone_number: Optional[str] = None):
        super().__init__(message, "SMS_ERROR", {
            "operation": operation,
            "phone_number": phone_number
        })


class SmsSendException(SmsException):
    """Raised when SMS sending fails."""
    
    def __init__(self, message: str, phone_number: Optional[str] = None, modem_id: Optional[str] = None):
        super().__init__(message, "SMS_SEND_FAILED", {
            "phone_number": phone_number,
            "modem_id": modem_id
        })


class SmsReadException(SmsException):
    """Raised when SMS reading fails."""
    
    def __init__(self, message: str, modem_id: Optional[str] = None):
        super().__init__(message, "SMS_READ_FAILED", {"modem_id": modem_id})


class SmsDeleteException(SmsException):
    """Raised when SMS deletion fails."""
    
    def __init__(self, message: str, message_id: Optional[int] = None, modem_id: Optional[str] = None):
        super().__init__(message, "SMS_DELETE_FAILED", {
            "message_id": message_id,
            "modem_id": modem_id
        })


# USSD Exceptions
class UssdException(SimManagerException):
    """Base exception for USSD-related errors."""
    
    def __init__(self, message: str, command: Optional[str] = None, modem_id: Optional[str] = None):
        super().__init__(message, "USSD_ERROR", {
            "command": command,
            "modem_id": modem_id
        })


class UssdTimeoutException(UssdException):
    """Raised when USSD command times out."""
    
    def __init__(self, command: str, timeout: int, modem_id: Optional[str] = None):
        message = f"USSD command '{command}' timed out after {timeout} seconds"
        super().__init__(message, "USSD_TIMEOUT", {
            "command": command,
            "timeout": timeout,
            "modem_id": modem_id
        })


# SIM Card Exceptions
class SimCardException(SimManagerException):
    """Raised when SIM card operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, modem_id: Optional[str] = None):
        super().__init__(message, "SIM_CARD_ERROR", {
            "operation": operation,
            "modem_id": modem_id
        })


class SimCardNotDetectedException(SimCardException):
    """Raised when SIM card is not detected."""
    
    def __init__(self, modem_id: Optional[str] = None):
        message = f"SIM card not detected in modem {modem_id}" if modem_id else "SIM card not detected"
        super().__init__(message, "SIM_CARD_NOT_DETECTED", {"modem_id": modem_id})


# Operator Exceptions
class OperatorDetectionException(SimManagerException):
    """Raised when operator detection fails."""
    
    def __init__(self, message: str, imsi: Optional[str] = None, iccid: Optional[str] = None):
        super().__init__(message, "OPERATOR_DETECTION_FAILED", {
            "imsi": imsi,
            "iccid": iccid
        })


class UnsupportedOperatorException(OperatorDetectionException):
    """Raised when an unsupported operator is detected."""
    
    def __init__(self, operator_info: Optional[str] = None, imsi: Optional[str] = None):
        message = f"Unsupported operator: {operator_info}" if operator_info else "Unsupported operator"
        super().__init__(message, "UNSUPPORTED_OPERATOR", {
            "operator_info": operator_info,
            "imsi": imsi
        })


# Configuration Exceptions
class ConfigurationException(SimManagerException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, "CONFIGURATION_ERROR", {"config_key": config_key})


class MissingConfigurationException(ConfigurationException):
    """Raised when required configuration is missing."""
    
    def __init__(self, config_key: str):
        message = f"Missing required configuration: {config_key}"
        super().__init__(message, "MISSING_CONFIGURATION", {"config_key": config_key})


# Multi-Modem Exceptions
class MultiModemException(SimManagerException):
    """Base exception for multi-modem operations."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(message, "MULTI_MODEM_ERROR", {"operation": operation})


class ModemLimitExceededException(MultiModemException):
    """Raised when trying to connect more modems than allowed."""
    
    def __init__(self, current_count: int, max_count: int):
        message = f"Modem limit exceeded: {current_count}/{max_count}"
        super().__init__(message, "MODEM_LIMIT_EXCEEDED", {
            "current_count": current_count,
            "max_count": max_count
        })


class ModemAlreadyConnectedException(MultiModemException):
    """Raised when trying to connect an already connected modem."""
    
    def __init__(self, modem_id: str):
        message = f"Modem {modem_id} is already connected"
        super().__init__(message, "MODEM_ALREADY_CONNECTED", {"modem_id": modem_id})


class ModemNotFoundException(MultiModemException):
    """Raised when a specific modem is not found."""
    
    def __init__(self, modem_id: str):
        message = f"Modem {modem_id} not found"
        super().__init__(message, "MODEM_NOT_FOUND", {"modem_id": modem_id})


# API Exceptions
class APIException(SimManagerException):
    """Base exception for API-related errors."""
    
    def __init__(self, message: str, endpoint: Optional[str] = None, status_code: int = 500):
        super().__init__(message, "API_ERROR", {
            "endpoint": endpoint,
            "status_code": status_code
        })
        self.status_code = status_code


class ValidationException(APIException):
    """Raised when API request validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(message, "VALIDATION_ERROR", {
            "field": field,
            "value": value
        })
        self.status_code = 400


class ResourceNotFoundException(APIException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: Optional[str] = None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(message, "RESOURCE_NOT_FOUND", {
            "resource_type": resource_type,
            "resource_id": resource_id
        })
        self.status_code = 404


# WebSocket Exceptions
class WebSocketException(SimManagerException):
    """Base exception for WebSocket-related errors."""
    
    def __init__(self, message: str, connection_id: Optional[str] = None):
        super().__init__(message, "WEBSOCKET_ERROR", {"connection_id": connection_id})


class WebSocketConnectionException(WebSocketException):
    """Raised when WebSocket connection fails."""
    
    def __init__(self, message: str, connection_id: Optional[str] = None):
        super().__init__(message, "WEBSOCKET_CONNECTION_FAILED", {"connection_id": connection_id})


# Error code mapping for HTTP status codes
ERROR_CODE_TO_STATUS = {
    "MODEM_NOT_CONNECTED": 503,
    "MODEM_DETECTION_FAILED": 503,
    "SERIAL_PORT_ERROR": 503,
    "AT_COMMAND_FAILED": 503,
    "AT_COMMAND_TIMEOUT": 408,
    "SMS_ERROR": 503,
    "SMS_SEND_FAILED": 503,
    "SMS_READ_FAILED": 503,
    "SMS_DELETE_FAILED": 503,
    "USSD_ERROR": 503,
    "USSD_TIMEOUT": 408,
    "SIM_CARD_ERROR": 503,
    "SIM_CARD_NOT_DETECTED": 503,
    "OPERATOR_DETECTION_FAILED": 503,
    "UNSUPPORTED_OPERATOR": 400,
    "CONFIGURATION_ERROR": 500,
    "MISSING_CONFIGURATION": 500,
    "MULTI_MODEM_ERROR": 503,
    "MODEM_LIMIT_EXCEEDED": 429,
    "MODEM_ALREADY_CONNECTED": 409,
    "MODEM_NOT_FOUND": 404,
    "API_ERROR": 500,
    "VALIDATION_ERROR": 400,
    "RESOURCE_NOT_FOUND": 404,
    "WEBSOCKET_ERROR": 503,
    "WEBSOCKET_CONNECTION_FAILED": 503,
}


def get_http_status_code(exception: SimManagerException) -> int:
    """
    Get appropriate HTTP status code for an exception.
    
    Args:
        exception: The exception instance
        
    Returns:
        HTTP status code
    """
    if hasattr(exception, 'status_code'):
        return exception.status_code
    
    return ERROR_CODE_TO_STATUS.get(exception.error_code, 500)
