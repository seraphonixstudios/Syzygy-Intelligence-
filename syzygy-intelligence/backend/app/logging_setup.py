"""Persistent structured logging system for Syzygy Intelligence.

Provides:
- Structured JSON logging to files and console
- Log levels with environment-aware configuration
- Automatic context injection (session_id, agent_id, polarity)
- Rotation and retention policies
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

from app.config import settings


class StructuredMessage:
    def __init__(self, message: str, **kwargs):
        self.message = message
        self.kwargs = kwargs

    def __str__(self) -> str:
        return f"{self.message} | {json.dumps(self.kwargs, default=str)}"


class SyzygyLogger:
    """Structured logger with file rotation, console output, and context injection."""

    def __init__(
        self,
        name: str = "syzygy",
        log_dir: Optional[str] = None,
        level: Optional[str] = None,
    ):
        self.name = name
        self.log_dir = Path(log_dir or f"{settings.data_dir}/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.level = (level or settings.log_level).upper()

        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, self.level, logging.INFO))
        self._logger.handlers.clear()

        self._setup_handlers()
        self._context: dict[str, Any] = {}

    def _setup_handlers(self):
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )

        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(formatter)
        console.addFilter(lambda r: r.levelno >= getattr(logging, self.level))
        self._logger.addHandler(console)

        file_handler = RotatingFileHandler(
            filename=self.log_dir / f"{self.name}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

        error_handler = RotatingFileHandler(
            filename=self.log_dir / f"{self.name}_error.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self._logger.addHandler(error_handler)

        audit_handler = RotatingFileHandler(
            filename=self.log_dir / f"{self.name}_audit.log",
            maxBytes=25 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8",
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | AUDIT | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S%z",
            )
        )
        self._logger.addHandler(audit_handler)

    def with_context(self, **kwargs) -> SyzygyLogger:
        self._context.update(kwargs)
        return self

    def _log(self, level: int, msg: str, **kwargs):
        extra = {**self._context, **kwargs}
        structured = StructuredMessage(msg, **extra)
        self._logger.log(level, str(structured), extra=extra)

    def debug(self, msg: str, **kwargs):
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        self._log(logging.CRITICAL, msg, **kwargs)

    def audit(self, action: str, **kwargs):
        """Audit trail: always logged at INFO level with AUDIT prefix."""
        self._log(
            logging.INFO,
            f"AUDIT | {action}",
            event_type="audit",
            audit_action=action,
            **kwargs,
        )

    def log_exception(self, exc: Exception, msg: str = "", **kwargs):
        self._logger.exception(
            str(StructuredMessage(msg or str(exc), **kwargs)),
            exc_info=exc,
        )


logger = SyzygyLogger()
