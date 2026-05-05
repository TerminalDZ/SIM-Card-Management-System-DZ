"""Logging setup — single configuration entry point used at startup.

Uses the stdlib ``logging`` package. We deliberately avoid pulling in a heavy
structured-logging dependency: a small JSON formatter is enough for the
operational needs of this service.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import Any

from app.config import Settings

LOGGER_NAME = "sim_manager"


class _JsonFormatter(logging.Formatter):
    """Serialize log records as one JSON object per line."""

    _RESERVED: frozenset[str] = frozenset(
        logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys()
    ) | {"message", "asctime"}

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "location": f"{record.filename}:{record.lineno}",
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(settings: Settings) -> logging.Logger:
    """Configure the root application logger; idempotent across calls."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(settings.log_level)
    logger.propagate = False
    if logger.handlers:
        return logger

    formatter: logging.Formatter
    if settings.log_json:
        formatter = _JsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    if settings.log_file is not None:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        rotating = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        rotating.setFormatter(formatter)
        logger.addHandler(rotating)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child logger scoped under the application logger."""
    if name is None or name == LOGGER_NAME:
        return logging.getLogger(LOGGER_NAME)
    return logging.getLogger(LOGGER_NAME).getChild(name)


@contextmanager
def timed_operation(logger: logging.Logger, label: str, **context: Any) -> Iterator[None]:
    """Log start / end of an operation along with its duration."""
    start = perf_counter()
    logger.debug("Starting %s", label, extra={"context": context} if context else None)
    try:
        yield
    except Exception as exc:
        elapsed = perf_counter() - start
        logger.error(
            "Failed %s after %.3fs: %s",
            label,
            elapsed,
            exc,
            extra={"context": context} if context else None,
        )
        raise
    else:
        elapsed = perf_counter() - start
        logger.debug(
            "Completed %s in %.3fs",
            label,
            elapsed,
            extra={"context": context} if context else None,
        )
