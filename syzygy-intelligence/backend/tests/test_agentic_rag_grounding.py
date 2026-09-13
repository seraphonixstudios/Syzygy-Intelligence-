"""Grounding tests for the agentic-RAG workflow.

Proves sub-query extraction never silently skips retrieval over formatting,
and results report real hop counts plus grounded flags.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.workflows.agentic_rag import AgenticRagWorkflow, _extract_sub_queries

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
    async def test_outputs_depend_on_query(self):
        async def _run(query):
            wf = AgenticRagWorkflow()
            wf.llm = _echo_llm()
            return await asyncio.wait_for(wf.execute(query), timeout=EXECUTE_TIMEOUT)

        first = await _run("lunar greenhouse calibration")
        second = await _run("harbor invoice reconciliation")
        assert "lunar greenhouse" in first["synthesized_answer"].lower()
        assert "harbor invoice" in second["synthesized_answer"].lower()
        assert first["synthesized_answer"] != second["synthesized_answer"]


class TestRetrieval:
    @pytest.mark.asyncio
    async def test_bulleted_decomposition_retrieves(self):
        llm = AsyncMock()
        llm.generate.side_effect = [
            "- first angle\n- second angle\n",  # decompose (bullets, not numbers)
            "retrieved one",
            "retrieved two",
            "synthesis",
            "validation",
        ]
        wf = AgenticRagWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("query", {"knowledge_base": "Some KB content here."}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["retrieval_hops"] == 2
        assert result["grounded"] is True
        assert result["retrieval_note"] == ""

    @pytest.mark.asyncio
    async def test_empty_decomposition_skips_honestly(self):
        llm = AsyncMock()
        llm.generate.return_value = ""
        wf = AgenticRagWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("query", {"knowledge_base": "Some KB content here."}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["retrieval_hops"] == 0
        assert result["grounded"] is False
        assert "No sub-queries extracted" in result["retrieval_note"]

    @pytest.mark.asyncio
    async def test_no_kb_labeled(self):
        wf = AgenticRagWorkflow()
        wf.llm = _echo_llm()
        result = await asyncio.wait_for(wf.execute("query"), timeout=EXECUTE_TIMEOUT)
        assert result["grounded"] is False
        assert "No knowledge base" in result["retrieval_note"]
        assert result["retrieval_hops"] == 0

    def test_extract_sub_queries(self):
        assert _extract_sub_queries("1. alpha\n2. beta\n") == ["alpha", "beta"]
        assert _extract_sub_queries("- alpha\n- beta\n") == ["alpha", "beta"]
        assert _extract_sub_queries("* alpha\n* beta\n") == ["alpha", "beta"]
        assert _extract_sub_queries("a sufficiently long plain line here") == [
            "a sufficiently long plain line here"
        ]
        assert _extract_sub_queries("") == []
        assert _extract_sub_queries("hi") == []
        assert len(_extract_sub_queries("\n".join(f"{i}. query number {i}" for i in range(9)))) == 5


class TestGenerateRobustness:
    @pytest.mark.asyncio
    async def test_retries_empty_once(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["", "hello"]
        wf = AgenticRagWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == "hello"

    @pytest.mark.asyncio
    async def test_failure_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = RuntimeError("down")
        wf = AgenticRagWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_error_string_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["[Ollama error] bad", "[Ollama error] bad"]
        wf = AgenticRagWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_passes_think_flag(self):
        llm = AsyncMock()
        llm.generate.return_value = "text"
        wf = AgenticRagWorkflow()
        wf.llm = llm
        await wf._generate("prompt")
        _, kwargs = llm.generate.call_args
        assert kwargs["think"] is False
        assert kwargs["role"] == "explorer"
