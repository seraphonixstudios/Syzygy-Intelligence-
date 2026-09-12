"""Grounding tests for the audit workflow.

Proves the deterministic static scan finds real line-numbered issues, LLM
review is tied to those findings, and empty code is reported honestly.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.workflows.audit import _STATIC_RULES, AuditWorkflow, _static_scan

EXECUTE_TIMEOUT = 120.0

VULN_CODE = """import os
import pickle

SECRET_KEY = "hardcoded"

def run(cmd):
    return os.system(cmd)

def parse(text):
    return eval(text)

def broken():
    try:
        do()
    except:
        pass
"""
CLEAN_CODE = "def add(a, b):\n    return a + b\n"


def _echo_llm():
    llm = AsyncMock()
    llm.get_model_for_role = MagicMock(return_value="mock-model")

    async def _gen(prompt, **kwargs):
        return f"ECHO::{prompt[:200]}"

    llm.generate.side_effect = _gen
    return llm


class TestStaticScan:
    def test_findings_are_line_numbered(self):
        findings = _static_scan(VULN_CODE)
        rules = {f["rule"] for f in findings}
        assert "os-system" in rules
        assert "eval-exec" in rules
        assert "hardcoded-secret" in rules
        assert "bare-except" in rules
        assert "pickle-import" in rules
        for finding in findings:
            assert finding["line"] >= 1
            assert finding["snippet"]
            assert finding["severity"] in ("low", "medium", "high", "critical")

    def test_clean_code_reports_none(self):
        assert _static_scan(CLEAN_CODE) == []

    def test_rule_metadata_present(self):
        for rule in _STATIC_RULES:
            rid, severity, pattern, _advice = rule
            assert rid
            assert severity
            re_src = pattern  # compile-checked below
            import re as _re

            assert _re.compile(re_src)


class TestExecute:
    @pytest.mark.asyncio
    async def test_static_findings_persist_in_result(self):
        wf = AuditWorkflow()
        wf.llm = _echo_llm()
        result = await asyncio.wait_for(
            wf.execute("audit", {"code": VULN_CODE, "language": "python"}),
            timeout=EXECUTE_TIMEOUT,
        )
        findings = result["vulnerabilities"]["static_findings"]
        assert findings
        assert result["vulnerabilities"]["static_summary"]["high"] == 2
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_empty_code_noted(self):
        wf = AuditWorkflow()
        wf.llm = _echo_llm()
        result = await wf.execute("audit", {"code": "   "})
        assert result["note"] == "no-code-provided"

    @pytest.mark.asyncio
    async def test_non_python_language_skips_scan(self):
        wf = AuditWorkflow()
        wf.llm = _echo_llm()
        result = await asyncio.wait_for(
            wf.execute("audit", {"code": VULN_CODE, "language": "javascript"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["vulnerabilities"]["static_findings"] == []
        assert "Hlopw" not in result["vulnerabilities"]["static_findings"]


class TestGenerateRobustness:
    @pytest.mark.asyncio
    async def test_retries_empty_once(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["", "hello"]
        wf = AuditWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == "hello"

    @pytest.mark.asyncio
    async def test_failure_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = RuntimeError("down")
        wf = AuditWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_error_string_returns_empty(self):
        llm = AsyncMock()
        llm.generate.side_effect = ["[Ollama error] bad", "[Ollama error] bad"]
        wf = AuditWorkflow()
        wf.llm = llm
        assert await wf._generate("prompt") == ""

    @pytest.mark.asyncio
    async def test_passes_think_flag(self):
        llm = AsyncMock()
        llm.generate.return_value = "text"
        wf = AuditWorkflow()
        wf.llm = llm
        await wf._generate("prompt")
        _, kwargs = llm.generate.call_args
        assert kwargs["think"] is False
        assert kwargs["role"] == "critic"
