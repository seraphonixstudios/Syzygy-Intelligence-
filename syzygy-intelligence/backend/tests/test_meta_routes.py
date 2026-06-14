"""Tests for meta-cognition API routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


class TestGetMetaSummary:
    @pytest.mark.asyncio
    async def test_returns_summary_with_data(self):
        mock_summary = {
            "total_evaluations": 5,
            "average_score": 0.75,
            "total_proposals": 3,
            "applied_proposals": 1,
            "latest_score": 0.82,
        }
        with patch("app.api.routes.meta.meta_engine") as m_engine:
            m_engine.get_summary.return_value = mock_summary
            from app.api.routes.meta import get_meta_summary

            result = await get_meta_summary()
            assert result["total_evaluations"] == 5
            assert result["average_score"] == 0.75
            assert result["applied_proposals"] == 1

    @pytest.mark.asyncio
    async def test_returns_empty_summary(self):
        mock_summary = {"total_evaluations": 0, "average_score": 0, "total_proposals": 0}
        with patch("app.api.routes.meta.meta_engine") as m_engine:
            m_engine.get_summary.return_value = mock_summary
            from app.api.routes.meta import get_meta_summary

            result = await get_meta_summary()
            assert result["total_evaluations"] == 0


class TestEvaluateOutput:
    @pytest.mark.asyncio
    async def test_evaluates_output(self):
        mock_result = MagicMock()
        mock_result.score = 0.65
        mock_result.dimensions = {"completeness": 0.5, "coherence": 0.8}
        mock_result.feedback = ["Needs more detail"]
        mock_result.suggestions = ["Add examples"]

        mock_proposal = MagicMock()
        mock_proposal.id = "imp-0-completeness"
        mock_proposal.target = "completeness"
        mock_proposal.change = "Improve completeness"
        mock_proposal.rationale = "Needs more detail"
        mock_proposal.expected_impact = 0.3

        with patch("app.api.routes.meta.meta_engine") as m_engine:
            m_engine.evaluate_output.return_value = mock_result
            m_engine.propose_improvements.return_value = [mock_proposal]
            from app.api.routes.meta import evaluate_output

            result = await evaluate_output({"output": "test output", "context": {"domain": "code"}})
            assert result["evaluation"]["score"] == 0.65
            assert result["evaluation"]["dimensions"]["completeness"] == 0.5
            assert len(result["proposals"]) == 1
            assert result["proposals"][0]["id"] == "imp-0-completeness"

    @pytest.mark.asyncio
    async def test_handles_empty_output(self):
        mock_result = MagicMock()
        mock_result.score = 0.0
        mock_result.dimensions = {}
        mock_result.feedback = []
        mock_result.suggestions = []

        with patch("app.api.routes.meta.meta_engine") as m_engine:
            m_engine.evaluate_output.return_value = mock_result
            m_engine.propose_improvements.return_value = []
            from app.api.routes.meta import evaluate_output

            result = await evaluate_output({"output": "", "context": {}})
            assert result["evaluation"]["score"] == 0.0
            assert result["proposals"] == []

    @pytest.mark.asyncio
    async def test_passes_context(self):
        with patch("app.api.routes.meta.meta_engine") as m_engine:
            mock_result = MagicMock()
            mock_result.score = 0.5
            mock_result.dimensions = {}
            mock_result.feedback = []
            mock_result.suggestions = []
            m_engine.evaluate_output.return_value = mock_result
            m_engine.propose_improvements.return_value = []
            from app.api.routes.meta import evaluate_output

            await evaluate_output({"output": "test", "context": {"domain": "research"}})
            m_engine.evaluate_output.assert_called_with("test", {"domain": "research"})


class TestGetEvaluationHistory:
    @pytest.mark.asyncio
    async def test_returns_history(self):
        mock_eval = MagicMock()
        mock_eval.score = 0.7
        mock_eval.dimensions = {"completeness": 0.7}
        mock_eval.feedback = ["Good"]
        mock_eval.timestamp = "2026-01-01T00:00:00"

        mock_proposal = MagicMock()
        mock_proposal.id = "imp-0"
        mock_proposal.target = "completeness"
        mock_proposal.change = "Improve"
        mock_proposal.status = "applied"
        mock_proposal.created_at = "2026-01-01T00:00:00"
        mock_proposal.applied_at = "2026-01-01T01:00:00"

        with patch("app.api.routes.meta.meta_engine") as m_engine:
            m_engine.get_history.return_value = [mock_eval]
            m_engine.get_proposals.return_value = [mock_proposal]
            from app.api.routes.meta import get_evaluation_history

            result = await get_evaluation_history()
            assert len(result["evaluations"]) == 1
            assert result["evaluations"][0]["score"] == 0.7
            assert len(result["proposals"]) == 1
            assert result["proposals"][0]["id"] == "imp-0"
            assert result["proposals"][0]["applied_at"] == "2026-01-01T01:00:00"

    @pytest.mark.asyncio
    async def test_returns_empty_history(self):
        with patch("app.api.routes.meta.meta_engine") as m_engine:
            m_engine.get_history.return_value = []
            m_engine.get_proposals.return_value = []
            from app.api.routes.meta import get_evaluation_history

            result = await get_evaluation_history()
            assert result["evaluations"] == []
            assert result["proposals"] == []


class TestApplyProposal:
    @pytest.mark.asyncio
    async def test_applies_proposal(self):
        mock_proposal = MagicMock()
        mock_proposal.id = "imp-0-completeness"
        mock_proposal.target = "completeness"
        mock_proposal.change = "Improve score"

        with patch("app.api.routes.meta.meta_engine") as m_engine:
            m_engine.apply_proposal.return_value = mock_proposal
            from app.api.routes.meta import apply_proposal

            result = await apply_proposal("imp-0-completeness")
            assert result["status"] == "applied"
            assert result["proposal"]["id"] == "imp-0-completeness"

    @pytest.mark.asyncio
    async def test_not_found(self):
        with patch("app.api.routes.meta.meta_engine") as m_engine:
            m_engine.apply_proposal.return_value = None
            from app.api.routes.meta import apply_proposal

            result = await apply_proposal("nonexistent")
            assert result["status"] == "error"
            assert "not found" in result["message"]


class TestRunSelfImprovement:
    @pytest.mark.asyncio
    async def test_evaluate_and_propose(self):
        mock_result = MagicMock()
        mock_result.score = 0.4
        mock_result.dimensions = {"completeness": 0.3, "coherence": 0.5}
        mock_result.feedback = ["Too short"]
        mock_result.suggestions = ["Add detail"]

        mock_proposal = MagicMock()
        mock_proposal.id = "imp-0-completeness"
        mock_proposal.target = "completeness"
        mock_proposal.change = "Improve completeness"
        mock_result.expected_impact = 0.3

        with patch("app.api.routes.meta.meta_engine") as m_engine:
            m_engine.evaluate_output.return_value = mock_result
            m_engine.propose_improvements.return_value = [mock_proposal]
            m_engine.get_summary.return_value = {"total_evaluations": 1}
            from app.api.routes.meta import run_self_improvement

            result = await run_self_improvement({"output": "test", "context": {}})
            assert result["evaluation"]["score"] == 0.4
            assert len(result["proposals"]) == 1
            assert result["auto_applied"] == []
            assert result["summary"]["total_evaluations"] == 1

    @pytest.mark.asyncio
    async def test_auto_applies_proposals(self):
        mock_result = MagicMock()
        mock_result.score = 0.3
        mock_result.dimensions = {"completeness": 0.2}
        mock_result.feedback = ["Too short"]
        mock_result.suggestions = ["Add detail"]

        prop1 = MagicMock()
        prop1.id = "imp-1"
        prop2 = MagicMock()
        prop2.id = "imp-2"

        with patch("app.api.routes.meta.meta_engine") as m_engine:
            m_engine.evaluate_output.return_value = mock_result
            m_engine.propose_improvements.return_value = [prop1, prop2]
            m_engine.get_summary.return_value = {"total_evaluations": 1}
            from app.api.routes.meta import run_self_improvement

            result = await run_self_improvement({"output": "test", "context": {}, "auto_apply": True})
            assert result["auto_applied"] == ["imp-1", "imp-2"]
            assert m_engine.apply_proposal.call_count == 2
            m_engine.apply_proposal.assert_any_call("imp-1")
            m_engine.apply_proposal.assert_any_call("imp-2")

    @pytest.mark.asyncio
    async def test_handles_no_proposals(self):
        mock_result = MagicMock()
        mock_result.score = 0.9
        mock_result.dimensions = {"completeness": 0.9}
        mock_result.feedback = ["Good"]
        mock_result.suggestions = []

        with patch("app.api.routes.meta.meta_engine") as m_engine:
            m_engine.evaluate_output.return_value = mock_result
            m_engine.propose_improvements.return_value = []
            m_engine.get_summary.return_value = {"total_evaluations": 1}
            from app.api.routes.meta import run_self_improvement

            result = await run_self_improvement({"output": "good output", "context": {}})
            assert result["proposals"] == []
            assert result["auto_applied"] == []
