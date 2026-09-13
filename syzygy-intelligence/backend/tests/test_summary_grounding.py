"""Grounding tests for the summary workflow.

Proves outputs depend on inputs, compression is measured (not claimed),
and empty input is reported instead of padded.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.workflows.summary import SummaryWorkflow, _numbered, _word_count

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
    async def test_outputs_depend_on_documents(self):
        async def _run(docs):
            wf = SummaryWorkflow()
            wf.llm = _echo_llm()
            return await asyncio.wait_for(
                wf.execute("summarize", {"documents": docs}), timeout=EXECUTE_TIMEOUT
            )

        first = await _run(["lunar greenhouse calibration procedures in detail"])
        second = await _run(["harbor invoice reconciliation audit procedures in detail"])
        assert "lunar greenhouse" in first["summary"].lower()
        assert "harbor invoice" in second["summary"].lower()
        assert first["summary"] != second["summary"]
        assert first["document_count"] == 1


class TestCompressionMeasured:
    @pytest.mark.asyncio
    async def test_counts_are_real(self):
        wf = SummaryWorkflow()
        wf.llm = _echo_llm()
        docs = ["word " * 100, "term " * 50]
        result = await asyncio.wait_for(
            wf.execute("summarize", {"documents": docs}), timeout=EXECUTE_TIMEOUT
        )
        assert result["input_words"] == 150
        assert result["summary_words"] == len(result["summary"].split())
        assert result["compression_ratio"] == round(result["summary_words"] / 150, 3)

    @pytest.mark.asyncio
    async def test_empty_documents_reported(self):
        wf = SummaryWorkflow()
        wf.llm = _echo_llm()
        result = await wf.execute("summarize", {"documents": ["", "   "]})
        assert result["status"] == "completed"
        assert result["document_count"] == 0
        assert result["summary"] == ""
        assert "No documents" in result["note"]

    @pytest.mark.asyncio
    async def test_bloated_summary_condensed(self):
        llm = AsyncMock()
        llm.generate.side_effect = [
            "points",  # key points
            "themes",  # themes
            "insights text here",  # insights
            "word " * 60,  # bloated first summary (60 words)
            "short version here",  # condensed retry
        ]
        wf = SummaryWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("summarize", {"documents": ["alpha beta gamma delta"]}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["summary"] == "short version here"
        assert result["compression_ratio"] == round(3 / 4, 3)

    @pytest.mark.asyncio
    async def test_condense_kept_when_retry_worse(self):
        llm = AsyncMock()
        llm.generate.side_effect = [
            "points",
            "themes",
            "insights text here",
            "word " * 60,
            "even longer retry text " * 20,
        ]
        wf = SummaryWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("summarize", {"documents": ["alpha beta gamma delta"]}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["summary"] == ("word " * 60).strip()
        assert result["compression_ratio"] > 1.0

    def test_word_count(self):
        assert _word_count("") == 0
        assert _word_count("  a  b c ") == 3

    def test_numbered(self):
        out = _numbered(["aaa", "bbb"])
        assert "--- Document 1 ---" in out
        assert "--- Document 2 ---" in out
        assert "aaa" in out


class TestGenerateRobustness:
    @pytest.mark.asyncio
    async def test_retries_empty_once(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["", "hello"]
        wf = SummaryWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == "hello"

    @pytest.mark.asyncio
    async def test_failure_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = RuntimeError("down")
        wf = SummaryWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_error_string_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["[Ollama error] bad", "[Ollama error] bad"]
        wf = SummaryWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_passes_think_flag(self):
        llm = AsyncMock()
        llm.generate.return_value = "text"
        wf = SummaryWorkflow()
        wf.llm = llm
        await wf._generate("prompt")
        _, kwargs = llm.generate.call_args
        assert kwargs["think"] is False
        assert kwargs["role"] == "synthesis"
