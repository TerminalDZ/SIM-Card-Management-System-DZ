import os
from typing import Optional

class Settings:
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    
    # Modem Configuration
    MODEM_TIMEOUT: int = int(os.getenv("MODEM_TIMEOUT", "30"))
    MODEM_RETRY_COUNT: int = int(os.getenv("MODEM_RETRY_COUNT", "3"))
    AUTO_DETECT_MODEM: bool = os.getenv("AUTO_DETECT_MODEM", "True").lower() == "true"
    
    # Frontend Configuration
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # CORS Origins
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        FRONTEND_URL
    ]

settings = Settings()
