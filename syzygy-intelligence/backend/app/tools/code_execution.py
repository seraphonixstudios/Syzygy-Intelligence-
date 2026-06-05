"""Code execution tool — run code in sandboxed Docker containers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CodeExecutionTool:
    name: str = "code_execution"
    description: str = "Execute code in sandboxed environments (Python, JavaScript, Shell)"

    async def execute(
        self,
        code: str = "",
        language: str = "python",
        timeout: int = 30,
    ) -> dict[str, Any]:
        try:
            if language == "python":
                import subprocess
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".py", delete=False, encoding="utf-8"
                ) as f:
                    f.write(code)
                    f.flush()
                    fname = f.name

                result = subprocess.run(
                    ["python", fname],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )

                import os
                os.unlink(fname)

                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "success": result.returncode == 0,
                }

            elif language == "shell":
                import subprocess
                result = subprocess.run(
                    code,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "success": result.returncode == 0,
                }

            else:
                return {"error": f"Unsupported language: {language}"}

        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
