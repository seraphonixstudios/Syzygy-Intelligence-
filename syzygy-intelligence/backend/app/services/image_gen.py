"""Image generation service — multi-provider support for SOTA image synthesis.

Supports ComfyUI (self-hosted Flux/SD3.5) and Replicate (cloud) backends.
Features: txt2img, upscale 4x, background removal, prompt enhancement.
"""

from __future__ import annotations

import base64
import io
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from typing import Protocol as TypingProtocol

from app.config import settings
from app.logging_setup import logger


class ImageGenError(Exception):
    """Base exception for image generation failures."""


# ─── Provider Protocol ──────────────────────────────────────────────

class ImageGenProvider(ABC):
    """Abstract base for image generation backends."""

    @abstractmethod
    async def txt2img(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 28,
        guidance_scale: float = 3.5,
        seed: int | None = None,
    ) -> bytes:
        ...

    @abstractmethod
    async def upscale(
        self,
        image_data: bytes,
        scale: int = 4,
    ) -> bytes:
        ...

    @abstractmethod
    async def remove_background(
        self,
        image_data: bytes,
    ) -> bytes:
        ...


# ─── ComfyUI Provider ──────────────────────────────────────────────

class ComfyUIProvider(ImageGenProvider):
    """Self-hosted ComfyUI backend for Flux/SD3.5.

    Requires a running ComfyUI instance at settings.comfyui_base_url.
    Workflow JSONs must be pre-uploaded or baked into the client.
    """

    def __init__(self, base_url: str = "") -> None:
        self.base_url = base_url or settings.comfyui_base_url
        self.client_id = str(uuid.uuid4())

    async def _queue_workflow(self, workflow: dict[str, Any]) -> bytes:
        import httpx

        payload = {
            "prompt": workflow,
            "client_id": self.client_id,
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(f"{self.base_url}/prompt", json=payload)
        except httpx.ConnectError as e:
            raise ImageGenError(f"ComfyUI connection failed: {e}")
        except httpx.TimeoutException as e:
            raise ImageGenError(f"ComfyUI request timed out: {e}")

        if resp.status_code != 200:
            raise ImageGenError(f"ComfyUI queue failed: {resp.status_code} {resp.text}")
        result = resp.json()
        prompt_id = result.get("prompt_id", "")

        async with httpx.AsyncClient(timeout=120.0) as client:
            while True:
                status_resp = await client.get(
                    f"{self.base_url}/history/{prompt_id}",
                )
                if status_resp.status_code == 200:
                    history = status_resp.json()
                    if prompt_id in history:
                        outputs = history[prompt_id].get("outputs", {})
                        for node_id, node_output in outputs.items():
                            for img_data in node_output.get("images", []):
                                filename = img_data.get("filename", "")
                                img_resp = await client.get(
                                    f"{self.base_url}/view",
                                    params={"filename": filename},
                                )
                                if img_resp.status_code == 200:
                                    return img_resp.content
                        raise ImageGenError("No image output found in ComfyUI result")
                import asyncio
                await asyncio.sleep(1.0)

    async def txt2img(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 28,
        guidance_scale: float = 3.5,
        seed: int | None = None,
    ) -> bytes:
        workflow = self._build_txt2img_workflow(
            prompt, negative_prompt, width, height, steps, guidance_scale, seed,
        )
        return await self._queue_workflow(workflow)

    async def upscale(self, image_data: bytes, scale: int = 4) -> bytes:
        workflow = self._build_upscale_workflow(image_data, scale)
        return await self._queue_workflow(workflow)

    async def remove_background(self, image_data: bytes) -> bytes:
        workflow = self._build_remove_bg_workflow(image_data)
        return await self._queue_workflow(workflow)

    def _build_txt2img_workflow(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 28,
        guidance_scale: float = 3.5,
        seed: int | None = None,
    ) -> dict[str, Any]:
        import random
        seed = seed if seed is not None else random.randint(0, 2**32 - 1)
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": guidance_scale,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": settings.comfyui_checkpoint}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["4", 1]},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt or settings.comfyui_default_negative, "clip": ["4", 1]},
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "syzygy_", "images": ["8", 0]},
            },
        }

    def _build_upscale_workflow(self, image_data: bytes, scale: int) -> dict[str, Any]:
        import hashlib
        img_hash = hashlib.md5(image_data).hexdigest()[:8]
        return {
            "1": {
                "class_type": "LoadImage",
                "inputs": {"image": f"syzygy_input_{img_hash}.png"},
            },
            "2": {
                "class_type": "ImageUpscaleWithModel",
                "inputs": {
                    "upscale_model": [ "3", 0 ],
                    "image": [ "1", 0 ],
                },
            },
            "3": {
                "class_type": "UpscaleModelLoader",
                "inputs": {"model_name": settings.comfyui_upscaler},
            },
            "4": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "syzygy_upscaled_", "images": ["2", 0]},
            },
        }

    def _build_remove_bg_workflow(self, image_data: bytes) -> dict[str, Any]:
        import hashlib
        img_hash = hashlib.md5(image_data).hexdigest()[:8]
        return {
            "1": {
                "class_type": "LoadImage",
                "inputs": {"image": f"syzygy_input_{img_hash}.png"},
            },
            "2": {
                "class_type": "ImageRemoveBackground",
                "inputs": {
                    "image": ["1", 0],
                    "model": settings.comfyui_rembg_model,
                },
            },
            "3": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "syzygy_nobg_", "images": ["2", 0]},
            },
        }


# ─── Replicate Provider (cloud fallback) ──────────────────────────

class ReplicateProvider(ImageGenProvider):
    """Cloud-based image generation via Replicate API.

    Uses Flux.1-schnell, SD3.5, or other models available on Replicate.
    Requires REPLICATE_API_TOKEN env var.
    """

    def __init__(self, api_token: str = "") -> None:
        self.api_token = api_token or settings.replicate_api_token

    async def _call_model(self, model: str, inputs: dict[str, Any]) -> bytes:
        if not self.api_token:
            raise ImageGenError("REPLICATE_API_TOKEN not configured")
        import httpx

        async with httpx.AsyncClient(timeout=300.0) as client:
            pred_resp = await client.post(
                "https://api.replicate.com/v1/predictions",
                headers={"Authorization": f"Bearer {self.api_token}"},
                json={"version": model, "input": inputs},
            )
            if pred_resp.status_code != 201:
                raise ImageGenError(f"Replicate prediction failed: {pred_resp.status_code}")
            prediction = pred_resp.json()
            url = prediction.get("urls", {}).get("get", "")

            while prediction.get("status") not in ("succeeded", "failed", "canceled"):
                import asyncio
                await asyncio.sleep(1.0)
                status_resp = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )
                if status_resp.status_code != 200:
                    break
                prediction = status_resp.json()

            if prediction.get("status") != "succeeded":
                raise ImageGenError(f"Replicate prediction failed: {prediction.get('error', 'unknown')}")

            output_url = prediction.get("output")
            if isinstance(output_url, list):
                output_url = output_url[0]
            if not output_url:
                raise ImageGenError("No output URL in Replicate response")

            img_resp = await client.get(output_url)
            if img_resp.status_code != 200:
                raise ImageGenError("Failed to download generated image")
            return img_resp.content

    async def txt2img(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 28,
        guidance_scale: float = 3.5,
        seed: int | None = None,
    ) -> bytes:
        import random
        return await self._call_model(settings.replicate_txt2img_model, {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "num_inference_steps": steps,
            "guidance_scale": guidance_scale,
            "seed": seed if seed is not None else random.randint(0, 2**32 - 1),
        })

    async def upscale(self, image_data: bytes, scale: int = 4) -> bytes:
        from app.services.file_store import save_temp_file
        img_url = await save_temp_file(image_data, suffix=".png")
        return await self._call_model(settings.replicate_upscaler_model, {
            "image": img_url,
            "scale": scale,
        })

    async def remove_background(self, image_data: bytes) -> bytes:
        from app.services.file_store import save_temp_file
        img_url = await save_temp_file(image_data, suffix=".png")
        return await self._call_model(settings.replicate_rembg_model, {
            "image": img_url,
        })


# ─── Mock Provider (for testing) ───────────────────────────────────

class MockImageGenProvider(ImageGenProvider):
    """Returns synthetic image data for testing."""

    def __init__(self, width: int = 64, height: int = 64) -> None:
        self.width = width
        self.height = height

    async def txt2img(
        self,
        prompt: str = "",
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 28,
        guidance_scale: float = 3.5,
        seed: int | None = None,
    ) -> bytes:
        return self._make_png(width, height)

    async def upscale(self, image_data: bytes, scale: int = 4) -> bytes:
        return self._make_png(self.width * scale, self.height * scale)

    async def remove_background(self, image_data: bytes) -> bytes:
        return self._make_png(self.width, self.height)

    def _make_png(self, w: int, h: int) -> bytes:
        try:
            from PIL import Image
        except ImportError:
            return b"PNG_MOCK_IMAGE_DATA"
        img = Image.new("RGB", (w, h), color=(127, 127, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


# ─── Factory ───────────────────────────────────────────────────────

def create_image_gen_provider(provider: str = "") -> ImageGenProvider:
    """Factory to create the appropriate image generation provider.

    Args:
        provider: "comfyui", "replicate", or "mock". Defaults to settings.
    """
    provider = provider or settings.image_gen_provider
    if provider == "comfyui":
        return ComfyUIProvider()
    elif provider == "replicate":
        return ReplicateProvider()
    elif provider == "mock":
        return MockImageGenProvider()
    else:
        logger.warning(f"Unknown image_gen_provider '{provider}', falling back to mock")
        return MockImageGenProvider()


# ─── Prompt Enhancement ────────────────────────────────────────────

async def enhance_prompt(raw_prompt: str, model_manager: Any = None) -> str:
    """Enhance a user prompt to match Midjourney/Grok-level quality.

    Uses the LLM to add detail, lighting, composition, and style keywords.
    Falls back to raw prompt if LLM unavailable.
    """
    try:
        from app.llm.model_manager import ModelManager
        llm = model_manager or ModelManager()

        system = (
            "You are a professional prompt engineer for SOTA image generation models "
            "(Flux, SD3.5, Midjourney). Given a user's raw concept, expand it into a "
            "detailed, visually-rich prompt that produces stunning results.\n\n"
            "Guidelines:\n"
            "- Add lighting (e.g., cinematic lighting, golden hour, volumetric)\n"
            "- Add camera details (e.g., shot on IMAX, 85mm lens, shallow DOF)\n"
            "- Add mood/atmosphere (e.g., ethereal, dramatic, serene)\n"
            "- Add style keywords (e.g., photorealistic, oil painting, concept art)\n"
            "- Add color palette hints (e.g., vibrant teal and orange, monochromatic)\n"
            "- Keep it to 1-3 sentences maximum\n"
            "- Do NOT use markdown or quotes — just return the enhanced prompt text"
        )

        enhanced = await llm.generate(
            f"Enhance this image prompt to maximize visual quality:\n\n{raw_prompt}",
            system=system,
            temperature=0.7,
        )
        enhanced = enhanced.strip().strip('"').strip("'")
        logger.info("Prompt enhanced", original=raw_prompt[:80], enhanced=enhanced[:120])
        return enhanced
    except Exception as e:
        logger.warning("Prompt enhancement failed, using raw prompt", error=str(e))
        return raw_prompt


# ─── Temp file store helper ────────────────────────────────────────

async def save_temp_file(data: bytes, suffix: str = ".png") -> str:
    """Save bytes to a temp file and return its URL/path.

    This is a minimal helper; the Replicate provider uses it to upload
    images for upscaling/rembg. In production, images are stored via
    the upload system.
    """
    path = Path(settings.upload_dir) / ".image_gen_temp"
    path.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    filepath = path / filename
    filepath.write_bytes(data)
    return f"/uploads/{filepath.name}"
