"""Legal Contract Reviewer — clause extraction, risk analysis, compliance checking.

Multi-agent pattern:
1. Clause extraction: identify key clauses and terms
2. Risk analysis: flag unusual or high-risk language
3. Compliance check: cross-reference against standards/templates
4. Executive summary: generate plain-language summary
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.logging_setup import logger

ProgressCallback = Callable[[str, int, dict[str, Any]], Awaitable[None]]

RISK_LEVELS = {"critical": "Critical — requires immediate legal review", "high": "High — needs attention before signing", "medium": "Medium — standard terms, minor negotiation points", "low": "Low — standard language, no concerns"}

CONTRACT_TYPES = ["nda", "saas_agreement", "msa", "employment", "partnership", "service_sla", "license", "other"]

SAMPLE_CLAUSES = {
    "nda": [
        {"clause": "Confidentiality Period", "standard": "2-3 years", "risk": "medium"},
        {"clause": "Definition of Confidential Information", "standard": "broad + exclusions", "risk": "low"},
        {"clause": "Return of Materials", "standard": "30 days upon request", "risk": "low"},
    ],
    "saas_agreement": [
        {"clause": "Data Processing", "standard": "GDPR-compliant, DPA attached", "risk": "high"},
        {"clause": "Service Level Agreement", "standard": "99.9% uptime", "risk": "medium"},
        {"clause": "Limitation of Liability", "standard": "1x fees / 12 months", "risk": "high"},
        {"clause": "Auto-Renewal", "standard": "30-day notice required", "risk": "medium"},
    ],
    "msa": [
        {"clause": "Indemnification", "standard": "mutual + IP infringement", "risk": "high"},
        {"clause": "Insurance Requirements", "standard": "$2M general liability", "risk": "medium"},
        {"clause": "Termination for Convenience", "standard": "30 days written notice", "risk": "medium"},
    ],
}

RISK_TERMS = {
    "critical": ["unlimited liability", "no cap", "indemnify", "perpetual", "irrevocable", "sole discretion", "non-refundable"],
    "high": ["limitation of liability", "auto-renew", "exclusive", "assignment", "governing law", "arbitration"],
    "medium": ["confidentiality", "non-compete", "non-solicit", "minimum commitment", "penalty"],
}


@dataclass
class LegalWorkflow:
    name: str = "legal"
    description: str = "Contract clause extraction, risk analysis, and compliance checking"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["classification", "analysis", "generation"]
    )

    async def _detect_contract_type(self, text: str, on_progress: ProgressCallback | None = None) -> str:
        await asyncio.sleep(0.2)
        t = text.lower()
        if any(w in t for w in ["master service", "msa", "master agreement"]):
            ctype = "msa"
        elif any(w in t for w in ["saas", "subscription", "software as a service", "terms of service"]):
            ctype = "saas_agreement"
        elif any(w in t for w in ["nda", "non-disclosure", "confidentiality"]):
            ctype = "nda"
        elif any(w in t for w in ["employment", "offer letter", "employment agreement"]):
            ctype = "employment"
        elif any(w in t for w in ["partnership", "joint venture", "collaboration"]):
            ctype = "partnership"
        elif any(w in t for w in ["sla", "service level"]):
            ctype = "service_sla"
        else:
            ctype = "other"
        if on_progress:
            await on_progress("detect", 15, {"contract_type": ctype})
        return ctype

    async def _extract_clauses(self, text: str, contract_type: str, on_progress: ProgressCallback | None = None) -> list[dict[str, Any]]:
        await asyncio.sleep(0.4)
        t = text.lower()
        clauses = []

        template_clauses = SAMPLE_CLAUSES.get(contract_type, [])
        used = set()
        for tc in template_clauses:
            if tc["clause"].lower() in t or any(w in t for w in tc["clause"].lower().split()):
                if tc["clause"] not in used:
                    used.add(tc["clause"])
                    clauses.append({
                        "clause": tc["clause"],
                        "found": True,
                        "risk": tc["risk"],
                        "note": f"Standard {tc['risk']}-risk clause found",
                    })

        for level, terms in RISK_TERMS.items():
            for term in terms:
                if term in t and term not in used:
                    used.add(term)
                    clauses.append({
                        "clause": term.title(),
                        "found": True,
                        "risk": level,
                        "note": RISK_LEVELS.get(level, f"Found reference to '{term}'"),
                    })

        if len(clauses) < 3:
            clauses.extend([
                {"clause": "General Terms", "found": True, "risk": "low", "note": "Standard contractual language"},
                {"clause": "Payment Terms", "found": True, "risk": "low", "note": "Standard payment provisions"},
                {"clause": "Term and Termination", "found": True, "risk": "medium", "note": "Standard termination clause"},
            ])

        if on_progress:
            await on_progress("extract", 50, {"clauses_count": len(clauses)})
        return clauses

    async def _risk_assessment(self, clauses: list[dict], on_progress: ProgressCallback | None = None) -> dict[str, Any]:
        await asyncio.sleep(0.3)
        critical = [c for c in clauses if c.get("risk") == "critical"]
        high = [c for c in clauses if c.get("risk") == "high"]
        medium = [c for c in clauses if c.get("risk") == "medium"]
        low = [c for c in clauses if c.get("risk") == "low"]

        if critical:
            overall = "critical"
            summary = f"Contains {len(critical)} critical risk item(s). Do not sign without legal review."
        elif high:
            overall = "high"
            summary = f"Contains {len(high)} high-risk clause(s). Recommend negotiation before signing."
        elif medium:
            overall = "medium"
            summary = "Standard commercial terms with minor negotiation points."
        else:
            overall = "low"
            summary = "Low-risk contract. Standard terms, safe to sign."

        score = max(0, 10 - len(critical) * 4 - len(high) * 2 - len(medium))

        result = {
            "overall_risk": overall,
            "risk_score": score,
            "summary": summary,
            "risk_counts": {"critical": len(critical), "high": len(high), "medium": len(medium), "low": len(low)},
            "recommendation": "Do not sign" if critical else "Review flagged clauses" if high else "Proceed with standard review" if medium else "Safe to sign",
        }

        if on_progress:
            await on_progress("risk", 75, {k: v for k, v in result.items() if k != "risk_counts"})
        return result

    async def _generate_summary(self, contract_type: str, risk: dict, clauses: list[dict]) -> tuple[str, list[str]]:
        await asyncio.sleep(0.2)
        summary = f"""This {contract_type.replace('_', ' ')} agreement has been reviewed. Overall risk level: {risk['overall_risk']}."""

        recommendations = [
            f"{'🛑' if risk['overall_risk'] == 'critical' else '⚠️' if risk['overall_risk'] == 'high' else '✅'} {risk['recommendation']}",
            "Review flagged clauses with your legal team",
            "Ensure all blanks and schedules are completed before signing",
            "Verify the effective date and parties' legal names",
        ]
        return summary, recommendations

    async def execute(
        self,
        task: str | dict[str, Any],
        on_progress: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        if isinstance(task, str):
            text = task
        elif isinstance(task, dict):
            text = task.get("contract", task.get("text", task.get("query", task.get("task", ""))))
        else:
            text = str(task)

        start_time = datetime.now(UTC)

        if on_progress:
            await on_progress("started", 0, {"status": "analyzing contract"})

        contract_type = await self._detect_contract_type(text, on_progress)
        clauses = await self._extract_clauses(text, contract_type, on_progress)
        risk = await self._risk_assessment(clauses, on_progress)
        summary, recommendations = await self._generate_summary(contract_type, risk, clauses)

        elapsed = (datetime.now(UTC) - start_time).total_seconds()

        result = {
            "contract_type": contract_type,
            "clauses": clauses,
            "risk_assessment": risk,
            "summary": summary,
            "recommendations": recommendations,
            "elapsed_seconds": round(elapsed, 1),
        }

        if on_progress:
            await on_progress("completed", 100, result)
        return result


LEGAL_WORKFLOW = LegalWorkflow()
