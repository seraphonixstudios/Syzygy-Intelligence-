"""Host-isolated code execution — the single policy point for running untrusted code.

Every execution gets: an isolated temp working directory (cwd jail), a scrubbed
environment (secrets never leak in), an enforced timeout, and truncated output.
Results are explicitly labeled ``backend="host"`` / ``sandboxed=False`` — this
is hardened host execution, NOT container isolation. Container isolation (Docker)
is the follow-up once a daemon is available; until then no result may claim it.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT = 30
DEFAULT_PYTEST_TIMEOUT = 180
DEFAULT_MAX_OUTPUT = 50000

# Env var name fragments that must never reach executed code.
SECRET_HINTS = ("SECRET", "TOKEN", "API_KEY", "PASSWORD", "PRIVATE", "CREDENTIAL", "AUTH")

_TRUNCATION_MARKER = "\n...[output truncated]"


def scrubbed_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Copy of os.environ minus secrets, plus safe executor defaults."""
    clean = {
        key: value
        for key, value in os.environ.items()
        if "SYZYGY_" not in key.upper() and not any(hint in key.upper() for hint in SECRET_HINTS)
    }
    clean["PYTHONDONTWRITEBYTECODE"] = "1"
    if extra:
        clean.update(extra)
    return clean


def _truncate(text: str, limit: int = DEFAULT_MAX_OUTPUT) -> str:
    if len(text) > limit:
        return text[:limit] + _TRUNCATION_MARKER
    return text


def _base_result() -> dict[str, Any]:
    return {"backend": "host", "sandboxed": False}


def run_python(code: str, timeout: int | float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Run Python code in an isolated temp dir with scrubbed env."""
    with tempfile.TemporaryDirectory(prefix="syzygy-sandbox-") as tmpdir:
        script = Path(tmpdir, "script.py")
        script.write_text(code, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
                env=scrubbed_env(),
            )
        except subprocess.TimeoutExpired:
            return {**_base_result(), "error": "Execution timed out", "success": False}
        except Exception as exc:
            return {**_base_result(), "error": str(exc), "success": False}
        return {
            **_base_result(),
            "stdout": _truncate(proc.stdout or ""),
            "stderr": _truncate(proc.stderr or ""),
            "return_code": proc.returncode,
            "success": proc.returncode == 0,
        }


def run_shell(command: str, timeout: int | float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Run a shell command in an isolated temp dir with scrubbed env."""
    with tempfile.TemporaryDirectory(prefix="syzygy-sandbox-") as tmpdir:
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
                env=scrubbed_env(),
            )
        except subprocess.TimeoutExpired:
            return {**_base_result(), "error": "Execution timed out", "success": False}
        except Exception as exc:
            return {**_base_result(), "error": str(exc), "success": False}
        return {
            **_base_result(),
            "stdout": _truncate(proc.stdout or ""),
            "stderr": _truncate(proc.stderr or ""),
            "return_code": proc.returncode,
            "success": proc.returncode == 0,
        }


def _parse_pytest_counts(output: str) -> dict[str, int]:
    counts = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
    for key in counts:
        match = re.search(rf"(\d+) {key}\b", output or "")
        if match:
            counts[key] = int(match.group(1))
    return counts


def run_pytest(workdir: str | Path, timeout: int | float = DEFAULT_PYTEST_TIMEOUT) -> dict[str, Any]:
    """Run pytest in an isolated env (cwd jail, scrubbed env) and report real counts."""
    workdir = str(workdir)
    pythonpath = workdir + os.pathsep + os.environ.get("PYTHONPATH", "")
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", workdir, "-q", "-p", "no:cacheprovider"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
            env=scrubbed_env({"PYTHONPATH": pythonpath}),
        )
    except subprocess.TimeoutExpired:
        return {
            **_base_result(),
            "passed": 0, "failed": 0, "skipped": 0, "errors": 0,
            "success": False, "note": "pytest timed out",
        }
    except Exception as exc:
        return {
            **_base_result(),
            "passed": 0, "failed": 0, "skipped": 0, "errors": 0,
            "success": False, "note": f"pytest runner error: {exc}",
        }
    output = (proc.stdout or "") + (proc.stderr or "")
    counts = _parse_pytest_counts(output)
    total = counts["passed"] + counts["failed"] + counts["errors"]
    note = ""
    if proc.returncode not in (0, 5) and total == 0:
        note = "pytest crashed before collecting tests"
    elif total == 0:
        note = "pytest collected no tests"
    return {
        **_base_result(),
        "success": proc.returncode == 0,
        "note": note,
        "output_tail": output[-2000:],
        **counts,
    }
