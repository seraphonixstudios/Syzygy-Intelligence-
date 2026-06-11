"""Global error handling middleware and exception classes for Syzygy."""

from __future__ import annotations

import traceback
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.logging_setup import logger


class SyzygyError(Exception):
    """Base exception for all Syzygy errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AgentNotFoundError(SyzygyError):
    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent '{agent_id}' not found",
            code="AGENT_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"agent_id": agent_id},
        )


class SessionNotFoundError(SyzygyError):
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session '{session_id}' not found",
            code="SESSION_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"session_id": session_id},
        )


class ConsensusError(SyzygyError):
    def __init__(self, message: str, details: dict[str, Any] = None):
        super().__init__(
            message=message,
            code="CONSENSUS_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class LLMConnectionError(SyzygyError):
    def __init__(self, model: str, original_error: str = ""):
        super().__init__(
            message=f"Failed to connect to model '{model}': {original_error}",
            code="LLM_CONNECTION_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"model": model, "original_error": original_error},
        )


class ToolExecutionError(SyzygyError):
    def __init__(self, tool_id: str, message: str):
        super().__init__(
            message=f"Tool '{tool_id}' execution failed: {message}",
            code="TOOL_EXECUTION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"tool_id": tool_id, "error": message},
        )


class ValidationError(SyzygyError):
    def __init__(self, message: str, details: dict[str, Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            details=details,
        )


def setup_error_handlers(app: FastAPI):
    """Register global error handlers on the FastAPI app."""

    @app.exception_handler(SyzygyError)
    async def syzygy_error_handler(request: Request, exc: SyzygyError):
        logger.error(
            f"SyzygyError: {exc.message}",
            code=exc.code,
            status_code=exc.status_code,
            path=str(request.url.path),
            method=request.method,
            details=exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        logger.warning(
            "Validation error",
            path=str(request.url.path),
            errors=errors,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"errors": errors},
                }
            },
        )

    @app.exception_handler(Exception)
    async def global_handler(request: Request, exc: Exception):
        tb = traceback.format_exc()
        logger.error(
            f"Unhandled exception: {exc}",
            path=str(request.url.path),
            traceback=tb,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {},
                }
            },
        )


__all__ = [
    "SyzygyError",
    "AgentNotFoundError",
    "SessionNotFoundError",
    "ConsensusError",
    "LLMConnectionError",
    "ToolExecutionError",
    "ValidationError",
    "setup_error_handlers",
]
