"""API Designer workflow — REST/GraphQL API design, OpenAPI spec generation, endpoint stubs, validation tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger


@dataclass
class ApiDesignerWorkflow:
    """Design REST/GraphQL APIs, generate OpenAPI specs, endpoint stubs, and validation tests."""

    name: str = "api_designer"
    description: str = "API design with OpenAPI spec generation, endpoint stubs, and validation tests"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["api_design", "openapi_generation", "code_generation", "test_generation"]
    )
    llm: OllamaClient | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm = OllamaClient()

    async def design_endpoints(self, description: str, style: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Design API endpoints for the following requirement:\n\n{description}\n\n"
            f"API Style: {style}\n\n"
            f"For each endpoint provide:\n"
            f"1. HTTP method and path\n"
            f"2. Request parameters and body schema\n"
            f"3. Response schema and status codes\n"
            f"4. Authentication requirements\n"
            f"5. Rate limiting considerations\n"
            f"6. Example request/response"
        )
        design = await self.llm.generate(prompt, temperature=0.3)
        return {"design": design, "style": style}

    async def generate_openapi_spec(self, description: str, design: dict[str, Any], style: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Generate a complete OpenAPI 3.1 specification for the following API:\n\n"
            f"Description: {description}\n\n"
            f"Design:\n{design.get('design', '')[:3000]}\n\n"
            f"API Style: {style}\n\n"
            f"Return the full YAML/JSON spec including:\n"
            f"1. Info, servers, paths, components\n"
            f"2. All request/response schemas\n"
            f"3. Security schemes\n"
            f"4. Tags and external docs"
        )
        spec = await self.llm.generate(prompt, temperature=0.2)
        return {"spec": spec}

    async def generate_stubs(self, spec: dict[str, Any], language: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Generate {language} endpoint stubs from this OpenAPI spec:\n\n"
            f"{spec.get('spec', '')[:3000]}\n\n"
            f"For each endpoint create:\n"
            f"1. A function/method stub with proper signatures\n"
            f"2. Input validation using Pydantic/dataclasses\n"
            f"3. Proper error handling skeleton\n"
            f"4. Logging statements\n"
            f"5. TODO comments for business logic"
        )
        stubs = await self.llm.generate(prompt, temperature=0.3)
        return {"stubs": stubs, "language": language}

    async def generate_tests(self, spec: dict[str, Any], language: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Generate validation tests in {language} for this API spec:\n\n"
            f"{spec.get('spec', '')[:3000]}\n\n"
            f"Create:\n"
            f"1. Happy path tests for each endpoint\n"
            f"2. Error case tests (400, 401, 403, 404, 500)\n"
            f"3. Schema validation tests\n"
            f"4. Auth/security tests\n"
            f"5. Rate limit tests"
        )
        tests = await self.llm.generate(prompt, temperature=0.3)
        return {"tests": tests}

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        description = ctx.get("description", task)
        style = ctx.get("api_style", "REST")
        language = ctx.get("language", "python")

        logger.info("API Designer workflow started", style=style, language=language)
        design = await self.design_endpoints(description, style)
        spec = await self.generate_openapi_spec(description, design, style)
        stubs = await self.generate_stubs(spec, language)
        tests = await self.generate_tests(spec, language)

        result = {
            "task": task,
            "api_style": style,
            "language": language,
            "endpoint_design": design,
            "openapi_spec": spec,
            "endpoint_stubs": stubs,
            "validation_tests": tests,
            "status": "completed",
        }
        logger.info("API Designer workflow completed")
        return result


API_DESIGNER_WORKFLOW = ApiDesignerWorkflow()
