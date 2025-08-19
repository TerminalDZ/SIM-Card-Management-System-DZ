"""
Configuration management for the Multi-Modem SIM Card Management System.

This module provides centralized configuration management using Pydantic Settings
for type-safe, validated configuration with environment variable support.
"""

import os
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with validation and environment variable support.
    
    This class defines all configuration parameters for the multi-modem system,
    including API settings, modem configuration, logging, and performance tuning.
    """
    
    # API Configuration
    HOST: str = Field("0.0.0.0", description="API server host")
    PORT: int = Field(8000, description="API server port")
    DEBUG: bool = Field(False, description="Debug mode")
    
    # API Metadata
    API_TITLE: str = Field("Multi-Modem SIM Card Management System", description="API title")
    API_VERSION: str = Field("2.0.0", description="API version")
    API_DESCRIPTION: str = Field(
        "Professional multi-modem SIM card management system for Algerian operators",
        description="API description"
    )
    
    # Logging Configuration
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    LOG_FILE: str = Field("logs/sim_manager.log", description="Log file path")
    LOG_MAX_SIZE: int = Field(10 * 1024 * 1024, description="Maximum log file size in bytes")  # 10MB
    LOG_BACKUP_COUNT: int = Field(5, description="Number of backup log files")
    
    # Modem Configuration
    MODEM_BAUDRATE: int = Field(115200, description="Modem baud rate")
    MODEM_TIMEOUT: int = Field(5, description="Modem timeout in seconds")
    MODEM_OPERATION_TIMEOUT: int = Field(10, description="Modem operation timeout in seconds")
    MAX_CONCURRENT_MODEMS: int = Field(10, description="Maximum number of concurrent modems")
    
    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = Field(30, description="WebSocket heartbeat interval in seconds")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of {valid_levels}')
        return v.upper()
    
    @validator('PORT')
    def validate_port(cls, v):
        """Validate port number."""
        if not 1 <= v <= 65535:
            raise ValueError('PORT must be between 1 and 65535')
        return v
    
    @validator('MODEM_TIMEOUT')
    def validate_modem_timeout(cls, v):
        """Validate modem timeout."""
        if not 1 <= v <= 60:
            raise ValueError('MODEM_TIMEOUT must be between 1 and 60 seconds')
        return v
    
    @validator('MAX_CONCURRENT_MODEMS')
    def validate_max_modems(cls, v):
        """Validate maximum concurrent modems."""
        if not 1 <= v <= 50:
            raise ValueError('MAX_CONCURRENT_MODEMS must be between 1 and 50')
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.
    
    Returns:
        Settings: The global settings instance
        
    Note:
        This function ensures that only one settings instance is created
        and reused throughout the application for consistency.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
