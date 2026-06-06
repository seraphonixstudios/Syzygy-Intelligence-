"""Test generation workflow — automated unit, integration, and edge-case test creation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger


@dataclass
class TestGenWorkflow:
    """Automated test generation with edge-case coverage and validation."""

    name: str = "test_gen"
    description: str = "Automated unit, integration, and edge-case test generation"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["test_generation", "code_analysis", "edge_case_detection"]
    )
    llm: Optional[OllamaClient] = None

    def __post_init__(self):
        if self.llm is None:
            self.llm = OllamaClient()

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
        analysis = await self.llm.generate(prompt, temperature=0.3)
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
            f"4. Follow {framework} best practices\n"
            f"Return ONLY the test code."
        )
        tests = await self.llm.generate(prompt, temperature=0.3)
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
        edge_cases = await self.llm.generate(prompt, temperature=0.3)
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
        validation = await self.llm.generate(prompt, temperature=0.3)
        return {"validation": validation}

    async def execute(self, task: str, context: dict[str, Any] = None) -> dict[str, Any]:
        ctx = context or {}
        code = ctx.get("code", task)
        language = ctx.get("language", "python")

        logger.info(f"Test generation workflow started", language=language)
        analysis = await self.analyze_code(code, language)
        unit_result = await self.generate_unit_tests(code, language)
        edge_result = await self.generate_edge_cases(code, language)
        validation = await self.validate_tests(unit_result.get("unit_tests", ""), language)

        result = {
            "task": task,
            "language": language,
            "analysis": analysis,
            "unit_tests": unit_result,
            "edge_cases": edge_result,
            "validation": validation,
            "status": "completed",
        }
        logger.info(f"Test generation workflow completed")
        return result


TEST_GEN_WORKFLOW = TestGenWorkflow()
