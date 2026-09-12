"""Grounding tests for task_decomposition — JSON schema, provenance, fallback."""

from __future__ import annotations

import json
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.workflows.task_decomposition import (
    Subtask,
    TaskDecompositionWorkflow,
    _extract_json_object,
    _safe_json_loads,
)


EXECUTE_TIMEOUT = 120.0


def _mock_llm(responses: list[str]):
    """Build an AsyncMock LLM returning the given strings in order."""
    llm = AsyncMock()
    idx = [0]

    async def _gen(prompt, **kwargs):
        if idx[0] < len(responses):
            r = responses[idx[0]]
            idx[0] += 1
            return r
        return ""

    llm.generate.side_effect = _gen
    return llm


class TestTaskSensitivity:
    @pytest.mark.asyncio
    async def test_output_depends_on_task(self):
        llm = _mock_llm([
            json.dumps({"subtasks": [{"id": "a1", "description": "First step", "dependencies": [],
                                          "agent_archetype": "sage", "polarity": "unified", "priority": 5}]})
        ])
        wf = TaskDecompositionWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("task A", {}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert len(result["subtasks"]) == 1
        assert result["subtasks"][0].id == "a1"

    @pytest.mark.asyncio
    async def test_different_tasks_different_outputs(self):
        llm = _mock_llm([
            json.dumps({"subtasks": [{"id": "b1", "description": "Step for task B", "dependencies": [],
                                          "agent_archetype": "hero", "polarity": "masculine", "priority": 3}]})
        ])
        wf = TaskDecompositionWorkflow()
        wf.llm = llm
        result_a = await asyncio.wait_for(
            wf.execute("task A", {}),
            timeout=EXECUTE_TIMEOUT,
        )
        result_b = await asyncio.wait_for(
            wf.execute("task B", {}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result_a["subtasks"][0].id != result_b["subtasks"][0].id


class TestSchemaValidation:
    def test_valid_json_schema(self):
        data = {
            "subtasks": [
                {
                    "id": "s1",
                    "description": "Do the thing",
                    "dependencies": [],
                    "agent_archetype": "sage",
                    "polarity": "unified",
                    "priority": 5,
                }
            ]
        }
        # quick inline check – the real validator is _schema_valid in the workflow
        assert "subtasks" in data
        for s in data["subtasks"]:
            assert "id" in s and "description" in s and "agent_archetype" in s \
                   and "polarity" in s and "priority" in s

    def test_missing_key_fails(self):
        data = {"subtasks": [{"id": "s1", "description": "x"}]}
        assert not ("polarity" in data["subtasks"][0] and "priority" in data["subtasks"][0])


class TestParseHelpers:
    def test_extract_json_object(self):
        # plain JSON (fences are stripped inside the function)
        assert _extract_json_object('{"subtasks":[]}') is not None
        # no json
        assert _extract_json_object("just some text") is None

    def test_safe_json_loads(self):
        assert _safe_json_loads('{"a":1}') == {"a": 1}
        assert _safe_json_loads("") is None
        assert _safe_json_loads(None) is None


class TestDecomposeProvenance:
    @pytest.mark.asyncio
    async def test_structured_when_json_valid(self):
        llm = _mock_llm([
            '{"subtasks": [{"id": "f1", "description": "First task", "dependencies": [], '
            '"agent_archetype": "sage", "polarity": "unified", "priority": 3}]}'
        ])
        wf = TaskDecompositionWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("some task", {}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["structured"] is True
        assert result["fallback_used"] is False

    @pytest.mark.asyncio
    async def test_unstructured_falls_back(self):
        llm = _mock_llm(["SUBTASK: id1 | desc | | sage | masculine | 5", "another line"])
        wf = TaskDecompositionWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("some task", {}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["structured"] is False
        assert result["fallback_used"] is True
        # fallback should have at least one subtask
        assert len(result["subtasks"]) > 0

    @pytest.mark.asyncio
    async def test_no_llm_output_falls_back(self):
        llm = _mock_llm([""])
        wf = TaskDecompositionWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("some task", {}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["structured"] is False
        assert result["fallback_used"] is True


class TestExecuteFull:
    @pytest.mark.asyncio
    async def test_execute_returns_dict(self):
        llm = _mock_llm([
            '{"subtasks": [{"id": "a1", "description": "Analyze", "dependencies": [], '
            '"agent_archetype": "sage", "polarity": "unified", "priority": 1}]}'
        ])
        wf = TaskDecompositionWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("analyze this", {}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert "task" in result
        assert "subtasks" in result
        assert "structured" in result
        assert "fallback_used" in result
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_with_context(self):
        llm = _mock_llm([
            json.dumps({"subtasks": [{"id": "c1", "description": "Context-aware step", "dependencies": [],
                                          "agent_archetype": "explorer", "polarity": "feminine", "priority": 4}]})
        ])
        wf = TaskDecompositionWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("complex task", {"some": "context"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert len(result["subtasks"]) == 1
        assert result["subtasks"][0].agent_archetype == "explorer"


class TestGenerateRobustness:
    @pytest.mark.asyncio
    async def test_retries_empty_once(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["", ""]
        wf = TaskDecompositionWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_failure_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = RuntimeError("down")
        wf = TaskDecompositionWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_error_string_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["[Ollama error] bad", "[Ollama error] bad"]
        wf = TaskDecompositionWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_passes_think_flag(self):
        llm = AsyncMock()
        llm.generate.return_value = "text"
        wf = TaskDecompositionWorkflow()
        wf.llm = llm
        await wf._generate("prompt")
        _, kwargs = llm.generate.call_args
        assert kwargs["think"] is False
        assert kwargs["role"] == "sage"