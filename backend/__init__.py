"""
Multi-Modem SIM Card Management System - Backend Package.

This package provides a comprehensive backend system for managing multiple
Huawei USB modems, including SMS, USSD, and SIM card operations.

The system is designed to be professional, scalable, and maintainable,
with robust error handling, comprehensive logging, and type-safe APIs.
"""

__version__ = "2.0.0"
__author__ = "Multi-Modem SIM Card Management System Team"
__description__ = "Professional multi-modem SIM card management system for Algerian operators"

# Core components
from .core.modem_manager import ModemManager
from .core.multi_modem_manager import MultiModemManager
from .core.operator_manager import OperatorManager
from .core.logger import SimManagerLogger, log_operation, log_performance
from .core.exceptions import (
    SimManagerException, ModemNotConnectedException, ModemDetectionException,
    SmsException, UssdException, SimCardException, get_http_status_code
)

# Configuration and models
from .config import get_settings
from .models.models import (
    ModemStatus, SimInfo, SmsMessage, UssdResponse, NetworkType, SmsStatus,
    OperatorProfile, ModemInfo, MultiModemStatus, ModemDetectionResponse,
    ModemConnectionRequest, ModemDisconnectionRequest, SmsRequest, UssdRequest,
    SuccessResponse, ErrorResponse
)

# Main application
from .main import app

__all__ = [
    # Version and metadata
    "__version__",
    "__author__", 
    "__description__",
    
    # Core components
    "ModemManager",
    "MultiModemManager", 
    "OperatorManager",
    "SimManagerLogger",
    "log_operation",
    "log_performance",
    
    # Exceptions
    "SimManagerException",
    "ModemNotConnectedException",
    "ModemDetectionException", 
    "SmsException",
    "UssdException",
    "SimCardException",
    "get_http_status_code",
    
    # Configuration and models
    "get_settings",
    "ModemStatus",
    "SimInfo",
    "SmsMessage", 
    "UssdResponse",
    "NetworkType",
    "SmsStatus",
    "OperatorProfile",
    "ModemInfo",
    "MultiModemStatus",
    "ModemDetectionResponse",
    "ModemConnectionRequest",
    "ModemDisconnectionRequest",
    "SmsRequest",
    "UssdRequest",
    "SuccessResponse",
    "ErrorResponse",
    
    # Main application
    "app"
]
