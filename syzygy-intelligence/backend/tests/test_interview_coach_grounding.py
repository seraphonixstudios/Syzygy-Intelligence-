"""Grounding tests for interview_coach — structured rubric, honest provenance."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.workflows.interview_coach import (
    InterviewCoachWorkflow,
    _normalize_eval,
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
    async def test_outputs_depend_on_role(self):
        async def _run(role):
            wf = InterviewCoachWorkflow()
            wf.llm = _echo_llm()
            return await asyncio.wait_for(
                wf.execute(role, {"role": role, "difficulty": "senior"}),
                timeout=EXECUTE_TIMEOUT,
            )
        first = await _run("data engineer")
        second = await _run("chef")
        assert "data engineer" in first["questions"]["questions"].lower()
        assert "chef" in second["questions"]["questions"].lower()
        assert first["difficulty"] == "senior"


class TestRubric:
    def test_normalize_eval_measured(self):
        out = _normalize_eval({
            "correctness": 7, "completeness": 5, "structure": "bad",
            "depth": 9, "communication": 6,
        })
        assert out["overall"] == round((7 + 5 + 9 + 6) / 4, 2)
        assert out["structure"] is None

    def test_normalize_eval_empty(self):
        out = _normalize_eval({})
        assert out["overall"] is None

    def test_parse_json_obj(self):
        assert _parse_json_obj('```json\n{"a": 1}\n```') == {"a": 1}
        assert _parse_json_obj("no json") is None
        assert _parse_json_obj("") is None
        assert _parse_json_obj("[1]") is None
        assert _parse_json_obj("{not valid json}") is None


class TestEvalProvenance:
    @pytest.mark.asyncio
    async def test_structured_json_method(self):
        llm = AsyncMock()
        llm.generate.return_value = (
            '{"correctness": 8, "structure": 7, "strengths": "good", '
            '"weaknesses": "x", "improvements": "y"}'
        )
        wf = InterviewCoachWorkflow()
        wf.llm = llm
        out = await wf.evaluate_answer("q", "a", "role")
        assert out["evaluation"]["structured"] is True
        assert out["evaluation"]["overall"] == round((8 + 7) / 2, 2)

    @pytest.mark.asyncio
    async def test_unstructured_prose_is_labeled(self):
        llm = AsyncMock()
        llm.generate.return_value = "the answer is decent but weak on depth"
        wf = InterviewCoachWorkflow()
        wf.llm = llm
        out = await wf.evaluate_answer("q", "a", "role")
        assert out["evaluation"]["structured"] is False
        assert out["evaluation"]["overall"] is None
        assert "decent" in out["evaluation"]["notes"]

    @pytest.mark.asyncio
    async def test_execute_counts(self):
        llm = AsyncMock()
        llm.generate.side_effect = [
            "qs",
            '{"correctness": 8, "structure": 7, "depth": 5, "communication": 6}',
            "feedback",
        ]
        wf = InterviewCoachWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("chef", {"answers": [{"question": "q1", "answer": "a1"}]}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["evaluations_present"] == 1
        assert result["structured_evals"] == 1
        assert result["notes"] == ""

    @pytest.mark.asyncio
    async def test_execute_no_answers_noted(self):
        wf = InterviewCoachWorkflow()
        wf.llm = _echo_llm()
        result = await wf.execute("chef")
        assert "no practice answers" in result["notes"]
        assert result["evaluations"] == []
        assert result["feedback"] is None


class TestGenerateRobustness:
    @pytest.mark.asyncio
    async def test_retries_empty_once(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["", "hello"]
        wf = InterviewCoachWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == "hello"

    @pytest.mark.asyncio
    async def test_failure_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = RuntimeError("down")
        wf = InterviewCoachWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_error_string_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["[Ollama error] bad", "[Ollama error] bad"]
        wf = InterviewCoachWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_passes_think_flag(self):
        llm = AsyncMock()
        llm.generate.return_value = "text"
        wf = InterviewCoachWorkflow()
        wf.llm = llm
        await wf._generate("prompt")
        _, kwargs = llm.generate.call_args
        assert kwargs["think"] is False
        assert kwargs["role"] == "sage"
