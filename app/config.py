"""Application settings loaded from environment variables.

Single source of truth for configuration. Validated at startup so the process
fails fast when something is wrong rather than crashing later in a request.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Strongly-typed runtime configuration.

    All values can be overridden through environment variables (prefix ``APP_``)
    or a ``.env`` file in the project root.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        case_sensitive=False,
        extra="ignore",
    )

    # HTTP API
    host: str = Field("0.0.0.0", description="Bind address for the HTTP server.")
    port: int = Field(8000, ge=1, le=65535)
    debug: bool = Field(False, description="Verbose logging and detailed error responses.")
    reload: bool = Field(False, description="Auto-reload the server on code changes (dev only).")

    # API metadata
    title: str = "SIM Card Management System"
    version: str = "3.0.0"
    description: str = "Professional multi-modem SIM card management API."

    # Logging
    log_level: str = Field("INFO")
    log_file: Path | None = Field(default=PROJECT_ROOT / "logs" / "sim_manager.log")
    log_max_bytes: int = Field(10 * 1024 * 1024, ge=1024)
    log_backup_count: int = Field(5, ge=0, le=100)
    log_json: bool = Field(False, description="Emit logs as JSON lines instead of human format.")

    # Modem hardware
    modem_baudrate: int = Field(115200)
    modem_open_timeout: float = Field(2.0, gt=0)
    modem_read_timeout: float = Field(10.0, gt=0)
    modem_command_retries: int = Field(2, ge=0, le=10)
    modem_default_apn: str = Field("internet")
    max_concurrent_modems: int = Field(10, ge=1, le=100)
    auto_detect_on_startup: bool = True

    # Manually registered modems — useful for emulators or remote modems
    # exposed via a TCP serial bridge. Each entry must be a pyserial URL
    # (``socket://host:port``, ``rfc2217://host:port``) or an absolute device
    # path (``/dev/ttyUSB0``, ``COM5``). They are appended to the detected
    # list with ``responsive=True`` and skip the AT probe.
    manual_modems: list[str] = Field(default_factory=list)

    # Operator data
    operators_file: Path = Field(default=PROJECT_ROOT / "data" / "operators.json")

    # WebSocket
    ws_heartbeat_interval: int = Field(30, ge=1)
    ws_broadcast_interval: int = Field(15, ge=1)

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True

    @field_validator("log_level")
    @classmethod
    def _normalize_log_level(cls, value: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {sorted(valid)}")
        return upper

    @field_validator("operators_file", mode="before")
    @classmethod
    def _resolve_operators_path(cls, value: str | Path | None) -> Path:
        if value in (None, ""):
            return PROJECT_ROOT / "data" / "operators.json"
        path = Path(value)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
