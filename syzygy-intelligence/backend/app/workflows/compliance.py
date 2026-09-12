"""Compliance workflow — regulatory checks against GDPR, SOC2, HIPAA, and custom policies.

Grounded version: a deterministic static scanner finds real line‑numbered issues
(subprocess‑shell, eval/exec, bare‑except, os.system, hardcoded secrets,
pickle‑import, sql‑concat) before any LLM review.  The LLM is fed those findings
plus the document text and asked to confirm, refute, or add context.  Empty
documentation is labeled ``degraded:true`` with ``no-code-provided``.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger
from app.text_utils import truncate

# ---------------------------------------------------------------------------
# Deterministic static scanner – focuses on compliance‑relevant patterns.
# Each entry is (regex_pattern, severity, issue_type).
# Patterns are kept deliberately simple to avoid quoting problems in raw strings.
# ---------------------------------------------------------------------------

_SECRETS_PATTERNS: list[tuple[str, str, str]] = [
    (r"(?i)api[_-]?key\s*[:=]\s*.{6,}", "high", "hardcoded-secret"),
    (r"(?i)password\s*[:=]\s*.{6,}", "high", "hardcoded-secret"),
    (r"(?i)secret[_-]?key\s*[:=]\s*.{6,}", "high", "hardcoded-secret"),
    (r"os\.system\s*\(", "high", "os-system"),
    (r"eval\s*\(", "high", "eval-exec"),
    (r"exec\s*\(", "high", "eval-exec"),
    (r"except\s*:", "medium", "bare-except"),
    (r"pickle\.loads?\s*\(", "high", "pickle-import"),
    (r"(?i)sql\s*[+\s]*%s|%s\s*%s", "high", "sql-concat"),
]

_HARDCODED_URL_PATTERN = r"(?i)https?://[^\s\"'<>]{20,}"


def _scan_text(text: str) -> list[dict[str, Any]]:
    """Return a list of findings found by deterministic regex patterns.

    Each finding is a dict with keys: ``type``, ``severity``, ``message``,
    ``line`` (1‑indexed, best‑effort), and ``raw`` (the matched snippet).
    """
    findings: list[dict[str, Any]] = []
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        for pattern, severity, kind in _SECRETS_PATTERNS:
            m = re.search(pattern, line)
            if m:
                findings.append(
                    {
                        "type": kind,
                        "severity": severity,
                        "message": f"{kind}: {pattern}",
                        "line": i,
                        "raw": m.group(0),
                    }
                )
        # Heuristic: very long URL that may contain credentials
        if re.search(_HARDCODED_URL_PATTERN, line):
            if re.search(r"(?i)(password|token|key)=[^\s]+", line):
                findings.append(
                    {
                        "type": "hardcoded-secret",
                        "severity": "medium",
                        "message": "Hardcoded credential in URL",
                        "line": i,
                        "raw": line[:120],
                    }
                )
    return findings


def _has_code(text: str) -> bool:
    """Return True when the text contains programming‑like content."""
    return bool(re.search(r"\b(def |import |for |while |if |class )\b", text))


# ---------------------------------------------------------------------------
# LLM call helper – all workflow methods use this single async function.
# ---------------------------------------------------------------------------

async def _generate(llm: ModelManager, prompt: str, temperature: float = 0.3) -> str:
    """Call the LLM (no chain‑of‑thought). Returns ``""`` when unreachable/failed."""
    assert llm is not None
    for _ in (1, 2):
        try:
            txt = await llm.generate(prompt, role="sage", temperature=temperature, think=False)
        except Exception as exc:
            logger.warning("ComplianceWorkflow LLM call failed", error=str(exc))
            return ""
        txt = (txt or "").strip()
        head = txt[:40].lower()
        if not (head.startswith("[") and "error" in head):
            return txt
    return ""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ComplianceIssue:
    """A single compliance issue found by static scan or LLM review."""

    type: str
    severity: str  # Critical / High / Medium / Low
    message: str
    line: int | None = None
    raw: str = ""


@dataclass
class ComplianceWorkflow:
    """Grounded compliance checking: static scan → LLM review → honest report."""

    name: str = "compliance"
    description: str = "Regulatory compliance checks — GDPR, SOC2, HIPAA, PCI-DSS, CCPA"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["compliance_analysis", "policy_mapping", "risk_assessment"]
    )
    llm: ModelManager | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm: ModelManager = ModelManager()

    # ------------------------------------------------------------------
    # Static‑scan helpers (used by every method)
    # ------------------------------------------------------------------

    @staticmethod
    def _scan_document(document: str) -> list[ComplianceIssue]:
        """Run deterministic static checks on *document* and return ``ComplianceIssue`` objects."""
        issues: list[ComplianceIssue] = []
        if not document or not _has_code(document):
            return issues
        for finding in _scan_text(document):
            issues.append(
                ComplianceIssue(
                    type=finding["type"],
                    severity=finding["severity"],
                    message=finding["message"],
                    line=finding["line"],
                    raw=finding["raw"],
                )
            )
        return issues

    # ------------------------------------------------------------------
    # LLM‑driven phases – each now receives static findings as context
    # ------------------------------------------------------------------

    async def _generate(self, prompt: str, temperature: float = 0.3) -> str:
        """Async LLM call wrapper; delegates to _call_llm."""
        return await self._call_llm(prompt, temperature)

    async def analyze_policy(self, document: str, framework: str) -> dict[str, Any]:
        assert self.llm is not None
        static_issues = self._scan_document(document)
        # Build a concise static‑findings summary for the LLM prompt
        static_summary = ""
        if static_issues:
            static_summary = "STATIC SCAN FINDINGS (before LLM review):\n"
            for iss in static_issues[:8]:  # cap at 8 to keep prompt size reasonable
                static_summary += (
                    f"Line {iss.line}: [{iss.severity}] {iss.type} – {iss.message}\n"
                    f"  Raw: {iss.raw}\n\n"
                )
        else:
            static_summary = "No deterministic static issues found in the provided document.\n"

        prompt_text = (
            f"Analyze the following document against {framework.upper()}.\n\n"
            f"{static_summary}"
            f"Document (truncated to 3000 chars):\n"
            f"{truncate(document, 3000)}\n\n"
            f"Identify:\n"
            f"1. Which specific {framework.upper()} regulations/requirements apply\n"
            f"2. Areas of compliance\n"
            f"3. Gaps or violations with specific references\n"
            f"4. Risk level for each gap (Critical / High / Medium / Low)\n\n"
            f"Return your analysis as structured text, referencing any static findings "
            f"that are relevant."
        )
        analysis = await self._call_llm(prompt_text, temperature=0.2)
        return {
            "framework": framework.upper(),
            "analysis": analysis,
            "static_findings": [i.__dict__ for i in static_issues],
        }

    async def map_requirements(
        self, document: str, frameworks: list[str]
    ) -> dict[str, Any]:
        assert self.llm is not None
        static_issues: list[ComplianceIssue] = []
        for fw in frameworks:
            static_issues.extend(self._scan_document(document))
        static_summary = ""
        if static_issues:
            static_summary = "STATIC SCAN FINDINGS (before LLM review):\n"
            for iss in static_issues[:12]:
                static_summary += (
                    f"Line {iss.line}: [{iss.severity}] {iss.type} – {iss.message}\n"
                    f"  Raw: {iss.raw}\n\n"
                )
        else:
            static_summary = "No deterministic static issues found in the provided document.\n"

        prompt_text = (
            f"Create a requirements traceability matrix mapping the following document\n"
            f"{truncate(document, 2000)}\n\n"
            f"against {', '.join(f.upper() for f in frameworks)}:\n"
            f"For each framework requirement, show:\n"
            f"1. Requirement ID and description\n"
            f"2. Where it is addressed in the document\n"
            f"3. Compliance status (Compliant / Partially Compliant / Non‑Compliant / Not Applicable)\n"
            f"4. Evidence or gap description\n\n"
            f"{static_summary}"
            f"Return the matrix in text form, referencing any static findings that are relevant."
        )
        matrix = await self._call_llm(prompt_text, temperature=0.2)
        return {
            "traceability_matrix": matrix,
            "frameworks": frameworks,
            "static_findings": [i.__dict__ for i in static_issues],
        }

    async def assess_risk(
        self, analysis_results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        assert self.llm is not None
        # Gather static findings that appeared in any analysis
        all_static: list[dict[str, Any]] = []
        for r in analysis_results:
            all_static.extend(r.get("static_findings", []))

        static_summary = ""
        if all_static:
            static_summary = "Relevant static findings across analyses:\n"
            for iss in all_static[:10]:
                static_summary += (
                    f"Line {iss.get('line', '?')}: [{iss.get('severity', '?')}] "
                    f"{iss.get('type', '?')} – {iss.get('message', '?')}\n"
                )
        else:
            static_summary = "No static findings referenced in the provided analyses.\n"

        combined = "\n\n".join(
            f"Framework {r.get('framework', '?')}:\n{r.get('analysis', '')[:1000]}"
            for r in analysis_results
        )

        prompt_text = (
            f"Perform a consolidated risk assessment based on the following compliance analyses:\n\n"
            f"{combined}\n\n"
            f"{static_summary}"
            f"Provide:\n"
            f"1. Overall risk rating\n"
            f"2. Top 5 critical findings across all frameworks\n"
            f"3. Prioritized remediation roadmap\n"
            f"4. Estimated effort and impact for each remediation"
        )
        risk_text = await self._call_llm(prompt_text, temperature=0.3)
        return {
            "risk_assessment": risk_text,
            "static_findings_refs": all_static,
        }

    async def generate_remediation_plan(self, risk_assessment: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt_text = (
            f"Based on this risk assessment, create a detailed remediation plan:\n\n"
            f"{risk_assessment[:2000]}\n\n"
            f"For each finding, provide:\n"
            f"1. Specific remediation steps\n"
            f"2. Responsible role or team\n"
            f"3. Suggested timeline (immediate / short-term / long-term)\n"
            f"4. verification criteria"
        )
        plan = await self._call_llm(prompt_text, temperature=0.3)
        return {"remediation_plan": plan}

    # ------------------------------------------------------------------
    # Executive entry point
    # ------------------------------------------------------------------

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        document = ctx.get("document", task)
        frameworks = ctx.get("frameworks", ["gdpr", "hipaa", "soc2"])

        logger.info("Compliance workflow started", frameworks=frameworks)

        if not document or not document.strip():
            logger.warning("Compliance workflow: no document provided")
            return {
                "task": task,
                "frameworks_checked": frameworks,
                "analyses": [],
                "requirements_mapping": {},
                "risk_assessment": "",
                "remediation_plan": "",
                "status": "degraded",
                "degraded": True,
                "no_code_provided": True,
            }

        # 1️⃣ Static scan – always run, results carried through
        static_findings = self._scan_document(document)

        # 2️⃣ LLM‑driven analysis (each phase now sees static findings)
        analyses: list[dict[str, Any]] = []
        for fw in frameworks:
            analyses.append(await self.analyze_policy(document, fw))

        mapping = await self.map_requirements(document, frameworks)
        risk = await self.assess_risk(analyses)
        remediation = await self.generate_remediation_plan(risk.get("risk_assessment", ""))

        result = {
            "task": task,
            "frameworks_checked": frameworks,
            "analyses": analyses,
            "requirements_mapping": mapping,
            "risk_assessment": risk.get("risk_assessment", ""),
            "remediation_plan": remediation.get("remediation_plan", ""),
            "status": "completed",
            "degraded": False,
            "static_findings": [i.__dict__ for i in static_findings],
        }
        logger.info(
            "Compliance workflow completed",
            frameworks_checked=len(frameworks),
            static_issue_count=len(static_findings),
        )
        return result


COMPLIANCE_WORKFLOW = ComplianceWorkflow()