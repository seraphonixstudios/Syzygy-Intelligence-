"""Tests for the host-isolation sandbox runner."""

from __future__ import annotations

import os
import subprocess
from unittest.mock import patch

import pytest

from app.tools.code_execution import CodeExecutionTool
from app.tools.sandbox import (
    _truncate,
    run_pytest,
    run_python,
    run_shell,
    scrubbed_env,
)


class TestScrubbedEnv:
    def test_removes_secrets(self):
        with patch.dict(
            os.environ,
            {
                "SYZYGY_SECRET_KEY": "shh",
                "MY_API_TOKEN": "shh",
                "DB_PASSWORD": "shh",
                "NORMAL_VAR": "visible",
            },
        ):
            env = scrubbed_env()
        assert "SYZYGY_SECRET_KEY" not in env
        assert "MY_API_TOKEN" not in env
        assert "DB_PASSWORD" not in env
        assert env["NORMAL_VAR"] == "visible"
        assert env["PYTHONDONTWRITEBYTECODE"] == "1"

    def test_extra_overrides(self):
        env = scrubbed_env({"PYTHONPATH": "/tmp/x"})
        assert env["PYTHONPATH"] == "/tmp/x"

    def test_secrets_never_reach_code(self):
        with patch.dict(os.environ, {"SYZYGY_SECRET_KEY": "super-shh"}):
            result = run_python("import os; print('SECRET' in str(os.environ))", timeout=60)
        assert result["success"] is True
        assert "False" in result["stdout"]
        assert "super-shh" not in result["stdout"]


class TestCwdJail:
    def test_runs_in_temp_dir(self):
        result = run_python("import os; print(os.getcwd())", timeout=60)
        assert result["success"] is True
        assert "syzygy-sandbox-" in result["stdout"]

    def test_relative_writes_stay_jailed(self):
        import pathlib

        marker = pathlib.Path("syzygy-jail-probe.txt")
        if marker.exists():
            marker.unlink()
        result = run_python("open('syzygy-jail-probe.txt', 'w').write('x')", timeout=60)
        assert result["success"] is True
        assert not marker.exists()


class TestRunPython:
    def test_success_labels(self):
        result = run_python("print('hi')", timeout=60)
        assert result["success"] is True
        assert result["return_code"] == 0
        assert "hi" in result["stdout"]
        assert result["backend"] == "host"
        assert result["sandboxed"] is False

    def test_failure(self):
        result = run_python("raise ValueError('boom')", timeout=60)
        assert result["success"] is False
        assert "boom" in result["stderr"]

    def test_timeout(self):
        with patch("app.tools.sandbox.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="x", timeout=1)
            result = run_python("pass", timeout=1)
        assert result["success"] is False
        assert "timed out" in result["error"].lower()

    def test_generic_error(self):
        with patch("app.tools.sandbox.subprocess.run") as mock_run:
            mock_run.side_effect = RuntimeError("weird")
            result = run_python("pass", timeout=60)
        assert result["success"] is False
        assert "weird" in result["error"]

    def test_output_truncated(self):
        result = run_python("print('y' * 100000)", timeout=60)
        assert result["success"] is True
        assert len(result["stdout"]) < 100000
        assert "truncated" in result["stdout"]


class TestRunShell:
    def test_success_labels(self):
        result = run_shell("echo hello_shell", timeout=60)
        assert result["success"] is True
        assert "hello_shell" in result["stdout"]
        assert result["backend"] == "host"
        assert result["sandboxed"] is False

    def test_failure_code(self):
        result = run_shell("exit 1", timeout=60)
        assert result["success"] is False
        assert result["return_code"] == 1

    def test_timeout(self):
        with patch("app.tools.sandbox.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="x", timeout=1)
            result = run_shell("sleep 100", timeout=1)
        assert "timed out" in result["error"].lower()

    def test_generic_error(self):
        with patch("app.tools.sandbox.subprocess.run") as mock_run:
            mock_run.side_effect = RuntimeError("weird")
            result = run_shell("echo hi", timeout=60)
        assert result["success"] is False


class TestTruncate:
    def test_short_passthrough(self):
        assert _truncate("abc", 10) == "abc"

    def test_long_truncated(self):
        out = _truncate("y" * 100, 10)
        assert len(out) < 100
        assert "truncated" in out


class TestRunPytest:
    def test_success(self, tmp_path):
        (tmp_path / "calc.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
        (tmp_path / "test_calc.py").write_text(
            "def test_add():\n    from calc import add\n    assert add(1, 2) == 3\n", encoding="utf-8"
        )
        result = run_pytest(tmp_path, timeout=120)
        assert result["success"] is True
        assert result["passed"] >= 1
        assert result["backend"] == "host"
        assert result["sandboxed"] is False

    def test_timeout(self, tmp_path):
        result = run_pytest(tmp_path, timeout=0)
        assert result["note"] == "pytest timed out"

    def test_runner_error(self, tmp_path):
        with patch("app.tools.sandbox.subprocess.run") as mock_run:
            mock_run.side_effect = RuntimeError("weird")
            result = run_pytest(tmp_path, timeout=60)
        assert "runner error" in result["note"]

    def test_crash(self, tmp_path):
        with patch("app.tools.sandbox.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=2, stdout="boom", stderr="")
            result = run_pytest(tmp_path, timeout=60)
        assert "crashed" in result["note"]

    def test_no_tests(self, tmp_path):
        (tmp_path / "helper.py").write_text("X = 1\n", encoding="utf-8")
        result = run_pytest(tmp_path, timeout=120)
        assert result["note"] == "pytest collected no tests"


class TestToolFacade:
    @pytest.mark.asyncio
    async def test_python_delegates(self):
        tool = CodeExecutionTool()
        result = await tool.execute(code="print('facade')", language="python", timeout=60)
        assert result["success"] is True
        assert "facade" in result["stdout"]
        assert result["sandboxed"] is False

    @pytest.mark.asyncio
    async def test_shell_delegates(self):
        result = await CodeExecutionTool().execute(code="echo facade_sh", language="shell", timeout=60)
        assert result["success"] is True
        assert "facade_sh" in result["stdout"]

    @pytest.mark.asyncio
    async def test_unsupported(self):
        result = await CodeExecutionTool().execute(code="x", language="brainfuck")
        assert result["success"] is False
        assert "error" in result

    def test_description_is_honest(self):
        assert "sandbox" not in CodeExecutionTool().description.lower() or "host" in CodeExecutionTool().description.lower()
