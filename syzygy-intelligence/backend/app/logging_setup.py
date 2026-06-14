"""Persistent structured logging system for Syzygy Intelligence.

Provides:
- Structured JSON logging to files and console
- Log levels with environment-aware configuration
- Automatic context injection (session_id, agent_id, polarity)
- Rotation and retention policies
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from app.config import settings


class StructuredMessage:
    def __init__(self, message: str, **kwargs: Any) -> None:
        self.message = message
        self.kwargs = kwargs

    def __str__(self) -> str:
        return f"{self.message} | {json.dumps(self.kwargs, default=str)}"


class JsonFormatter(logging.Formatter):
    """Outputs each log record as a single JSON object.

    Compatible with log aggregators (Datadog, Grafana Loki, CloudWatch).
    """

    def format(self, record: logging.LogRecord) -> str:
        obj: dict[str, Any] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            for k, v in record.extra.items():
                if k not in obj:
                    try:
                        json.dumps(v)
                        obj[k] = v
                    except (TypeError, ValueError):
                        obj[k] = str(v)
        if record.exc_info and record.exc_info[0]:
            obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(obj, default=str)


class SyzygyLogger:
    """Structured logger with file rotation, console output, and context injection.

    Uses contextvars for request-scoped logging context to prevent context bleed
    in async code with concurrent requests.
    """

    def __init__(
        self,
        name: str = "syzygy",
        log_dir: str | None = None,
        level: str | None = None,
    ):
        self.name = name
        self.log_dir = Path(log_dir or f"{settings.data_dir}/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.level = (level or settings.log_level).upper()

        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, self.level, logging.INFO))
        self._logger.handlers.clear()

        self._setup_handlers()
        self._context: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
            "syzygy_log_context", default={}
        )

    def _setup_handlers(self) -> None:
        use_json = settings.effective_log_format == "json"

        text_fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
        json_fmt = JsonFormatter()

        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(json_fmt if use_json else text_fmt)
        console.addFilter(lambda r: r.levelno >= getattr(logging, self.level))
        self._logger.addHandler(console)

        file_handler = RotatingFileHandler(
            filename=self.log_dir / f"{self.name}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(json_fmt if use_json else text_fmt)
        self._logger.addHandler(file_handler)

        error_handler = RotatingFileHandler(
            filename=self.log_dir / f"{self.name}_error.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(json_fmt if use_json else text_fmt)
        self._logger.addHandler(error_handler)

        audit_handler = RotatingFileHandler(
            filename=self.log_dir / f"{self.name}_audit.log",
            maxBytes=25 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8",
        )
        audit_handler.setLevel(logging.INFO)
        # Add filter to only capture audit logs
        audit_handler.addFilter(
            lambda r: hasattr(r, "audit_action") or "AUDIT" in r.getMessage()
        )
        audit_handler.setFormatter(
            JsonFormatter() if use_json
            else logging.Formatter(
                "%(asctime)s | AUDIT | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S%z",
            )
        )
        self._logger.addHandler(audit_handler)

    def with_context(self, **kwargs: Any) -> SyzygyLogger:
        """Set context variables for the current async task (thread-safe)."""
        current_context = self._context.get().copy()
        current_context.update(kwargs)
        self._context.set(current_context)
        return self

    def _log(self, level: int, msg: str, **kwargs: Any) -> None:
        extra = {**self._context.get(), **kwargs}
        structured = StructuredMessage(msg, **extra)
        self._logger.log(level, str(structured), extra=extra)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, msg, **kwargs)

    def audit(self, action: str, **kwargs: Any) -> None:
        """Audit trail: always logged at INFO level with AUDIT prefix."""
        self._log(
            logging.INFO,
            f"AUDIT | {action}",
            audit_action=action,
            **kwargs,
        )

    def log_exception(self, exc: Exception, msg: str = "", **kwargs: Any) -> None:
        self._logger.exception(
            str(StructuredMessage(msg or str(exc), **kwargs)),
            exc_info=exc,
        )


logger = SyzygyLogger()
