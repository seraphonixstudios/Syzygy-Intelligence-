"""Image generation workflow — prompt enhancement → txt2img → refine iterations."""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger
from app.services.image_gen import (
    ImageGenError,
    create_image_gen_provider,
    enhance_prompt,
)


@dataclass
class ImageGenWorkflow:
    """End-to-end image creation: concept → enhanced prompt → generate → refine."""

    name: str = "image_gen"
    description: str = (
        "Generate high-quality images from text descriptions using SOTA diffusion models. "
        "Supports style transfer, iterative refinement, and multiple variations."
    )
    required_capabilities: list[str] = field(
        default_factory=lambda: ["image_generation", "prompt_engineering", "creative_direction"]
    )
    llm: ModelManager | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm = ModelManager()

    async def analyze_concept(self, task: str) -> dict[str, Any]:
        """Analyze the user's concept and produce generation parameters."""
        assert self.llm is not None
        prompt = (
            f"Analyze this image concept and extract key generation parameters:\n\n{task}\n\n"
            f"Return a JSON object with:\n"
            f"- subject: main subject description\n"
            f"- style: artistic style (photorealistic, oil painting, concept art, anime, etc.)\n"
            f"- mood: mood/atmosphere\n"
            f"- lighting: lighting type\n"
            f"- color_palette: dominant colors\n"
            f"- composition: framing/composition\n"
            f"- aspect_ratio: 'square', 'landscape', or 'portrait'\n"
            f"- negative: things to avoid\n"
            f"Return ONLY valid JSON, no other text."
        )
        analysis = await self.llm.generate(prompt, temperature=0.3)
        try:
            import json
            return json.loads(analysis)
        except (json.JSONDecodeError, TypeError):
            return {"subject": task, "style": "photorealistic", "mood": "neutral"}

    async def generate(
        self,
        prompt: str,
        params: dict[str, Any],
        variation_count: int = 1,
    ) -> dict[str, Any]:
        """Generate images from the enhanced prompt."""
        aspect = params.get("aspect_ratio", "square")
        dims = {"square": (1024, 1024), "landscape": (1216, 832), "portrait": (832, 1216)}
        width, height = dims.get(aspect, (1024, 1024))

        negative = params.get("negative", "")
        provider = create_image_gen_provider()

        try:
            img_bytes = await provider.txt2img(
                prompt=prompt,
                negative_prompt=negative,
                width=width,
                height=height,
            )
        except ImageGenError as e:
            return {"error": str(e), "status": "failed"}

        return {
            "image": base64.b64encode(img_bytes).decode(),
            "format": "png",
            "width": width,
            "height": height,
            "prompt": prompt,
            "status": "completed",
        }

    async def refine(
        self,
        previous: dict[str, Any],
        feedback: str,
    ) -> dict[str, Any]:
        """Refine a previously generated image based on feedback."""
        assert self.llm is not None
        current_prompt = previous.get("prompt", "")

        improvement = await self.llm.generate(
            f"Original prompt: {current_prompt}\n\n"
            f"User feedback: {feedback}\n\n"
            f"Rewrite the prompt to address the feedback while keeping the original intent. "
            f"Return ONLY the new prompt, no explanation.",
            temperature=0.6,
        )
        new_prompt = improvement.strip().strip('"').strip("'")

        provider = create_image_gen_provider()
        try:
            aspect = previous.get("aspect_ratio", "square")
            dims = {"square": (1024, 1024), "landscape": (1216, 832), "portrait": (832, 1216)}
            width, height = dims.get(aspect, (1024, 1024))

            img_bytes = await provider.txt2img(prompt=new_prompt, width=width, height=height)
        except ImageGenError as e:
            return {"error": str(e), "status": "failed"}

        return {
            "image": base64.b64encode(img_bytes).decode(),
            "format": "png",
            "width": width,
            "height": height,
            "prompt": new_prompt,
            "status": "completed",
        }

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        logger.info("ImageGen workflow started", task=task[:100])

        concept = await self.analyze_concept(task)

        raw_prompt = ctx.get("prompt_override", task)
        enhanced = await enhance_prompt(raw_prompt, self.llm)
        concept["enhanced_prompt"] = enhanced

        result = await self.generate(enhanced, concept)
        if result.get("status") == "failed":
            return result

        feedback_rounds = ctx.get("feedback_rounds", 0)
        current = result
        for i in range(feedback_rounds):
            fb = ctx.get(f"feedback_{i}", "")
            if fb:
                current = await self.refine(current, fb)
                if current.get("status") == "failed":
                    return current

        return {
            "task": task,
            "concept_analysis": concept,
            "result": current,
            "status": "completed",
        }


IMAGE_GEN_WORKFLOW = ImageGenWorkflow()
