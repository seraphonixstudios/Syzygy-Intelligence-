"""Translation workflow — multi-language translation with cultural adaptation and review."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger


@dataclass
class TranslateWorkflow:
    """Multi-language translation with cultural adaptation, glossary support, and quality review."""

    name: str = "translate"
    description: str = "Multi-language translation with cultural adaptation and quality review"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["translation", "cultural_adaptation", "language_review"]
    )
    llm: ModelManager | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm: ModelManager = ModelManager()

    async def detect_language(self, text: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Detect the language of the following text. Return ISO 639-1 code and language name:\n\n"
            f"{text[:1000]}"
        )
        result = await self.llm.generate(prompt, temperature=0.1)
        return {"detected": result}

    async def translate_direct(self, text: str, source: str, target: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Translate the following text from {source} to {target}:\n\n"
            f"{text[:3000]}\n\n"
            f"Return ONLY the translated text without explanations or notes. "
            f"Preserve formatting, markdown, and special characters."
        )
        translation = await self.llm.generate(prompt, temperature=0.2)
        return {"source": source, "target": target, "translation": translation}

    async def cultural_adapt(self, text: str, translation: str, source: str, target: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Review and adapt the following translation from {source} to {target} "
            f"for cultural appropriateness:\n\n"
            f"Original: {text[:1500]}\n\n"
            f"Translation: {translation[:1500]}\n\n"
            f"Check for:\n"
            f"1. Idioms and metaphors that may not translate\n"
            f"2. Cultural references that need localization\n"
            f"3. Formality level (tone, pronouns, honorifics)\n"
            f"4. Date, time, number, and currency formats\n"
            f"5. Taboos or sensitive content\n"
            f"Provide adapted version with explanation of changes."
        )
        adapted = await self.llm.generate(prompt, temperature=0.3)
        return {"adaptation": adapted}

    async def quality_review(self, text: str, translation: str, source: str, target: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Perform a quality review of this translation from {source} to {target}:\n\n"
            f"Original: {text[:2000]}\n\n"
            f"Translation: {translation[:2000]}\n\n"
            f"Score the following (1-10):\n"
            f"1. Accuracy — meaning preserved\n"
            f"2. Fluency — natural in target language\n"
            f"3. Terminology — consistent with domain\n"
            f"4. Style — matches original tone\n"
            f"5. Completeness — no omissions\n"
            f"Provide overall score and revision suggestions."
        )
        review = await self.llm.generate(prompt, temperature=0.3)
        return {"review": review}

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

        result = {
            "task": task,
            "source_language": source,
            "target_language": target,
            "detection": detected,
            "direct_translation": direct,
            "cultural_adaptation": adaptation,
            "quality_review": quality,
            "status": "completed",
        }
        logger.info("Translation workflow completed", source=source, target=target)
        return result


TRANSLATE_WORKFLOW = TranslateWorkflow()
