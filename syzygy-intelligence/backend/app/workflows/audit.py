"""Audit workflow — security scanning, code review, anti-pattern detection, compliance checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger


@dataclass
class AuditWorkflow:
    """Security audit and code review with vulnerability scanning and compliance checks."""

    name: str = "audit"
    description: str = "Security scanning, code review, anti-pattern detection, and compliance checks"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["code_review", "vulnerability_scanning", "compliance_checking"]
    )
    llm: Optional[OllamaClient] = None

    def __post_init__(self):
        if self.llm is None:
            self.llm = OllamaClient()

    async def scan_vulnerabilities(self, code: str, language: str = "python") -> dict[str, Any]:
        prompt = (
            f"Scan the following {language} code for security vulnerabilities:\n\n"
            f"```{language}\n{code[:4000]}\n```\n\n"
            f"Identify:\n"
            f"1. Injection flaws (SQL, command, XSS)\n"
            f"2. Authentication/authorization issues\n"
            f"3. Sensitive data exposure\n"
            f"4. Insecure deserialization\n"
            f"5. Known vulnerable dependencies\n"
            f"Rate each finding: Critical / High / Medium / Low"
        )
        result = await self.llm.generate(prompt, temperature=0.2)
        return {"vulnerabilities": result, "language": language}

    async def review_code_quality(self, code: str, language: str = "python") -> dict[str, Any]:
        prompt = (
            f"Review the following {language} code for quality issues:\n\n"
            f"```{language}\n{code[:4000]}\n```\n\n"
            f"Analyze:\n"
            f"1. Anti-patterns and code smells\n"
            f"2. Performance bottlenecks\n"
            f"3. Error handling gaps\n"
            f"4. Type safety and null safety\n"
            f"5. Test coverage gaps\n"
            f"Provide specific line-level recommendations."
        )
        result = await self.llm.generate(prompt, temperature=0.3)
        return {"quality_review": result}

    async def check_compliance(
        self, code: str, standards: list[str] = None, language: str = "python"
    ) -> dict[str, Any]:
        standards = standards or ["owasp", "pci-dss"]
        prompt = (
            f"Check the following {language} code against {', '.join(standards)}:\n\n"
            f"```{language}\n{code[:4000]}\n```\n\n"
            f"For each standard, list:\n"
            f"1. Requirements that apply\n"
            f"2. Whether they pass or fail\n"
            f"3. Remediation steps for failures"
        )
        result = await self.llm.generate(prompt, temperature=0.2)
        return {"compliance_check": result, "standards": standards}

    async def generate_report(
        self, vulnerabilities: dict, quality: dict, compliance: dict
    ) -> str:
        combined = (
            f"Vulnerability Scan:\n{vulnerabilities.get('vulnerabilities', 'N/A')}\n\n"
            f"Code Quality Review:\n{quality.get('quality_review', 'N/A')}\n\n"
            f"Compliance Check:\n{compliance.get('compliance_check', 'N/A')}"
        )
        prompt = (
            f"Generate a concise executive audit report from the following findings:\n\n{combined}\n\n"
            f"Structure: Executive Summary, Critical Issues, Recommendations, Priority Matrix."
        )
        return await self.llm.generate(prompt, temperature=0.3)

    async def execute(self, task: str, context: dict[str, Any] = None) -> dict[str, Any]:
        ctx = context or {}
        code = ctx.get("code", task)
        language = ctx.get("language", "python")
        standards = ctx.get("standards", ["owasp", "pci-dss"])

        logger.info(f"Audit workflow started", language=language, standards=standards)
        vulnerabilities = await self.scan_vulnerabilities(code, language)
        quality = await self.review_code_quality(code, language)
        compliance = await self.check_compliance(code, standards, language)
        report = await self.generate_report(vulnerabilities, quality, compliance)

        result = {
            "task": task,
            "language": language,
            "vulnerabilities": vulnerabilities,
            "quality_review": quality,
            "compliance_check": compliance,
            "report": report,
            "status": "completed",
        }
        logger.info(f"Audit workflow completed")
        return result


AUDIT_WORKFLOW = AuditWorkflow()
