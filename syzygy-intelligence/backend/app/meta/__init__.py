"""Self-evaluation and meta-cognition module for recursive self-improvement."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class EvaluationResult:
    """Result of a self-evaluation."""
    score: float
    dimensions: dict[str, float]
    feedback: list[str]
    suggestions: list[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ImprovementProposal:
    """A proposed self-improvement action."""
    id: str
    target: str
    change: str
    rationale: str
    expected_impact: float
    status: str = "proposed"  # proposed, applied, rejected
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    applied_at: str | None = None
    result_score: float | None = None


class MetaCognitionEngine:
    """Evaluates system outputs and proposes improvements."""

    def __init__(self):
        self._history: list[EvaluationResult] = []
        self._proposals: list[ImprovementProposal] = []
        self._improvement_count = 0

    def evaluate_output(self, output: str, context: dict[str, Any]) -> EvaluationResult:
        """Evaluate a system output across multiple dimensions."""
        lines = output.strip().split("\n")
        word_count = len(output.split())
        line_count = len(lines)

        dimensions = {
            "completeness": min(1.0, word_count / 500) if word_count > 0 else 0,
            "coherence": min(1.0, 1.0 - (line_count / max(word_count, 1)) * 0.1),
            "specificity": min(1.0, len(set(output.lower().split())) / max(word_count, 1) * 5),
            "actionability": 0.8 if any(w in output.lower() for w in ["implement", "run", "build", "create", "use"]) else 0.3,
            "structure": 0.9 if any(c in output for c in ["\n1.", "\n- ", "\n  "]) else 0.5,
        }
        score = sum(dimensions.values()) / len(dimensions)

        feedback: list[str] = []
        suggestions: list[str] = []

        if dimensions["completeness"] < 0.4:
            feedback.append("Output is too short — needs more detail")
            suggestions.append("Increase output verbosity by including examples and explanations")
        if dimensions["actionability"] < 0.5:
            feedback.append("Output lacks actionable instructions")
            suggestions.append("Include explicit commands, code snippets, or step-by-step guidance")
        if dimensions["structure"] < 0.6:
            feedback.append("Output could benefit from better structure")
            suggestions.append("Use numbered lists, headers, or bullet points for clarity")

        result = EvaluationResult(
            score=score,
            dimensions=dimensions,
            feedback=feedback,
            suggestions=suggestions or ["Output meets quality thresholds"],
        )
        self._history.append(result)
        return result

    def propose_improvements(self, eval_result: EvaluationResult) -> list[ImprovementProposal]:
        """Generate improvement proposals based on evaluation."""
        proposals: list[ImprovementProposal] = []

        for dim, val in eval_result.dimensions.items():
            if val < 0.5:
                proposal = ImprovementProposal(
                    id=f"imp-{self._improvement_count}-{dim}",
                    target=dim,
                    change=f"Improve {dim} score from {val:.2f} to {min(1.0, val + 0.3):.2f}",
                    rationale=eval_result.feedback[0] if eval_result.feedback else f"Low {dim} score",
                    expected_impact=0.3,
                )
                proposals.append(proposal)
                self._proposals.append(proposal)
                self._improvement_count += 1

        return proposals

    def apply_proposal(self, proposal_id: str) -> ImprovementProposal | None:
        """Mark a proposal as applied."""
        for p in self._proposals:
            if p.id == proposal_id and p.status == "proposed":
                p.status = "applied"
                p.applied_at = datetime.utcnow().isoformat()
                return p
        return None

    def get_history(self) -> list[EvaluationResult]:
        return self._history

    def get_proposals(self, status: str | None = None) -> list[ImprovementProposal]:
        if status:
            return [p for p in self._proposals if p.status == status]
        return self._proposals

    def get_summary(self) -> dict[str, Any]:
        if not self._history:
            return {"total_evaluations": 0, "average_score": 0, "total_proposals": 0}
        avg_score = sum(e.score for e in self._history) / len(self._history)
        return {
            "total_evaluations": len(self._history),
            "average_score": round(avg_score, 3),
            "total_proposals": len(self._proposals),
            "applied_proposals": sum(1 for p in self._proposals if p.status == "applied"),
            "latest_score": self._history[-1].score,
        }


# Global singleton
meta_engine = MetaCognitionEngine()
