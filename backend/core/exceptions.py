"""
Custom exceptions for the SIM Card Management System
"""

class SimManagerException(Exception):
    """Base exception for SIM Manager errors"""
    pass

class ModemNotConnectedException(SimManagerException):
    """Raised when modem is not connected"""
    pass

class ModemDetectionException(SimManagerException):
    """Raised when modem detection fails"""
    pass

class ATCommandException(SimManagerException):
    """Raised when AT command execution fails"""
    pass

class SmsException(SimManagerException):
    """Raised when SMS operations fail"""
    pass

class UssdException(SimManagerException):
    """Raised when USSD operations fail"""
    pass

class SimCardException(SimManagerException):
    """Raised when SIM card operations fail"""
    pass

class OperatorDetectionException(SimManagerException):
    """Raised when operator detection fails"""
    pass

class SerialPortException(SimManagerException):
    """Raised when serial port operations fail"""
    pass

class ConfigurationException(SimManagerException):
    """Raised when configuration is invalid"""
    pass
