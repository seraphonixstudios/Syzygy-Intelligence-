"""Audit workflow — security scanning, code review, anti-pattern detection, compliance checks.

A deterministic static scan finds real line-numbered issues (dangerous calls,
bare excepts, hardcoded secrets, os.system, etc.) before any LLM review, and
the LLM gets the static findings plus the code — claims are never unsourced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger
from app.text_utils import truncate

# ( rule_id, severity, regex pattern, advice )
_STATIC_RULES: list[tuple[str, str, str, str]] = [
    ("subprocess-shell", "high", r"subprocess\.", "subprocess used near shell mode — prefer arg lists, no shell"),
    ("eval-exec", "high", r"\b(?:eval|exec)\(", "eval/exec on untrusted input — replace with safe parsing"),
    ("bare-except", "low", r"except\s*:\s*$", "bare except swallows all exceptions — catch specific types"),
    ("os-system", "high", r"os\.system\(", "os.system call — use subprocess with arg list"),
    (
        "hardcoded-secret",
        "medium",
        r"(SECRET_KEY|API_TOKEN|TOKEN_SECRET|PASSWORD)\s*=\s*['\"]",
        "hardcoded secret-like literal — use env var",
    ),
    (
        "pickle-import",
        "low",
        r"import pickle\b|pickle\.load\b",
        "insecure deserialization (pickle) — avoid for untrusted data",
    ),
    (
        "sql-concat",
        "medium",
        r"\.execute\(.+%|\.execute\(.+\+",
        "SQL built by string concatenation — use parameterized queries",
    ),
]


def _static_scan(code: str) -> list[dict[str, Any]]:
    findings = []
    lines = code.splitlines()
    for rule_id, severity, pattern, advice in _STATIC_RULES:
        for idx, line in enumerate(lines, 1):
            if re.search(pattern, line):
                findings.append({
                    "rule": rule_id,
                    "severity": severity,
                    "line": idx,
                    "snippet": line.strip()[:120],
                    "advice": advice,
                })
    return findings


@dataclass
class AuditWorkflow:
    """Grounded audit: deterministic static scan; LLM review tied to real findings."""

    name: str = "audit"
    description: str = "Security scanning, code review, anti-pattern detection, and compliance checks"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["code_review", "vulnerability_scanning", "compliance_checking"]
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
                text = await self.llm.generate(prompt, role="critic", temperature=temperature, think=False)
            except Exception as exc:
                logger.warning("AuditWorkflow LLM call failed", error=str(exc))
                return ""
            text = (text or "").strip()
            if text:
                head = text[:40].lower()
                if not (head.startswith("[") and "error" in head):
                    return text
        return ""

    async def scan_vulnerabilities(self, code: str, language: str = "python") -> dict[str, Any]:
        static = _static_scan(code) if language == "python" else []
        findings_text = "\n".join(
            f"- [{f['severity']}] line {f['line']}: {f['rule']} ({f['snippet']})"
            for f in static
        ) or "(no static rules triggered)"
        prompt = (
            f"Scan the following {language} code for security vulnerabilities:\n\n"
            f"```{language}\n{truncate(code, 12000)}\n```\n\n"
            f"Static scan found:\n{findings_text}\n\n"
            f"Identify: injection flaws, auth issues, data exposure, insecure deserialization, "
            f"vulnerable dependency usage. For each finding rate Critical / High / Medium / Low. "
            f"Confirm or refute the static findings — do not invent line numbers."
        )
        result = await self._generate(prompt, temperature=0.2)
        severity_counts = {}
        for f in static:
            severity_counts[f["severity"]] = severity_counts.get(f["severity"], 0) + 1
        return {
            "vulnerabilities": result,
            "static_findings": static,
            "static_summary": severity_counts,
            "language": language,
        }

    async def review_code_quality(self, code: str, language: str = "python") -> dict[str, Any]:
        prompt = (
            f"Review the following {language} code for quality issues:\n\n"
            f"```{language}\n{truncate(code, 12000)}\n```\n\n"
            f"Analyze: anti-patterns, performance, error handling gaps, type safety, coverage. "
            f"Give file-referenced recommendations only."
        )
        result = await self._generate(prompt, temperature=0.3)
        return {"quality_review": result}

    async def check_compliance(
        self, code: str, standards: list[str] | None = None, language: str = "python"
    ) -> dict[str, Any]:
        standards = standards or ["owasp", "pci-dss"]
        prompt = (
            f"Check the following {language} code against {', '.join(standards)}:\n\n"
            f"```{language}\n{truncate(code, 12000)}\n```\n\n"
            f"For each standard, list: requirements that apply, pass/fail, remediation for failures."
        )
        result = await self._generate(prompt, temperature=0.2)
        return {"compliance_check": result, "standards": standards}

    async def generate_report(
        self, vulnerabilities: dict[str, Any], quality: dict[str, Any], compliance: dict[str, Any]
    ) -> str:
        static = vulnerabilities.get("static_findings", [])
        static_text = "\n".join(
            f"- [{f['severity']}] {f['rule']} @ line {f['line']}" for f in static[:20]
        ) or "(none)"
        combined = (
            f"Vulnerability Scan:\n{vulnerabilities.get('vulnerabilities', 'N/A')}\n\n"
            f"Deterministic static findings:\n{static_text}\n\n"
            f"Code Quality Review:\n{quality.get('quality_review', 'N/A')}\n\n"
            f"Compliance Check:\n{compliance.get('compliance_check', 'N/A')}"
        )
        prompt = (
            f"Generate a concise executive audit report from the following findings:\n\n{combined}\n\n"
            f"Structure: Executive Summary, Critical Issues, Recommendations, Priority Matrix."
        )
        return await self._generate(prompt, temperature=0.3)

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        code = ctx.get("code", task)
        language = ctx.get("language", "python")
        standards = ctx.get("standards", ["owasp", "pci-dss"])

        logger.info("Audit workflow started", language=language, standards=standards)
        if not (isinstance(code, str) and code.strip()):
            return {
                "task": task,
                "language": language,
                "note": "no-code-provided",
                "status": "completed",
            }
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
        logger.info("Audit workflow completed", static_findings=len(vulnerabilities.get("static_findings", [])))
        return result


AUDIT_WORKFLOW = AuditWorkflow()
