"""
Comprehensive logging system for SIM Card Management System
"""

import logging
import logging.handlers
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

class SimManagerLogger:
    """Centralized logging system for the SIM Manager"""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        self.log_level = getattr(logging, log_level.upper())
        self.log_file = log_file
        self.logger = logging.getLogger("sim_manager")
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging system"""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(self.log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        if self.log_file:
            # Create logs directory if it doesn't exist
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Rotating file handler (max 10MB, keep 5 files)
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance with the given name"""
        return logging.getLogger(f"sim_manager.{name}")

# Global logger instance
_logger_instance: Optional[SimManagerLogger] = None

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Setup global logging configuration"""
    global _logger_instance
    _logger_instance = SimManagerLogger(log_level, log_file)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    if _logger_instance is None:
        setup_logging()
    return _logger_instance.get_logger(name)

# Module-specific loggers
def get_modem_logger() -> logging.Logger:
    return get_logger("modem")

def get_operator_logger() -> logging.Logger:
    return get_logger("operator")

def get_api_logger() -> logging.Logger:
    return get_logger("api")

def get_sms_logger() -> logging.Logger:
    return get_logger("sms")

def get_ussd_logger() -> logging.Logger:
    return get_logger("ussd")
