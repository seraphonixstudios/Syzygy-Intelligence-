"""Phase 2 grounding tests — research, content, and test_gen workflows.

Proves outputs depend on inputs, validation/analysis text is kept (not
discarded), diffs are computed (not asserted), and tests are really executed.
"""

from __future__ import annotations

import asyncio
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workflows.content import ContentWorkflow, _diff_stats
from app.workflows.research import ResearchWorkflow
from app.workflows.test_gen import TestGenWorkflow

EXECUTE_TIMEOUT = 60.0


def _echo_llm():
    llm = AsyncMock()
    llm.get_model_for_role = MagicMock(return_value="mock-model")

    async def _gen(prompt, **kwargs):
        return f"ECHO::{prompt[:150]}"

    llm.generate.side_effect = _gen
    return llm


def _mock_search_tool(results):
    tool = AsyncMock()
    tool.execute.return_value = {"results": results}
    return tool


# ===================================================================
# Research
# ===================================================================

class TestResearchGrounding:
    @pytest.mark.asyncio
    async def test_outputs_depend_on_task(self):
        def _wf(topic):
            wf = ResearchWorkflow()
            wf.llm = _echo_llm()
            wf.search_tool = _mock_search_tool([
                {"url": "http://example.com/1", "title": "T1", "snippet": "S1"},
            ])
            return wf

        first = await asyncio.wait_for(_wf("quantum dots").execute("quantum dots"), timeout=EXECUTE_TIMEOUT)
        second = await asyncio.wait_for(_wf("sourdough bread").execute("sourdough bread"), timeout=EXECUTE_TIMEOUT)
        assert "quantum dots" in first["synthesis"].lower()
        assert "sourdough" in second["synthesis"].lower()
        assert first["synthesis"] != second["synthesis"]
        assert first["grounded"] is True

    @pytest.mark.asyncio
    async def test_validation_text_is_kept(self):
        wf = ResearchWorkflow()
        wf.llm = _echo_llm()
        out = await wf.validate([{"url": "http://example.com/1", "snippet": "Claim X"}])
        assert out["findings"][0]["validated"] is True
        assert "Claim X" in out["validation"]  # validation prompt echoes the finding
        assert "Cross-validate" in out["validation"]

    @pytest.mark.asyncio
    async def test_synthesize_cites_sources(self):
        wf = ResearchWorkflow()
        wf.llm = _echo_llm()
        findings = [
            {"url": "http://example.com/1", "title": "First", "snippet": "AAA"},
            {"url": "http://example.com/2", "title": "Second", "snippet": "BBB"},
        ]
        out = await wf.synthesize(findings, "test query")
        assert out["grounded"] is True
        assert out["sources"] == [
            {"n": 1, "title": "First", "url": "http://example.com/1"},
            {"n": 2, "title": "Second", "url": "http://example.com/2"},
        ]
        assert "[1]" in out["synthesis"]  # prompt carries numbered sources through the echo

    @pytest.mark.asyncio
    async def test_synthesize_ungrounded_without_sources(self):
        wf = ResearchWorkflow()
        wf.llm = _echo_llm()
        out = await wf.synthesize([], "test query")
        assert out["grounded"] is False
        assert out["sources"] == []

    @pytest.mark.asyncio
    async def test_search_falls_back_to_query(self):
        wf = ResearchWorkflow()
        llm = AsyncMock()
        llm.generate.return_value = "no bullets here"
        wf.llm = llm
        wf.search_tool = _mock_search_tool([
            {"url": "http://example.com/1", "title": "T", "snippet": "S"},
        ])
        results = await wf.search("fallback query")
        assert len(results) == 1
        wf.search_tool.execute.assert_called_once_with("fallback query", num_results=5)

    @pytest.mark.asyncio
    async def test_search_tolerates_tool_errors(self):
        wf = ResearchWorkflow()
        wf.llm = _echo_llm()
        tool = AsyncMock()
        tool.execute.side_effect = RuntimeError("network down")
        wf.search_tool = tool
        assert await wf.search("anything") == []

    @pytest.mark.asyncio
    async def test_generate_retries_then_fails(self):
        wf = ResearchWorkflow()
        llm = AsyncMock()
        llm.generate.side_effect = ["", "recovered"]
        wf.llm = llm
        assert await wf._generate("prompt") == "recovered"

        llm2 = AsyncMock()
        llm2.generate.side_effect = RuntimeError("down")
        wf.llm = llm2
        assert await wf._generate("prompt") == ""

        llm3 = AsyncMock()
        llm3.generate.side_effect = ["[Ollama error] bad", "[Ollama error] bad"]
        wf.llm = llm3
        assert await wf._generate("prompt") == ""


# ===================================================================
# Search fallback (DuckDuckGo gated -> Wikipedia)
# ===================================================================

class TestSearchFallback:
    @pytest.mark.asyncio
    async def test_wikipedia_used_when_ddg_empty(self):
        from app.tools.search import SearchTool

        tool = SearchTool()
        with (
            patch.object(SearchTool, "_duckduckgo", return_value=[]),
            patch.object(
                SearchTool, "_wikipedia",
                return_value=[{"title": "T", "url": "http://example.com/t", "snippet": "S"}],
            ),
        ):
            result = await tool.execute(query="test", num_results=3)
        assert result["source"] == "wikipedia"
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_duckduckgo_preferred(self):
        from app.tools.search import SearchTool

        tool = SearchTool()
        with patch.object(
            SearchTool, "_duckduckgo",
            return_value=[{"title": "T", "url": "http://example.com/t", "snippet": "S"}],
        ):
            result = await tool.execute(query="test", num_results=3)
        assert result["source"] == "duckduckgo"

    @pytest.mark.asyncio
    async def test_none_when_all_empty(self):
        from app.tools.search import SearchTool

        tool = SearchTool()
        with (
            patch.object(SearchTool, "_duckduckgo", return_value=[]),
            patch.object(SearchTool, "_wikipedia", return_value=[]),
        ):
            result = await tool.execute(query="test", num_results=3)
        assert result["source"] == "none"
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_wikipedia_parses_and_strips_html(self):
        from app.tools.search import SearchTool

        payload = {"query": {"search": [
            {"title": "Asyncio", "snippet": 'Concurrency with <span class="searchmatch">async</span> lib'},
        ]}}
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = payload
        client = MagicMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        client.get = AsyncMock(return_value=response)
        with patch("httpx.AsyncClient", return_value=client):
            results = await SearchTool()._wikipedia("asyncio", 5)
        assert results == [{
            "title": "Asyncio",
            "url": "https://en.wikipedia.org/wiki/Asyncio",
            "snippet": "Concurrency with async lib",
        }]

    @pytest.mark.asyncio
    async def test_wikipedia_failures_return_empty(self):
        from app.tools.search import SearchTool

        assert await SearchTool()._wikipedia("   ", 5) == []
        bad = MagicMock()
        bad.status_code = 500
        client = MagicMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        client.get = AsyncMock(return_value=bad)
        with patch("httpx.AsyncClient", return_value=client):
            assert await SearchTool()._wikipedia("x", 5) == []
        with patch("httpx.AsyncClient", side_effect=RuntimeError("down")):
            assert await SearchTool()._wikipedia("x", 5) == []


# ===================================================================
# Content
# ===================================================================

class TestContentGrounding:
    @pytest.mark.asyncio
    async def test_outputs_depend_on_topic(self):
        async def _run(topic):
            wf = ContentWorkflow()
            wf.llm = _echo_llm()
            return await asyncio.wait_for(wf.execute(topic), timeout=EXECUTE_TIMEOUT)

        first = await _run("quantum dots")
        second = await _run("sourdough bread")
        assert "quantum dots" in first["research"]["research"].lower()
        assert "sourdough" in second["research"]["research"].lower()
        assert first["research"]["research"] != second["research"]["research"]
        assert first["degraded"] is False
        assert first["status"] == "completed"

    @pytest.mark.asyncio
    async def test_edit_reports_real_diff(self):
        llm = AsyncMock()
        llm.generate.return_value = "line one\nline TWO\nline three\nline four"
        wf = ContentWorkflow()
        wf.llm = llm
        out = await wf.edit({"draft": "line one\nline two\nline three"})
        assert out["changes"] == "2 additions, 1 deletions across 1 hunk(s)"
        assert "-line two" in out["diff"]
        assert "+line TWO" in out["diff"]
        assert out["word_count"] == 8

    @pytest.mark.asyncio
    async def test_degraded_when_phases_empty(self):
        llm = AsyncMock()
        llm.generate.return_value = ""
        wf = ContentWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(wf.execute("topic"), timeout=EXECUTE_TIMEOUT)
        assert result["degraded"] is True
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_generate_failure_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = RuntimeError("down")
        wf = ContentWorkflow()
        wf.llm = llm
        assert await wf.research("topic") == {"topic": "topic", "research": ""}

    def test_diff_stats(self):
        assert _diff_stats("a\nb", "a\nb") == {"added_lines": 0, "removed_lines": 0, "hunks": 0, "diff": ""}
        stats = _diff_stats("", "hello")
        assert stats["added_lines"] == 1


# ===================================================================
# Test generation + real execution
# ===================================================================

PASSING_CODE = "def add(a, b):\n    return a + b\n"
PASSING_TESTS = "def test_add():\n    from main import add\n    assert add(1, 2) == 3\n"
FAILING_TESTS = "def test_add():\n    from main import add\n    assert add(1, 2) == 99\n"


class TestTestGenGrounding:
    @pytest.mark.asyncio
    async def test_analysis_depends_on_code(self):
        async def _run(code):
            wf = TestGenWorkflow()
            wf.llm = _echo_llm()
            return await asyncio.wait_for(
                wf.execute("make tests", {"code": code, "language": "python"}),
                timeout=EXECUTE_TIMEOUT,
            )

        first = await _run("def add(a, b):\n    return a + b\n")
        second = await _run("def multiply(x, y):\n    return x * y\n")
        assert "def add" in first["analysis"]["analysis"]
        assert "def multiply" in second["analysis"]["analysis"]
        assert first["analysis"]["analysis"] != second["analysis"]["analysis"]

    @pytest.mark.asyncio
    async def test_passing_execution(self):
        llm = AsyncMock()
        llm.generate.return_value = PASSING_TESTS
        wf = TestGenWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("make tests", {"code": PASSING_CODE, "language": "python"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["execution"]["success"] is True
        assert result["execution"]["passed"] >= 1
        assert "unit_tests" in result

    @pytest.mark.asyncio
    async def test_failing_execution_reported(self):
        llm = AsyncMock()
        llm.generate.return_value = FAILING_TESTS
        wf = TestGenWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("make tests", {"code": PASSING_CODE, "language": "python"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["execution"]["success"] is False
        assert result["execution"]["failed"] >= 1

    @pytest.mark.asyncio
    async def test_non_code_input_rejected(self):
        wf = TestGenWorkflow()
        wf.llm = _echo_llm()
        result = await wf.execute("Test calculator function")
        assert result["status"] == "completed"
        assert result["note"] == "no-code-provided"
        assert "unit_tests" not in result

    @pytest.mark.asyncio
    async def test_unparseable_tests_noted(self):
        llm = AsyncMock()
        llm.generate.return_value = "here are some thoughts about testing"
        wf = TestGenWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.execute("make tests", {"code": PASSING_CODE, "language": "python"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["execution"]["note"] == "no-tests-generated"

    @pytest.mark.asyncio
    async def test_non_python_skips_execution(self):
        wf = TestGenWorkflow()
        wf.llm = _echo_llm()
        result = await asyncio.wait_for(
            wf.execute("make tests", {"code": PASSING_CODE, "language": "javascript"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["execution"]["note"] == "not-run"

    @pytest.mark.asyncio
    async def test_generate_failure_yields_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = RuntimeError("down")
        wf = TestGenWorkflow()
        wf.llm = llm
        assert await wf.analyze_code("def f(): pass") == {"analysis": ""}

    @pytest.mark.asyncio
    async def test_error_strings_exhausted(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["[Ollama error] bad", "[LiteLLM error] bad"]
        wf = TestGenWorkflow()
        wf.llm = llm
        assert await wf.analyze_code("def f(): pass") == {"analysis": ""}

    def test_run_tests_timeout(self):
        wf = TestGenWorkflow()
        out = wf.run_tests("x = 1", "def test_a():\n    assert True\n", timeout=0)
        assert out["note"] == "pytest timed out"
        assert out["success"] is False

    def test_run_tests_crash(self):
        wf = TestGenWorkflow()
        with patch(
            "app.tools.sandbox.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=2, stdout="boom", stderr=""),
        ):
            out = wf.run_tests("x = 1", "def test_a():\n    assert True\n")
        assert out["note"] == "pytest crashed before collecting tests"

    def test_run_tests_no_tests_collected(self):
        wf = TestGenWorkflow()
        out = wf.run_tests("x = 1", "def helper():\n    return 1\n")
        assert out["note"] == "pytest collected no tests"
