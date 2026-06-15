"""Tests for workflow API routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestListWorkflows:
    @pytest.mark.asyncio
    async def test_returns_workflows(self):
        wf1 = MagicMock()
        wf1.name = "coding"
        wf1.description = "Write code"
        wf2 = MagicMock()
        wf2.name = "research"
        wf2.description = "Research topics"
        with patch("app.api.routes.workflows.WORKFLOW_REGISTRY", {"coding": wf1, "research": wf2}):
            from app.api.routes.workflows import list_workflows
            result = await list_workflows()
            assert len(result["workflows"]) == 2
            names = {w["name"] for w in result["workflows"]}
            assert "coding" in names
            assert "research" in names

    @pytest.mark.asyncio
    async def test_returns_empty(self):
        with patch("app.api.routes.workflows.WORKFLOW_REGISTRY", {}):
            from app.api.routes.workflows import list_workflows
            result = await list_workflows()
            assert result["workflows"] == []


def _mock_user(uid="u1"):
    u = MagicMock()
    u.id = uid
    u.message_count = 0
    return u


class TestExecuteWorkflow:
    @pytest.mark.asyncio
    async def test_executes_workflow(self):
        wf = AsyncMock()
        wf.execute.return_value = {"output": "done"}
        user = _mock_user()
        db = AsyncMock()
        db.add = MagicMock()
        with (
            patch("app.api.routes.workflows.get_workflow", return_value=wf),
            patch("app.api.routes.workflows.check_usage_limit", AsyncMock()),
        ):
            from app.api.routes.workflows import execute_workflow
            result = await execute_workflow("coding", {"task": "write tests", "context": {"lang": "py"}}, user=user, db=db)
            assert result["workflow"] == "coding"
            assert result["result"]["output"] == "done"
            wf.execute.assert_called_once_with(task="write tests", context={"lang": "py"})
            assert user.message_count == 1
            db.add.assert_called_once_with(user)
            db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_executes_with_default_context(self):
        wf = AsyncMock()
        wf.execute.return_value = {"output": "done"}
        user = _mock_user()
        db = AsyncMock()
        db.add = MagicMock()
        with (
            patch("app.api.routes.workflows.get_workflow", return_value=wf),
            patch("app.api.routes.workflows.check_usage_limit", AsyncMock()),
        ):
            from app.api.routes.workflows import execute_workflow
            result = await execute_workflow("coding", {"task": "write code"}, user=user, db=db)
            wf.execute.assert_called_once_with(task="write code", context={})

    @pytest.mark.asyncio
    async def test_returns_404_for_unknown_workflow(self):
        user = _mock_user()
        db = AsyncMock()
        with patch("app.api.routes.workflows.get_workflow", return_value=None):
            from app.api.routes.workflows import execute_workflow
            with pytest.raises(HTTPException) as exc:
                await execute_workflow("nonexistent", {"task": "do"}, user=user, db=db)
            assert exc.value.status_code == 404
            assert "nonexistent" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_returns_500_on_execution_error(self):
        wf = AsyncMock()
        wf.execute.side_effect = RuntimeError("execution failed")
        user = _mock_user()
        db = AsyncMock()
        with (
            patch("app.api.routes.workflows.get_workflow", return_value=wf),
            patch("app.api.routes.workflows.check_usage_limit", AsyncMock()),
        ):
            from app.api.routes.workflows import execute_workflow
            with pytest.raises(HTTPException) as exc:
                await execute_workflow("coding", {"task": "do"}, user=user, db=db)
            assert exc.value.status_code == 500
            assert "execution failed" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_passes_through_http_exception(self):
        user = _mock_user()
        db = AsyncMock()
        with (
            patch("app.api.routes.workflows.get_workflow", side_effect=HTTPException(400, "bad request")),
        ):
            from app.api.routes.workflows import execute_workflow
            with pytest.raises(HTTPException) as exc:
                await execute_workflow("coding", {"task": "do"}, user=user, db=db)
            assert exc.value.status_code == 400
