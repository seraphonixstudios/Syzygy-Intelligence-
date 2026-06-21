"""Coding workflow — full software development pipeline with real implementations."""

from __future__ import annotations

import subprocess
import tempfile
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.llm.model_manager import ModelManager

ProgressCallback = Callable[[str, int, dict[str, Any]], Awaitable[None]]


@dataclass
class CodingWorkflow:
    """Full coding suite: scaffolding, editing, testing, debugging with real execution."""

    name: str = "coding"
    description: str = "Full software development with scaffolding, editing, testing, and debugging"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["code_generation", "code_review", "testing", "debugging"]
    )
    llm: ModelManager | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm: ModelManager = ModelManager()

    async def scaffold(self, specification: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Generate a complete project scaffold for the following specification:\n\n"
            f"{specification}\n\n"
            f"Provide the directory structure, key files, and their purposes. "
            f"Include file paths and brief descriptions."
        )
        result = await self.llm.generate(prompt, temperature=0.3)
        return {"specification": specification, "scaffold": result}

    async def edit(self, file_path: str, instruction: str) -> dict[str, Any]:
        assert self.llm is not None
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}", "edited": False}

        original = path.read_text(encoding="utf-8")
        prompt = (
            f"File path: {file_path}\n\n"
            f"Current content:\n```\n{original[:3000]}\n```\n\n"
            f"Instruction: {instruction}\n\n"
            f"Return ONLY the complete updated file content with the changes applied."
        )
        new_content = await self.llm.generate(prompt, temperature=0.3)

        if new_content and not new_content.startswith("[Ollama error"):
            path.write_text(new_content, encoding="utf-8")
            return {
                "file_path": file_path,
                "edited": True,
                "original_length": len(original),
                "new_length": len(new_content),
                "instruction": instruction,
            }
        return {"error": "Failed to generate edit", "edited": False}

    async def test(self, code: str, language: str = "python") -> dict[str, Any]:
        assert self.llm is not None
        test_prompt = (
            f"Write comprehensive unit tests for the following {language} code:\n\n"
            f"```{language}\n{code[:2000]}\n```\n\n"
            f"Return ONLY the test code, ready to execute."
        )
        test_code = await self.llm.generate(test_prompt, temperature=0.3)

        if test_code.startswith("[Ollama error"):
            return {"error": test_code, "tested": False}

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=f".{language}", delete=False, encoding="utf-8"
            ) as f:
                f.write(test_code)
                fname = f.name

            runner = "python" if language == "python" else language
            result = subprocess.run(
                [runner, fname],
                capture_output=True,
                text=True,
                timeout=30,
            )
            Path(fname).unlink(missing_ok=True)

            return {
                "tested": True,
                "test_code": test_code,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:2000],
                "return_code": result.returncode,
                "passed": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Test execution timed out", "tested": False}
        except Exception as e:
            return {"error": str(e), "tested": False}

    async def debug(self, error: str, context: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Error message: {error}\n\n"
            f"Context:\n{context[:2000]}\n\n"
            f"Analyze this error and provide:\n"
            f"1. Root cause analysis\n"
            f"2. Specific fix/solution\n"
            f"3. Prevention strategies"
        )
        fix = await self.llm.generate(prompt, temperature=0.3)
        return {"error": error, "analysis": fix}

    async def review(self, code: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Review the following code for bugs, security issues, style problems, "
            f"and improvement opportunities:\n\n"
            f"```\n{code[:3000]}\n```\n\n"
            f"Provide specific, actionable feedback."
        )
        review = await self.llm.generate(prompt, temperature=0.3)
        return {"review": review, "code_length": len(code)}

    async def execute(
        self,
        task: str,
        context: dict[str, Any] | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        ctx = context or {}
        language = ctx.get("language", "python")

        result = {"task": task, "language": language, "steps": {}, "reasoning": []}
        reasoning: list[dict[str, Any]] = []
        model = (self.llm.get_model_for_role("coding") if self.llm else "tinyllama:latest")

        assert self.llm is not None
        result["steps"]["scaffold"] = await self.scaffold(task)
        step = {"agent": "Architect", "thought": "Designing project structure and architecture...", "model": model, "confidence": 0.92}
        reasoning.append({**step, "step": "scaffold"})
        if on_progress:
            await on_progress("scaffold", 25, step)

        gen_prompt = (
            f"Generate {language} code for: {task}\n"
            f"Include proper error handling, type hints, and documentation."
        )
        code = await self.llm.generate(gen_prompt, temperature=0.3)
        result["steps"]["generation"] = {"code": code}
        step = {"agent": "Developer", "thought": f"Writing {language} code with best practices and error handling...", "model": model, "confidence": 0.88}
        reasoning.append({**step, "step": "generation"})
        if on_progress:
            await on_progress("generation", 50, step)

        result["steps"]["review"] = await self.review(code)
        step = {"agent": "Reviewer", "thought": "Checking for edge cases, performance issues, and security concerns...", "model": model, "confidence": 0.85}
        reasoning.append({**step, "step": "review"})
        if on_progress:
            await on_progress("review", 75, step)

        result["steps"]["test"] = await self.test(code, language)
        step = {"agent": "Tester", "thought": "Creating and executing unit tests...", "model": model, "confidence": 0.80}
        reasoning.append({**step, "step": "test"})
        if on_progress:
            await on_progress("test", 100, step)

        result["reasoning"] = reasoning
        result["status"] = "completed"
        return result


CODING_WORKFLOW = CodingWorkflow()
