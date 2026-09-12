"""Tripwire + unit tests for the real (LLM-driven) coding workflow.

These tests prove the workflow consumes the task and the LLM — i.e. outputs
change with inputs — and that test results come from executed pytest runs.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tools.sandbox import _parse_pytest_counts as _parse_pytest_summary
from app.workflows.coding import (
    CodingWorkflow,
    _looks_like_code,
    _normalize_issue,
    _parse_files,
    _parse_json_list,
    _safe_filename,
    _score_from_issues,
)

EXECUTE_TIMEOUT = 60.0


def _echo_llm():
    """Mock LLM that echoes the prompt — proves task text flows into prompts."""
    llm = AsyncMock()
    llm.get_model_for_role = MagicMock(return_value="mock-model")

    async def _gen(prompt, **kwargs):
        return f"ECHO::{prompt[:150]}"

    llm.generate.side_effect = _gen
    return llm


def _script_llm(responses):
    """Mock LLM returning canned responses in call order."""
    llm = AsyncMock()
    llm.get_model_for_role = MagicMock(return_value="mock-model")
    llm.generate.side_effect = list(responses)
    return llm


# ===================================================================
# Tripwires: outputs must depend on inputs (no canned templates)
# ===================================================================

class TestTaskSensitivity:
    @pytest.mark.asyncio
    async def test_outputs_depend_on_task(self):
        wf = CodingWorkflow()
        wf.llm = _echo_llm()
        first = await asyncio.wait_for(
            wf.execute("Build a calculator", {"language": "python"}), timeout=EXECUTE_TIMEOUT
        )
        wf2 = CodingWorkflow()
        wf2.llm = _echo_llm()
        second = await asyncio.wait_for(
            wf2.execute("Write a haiku generator", {"language": "python"}), timeout=EXECUTE_TIMEOUT
        )
        assert first["phases"]["plan"]["summary"] != second["phases"]["plan"]["summary"]
        assert "calculator" in first["phases"]["plan"]["summary"].lower()
        assert "haiku" in second["phases"]["plan"]["summary"].lower()
        assert first["simulated"] is False

    @pytest.mark.asyncio
    async def test_no_canned_markers(self):
        wf = CodingWorkflow()
        wf.llm = _echo_llm()
        result = await asyncio.wait_for(wf.execute("Build a calculator", {}), timeout=EXECUTE_TIMEOUT)
        blob = json.dumps(result)
        assert "hexagonal architecture" not in blob
        assert "coverage_estimate" not in blob
        assert result["phases"]["implement"]["files"] == {}
        assert result["phases"]["test"]["test_results"]["passed"] == 0


# ===================================================================
# Phase fallbacks: LLM failure must be labeled, never fabricated
# ===================================================================

class TestFallbacks:
    @pytest.mark.asyncio
    async def test_all_simulated_when_llm_down(self):
        llm = AsyncMock()
        llm.get_model_for_role = MagicMock(return_value="mock-model")
        llm.generate.side_effect = RuntimeError("ollama down")
        wf = CodingWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(wf.execute("Build anything", {}), timeout=EXECUTE_TIMEOUT)
        assert result["status"] == "completed"
        assert result["simulated"] is True
        for phase in ("plan", "design", "implement", "review", "test", "document"):
            assert result["phases"][phase]["simulated"] is True

    @pytest.mark.asyncio
    async def test_error_string_treated_as_failure(self):
        llm = AsyncMock()
        llm.generate.return_value = "[Ollama error] connection refused"
        wf = CodingWorkflow()
        wf.llm = llm
        result = await wf.plan("task")
        assert result["simulated"] is True
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_empty_string_treated_as_failure(self):
        llm = AsyncMock()
        llm.generate.return_value = "   "
        wf = CodingWorkflow()
        wf.llm = llm
        assert (await wf.design("task", {"summary": "plan"}))["simulated"] is True

    @pytest.mark.asyncio
    async def test_model_fallback_without_role_helper(self):
        wf = CodingWorkflow()
        wf.llm = SimpleNamespace()  # no get_model_for_role, no generate
        result = await asyncio.wait_for(wf.execute("Build anything", {}), timeout=EXECUTE_TIMEOUT)
        assert result["simulated"] is True
        assert result["reasoning"][0]["model"] == "tinyllama:latest"


# ===================================================================
# Generate robustness: retry, think/ctx flags, format re-ask
# ===================================================================

class TestGenerateRobustness:
    @pytest.mark.asyncio
    async def test_retries_empty_once(self):
        llm = AsyncMock()
        llm.get_model_for_role = MagicMock(return_value="mock-model")
        llm.generate.side_effect = ["", "hello"]
        wf = CodingWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == "hello"
        assert llm.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_gives_up_after_two_empties(self):
        llm = AsyncMock()
        llm.get_model_for_role = MagicMock(return_value="mock-model")
        llm.generate.side_effect = ["", "  "]
        wf = CodingWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") is None

    @pytest.mark.asyncio
    async def test_passes_think_and_ctx(self):
        llm = AsyncMock()
        llm.get_model_for_role = MagicMock(return_value="mock-model")
        llm.generate.return_value = "text"
        wf = CodingWorkflow()
        wf.llm = llm
        await wf._generate("prompt", num_ctx=8192)
        _, kwargs = llm.generate.call_args
        assert kwargs["think"] is False
        assert kwargs["num_ctx"] == 8192
        assert kwargs["role"] == "coding"

    @pytest.mark.asyncio
    async def test_implement_reasks_on_prose(self):
        llm = AsyncMock()
        llm.get_model_for_role = MagicMock(return_value="mock-model")
        llm.generate.side_effect = [
            "Here is some code without fences, hope you like it",
            "```python:calc.py\nX = 1\n```",
        ]
        wf = CodingWorkflow()
        wf.llm = llm
        result = await wf.implement("task", {"summary": "design"})
        assert result["files"] == {"calc.py": "X = 1"}
        assert result.get("simulated") is not True

    @pytest.mark.asyncio
    async def test_implement_honest_when_reask_fails(self):
        llm = AsyncMock()
        llm.get_model_for_role = MagicMock(return_value="mock-model")
        llm.generate.side_effect = ["prose one", "prose two"]
        wf = CodingWorkflow()
        wf.llm = llm
        result = await wf.implement("task", {"summary": "design"})
        assert result["files"] == {}
        assert "no parseable files" in result["summary"]


# ===================================================================
# Parsing helpers
# ===================================================================

class TestParsing:
    def test_parse_lang_colon_file(self):
        files = _parse_files("```python:models.py\nX = 1\n```")
        assert files == {"models.py": "X = 1"}

    def test_parse_bare_filename(self):
        files = _parse_files("```routes.py\nY = 2\n```")
        assert files == {"routes.py": "Y = 2"}

    def test_skip_bare_language_block(self):
        assert _parse_files("```python\nZ = 3\n```") == {}

    def test_reject_traversal_and_absolute(self):
        assert _parse_files("```python:../evil.py\nbad\n```") == {}
        assert _parse_files("```python:/abs/evil.py\nbad\n```") == {}
        assert _parse_files("```python:my file.py\nbad\n```") == {}
        assert _parse_files("```python:noext\nbad\n```") == {}
        assert _parse_files("") == {}

    def test_strip_fences(self):
        from app.workflows.coding import _strip_fences

        assert _strip_fences("```python\nX = 1\n") == "X = 1"
        assert _strip_fences("no fences") == "no fences"
        assert _strip_fences("") == ""

    def test_safe_filename(self):
        assert _safe_filename("a/b.py") == "a/b.py"
        assert _safe_filename("../x.py") is None
        assert _safe_filename("/x.py") is None
        assert _safe_filename("x y.py") is None
        assert _safe_filename("noext") is None
        assert _safe_filename("") is None

    def test_looks_like_code(self):
        assert _looks_like_code("def f(): pass")
        assert not _looks_like_code("mock output")

    def test_parse_json_list_fenced(self):
        items = _parse_json_list('[{"severity": "high", "message": "m"}]')
        assert items == [{"severity": "high", "message": "m"}]

    def test_parse_json_list_invalid(self):
        assert _parse_json_list("no json here") is None
        assert _parse_json_list("") is None
        assert _parse_json_list("[not valid json]") is None
        assert _parse_json_list("[unclosed") is None

    def test_normalize_issue(self):
        assert _normalize_issue({"severity": "BOGUS", "line": "xx"})["severity"] == "info"
        assert _normalize_issue({"severity": "high", "line": "xx"})["line"] is None
        assert _normalize_issue({"severity": "high", "line": "7", "file": "a.py", "message": "m"})["line"] == 7

    def test_score_math(self):
        assert _score_from_issues([]) == 10.0
        assert _score_from_issues([{"severity": "medium"}]) == 9.0
        assert _score_from_issues([{"severity": "critical"}] * 10) == 0.0

    def test_pytest_summary(self):
        assert _parse_pytest_summary("3 passed, 1 failed, 2 skipped in 1s") == {
            "passed": 3, "failed": 1, "skipped": 2, "errors": 0,
        }
        assert _parse_pytest_summary("no tests ran")["passed"] == 0


# ===================================================================
# Review phase
# ===================================================================

class TestReview:
    @pytest.mark.asyncio
    async def test_review_parses_json(self):
        llm = AsyncMock()
        llm.generate.return_value = (
            '[{"severity": "medium", "file": "a.py", "line": 3, "message": "fix"}, '
            '{"severity": "low", "file": "b.py", "line": 1, "message": "nit"}]'
        )
        wf = CodingWorkflow()
        wf.llm = llm
        result = await wf.review("x = 1")
        assert len(result["issues"]) == 2
        assert result["score"] == 8.5  # 10 - 1.0 - 0.5

    @pytest.mark.asyncio
    async def test_review_unstructured(self):
        llm = AsyncMock()
        llm.generate.return_value = "looks fine, no json"
        wf = CodingWorkflow()
        wf.llm = llm
        result = await wf.review("x = 1")
        assert result["score"] == 0.0
        assert result["issues"][0]["severity"] == "info"

    @pytest.mark.asyncio
    async def test_review_no_code(self):
        wf = CodingWorkflow()
        wf.llm = _echo_llm()
        result = await wf.review("   ")
        assert result["score"] == 0.0
        assert result["issues"] == []


# ===================================================================
# Test phase — real pytest execution
# ===================================================================

PASSING_CODE = "def add(a, b):\n    return a + b\n"
PASSING_TESTS = "def test_add():\n    from calc import add\n    assert add(1, 2) == 3\n"
FAILING_TESTS = "def test_add():\n    from calc import add\n    assert add(1, 2) == 99\n"


class TestRealExecution:
    @pytest.mark.asyncio
    async def test_passing_suite(self):
        llm = AsyncMock()
        llm.generate.return_value = PASSING_TESTS
        wf = CodingWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.test("", "python", files={"calc.py": PASSING_CODE}), timeout=EXECUTE_TIMEOUT
        )
        assert result["test_results"]["success"] is True
        assert result["test_results"]["passed"] >= 1

    @pytest.mark.asyncio
    async def test_failing_suite_reported_honestly(self):
        llm = AsyncMock()
        llm.generate.return_value = FAILING_TESTS
        wf = CodingWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.test("", "python", files={"calc.py": PASSING_CODE}), timeout=EXECUTE_TIMEOUT
        )
        assert result["test_results"]["success"] is False
        assert result["test_results"]["failed"] >= 1

    @pytest.mark.asyncio
    async def test_no_tests_collected(self):
        llm = AsyncMock()
        llm.generate.return_value = "def helper():\n    return 1\n"
        wf = CodingWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.test("", "python", files={"calc.py": PASSING_CODE}), timeout=EXECUTE_TIMEOUT
        )
        assert result["test_results"]["success"] is False
        assert "no tests" in result["test_results"]["note"]

    @pytest.mark.asyncio
    async def test_unterminated_block_stripped(self):
        llm = AsyncMock()
        llm.generate.return_value = "```python\ndef test_ok():\n    assert True\n"
        wf = CodingWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.test("", "python", files={"ok.py": "Y = 2"}), timeout=EXECUTE_TIMEOUT
        )
        assert result["test_results"]["success"] is True
        assert result["test_results"]["passed"] >= 1

    @pytest.mark.asyncio
    async def test_no_tests_generated(self):
        llm = AsyncMock()
        llm.generate.return_value = "I cannot write tests for this"
        wf = CodingWorkflow()
        wf.llm = llm
        result = await wf.test("", "python", files={"calc.py": PASSING_CODE})
        assert result["test_results"]["note"] == "no-tests-generated"

    @pytest.mark.asyncio
    async def test_no_code(self):
        wf = CodingWorkflow()
        wf.llm = _echo_llm()
        result = await wf.test("plain english, no code here", "python")
        assert result["test_results"]["note"] == "no-code"

    @pytest.mark.asyncio
    async def test_single_code_string_runs(self):
        llm = AsyncMock()
        llm.generate.return_value = "def test_hello():\n    from main import hello\n    assert hello() == 1\n"
        wf = CodingWorkflow()
        wf.llm = llm
        result = await asyncio.wait_for(
            wf.test("def hello():\n    return 1\n", "python"), timeout=EXECUTE_TIMEOUT
        )
        assert result["test_results"]["success"] is True
        assert result["test_results"]["passed"] >= 1

    @pytest.mark.asyncio
    async def test_unsupported_language(self):
        wf = CodingWorkflow()
        wf.llm = _echo_llm()
        result = await wf.test("code", "cobol", files={"a.cob": "code"})
        assert result["test_results"]["note"] == "unsupported-language"

    @pytest.mark.asyncio
    async def test_pytest_crash_reported(self):
        wf = CodingWorkflow()
        wf.llm = _echo_llm()
        with patch(
            "app.tools.sandbox.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=2, stdout="boom", stderr=""),
        ):
            results = wf._run_tests({"a.py": "x = 1"}, "def test_a():\n    assert True\n")
        assert results["success"] is False
        assert "crashed" in results["note"]

    @pytest.mark.asyncio
    async def test_pytest_timeout(self):
        wf = CodingWorkflow()
        results = wf._run_tests({"a.py": "x = 1"}, "def test_a():\n    assert True\n", timeout=0)
        assert results["success"] is False
        assert results["note"] == "pytest timed out"

    def test_run_skips_unsafe_filenames(self):
        wf = CodingWorkflow()
        results = wf._run_tests(
            {"../evil.py": "x = 1", "ok.py": "Y = 2"},
            "def test_ok():\n    from ok import Y\n    assert Y == 2\n",
        )
        assert results["success"] is True

    def test_run_supports_subdirectories(self):
        wf = CodingWorkflow()
        results = wf._run_tests(
            {"app/calc.py": "def add(a, b):\n    return a + b\n"},
            "def test_add():\n    from app.calc import add\n    assert add(1, 2) == 3\n",
        )
        assert results["success"] is True
        assert results["passed"] >= 1


# ===================================================================
# Repair loop + implement parsing
# ===================================================================

class TestRepairLoop:
    @pytest.mark.asyncio
    async def test_repair_on_failure(self):
        buggy = "```python:calc.py\ndef add(a, b):\n    return a - b\n```"
        fixed = "```python:calc.py\ndef add(a, b):\n    return a + b\n```"
        llm = _script_llm([
            "plan text",  # plan
            "design text",  # design
            buggy,  # implement
            "[]",  # review
            PASSING_TESTS,  # test-gen attempt 1 -> fails against buggy code
            fixed,  # implement repair
            PASSING_TESTS,  # test-gen attempt 2 -> passes
            "readme text",  # document
        ])
        wf = CodingWorkflow()
        wf.llm = llm
        seen = []

        async def _progress(step, pct, info):
            seen.append(step)

        result = await asyncio.wait_for(
            wf.execute("Build an adder", {"language": "python"}, on_progress=_progress),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["test_attempts"] == 2
        assert result["phases"]["test"]["test_results"]["success"] is True
        assert result["phases"]["test"]["test_results"]["passed"] >= 1
        assert result["simulated"] is False
        assert seen == ["plan", "design", "implement", "review", "test", "document"]

    @pytest.mark.asyncio
    async def test_implement_parses_blocks(self):
        llm = AsyncMock()
        llm.generate.return_value = "```python:calc.py\nX = 1\n```\n```python:util.py\nY = 2\n```"
        wf = CodingWorkflow()
        wf.llm = llm
        result = await wf.implement("task", {"summary": "design"})
        assert sorted(result["files"]) == ["calc.py", "util.py"]

    @pytest.mark.asyncio
    async def test_document_uses_task(self):
        wf = CodingWorkflow()
        wf.llm = _echo_llm()
        result = await wf.document("Build a calculator", {})
        assert "calculator" in result["readme"].lower()


# ===================================================================
# Legacy contract: edit()/debug() unchanged
# ===================================================================

class TestLegacyHelpers:
    @pytest.mark.asyncio
    async def test_debug_ok(self):
        llm = AsyncMock()
        llm.generate.return_value = "analysis text"
        wf = CodingWorkflow()
        wf.llm = llm
        result = await wf.debug("SyntaxError", "def foo() pass")
        assert result["error"] == "SyntaxError"
        assert result["analysis"] == "analysis text"

    @pytest.mark.asyncio
    async def test_edit_missing_file(self):
        wf = CodingWorkflow()
        wf.llm = _echo_llm()
        result = await wf.edit("nonexistent_path_abc123/file.py", "fix it")
        assert result["edited"] is False
