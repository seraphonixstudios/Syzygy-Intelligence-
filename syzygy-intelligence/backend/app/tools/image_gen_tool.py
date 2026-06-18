"""Image generation tool — txt2img, upscale, remove background for agents."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from app.services.image_gen import (
    ImageGenError,
    create_image_gen_provider,
    enhance_prompt,
)


@dataclass
class ImageGenTool:
    name: str = "image_gen"
    description: str = (
        "Generate, upscale, or edit images using SOTA diffusion models "
        "(Flux, SD3.5). Supports txt2img, upscale 4x, and background removal."
    )

    async def execute(
        self,
        action: str = "txt2img",
        prompt: str = "",
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        image_data: str = "",
        enhance: bool = True,
    ) -> dict[str, Any]:
        """Execute an image generation action.

        Args:
            action: 'txt2img', 'upscale', or 'remove_background'
            prompt: Text description for txt2img
            negative_prompt: Things to avoid in the image
            width, height: Output dimensions
            image_data: Base64-encoded image for upscale/rembg
            enhance: Whether to LLM-enhance the prompt

        Returns:
            dict with 'image' (base64), 'format', and optional 'enhanced_prompt'
        """
        try:
            provider = create_image_gen_provider()
        except Exception as e:
            return {"error": f"Failed to create image provider: {e}"}

        if action == "txt2img":
            if not prompt:
                return {"error": "prompt is required for txt2img"}
            final_prompt = prompt
            if enhance:
                try:
                    final_prompt = await enhance_prompt(prompt)
                except Exception:
                    pass
            try:
                img_bytes = await provider.txt2img(
                    prompt=final_prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                )
            except ImageGenError as e:
                return {"error": f"Image generation failed: {e}"}

            result: dict[str, Any] = {
                "image": base64.b64encode(img_bytes).decode(),
                "format": "png",
                "width": width,
                "height": height,
            }
            if enhance and final_prompt != prompt:
                result["enhanced_prompt"] = final_prompt
            return result

        elif action == "upscale":
            if not image_data:
                return {"error": "image_data (base64) is required for upscale"}
            try:
                img_bytes = base64.b64decode(image_data)
            except Exception:
                return {"error": "Invalid base64 image_data"}
            try:
                upscaled = await provider.upscale(img_bytes)
            except ImageGenError as e:
                return {"error": f"Upscale failed: {e}"}
            return {
                "image": base64.b64encode(upscaled).decode(),
                "format": "png",
            }

        elif action == "remove_background":
            if not image_data:
                return {"error": "image_data (base64) is required for remove_background"}
            try:
                img_bytes = base64.b64decode(image_data)
            except Exception:
                return {"error": "Invalid base64 image_data"}
            try:
                nobg = await provider.remove_background(img_bytes)
            except ImageGenError as e:
                return {"error": f"Background removal failed: {e}"}
            return {
                "image": base64.b64encode(nobg).decode(),
                "format": "png",
            }

        else:
            return {"error": f"Unknown action: {action}. Use txt2img, upscale, or remove_background."}
