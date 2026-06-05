"""Consensus phase implementations for Syzygy."""

from __future__ import annotations

PHASE_DESCRIPTIONS = {
    "proposal": "Each agent produces an independent proposal tagged by polarity and archetype.",
    "critique": "Cross-polarity critique with shadow archetype activation and memory masking.",
    "refinement": "Agents revise proposals incorporating cross-polarity feedback.",
    "evaluation": "Multi-axis scoring across accuracy, holistic insight, creativity, feasibility, and polarity balance.",
    "convergence": "Early stop on high polarity balance or low variance (max 4-6 rounds).",
    "synthesis": "Rebis/Self Oracle produces unified output with Polarity Fusion Report.",
}

PHASE_ORDER = ["proposal", "critique", "refinement", "evaluation", "convergence", "synthesis"]
