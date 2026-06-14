"""Tests for agent CRUD routes — list, create, get, delete, compose, shadow operations."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


def _mock_agent(to_dict_result: dict | None = None):
    agent = MagicMock()
    agent.to_dict.return_value = to_dict_result or {"id": "a1", "name": "Test Agent"}
    return agent


def _mock_shadow(to_dict_result: dict | None = None):
    shadow = MagicMock()
    shadow.to_dict.return_value = to_dict_result or {"id": "s1", "alignment_score": 0.5}
    return shadow


@pytest.fixture
def mock_registry():
    agent = _mock_agent()
    with patch("app.api.routes.agents.agent_registry") as mr:
        mr.list_agents = MagicMock(return_value=[])
        mr.create_agent = MagicMock(return_value=agent)
        mr.get = MagicMock(return_value=agent)
        mr.remove = MagicMock(return_value=True)
        mr.create_default_team = MagicMock(return_value=[_mock_agent(), _mock_agent()])
        mr.list_shadow_agents = MagicMock(return_value=[])
        mr.create_shadow_agent = MagicMock(return_value=_mock_shadow())
        mr.get_shadow = MagicMock(return_value=_mock_shadow())
        mr.remove_shadow = MagicMock(return_value=True)
        mr.clear_shadows = MagicMock()
        mr.create_shadow_balanced_team = MagicMock(return_value=[_mock_shadow(), _mock_shadow()])
        yield mr


class TestListAgents:
    @pytest.mark.asyncio
    async def test_returns_agent_list(self, mock_registry):
        from app.api.routes.agents import list_agents
        result = await list_agents()
        assert result["agents"] == []


class TestCreateAgent:
    @pytest.mark.asyncio
    async def test_creates_agent(self, mock_registry):
        from app.api.routes.agents import create_agent
        result = await create_agent({"name": "Test Agent", "archetype": "sage"})
        assert result["agent"]["name"] == "Test Agent"

    @pytest.mark.asyncio
    async def test_handles_error(self, mock_registry):
        mock_registry.create_agent.side_effect = ValueError("invalid archetype")
        from app.api.routes.agents import create_agent
        with pytest.raises(HTTPException) as exc:
            await create_agent({"name": "Bad"})
        assert exc.value.status_code == 500


class TestGetAgent:
    @pytest.mark.asyncio
    async def test_returns_agent(self, mock_registry):
        from app.api.routes.agents import get_agent
        result = await get_agent("a1")
        assert result["agent"]["id"] == "a1"

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, mock_registry):
        mock_registry.get.return_value = None
        from app.api.routes.agents import get_agent
        with pytest.raises(HTTPException) as exc:
            await get_agent("nonexistent")
        assert exc.value.status_code == 404


class TestDeleteAgent:
    @pytest.mark.asyncio
    async def test_deletes_agent(self, mock_registry):
        from app.api.routes.agents import delete_agent
        result = await delete_agent("a1")
        assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, mock_registry):
        mock_registry.remove.return_value = False
        from app.api.routes.agents import delete_agent
        with pytest.raises(HTTPException) as exc:
            await delete_agent("nonexistent")
        assert exc.value.status_code == 404


class TestComposeTeam:
    @pytest.mark.asyncio
    async def test_composes_team(self, mock_registry):
        from app.api.routes.agents import compose_team
        result = await compose_team()
        assert len(result["agents"]) == 2


class TestToggleShadow:
    @pytest.mark.asyncio
    async def test_activates_shadow(self, mock_registry):
        agent = MagicMock()
        agent.shadow_active = False
        agent.activate_shadow = MagicMock(side_effect=lambda: setattr(agent, "shadow_active", True))
        agent.deactivate_shadow = MagicMock()
        mock_registry.get.return_value = agent
        from app.api.routes.agents import toggle_shadow
        result = await toggle_shadow("a1")
        assert result["shadow_active"] is True
        agent.activate_shadow.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivates_shadow(self, mock_registry):
        agent = MagicMock()
        agent.shadow_active = True
        agent.activate_shadow = MagicMock()
        agent.deactivate_shadow = MagicMock(side_effect=lambda: setattr(agent, "shadow_active", False))
        mock_registry.get.return_value = agent
        from app.api.routes.agents import toggle_shadow
        result = await toggle_shadow("a1")
        assert result["shadow_active"] is False
        agent.deactivate_shadow.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_404_when_agent_not_found(self, mock_registry):
        mock_registry.get.return_value = None
        from app.api.routes.agents import toggle_shadow
        with pytest.raises(HTTPException) as exc:
            await toggle_shadow("nonexistent")
        assert exc.value.status_code == 404


class TestListShadowAgents:
    @pytest.mark.asyncio
    async def test_lists_shadows(self, mock_registry):
        from app.api.routes.agents import list_shadow_agents
        result = await list_shadow_agents()
        assert result["shadow_agents"] == []

    @pytest.mark.asyncio
    async def test_lists_shadows_by_archetype(self, mock_registry):
        from app.api.routes.agents import list_shadow_agents
        result = await list_shadow_agents(parent_archetype="sage")
        assert result["shadow_agents"] == []


class TestCreateShadowAgent:
    @pytest.mark.asyncio
    async def test_creates_shadow(self, mock_registry):
        mock_registry.create_shadow_agent = MagicMock(return_value=_mock_shadow({"id": "s1", "name": "Shadow"}))
        from app.api.routes.agents import create_shadow_agent
        result = await create_shadow_agent({"name": "Shadow", "parent_archetype": "sage"})
        assert result["shadow_agent"]["id"] == "s1"

    @pytest.mark.asyncio
    async def test_handles_value_error(self, mock_registry):
        mock_registry.create_shadow_agent = MagicMock(side_effect=ValueError("invalid"))
        from app.api.routes.agents import create_shadow_agent
        with pytest.raises(HTTPException) as exc:
            await create_shadow_agent({"name": "Bad"})
        assert exc.value.status_code == 400


class TestGetShadowAgent:
    @pytest.mark.asyncio
    async def test_returns_shadow(self, mock_registry):
        from app.api.routes.agents import get_shadow_agent
        result = await get_shadow_agent("s1")
        assert result["shadow_agent"]["id"] == "s1"

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, mock_registry):
        mock_registry.get_shadow.return_value = None
        from app.api.routes.agents import get_shadow_agent
        with pytest.raises(HTTPException) as exc:
            await get_shadow_agent("nonexistent")
        assert exc.value.status_code == 404


class TestDeleteShadowAgent:
    @pytest.mark.asyncio
    async def test_deletes_shadow(self, mock_registry):
        from app.api.routes.agents import delete_shadow_agent
        result = await delete_shadow_agent("s1")
        assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, mock_registry):
        mock_registry.remove_shadow.return_value = False
        from app.api.routes.agents import delete_shadow_agent
        with pytest.raises(HTTPException) as exc:
            await delete_shadow_agent("nonexistent")
        assert exc.value.status_code == 404


class TestAlignShadowAgent:
    @pytest.mark.asyncio
    async def test_aligns_shadow(self, mock_registry):
        shadow = MagicMock()
        shadow.align = MagicMock(return_value=0.8)
        shadow.to_dict = MagicMock(return_value={"id": "s1"})
        mock_registry.get_shadow.return_value = shadow
        from app.api.routes.agents import align_shadow_agent
        result = await align_shadow_agent("s1", {"delta": 0.1})
        assert result["alignment_score"] == 0.8

    @pytest.mark.asyncio
    async def test_align_without_data(self, mock_registry):
        shadow = MagicMock()
        shadow.align = MagicMock(return_value=0.8)
        shadow.to_dict = MagicMock(return_value={"id": "s1"})
        mock_registry.get_shadow.return_value = shadow
        from app.api.routes.agents import align_shadow_agent
        result = await align_shadow_agent("s1", None)
        assert result["alignment_score"] == 0.8

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, mock_registry):
        mock_registry.get_shadow.return_value = None
        from app.api.routes.agents import align_shadow_agent
        with pytest.raises(HTTPException) as exc:
            await align_shadow_agent("nonexistent", {})
        assert exc.value.status_code == 404


class TestMisalignShadowAgent:
    @pytest.mark.asyncio
    async def test_misaligns_shadow(self, mock_registry):
        shadow = MagicMock()
        shadow.misalign = MagicMock(return_value=0.3)
        shadow.to_dict = MagicMock(return_value={"id": "s1"})
        mock_registry.get_shadow.return_value = shadow
        from app.api.routes.agents import misalign_shadow_agent
        result = await misalign_shadow_agent("s1", {"delta": 0.1})
        assert result["alignment_score"] == 0.3

    @pytest.mark.asyncio
    async def test_misalign_without_data(self, mock_registry):
        shadow = MagicMock()
        shadow.misalign = MagicMock(return_value=0.3)
        shadow.to_dict = MagicMock(return_value={"id": "s1"})
        mock_registry.get_shadow.return_value = shadow
        from app.api.routes.agents import misalign_shadow_agent
        result = await misalign_shadow_agent("s1", None)
        assert result["alignment_score"] == 0.3

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, mock_registry):
        mock_registry.get_shadow.return_value = None
        from app.api.routes.agents import misalign_shadow_agent
        with pytest.raises(HTTPException) as exc:
            await misalign_shadow_agent("nonexistent", {})
        assert exc.value.status_code == 404


class TestIntegrateShadowAgent:
    @pytest.mark.asyncio
    async def test_integrates_shadow(self, mock_registry):
        report = MagicMock()
        report.parent_agent_id = "a1"
        report.shadow_agent_id = "s1"
        report.insights = ["insight"]
        report.alignment_delta = 0.05
        report.new_alignment_score = 0.85
        report.timestamp = "2026-01-01T00:00:00"
        shadow = MagicMock()
        shadow.integrate = MagicMock(return_value=report)
        shadow.alignment_score = 0.8
        parent = MagicMock()
        mock_registry.get_shadow.return_value = shadow
        mock_registry.get.return_value = parent
        from app.api.routes.agents import integrate_shadow_agent
        result = await integrate_shadow_agent("s1", "a1")
        assert result["integration_report"]["parent_agent_id"] == "a1"

    @pytest.mark.asyncio
    async def test_returns_404_when_shadow_not_found(self, mock_registry):
        mock_registry.get_shadow.return_value = None
        from app.api.routes.agents import integrate_shadow_agent
        with pytest.raises(HTTPException) as exc:
            await integrate_shadow_agent("nonexistent", "a1")
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_404_when_parent_not_found(self, mock_registry):
        mock_registry.get_shadow.return_value = MagicMock()
        mock_registry.get.return_value = None
        from app.api.routes.agents import integrate_shadow_agent
        with pytest.raises(HTTPException) as exc:
            await integrate_shadow_agent("s1", "nonexistent")
        assert exc.value.status_code == 404


class TestComposeShadowTeam:
    @pytest.mark.asyncio
    async def test_composes_shadow_team(self, mock_registry):
        from app.api.routes.agents import compose_shadow_team
        result = await compose_shadow_team()
        assert len(result["shadow_agents"]) == 2
