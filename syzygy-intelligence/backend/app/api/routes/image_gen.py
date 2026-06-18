"""Image generation API routes — txt2img, upscale, remove background."""

from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.api.auth import require_user
from app.db.models import User
from app.services.image_gen import (
    ImageGenError,
    create_image_gen_provider,
    enhance_prompt,
)

router = APIRouter()


@router.post("/generate")
async def generate_image(
    prompt: str = "",
    negative_prompt: str = "",
    width: int = 1024,
    height: int = 1024,
    enhance: bool = True,
    user: User = Depends(require_user),
) -> dict[str, Any]:
    """Generate an image from a text prompt.

    Uses the configured provider (ComfyUI/Replicate/Mock).
    Optionally enhances the prompt via LLM for better quality.
    """
    if not prompt:
        raise HTTPException(status_code=422, detail="prompt is required")

    final_prompt = prompt
    if enhance:
        try:
            final_prompt = await enhance_prompt(prompt)
        except Exception as e:
            from app.logging_setup import logger
            logger.warning("Prompt enhancement failed", error=str(e))

    provider = create_image_gen_provider()
    try:
        img_bytes = await provider.txt2img(
            prompt=final_prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
        )
    except ImageGenError as e:
        raise HTTPException(status_code=500, detail=str(e))

    result: dict[str, Any] = {
        "image": base64.b64encode(img_bytes).decode(),
        "format": "png",
        "width": width,
        "height": height,
    }
    if enhance and final_prompt != prompt:
        result["enhanced_prompt"] = final_prompt
    return result


@router.post("/upscale")
async def upscale_image(
    file: UploadFile,
    scale: int = 4,
    user: User = Depends(require_user),
) -> dict[str, Any]:
    """Upscale an uploaded image by 4x (default).

    Accepts PNG/JPEG uploads, returns base64-encoded image.
    """
    if scale not in (2, 4):
        raise HTTPException(status_code=422, detail="scale must be 2 or 4")

    image_data = await file.read()
    if not image_data:
        raise HTTPException(status_code=422, detail="Empty file")

    provider = create_image_gen_provider()
    try:
        upscaled = await provider.upscale(image_data, scale=scale)
    except ImageGenError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "image": base64.b64encode(upscaled).decode(),
        "format": "png",
        "scale": scale,
    }


@router.post("/remove-background")
async def remove_background(
    file: UploadFile,
    user: User = Depends(require_user),
) -> dict[str, Any]:
    """Remove background from an uploaded image."""
    image_data = await file.read()
    if not image_data:
        raise HTTPException(status_code=422, detail="Empty file")

    provider = create_image_gen_provider()
    try:
        nobg = await provider.remove_background(image_data)
    except ImageGenError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "image": base64.b64encode(nobg).decode(),
        "format": "png",
    }


@router.post("/enhance-prompt")
async def enhance_prompt_endpoint(
    prompt: str = "",
    user: User = Depends(require_user),
) -> dict[str, Any]:
    """Enhance a prompt using LLM for better image generation quality."""
    if not prompt:
        raise HTTPException(status_code=422, detail="prompt is required")
    enhanced = await enhance_prompt(prompt)
    return {"original": prompt, "enhanced": enhanced}
