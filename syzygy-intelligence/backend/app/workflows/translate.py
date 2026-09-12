"""Translation workflow — multi-language translation with cultural adaptation and quality review.

Grounded version: round‑trip fidelity (source → target → back‑translate) with a
divergence score; ``degraded`` is set when the divergence exceeds a threshold
or when any phase returns empty output.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger
from app.text_utils import truncate

_THRESHOLD = 0.20  # max allowed divergence (0–1) before marking degraded


def _safe_float(value: Any) -> float | None:
    """Return the float value or None if conversion fails."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compute_divergence(original: str, back_translated: str) -> float:
    """Return a 0–1 divergence score: proportion of original words not found
    in the back‑translation (case‑insensitive, simple word‑set overlap)."""
    if not original or not back_translated:
        return 1.0
    orig_words = {w.lower() for w in re.findall(r"\b\w+\b", original)}
    back_words = {w.lower() for w in re.findall(r"\b\w+\b", back_translated)}
    if not orig_words:
        return 1.0
    missing = orig_words - back_words
    return len(missing) / len(orig_words)


def _parse_json_obj(text: str) -> dict[str, Any] | None:
    """Leniently extract a JSON object from LLM output."""
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\n(.*?)```", text, re.DOTALL)
    candidate = fenced.group(1).strip() if fenced else text.strip()
    start, end = candidate.find("{"), candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(candidate[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


@dataclass
class TranslateWorkflow:
    """Grounded translation: real LLM calls + round‑trip fidelity check."""

    name: str = "translate"
    description: str = "Multi-language translation with cultural adaptation and quality review"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["translation", "cultural_adaptation", "language_review"]
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
                text = await self.llm.generate(prompt, role="sage", temperature=temperature, think=False)
            except Exception as exc:
                logger.warning("TranslateWorkflow LLM call failed", error=str(exc))
                return ""
            text = (text or "").strip()
            head = text[:40].lower()
            if not (head.startswith("[") and "error" in head):
                return text
        return ""

    async def detect_language(self, text: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Detect the language of the following text. Return ISO 639-1 code and language name:\n\n"
            f"{truncate(text, 1000)}"
        )
        result = await self._generate(prompt, temperature=0.1)
        return {"detected": result}

    async def translate_direct(self, text: str, source: str, target: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Translate the following text from {source} to {target}:\n\n"
            f"{truncate(text, 3000)}\n\n"
            f"Return ONLY the translated text without explanations or notes. "
            f"Preserve formatting, markdown, and special characters."
        )
        translation = await self._generate(prompt, temperature=0.2)
        return {"source": source, "target": target, "translation": translation}

    async def cultural_adapt(self, text: str, translation: str, source: str, target: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Review and adapt the following translation from {source} to {target} "
            f"for cultural appropriateness:\n\n"
            f"Original: {truncate(text, 1500)}\n\n"
            f"Translation: {truncate(translation, 1500)}\n\n"
            f"Check for:\n"
            f"1. Idioms and metaphors that may not translate\n"
            f"2. Cultural references that need localization\n"
            f"3. Formality level (tone, pronouns, honorifics)\n"
            f"4. Date, time, number, and currency formats\n"
            f"5. Taboos or sensitive content\n"
            f"Provide adapted version with explanation of changes."
        )
        adapted = await self._generate(prompt, temperature=0.3)
        return {"adaptation": adapted}

    async def quality_review(self, text: str, translation: str, source: str, target: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Perform a quality review of this translation from {source} to {target}:\n\n"
            f"Original: {truncate(text, 2000)}\n\n"
            f"Translation: {truncate(translation, 2000)}\n\n"
            f"Score the following (1-10):\n"
            f"1. Accuracy — meaning preserved\n"
            f"2. Fluency — natural in target language\n"
            f"3. Terminology — consistent with domain\n"
            f"4. Style — matches original tone\n"
            f"5. Completeness — no omissions\n"
            f"Provide overall score and revision suggestions."
        )
        review = await self._generate(prompt, temperature=0.3)
        return {"review": review}

    async def translate_roundtrip(self, text: str, source: str, target: str) -> dict[str, Any]:
        """Perform source→target translation then back‑translate target→source.

        Returns a dict with:
        - direct_translation: the forward translation
        - back_translation: the target→source translation
        - divergence: 0–1 score (1 = completely different)
        - degraded: True if divergence > _THRESHOLD or any phase empty
        """
        # Forward translation
        forward = await self.translate_direct(text, source, target)
        forward_text = forward.get("translation", "") or ""

        # Back‑translation (target → source). We reuse translate_direct with swapped languages.
        back = await self.translate_direct(forward_text, target, source)
        back_text = back.get("translation", "") or ""

        # Divergence score
        divergence = _compute_divergence(text, back_text)

        degraded = divergence > _THRESHOLD or not forward_text or not back_text

        return {
            "direct_translation": forward,
            "back_translation": back,
            "divergence": divergence,
            "degraded": degraded,
        }

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        text = ctx.get("text", task)
        source = ctx.get("source_language", None)
        target = ctx.get("target_language", "spanish")

        logger.info("Translation workflow started", target=target, source=source or "auto-detect")

        if not source:
            detected = await self.detect_language(text)
            source = detected.get("detected", "unknown")
        else:
            detected = None

        direct = await self.translate_direct(text, source, target)
        adaptation = await self.cultural_adapt(text, direct.get("translation", ""), source, target)
        quality = await self.quality_review(text, direct.get("translation", ""), source, target)

        # Round‑trip fidelity check
        rt = await self.translate_roundtrip(text, source, target)

        result = {
            "task": task,
            "source_language": source,
            "target_language": target,
            "detection": detected,
            "direct_translation": direct,
            "cultural_adaptation": adaptation,
            "quality_review": quality,
            "roundtrip": rt,
            "status": "completed" if not rt.get("degraded") else "degraded",
        }
        logger.info(
            "Translation workflow completed",
            source=source,
            target=target,
            degraded=rt.get("degraded"),
        )
        return result


TRANSLATE_WORKFLOW = TranslateWorkflow()