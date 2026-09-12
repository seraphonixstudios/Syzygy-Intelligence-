"""Test generation workflow — automated unit, integration, and edge-case test creation.

Generated tests are actually executed with pytest and the real pass/fail counts
are reported. Nothing is asserted without running.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger

_CODE_HINTS = ("def ", "class ", "import ", "print(", "assert ", "=>", "function ", "#include")


def _looks_like_code(text: str) -> bool:
    return any(hint in (text or "") for hint in _CODE_HINTS)


def _strip_fences(text: str) -> str:
    """Remove ``` fence marker lines (handles unterminated single-block output)."""
    lines = [line for line in (text or "").splitlines() if not line.strip().startswith("```")]
    return "\n".join(lines).strip()


@dataclass
class TestGenWorkflow:
    """Automated test generation with edge-case coverage, validation, and real execution."""

    name: str = "test_gen"
    description: str = "Automated unit, integration, and edge-case test generation"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["test_generation", "code_analysis", "edge_case_detection"]
    )
    llm: ModelManager | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm: ModelManager = ModelManager()

    async def _generate(self, prompt: str, temperature: float = 0.3) -> str:
        """Call the LLM (no chain-of-thought). Returns "" when unreachable/failed."""
        assert self.llm is not None
        for _ in (1, 2):
            try:
                text = await self.llm.generate(prompt, role="coding", temperature=temperature, think=False)
            except Exception as exc:
                logger.warning("TestGenWorkflow LLM call failed", error=str(exc))
                return ""
            text = (text or "").strip()
            if text:
                head = text[:40].lower()
                if not (head.startswith("[") and "error" in head):
                    return text
        return ""

    async def analyze_code(self, code: str, language: str = "python") -> dict[str, Any]:
        prompt = (
            f"Analyze the following {language} code for testability:\n\n"
            f"```{language}\n{code[:3000]}\n```\n\n"
            f"Identify:\n"
            f"1. Functions and methods that need tests\n"
            f"2. Input/output types and ranges\n"
            f"3. Dependencies to mock\n"
            f"4. Error conditions and edge cases"
        )
        analysis = await self._generate(prompt, temperature=0.3)
        return {"analysis": analysis}

    async def generate_unit_tests(self, code: str, language: str = "python") -> dict[str, Any]:
        framework = "pytest" if language == "python" else language
        prompt = (
            f"Write comprehensive unit tests using {framework} for:\n\n"
            f"```{language}\n{code[:3000]}\n```\n\n"
            f"Requirements:\n"
            f"1. Cover all public functions\n"
            f"2. Include happy path, edge cases, and error conditions\n"
            f"3. Use proper mocking for external dependencies\n"
            f"4. The code under test is saved as main.py — import from `main` "
            f"(e.g. `from main import my_function`). Test file lives next to it.\n"
            f"5. Follow {framework} best practices\n"
            f"Return ONLY the test code, no prose."
        )
        tests = await self._generate(prompt, temperature=0.3)
        return {"unit_tests": tests, "framework": framework}

    async def generate_edge_cases(self, code: str, language: str = "python") -> dict[str, Any]:
        prompt = (
            f"Analyze the following {language} code for edge cases and boundary conditions:\n\n"
            f"```{language}\n{code[:3000]}\n```\n\n"
            f"Generate test cases for:\n"
            f"1. Boundary values (min, max, empty, null)\n"
            f"2. Type mismatches\n"
            f"3. Concurrency / race conditions\n"
            f"4. Resource exhaustion\n"
            f"5. Invalid state transitions\n"
            f"Provide specific inputs and expected outputs."
        )
        edge_cases = await self._generate(prompt, temperature=0.3)
        return {"edge_cases": edge_cases}

    async def validate_tests(self, test_code: str, language: str = "python") -> dict[str, Any]:
        prompt = (
            f"Review the following {language} test code for correctness:\n\n"
            f"```{language}\n{test_code[:3000]}\n```\n\n"
            f"Check for:\n"
            f"1. Syntax errors\n"
            f"2. Missing imports\n"
            f"3. Logical correctness\n"
            f"4. Proper assertions\n"
            f"5. Test isolation (no shared state)"
        )
        validation = await self._generate(prompt, temperature=0.3)
        return {"validation": validation}

    def run_tests(self, code: str, test_code: str, timeout: int = 180) -> dict[str, Any]:
        """Write code + tests to an isolated temp dir and run pytest via the sandbox runner."""
        from app.tools.sandbox import run_pytest

        with tempfile.TemporaryDirectory(prefix="syzygy-testgen-") as tmpdir:
            Path(tmpdir, "main.py").write_text(code, encoding="utf-8")
            Path(tmpdir, "test_generated.py").write_text(test_code, encoding="utf-8")
            return run_pytest(tmpdir, timeout=timeout)

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        code = ctx.get("code", task)
        language = ctx.get("language", "python")

        logger.info("Test generation workflow started", language=language)
        if language == "python" and not _looks_like_code(code):
            return {
                "task": task,
                "language": language,
                "status": "completed",
                "note": "no-code-provided",
                "summary": "Input does not look like code — nothing to test.",
            }
        analysis = await self.analyze_code(code, language)
        unit_result = await self.generate_unit_tests(code, language)
        edge_result = await self.generate_edge_cases(code, language)
        validation = await self.validate_tests(unit_result.get("unit_tests", ""), language)

        execution: dict[str, Any] = {"success": False, "note": "not-run"}
        test_code = _strip_fences(unit_result.get("unit_tests", ""))
        if language == "python" and _looks_like_code(test_code):
            execution = self.run_tests(code, test_code)
        elif language == "python":
            execution = {
                "passed": 0, "failed": 0, "skipped": 0, "errors": 0,
                "success": False, "note": "no-tests-generated",
            }

        result = {
            "task": task,
            "language": language,
            "analysis": analysis,
            "unit_tests": unit_result,
            "edge_cases": edge_result,
            "validation": validation,
            "execution": execution,
            "status": "completed",
        }
        logger.info("Test generation workflow completed", success=execution.get("success"))
        return result


TEST_GEN_WORKFLOW = TestGenWorkflow()
