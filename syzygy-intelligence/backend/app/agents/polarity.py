"""Polarity system for Syzygy agents.

Manages the balance between Masculine (☉), Feminine (☽), and Unified (☿) polarities.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PolarityType(StrEnum):
    MASCULINE = "masculine"
    FEMININE = "feminine"
    UNIFIED = "unified"


@dataclass
class PolarityConfig:
    type: PolarityType
    glyph: str
    keyword: str
    qualities: list[str]

    @property
    def opposite(self) -> PolarityType:
        if self.type == PolarityType.MASCULINE:
            return PolarityType.FEMININE
        elif self.type == PolarityType.FEMININE:
            return PolarityType.MASCULINE
        return PolarityType.UNIFIED

    @property
    def color_hex(self) -> str:
        return {
            PolarityType.MASCULINE: "#c9a84c",
            PolarityType.FEMININE: "#b0b0c0",
            PolarityType.UNIFIED: "#00f0ff",
        }[self.type]


POLARITY_CONFIGS = {
    PolarityType.MASCULINE: PolarityConfig(
        type=PolarityType.MASCULINE,
        glyph="☉",
        keyword="Sol",
        qualities=["active", "assertive", "structured", "analytical", "decisive", "protective"],
    ),
    PolarityType.FEMININE: PolarityConfig(
        type=PolarityType.FEMININE,
        glyph="☽",
        keyword="Luna",
        qualities=["receptive", "nurturing", "intuitive", "holistic", "empathetic", "creative"],
    ),
    PolarityType.UNIFIED: PolarityConfig(
        type=PolarityType.UNIFIED,
        glyph="☿",
        keyword="Rebis",
        qualities=["integrated", "transcendent", "balanced", "synthetic", "wise", "whole"],
    ),
}


POLARITY_DIMENSIONS = [
    "assertiveness",  # masculine vs. feminine
    "analysis",       # analytical vs. holistic
    "structure",      # structured vs. fluid
    "action",         # active vs. receptive
    "expression",     # decisive vs. emergent
]


def compute_polarity_balance(polarities: list[PolarityType]) -> float:
    """Compute polarity balance score from 0 (all masculine) to 1 (all feminine).

    Returns 0.5 for perfect balance or unified-only teams.
    """
    if not polarities:
        return 0.5

    counts = {
        PolarityType.MASCULINE: 0,
        PolarityType.FEMININE: 0,
        PolarityType.UNIFIED: 0,
    }

    for p in polarities:
        counts[p] = counts.get(p, 0) + 1

    total = sum(counts.values())
    if total == 0:
        return 0.5

    # Unified count contributes to balance
    masc_ratio = counts[PolarityType.MASCULINE] / total
    fem_ratio = counts[PolarityType.FEMININE] / total

    # Perfect balance target: 0.5
    return 1.0 - abs(masc_ratio - fem_ratio)


def is_balanced(score: float, threshold: float = 0.6) -> bool:
    return score >= threshold


def get_dominant_polarity(polarities: list[PolarityType]) -> PolarityType | None:
    """Determine the dominant polarity in a set."""
    if not polarities:
        return None
    masc = polarities.count(PolarityType.MASCULINE)
    fem = polarities.count(PolarityType.FEMININE)
    unified = polarities.count(PolarityType.UNIFIED)
    if masc > fem and masc > unified:
        return PolarityType.MASCULINE
    elif fem > masc and fem > unified:
        return PolarityType.FEMININE
    return PolarityType.UNIFIED


__all__ = [
    "PolarityType",
    "PolarityConfig",
    "POLARITY_CONFIGS",
    "POLARITY_DIMENSIONS",
    "compute_polarity_balance",
    "is_balanced",
    "get_dominant_polarity",
]
