"""Grounding tests for translate — round‑trip fidelity, divergence score, degraded flag."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.workflows.translate import (
    _compute_divergence,
    _parse_json_obj,
    TranslateWorkflow,
)

EXECUTE_TIMEOUT = 120.0


def _mock_llm(responses: list[str]):
    """Build an AsyncMock LLM that returns the given responses in order."""
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
    async def test_outputs_depend_on_languages(self):
        responses = [
            "Hola, ¿cómo estás?",
            "Hello, how are you?",
        ]
        llm = _mock_llm(responses)
        wf = TranslateWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("greeting", {"source_language": "english", "target_language": "spanish"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert "spanish" in result["target_language"]
        assert "english" in result["source_language"]
        assert "roundtrip" in result


class TestRoundtrip:
    @pytest.mark.asyncio
    async def test_roundtrip_empty_text(self):
        llm = _mock_llm(["", ""])
        wf = TranslateWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("empty", {"source_language": "english", "target_language": "spanish"}),
            timeout=EXECUTE_TIMEOUT,
        )
        rt = result.get("roundtrip", {})
        assert rt.get("degraded") is True

    @pytest.mark.asyncio
    async def test_divergence_identical(self):
        assert _compute_divergence("hello world", "hello world") == 0.0

    @pytest.mark.asyncio
    async def test_divergence_completely_different(self):
        assert _compute_divergence("hello", "goodbye") == 1.0

    @pytest.mark.asyncio
    async def test_divergence_partial_overlap(self):
        assert _compute_divergence("hello world", "hello there") == 0.5


class TestDivergence:
    def test_identical(self):
        assert _compute_divergence("hello world", "hello world") == 0.0

    def test_completely_different(self):
        assert _compute_divergence("hello", "goodbye") == 1.0

    def test_partial_overlap(self):
        # "hello world" vs "hello there": "world" missing -> 1/2 = 0.5
        assert _compute_divergence("hello world", "hello there") == 0.5

    def test_empty_original(self):
        assert _compute_divergence("", "anything") == 1.0

    def test_empty_back(self):
        assert _compute_divergence("hello", "") == 1.0


class TestProvenance:
    def test_parse_json_obj(self):
        assert _parse_json_obj('```json\n{"a":1}\n```') == {"a": 1}
        assert _parse_json_obj("no json") is None
        assert _parse_json_obj("") is None
        assert _parse_json_obj("{bad") is None


class TestGenerateRobustness:
    @pytest.mark.asyncio
    async def test_retries_empty_once(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["", ""]
        wf = TranslateWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_failure_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = RuntimeError("down")
        wf = TranslateWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_error_string_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["[Ollama error] bad", "[Ollama error] bad"]
        wf = TranslateWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_passes_think_flag(self):
        llm = AsyncMock()
        llm.generate.return_value = "text"
        wf = TranslateWorkflow()
        wf.llm = llm
        await wf._generate("prompt")
        _, kwargs = llm.generate.call_args
        assert kwargs["think"] is False
        assert kwargs["role"] == "sage"