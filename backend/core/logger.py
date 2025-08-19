"""
Logging system for the Multi-Modem SIM Card Management System.

This module provides a comprehensive logging system with structured formatting,
file rotation, performance tracking, and WebSocket-specific logging capabilities.
"""

import logging
import logging.handlers
import os
import sys
from contextlib import contextmanager
from typing import Optional, Dict, Any
from datetime import datetime
import time

from backend.config import get_settings


class StructuredFormatter(logging.Formatter):
    """
    Structured formatter for consistent log output across all components.
    
    Provides consistent formatting with timestamp, level, component, and message
    in a structured format suitable for both human reading and log parsing.
    """
    
    def __init__(self, include_component: bool = True):
        """
        Initialize the structured formatter.
        
        Args:
            include_component: Whether to include component name in log format
        """
        if include_component:
            fmt = '%(asctime)s | %(levelname)-8s | %(name)-20s | %(filename)s:%(lineno)d | %(message)s'
        else:
            fmt = '%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s'
        
        super().__init__(
            fmt=fmt,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with additional context."""
        # Add component name if not present
        if not hasattr(record, 'component'):
            record.component = record.name.split('.')[-1] if '.' in record.name else record.name
        
        return super().format(record)


class SimManagerLogger:
    """
    Centralized logging system for the SIM Manager.
    
    Provides configurable logging with file rotation, multiple handlers,
    and structured output for better debugging and monitoring.
    """
    
    def __init__(self, settings=None):
        """
        Initialize the logging system.
        
        Args:
            settings: Application settings instance
        """
        self.settings = settings or get_settings()
        self.logger = logging.getLogger("sim_manager")
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure the logging system with handlers and formatters."""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(getattr(logging, self.settings.LOG_LEVEL))
        
        # Prevent propagation to root logger
        self.logger.propagate = False
        
        # Console handler with structured formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.settings.LOG_LEVEL)
        console_handler.setFormatter(StructuredFormatter(include_component=True))
        self.logger.addHandler(console_handler)
        
        # File handler with rotation (if configured)
        if self.settings.LOG_FILE:
            self._setup_file_handler()
    
    def _setup_file_handler(self):
        """Setup rotating file handler for persistent logging."""
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(self.settings.LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Rotating file handler with size and count limits
        file_handler = logging.handlers.RotatingFileHandler(
            self.settings.LOG_FILE,
            maxBytes=self.settings.LOG_MAX_SIZE,
            backupCount=self.settings.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        
        file_handler.setLevel(self.settings.LOG_LEVEL)
        file_handler.setFormatter(StructuredFormatter(include_component=True))
        self.logger.addHandler(file_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance with the given name.
        
        Args:
            name: Logger name (usually component name)
            
        Returns:
            Configured logger instance
        """
        return logging.getLogger(f"sim_manager.{name}")
    
    def set_level(self, level: str):
        """Set the logging level dynamically."""
        self.logger.setLevel(getattr(logging, level.upper()))
        for handler in self.logger.handlers:
            handler.setLevel(getattr(logging, level.upper()))
    
    # Standard logging methods
    def debug(self, message: str, *args, **kwargs):
        """Log a debug message."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log an info message."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log a warning message."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log an error message."""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log a critical message."""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log an exception message with traceback."""
        self.logger.exception(message, *args, **kwargs)


# Global logger instance
_logger_instance: Optional[SimManagerLogger] = None


def setup_logging(settings=None) -> SimManagerLogger:
    """
    Setup global logging configuration.
    
    Args:
        settings: Application settings instance
        
    Returns:
        Configured logger instance
    """
    global _logger_instance
    _logger_instance = SimManagerLogger(settings)
    return _logger_instance


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified component.
    
    Args:
        name: Component name for the logger
        
    Returns:
        Configured logger instance
    """
    if _logger_instance is None:
        setup_logging()
    return _logger_instance.get_logger(name)


# Module-specific logger factories
def get_modem_logger() -> logging.Logger:
    """Get logger for modem operations."""
    return get_logger("modem")


def get_operator_logger() -> logging.Logger:
    """Get logger for operator management."""
    return get_logger("operator")


def get_api_logger() -> logging.Logger:
    """Get logger for API operations."""
    return get_logger("api")


def get_sms_logger() -> logging.Logger:
    """Get logger for SMS operations."""
    return get_logger("sms")


def get_ussd_logger() -> logging.Logger:
    """Get logger for USSD operations."""
    return get_logger("ussd")


def get_websocket_logger() -> logging.Logger:
    """Get logger for WebSocket operations."""
    return get_logger("websocket")


@contextmanager
def log_operation(logger: logging.Logger, operation_name: str, **context):
    """
    Context manager for logging operation execution with timing.
    
    Args:
        logger: Logger instance to use
        operation_name: Name of the operation being logged
        **context: Additional context to log
    """
    start_time = time.time()
    logger.info(f"Starting {operation_name}", extra={'context': context})
    
    try:
        yield
        duration = time.time() - start_time
        logger.info(f"Completed {operation_name} in {duration:.2f}s", extra={'context': context})
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed {operation_name} after {duration:.2f}s: {e}", extra={'context': context})
        raise


def log_performance(logger: logging.Logger, operation: str, **context):
    """
    Log performance metrics for operations.
    
    Args:
        logger: Logger instance
        operation: Operation name
        **context: Additional context
    """
    logger.debug(f"Performance: {operation}", extra={'context': context})
