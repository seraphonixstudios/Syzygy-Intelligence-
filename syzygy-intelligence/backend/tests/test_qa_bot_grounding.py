"""Grounding tests for the QA-bot workflow.

Proves retrieval reports exactly the documents the model found relevant,
answers are traceable to queries, and empty knowledge bases are labeled.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.workflows.qa_bot import QABotWorkflow, _parse_sources

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
    async def test_answers_depend_on_query(self):
        async def _run(query):
            wf = QABotWorkflow()
            wf.llm = _echo_llm()
            wf.knowledge_base = {"doc1": "Content about lunar greenhouses."}
            return await asyncio.wait_for(wf.execute(query), timeout=EXECUTE_TIMEOUT)

        first = await _run("lunar greenhouse calibration")
        second = await _run("harbor invoice reconciliation")
        assert "lunar greenhouse" in first["answer"].lower()
        assert "harbor invoice" in second["answer"].lower()
        assert first["answer"] != second["answer"]
        assert first["query"] == "lunar greenhouse calibration"


class TestRetrieval:
    @pytest.mark.asyncio
    async def test_only_relevant_sources_reported(self):
        llm = AsyncMock()
        llm.generate.return_value = "Passage about billing.\nSOURCES: doc2"
        wf = QABotWorkflow()
        wf.llm = llm
        wf.knowledge_base = {"doc1": "Content A.", "doc2": "Content B."}
        result = await wf.retrieve_context("billing question")
        assert result["sources"] == ["doc2"]
        assert result["grounded"] is True
        assert "unconfirmed" not in result["note"]

    @pytest.mark.asyncio
    async def test_unknown_ids_filtered(self):
        llm = AsyncMock()
        llm.generate.return_value = "Some text.\nSOURCES: doc2, ghost_doc"
        wf = QABotWorkflow()
        wf.llm = llm
        wf.knowledge_base = {"doc1": "A.", "doc2": "B."}
        result = await wf.retrieve_context("q")
        assert result["sources"] == ["doc2"]

    @pytest.mark.asyncio
    async def test_missing_sources_line_is_labeled(self):
        llm = AsyncMock()
        llm.generate.return_value = "A fine answer with no source line."
        wf = QABotWorkflow()
        wf.llm = llm
        wf.knowledge_base = {"doc1": "A.", "doc2": "B."}
        result = await wf.retrieve_context("q")
        assert result["sources"] == ["doc1", "doc2"]
        assert "unconfirmed" in result["note"]
        assert result["grounded"] is True

    @pytest.mark.asyncio
    async def test_empty_kb_is_ungrounded(self):
        wf = QABotWorkflow()
        wf.llm = _echo_llm()
        result = await wf.execute("anything at all")
        assert result["grounded"] is False
        assert "No documents ingested" in result["context_used"]["note"]

    def test_parse_sources(self):
        assert _parse_sources("text\nSOURCES: a, b", ["a", "b", "c"]) == ["a", "b"]
        assert _parse_sources("SOURCES: ghost", ["a"]) == []
        assert _parse_sources("SOURCES: ", ["a"]) == []
        assert _parse_sources("no line here", ["a"]) == []
        assert _parse_sources("", ["a"]) == []
        assert _parse_sources("sources: A", ["A"]) == ["A"]


class TestIngest:
    @pytest.mark.asyncio
    async def test_ingest_stores_and_summarizes(self):
        wf = QABotWorkflow()
        wf.llm = _echo_llm()
        result = await wf.execute("Some text", {"action": "ingest", "doc_id": "d1"})
        assert result["status"] == "completed"
        assert result["result"]["doc_id"] == "d1"
        assert wf.knowledge_base["d1"] == "Some text"
        assert "d1" in result["result"]["summary"]


class TestGenerateRobustness:
    @pytest.mark.asyncio
    async def test_retries_empty_once(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["", "hello"]
        wf = QABotWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == "hello"

    @pytest.mark.asyncio
    async def test_failure_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = RuntimeError("down")
        wf = QABotWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_error_string_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["[Ollama error] bad", "[Ollama error] bad"]
        wf = QABotWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_passes_think_flag(self):
        llm = AsyncMock()
        llm.generate.return_value = "text"
        wf = QABotWorkflow()
        wf.llm = llm
        await wf._generate("prompt")
        _, kwargs = llm.generate.call_args
        assert kwargs["think"] is False
        assert kwargs["role"] == "sage"
