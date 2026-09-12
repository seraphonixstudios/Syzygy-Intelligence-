"""Shared text helpers — sentence-boundary truncation with an explicit marker.

Bare `text[:N]` slicing silently cuts content mid-word with no indication
that anything was dropped. Every prompt-side slice in workflows should go
through this helper instead, so cut content is always visibly cut.
"""

from __future__ import annotations

import re

TRUNCATION_MARKER = "…[truncated]"


def truncate(text: str, limit: int, marker: str = TRUNCATION_MARKER) -> str:
    """Cut `text` to at most `limit` chars, breaking at a sentence boundary."""
    if not isinstance(text, str):
        return text
    if len(text) <= limit:
        return text
    if limit <= 0:
        return ""
    budget = limit - len(marker)
    if budget <= 0:
        return marker
    window = text[:budget]
    # Prefer ending at the last sentence/paragraph boundary inside the window.
    boundary = max(
        window.rfind(". "),
        window.rfind("! "),
        window.rfind("? "),
        window.rfind("\n\n"),
    )
    if boundary <= 0 or boundary < budget * 0.5:
        # No usable boundary — hard cut on word boundary instead.
        match = re.search(r"\s", window[budget - 20 : budget])
        boundary = (budget - 20 + match.start()) if match else budget
    return window[:boundary].rstrip() + " " + marker
