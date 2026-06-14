"""Tests for error handling — SyzygyError subclasses, exception handlers, FastAPI integration."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from app.errors import (
    AgentNotFoundError,
    ConsensusError,
    LLMConnectionError,
    SessionNotFoundError,
    SyzygyError,
    ToolExecutionError,
    ValidationError,
    setup_error_handlers,
)


class TestSyzygyErrorSubclasses:
    def test_agent_not_found(self):
        err = AgentNotFoundError("agent-1")
        assert err.code == "AGENT_NOT_FOUND"
        assert err.status_code == 404

    def test_session_not_found(self):
        err = SessionNotFoundError("session-1")
        assert err.code == "SESSION_NOT_FOUND"
        assert err.status_code == 404

    def test_consensus_error(self):
        err = ConsensusError("consensus failed")
        assert err.code == "CONSENSUS_ERROR"
        assert err.status_code == 500

    def test_llm_connection_error(self):
        err = LLMConnectionError("qwen3:8b", "timeout")
        assert err.code == "LLM_CONNECTION_ERROR"
        assert err.status_code == 503
        assert "qwen3:8b" in err.message

    def test_tool_execution_error(self):
        err = ToolExecutionError("code-runner", "syntax error")
        assert err.code == "TOOL_EXECUTION_ERROR"
        assert "code-runner" in err.message

    def test_validation_error(self):
        err = ValidationError("invalid input", {"field": "name"})
        assert err.code == "VALIDATION_ERROR"
        assert err.status_code == 422
        assert err.details["field"] == "name"


@pytest.fixture
def scope():
    return {"type": "http", "method": "GET", "path": "/test", "headers": []}


class TestSetupErrorHandlers:
    @pytest.fixture
    def app(self):
        app = FastAPI()
        setup_error_handlers(app)
        return app

    @pytest.mark.asyncio
    async def test_syzygy_error_handler(self, app, scope):
        with patch("app.errors.settings") as ms:
            ms.env = "development"
            handler = app.exception_handlers[SyzygyError]
            request = Request(scope)
            resp = await handler(request, SyzygyError("something broke", code="TEST_ERROR", status_code=400))
            assert resp.status_code == 400
            body = json.loads(resp.body)
            assert body["error"]["code"] == "TEST_ERROR"
            assert "something broke" in body["error"]["message"]

    @pytest.mark.asyncio
    async def test_validation_error_handler(self, app, scope):
        with patch("app.errors.settings") as ms:
            ms.env = "development"
            handler = app.exception_handlers[RequestValidationError]
            request = Request(scope)
            resp = await handler(
                request,
                RequestValidationError([{"loc": ["body"], "msg": "invalid", "type": "value_error"}]),
            )
            body = json.loads(resp.body)
            assert body["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_global_handler_development(self, app, scope):
        with patch("app.errors.settings") as ms:
            ms.env = "development"
            handler = app.exception_handlers[Exception]
            request = Request(scope)
            resp = await handler(request, RuntimeError("unhandled"))
            body = json.loads(resp.body)
            assert body["error"]["code"] == "INTERNAL_ERROR"
            assert "unhandled" in body["error"]["message"]

    @pytest.mark.asyncio
    async def test_global_handler_production(self, app, scope):
        with patch("app.errors.settings") as ms:
            ms.env = "production"
            handler = app.exception_handlers[Exception]
            request = Request(scope)
            resp = await handler(request, RuntimeError("secret detail"))
            body = json.loads(resp.body)
            assert body["error"]["code"] == "INTERNAL_ERROR"
            assert body["error"]["message"] == "An unexpected error occurred"
