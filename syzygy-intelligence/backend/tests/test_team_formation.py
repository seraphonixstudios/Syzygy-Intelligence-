"""Tests for polarity-aware team formation."""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestTeamFormation:
    @pytest.mark.asyncio
    async def test_form_team_default(self):
        from app.orchestration.team_formation import TeamFormation
        tf = TeamFormation()
        result = await tf.form_team(task="test", num_agents=5)
        assert "agents" in result
        assert "polarity_balance" in result
        assert "balanced" in result
        assert result["num_agents"] <= 5

    @pytest.mark.asyncio
    async def test_form_team_with_required_archetypes(self):
        from app.orchestration.team_formation import TeamFormation
        tf = TeamFormation()
        result = await tf.form_team(task="test", num_agents=5, required_archetypes=["self"])
        for a in result["agents"]:
            assert a["archetype"] == "self"

    @pytest.mark.asyncio
    async def test_form_team_filters_by_archetype(self):
        from app.orchestration.team_formation import TeamFormation
        tf = TeamFormation()
        result = await tf.form_team(task="test", num_agents=5, required_archetypes=["nonexistent"])
        assert result["num_agents"] == 0

    @pytest.mark.asyncio
    async def test_suggest_team_for_task_critique(self):
        from app.orchestration.team_formation import TeamFormation
        tf = TeamFormation()
        result = await tf.suggest_team_for_task("critique this design")
        assert "trickster" in result["recommended_archetypes"]
        assert "sage" in result["recommended_archetypes"]

    @pytest.mark.asyncio
    async def test_suggest_team_for_task_synthesis(self):
        from app.orchestration.team_formation import TeamFormation
        tf = TeamFormation()
        result = await tf.suggest_team_for_task("synthesize these findings")
        assert "self" in result["recommended_archetypes"]
        assert "hermes" in result["recommended_archetypes"]

    @pytest.mark.asyncio
    async def test_suggest_team_for_task_no_keywords(self):
        from app.orchestration.team_formation import TeamFormation
        tf = TeamFormation()
        result = await tf.suggest_team_for_task("unknown task type")
        # Falls back to default set
        assert len(result["recommended_archetypes"]) == 5
        assert "sage" in result["recommended_archetypes"]
        assert "great_mother" in result["recommended_archetypes"]
