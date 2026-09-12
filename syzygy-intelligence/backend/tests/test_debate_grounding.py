"""Grounding tests for the debate workflow.

Proves every listed round actually runs, the completed count is measured,
and judging reports real verdicts (or honest unknowns).
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.workflows.debate import (
    DebateWorkflow,
    _normalize_judgment,
    _parse_json_obj,
)

EXECUTE_TIMEOUT = 120.0


def _echo_llm():
    llm = AsyncMock()
    llm.get_model_for_role = MagicMock(return_value="mock-model")

    async def _gen(prompt, **kwargs):
        return f"ECHO::{prompt[:200]}"

    llm.generate.side_effect = _gen
    return llm


class TestTaskSensitivity:
    @pytest.mark.asyncio
    async def test_outputs_depend_on_topic(self):
        async def _run(topic):
            wf = DebateWorkflow()
            wf.llm = _echo_llm()
            return await asyncio.wait_for(wf.execute(topic), timeout=EXECUTE_TIMEOUT)

        first = await _run("lunar greenhouse calibration")
        second = await _run("harbor invoice reconciliation")
        assert "lunar greenhouse" in first["openings"]["pro"].lower()
        assert "harbor invoice" in second["openings"]["pro"].lower()
        assert first["openings"]["pro"] != second["openings"]["pro"]
        assert first["topic"] == "lunar greenhouse calibration"


class TestRoundsActuallyRun:
    @pytest.mark.asyncio
    async def test_all_rounds_run_and_counted(self):
        wf = DebateWorkflow()
        wf.llm = _echo_llm()
        result = await asyncio.wait_for(wf.execute("test topic"), timeout=EXECUTE_TIMEOUT)
        assert result["rounds_run"] == ["opening", "rebuttal", "cross_examination", "closing", "synthesis"]
        assert result["rounds_completed"] == 5
        assert result["degraded"] is False
        assert set(result["cross_examinations"]) == {"pro", "con", "neutral"}
        assert all(result["cross_examinations"].values())

    @pytest.mark.asyncio
    async def test_empty_phases_counted_honestly(self):
        llm = AsyncMock()
        llm.get_model_for_role = MagicMock(return_value="mock-model")
        llm.generate.return_value = ""
        wf = DebateWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(wf.execute("test topic"), timeout=EXECUTE_TIMEOUT)
        assert result["rounds_run"] == []
        assert result["rounds_completed"] == 0
        assert result["degraded"] is True
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_malformed_positions_get_defaults(self):
        wf = DebateWorkflow()
        wf.llm = _echo_llm()
        result = await asyncio.wait_for(
            wf.execute("test topic", {"positions": {"pro": "just a string", "con": {}}}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert set(result["openings"]) == {"pro", "con"}


class TestJudging:
    @pytest.mark.asyncio
    async def test_judge_parses_verdict(self):
        llm = AsyncMock()
        llm.generate.return_value = '{"score": 8, "stance": "supports", "notes": "strong case"}'
        wf = DebateWorkflow()
        wf.llm = llm
        out = await wf.judge_statement("topic", "In favor", "we should do it because reasons")
        assert out == {"score": 8.0, "stance": "supports", "notes": "strong case"}

    @pytest.mark.asyncio
    async def test_judge_unstructured_is_unknown(self):
        llm = AsyncMock()
        llm.generate.return_value = "both sides made sense honestly"
        wf = DebateWorkflow()
        wf.llm = llm
        out = await wf.judge_statement("topic", "In favor", "some text")
        assert out["score"] is None
        assert out["stance"] == "unknown"
        assert "both sides" in out["notes"]

    @pytest.mark.asyncio
    async def test_judge_empty_text(self):
        wf = DebateWorkflow()
        wf.llm = _echo_llm()
        out = await wf.judge_statement("topic", "In favor", "   ")
        assert out == {"score": None, "stance": "unknown", "notes": "Nothing to judge."}

    @pytest.mark.asyncio
    async def test_execute_judges_openings(self):
        wf = DebateWorkflow()
        wf.llm = _echo_llm()
        result = await asyncio.wait_for(wf.execute("test topic"), timeout=EXECUTE_TIMEOUT)
        assert set(result["judging"]) == {"pro", "con", "neutral"}
        # Echo output is not JSON, so verdicts are honestly unknown.
        assert all(v["stance"] == "unknown" for v in result["judging"].values())

    def test_normalize_judgment(self):
        assert _normalize_judgment({"score": "bad", "stance": "BOGUS"})["score"] == 0.0
        assert _normalize_judgment({"score": "bad", "stance": "BOGUS"})["stance"] == "unknown"
        assert _normalize_judgment({"score": 99, "stance": "supports"})["score"] == 10.0
        assert _normalize_judgment({"score": -3, "stance": "opposes"})["score"] == 0.0
        assert _normalize_judgment({"score": 7, "stance": "opposes"})["stance"] == "opposes"

    def test_parse_json_obj(self):
        assert _parse_json_obj('```json\n{"a": 1}\n```') == {"a": 1}
        assert _parse_json_obj('prefix {"a": 1} suffix') == {"a": 1}
        assert _parse_json_obj("no json") is None
        assert _parse_json_obj("") is None
        assert _parse_json_obj("[1, 2]") is None
        assert _parse_json_obj("[unclosed") is None
        assert _parse_json_obj("{not valid json}") is None


class TestGenerateRobustness:
    @pytest.mark.asyncio
    async def test_retries_empty_once(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["", "hello"]
        wf = DebateWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == "hello"

    @pytest.mark.asyncio
    async def test_failure_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = RuntimeError("down")
        wf = DebateWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_error_string_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["[Ollama error] bad", "[Ollama error] bad"]
        wf = DebateWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_passes_think_flag(self):
        llm = AsyncMock()
        llm.generate.return_value = "text"
        wf = DebateWorkflow()
        wf.llm = llm
        await wf._generate("prompt")
        _, kwargs = llm.generate.call_args
        assert kwargs["think"] is False
        assert kwargs["role"] == "critic"
