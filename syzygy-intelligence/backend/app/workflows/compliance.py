"""Compliance workflow — regulatory checks against GDPR, SOC2, HIPAA, and custom policies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger

REGULATORY_FRAMEWORKS = {
    "gdpr": "General Data Protection Regulation — data privacy, consent, right to erasure, breach notification",
    "soc2": "Service Organization Control 2 — security, availability, processing integrity, confidentiality, privacy",
    "hipaa": "Health Insurance Portability and Accountability Act — PHI protection, privacy rules, security rules",
    "pci-dss": "Payment Card Industry Data Security Standard — cardholder data protection, access control, monitoring",
    "ccpa": "California Consumer Privacy Act — data rights, opt-out, disclosure requirements",
}


@dataclass
class ComplianceWorkflow:
    """Regulatory compliance checking against GDPR, SOC2, HIPAA, PCI-DSS, CCPA, and custom policies."""

    name: str = "compliance"
    description: str = "Regulatory compliance checks — GDPR, SOC2, HIPAA, PCI-DSS, CCPA"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["compliance_analysis", "policy_mapping", "risk_assessment"]
    )
    llm: OllamaClient | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm = OllamaClient()

    async def analyze_policy(self, document: str, framework: str) -> dict[str, Any]:
        assert self.llm is not None
        framework_desc = REGULATORY_FRAMEWORKS.get(framework.lower(), framework)
        prompt = (
            f"Analyze the following document against {framework.upper()} ({framework_desc}):\n\n"
            f"{document[:3000]}\n\n"
            f"Identify:\n"
            f"1. Which specific regulations/requirements apply\n"
            f"2. Areas of compliance\n"
            f"3. Gaps or violations with specific references\n"
            f"4. Risk level for each gap (Critical / High / Medium / Low)"
        )
        analysis = await self.llm.generate(prompt, temperature=0.2)
        return {"framework": framework.upper(), "analysis": analysis}

    async def map_requirements(
        self, document: str, frameworks: list[str]
    ) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Create a requirements traceability matrix mapping the following document\n"
            f"{document[:2000]}\n\n"
            f"against {', '.join(f.upper() for f in frameworks)}:\n"
            f"For each framework requirement, show:\n"
            f"1. Requirement ID and description\n"
            f"2. Where it is addressed in the document\n"
            f"3. Compliance status (Compliant / Partially Compliant / Non-Compliant / Not Applicable)\n"
            f"4. Evidence or gap description"
        )
        matrix = await self.llm.generate(prompt, temperature=0.2)
        return {"traceability_matrix": matrix, "frameworks": frameworks}

    async def assess_risk(self, analysis_results: list[dict[str, Any]]) -> str:
        assert self.llm is not None
        combined = "\n\n".join(
            f"Framework {r.get('framework', '?')}:\n{r.get('analysis', '')[:1000]}"
            for r in analysis_results
        )
        prompt = (
            f"Perform a consolidated risk assessment based on the following compliance analyses:\n\n{combined}\n\n"
            f"Provide:\n"
            f"1. Overall risk rating\n"
            f"2. Top 5 critical findings across all frameworks\n"
            f"3. Prioritized remediation roadmap\n"
            f"4. Estimated effort and impact for each remediation"
        )
        return await self.llm.generate(prompt, temperature=0.3)

    async def generate_remediation_plan(self, risk_assessment: str) -> str:
        assert self.llm is not None
        prompt = (
            f"Based on this risk assessment, create a detailed remediation plan:\n\n"
            f"{risk_assessment[:2000]}\n\n"
            f"For each finding, provide:\n"
            f"1. Specific remediation steps\n"
            f"2. Responsible role or team\n"
            f"3. Suggested timeline (immediate / short-term / long-term)\n"
            f"4. verification criteria"
        )
        return await self.llm.generate(prompt, temperature=0.3)

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        document = ctx.get("document", task)
        frameworks = ctx.get("frameworks", ["gdpr", "hipaa", "soc2"])

        logger.info("Compliance workflow started", frameworks=frameworks)
        analyses = []
        for fw in frameworks:
            analysis = await self.analyze_policy(document, fw)
            analyses.append(analysis)
        mapping = await self.map_requirements(document, frameworks)
        risk = await self.assess_risk(analyses)
        remediation = await self.generate_remediation_plan(risk)

        result = {
            "task": task,
            "frameworks_checked": frameworks,
            "analyses": analyses,
            "requirements_mapping": mapping,
            "risk_assessment": risk,
            "remediation_plan": remediation,
            "status": "completed",
        }
        logger.info("Compliance workflow completed", frameworks_checked=len(frameworks))
        return result


COMPLIANCE_WORKFLOW = ComplianceWorkflow()
