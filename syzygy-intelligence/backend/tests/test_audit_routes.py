"""Tests for audit log API routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException


class TestListAuditLogs:
    @pytest.mark.asyncio
    async def test_returns_empty(self):
        with patch("app.api.routes.audit.audit_service") as m_svc:
            m_svc.query = AsyncMock(return_value=[])
            from app.api.routes.audit import list_audit_logs
            result = await list_audit_logs()
            assert result["entries"] == []
            assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_returns_entries(self):
        entries = [
            {"id": "1", "event_type": "login", "action": "user_login"},
            {"id": "2", "event_type": "logout", "action": "user_logout"},
        ]
        with patch("app.api.routes.audit.audit_service") as m_svc:
            m_svc.query = AsyncMock(return_value=entries)
            from app.api.routes.audit import list_audit_logs
            result = await list_audit_logs()
            assert result["entries"] == entries
            assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_passes_filters(self):
        with patch("app.api.routes.audit.audit_service") as m_svc:
            m_svc.query = AsyncMock(return_value=[])
            from app.api.routes.audit import list_audit_logs
            await list_audit_logs(event_type="login", agent_id="a1", session_id="s1", limit=50, offset=10)
            m_svc.query.assert_called_once_with(
                event_type="login", agent_id="a1", session_id="s1", limit=50, offset=10
            )

    @pytest.mark.asyncio
    async def test_empty_filters_passed_as_none(self):
        with patch("app.api.routes.audit.audit_service") as m_svc:
            m_svc.query = AsyncMock(return_value=[])
            from app.api.routes.audit import list_audit_logs
            await list_audit_logs(event_type="", agent_id="", session_id="", limit=100, offset=0)
            m_svc.query.assert_called_once_with(
                event_type=None, agent_id=None, session_id=None, limit=100, offset=0
            )

    @pytest.mark.asyncio
    async def test_uses_defaults(self):
        with patch("app.api.routes.audit.audit_service") as m_svc:
            m_svc.query = AsyncMock(return_value=[])
            from app.api.routes.audit import list_audit_logs
            await list_audit_logs(event_type="", agent_id="", session_id="", limit=100, offset=0)
            m_svc.query.assert_called_once_with(
                event_type=None, agent_id=None, session_id=None, limit=100, offset=0
            )


class TestCountAuditLogs:
    @pytest.mark.asyncio
    async def test_returns_count(self):
        with patch("app.api.routes.audit.audit_service") as m_svc:
            m_svc.count = AsyncMock(return_value=42)
            from app.api.routes.audit import count_audit_logs
            result = await count_audit_logs()
            assert result["count"] == 42

    @pytest.mark.asyncio
    async def test_returns_zero(self):
        with patch("app.api.routes.audit.audit_service") as m_svc:
            m_svc.count = AsyncMock(return_value=0)
            from app.api.routes.audit import count_audit_logs
            result = await count_audit_logs()
            assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_passes_filters(self):
        with patch("app.api.routes.audit.audit_service") as m_svc:
            m_svc.count = AsyncMock(return_value=5)
            from app.api.routes.audit import count_audit_logs
            await count_audit_logs(event_type="login", agent_id="a1", session_id="s1")
            m_svc.count.assert_called_once_with(
                event_type="login", agent_id="a1", session_id="s1"
            )

    @pytest.mark.asyncio
    async def test_empty_filters_passed_as_none(self):
        with patch("app.api.routes.audit.audit_service") as m_svc:
            m_svc.count = AsyncMock(return_value=0)
            from app.api.routes.audit import count_audit_logs
            await count_audit_logs(event_type="", agent_id="", session_id="")
            m_svc.count.assert_called_once_with(
                event_type=None, agent_id=None, session_id=None
            )
