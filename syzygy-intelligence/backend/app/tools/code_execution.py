"""Code execution tool — run code with host isolation via the sandbox module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.tools.sandbox import run_python, run_shell


@dataclass
class CodeExecutionTool:
    name: str = "code_execution"
    description: str = "Execute code with host isolation: temp workspace, scrubbed env, timeouts (Python, Shell)"

    async def execute(
        self,
        code: str = "",
        language: str = "python",
        timeout: int = 30,
    ) -> dict[str, Any]:
        if language == "python":
            return run_python(code, timeout=timeout)
        elif language == "shell":
            return run_shell(code, timeout=timeout)
        else:
            return {"error": f"Unsupported language: {language}", "success": False}
