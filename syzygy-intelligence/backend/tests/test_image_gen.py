"""Tests for image generation tool, workflow, and service."""

from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.image_gen import (
    ComfyUIProvider,
    ImageGenError,
    MockImageGenProvider,
    ReplicateProvider,
    create_image_gen_provider,
    enhance_prompt,
)
from app.tools.image_gen_tool import ImageGenTool
from app.workflows.image_gen import ImageGenWorkflow


# ─── Provider Tests ────────────────────────────────────────────────

class TestMockImageGenProvider:
    @pytest.mark.asyncio
    async def test_txt2img_returns_bytes(self):
        provider = MockImageGenProvider()
        result = await provider.txt2img(prompt="a cat")
        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_txt2img_respects_dimensions(self):
        provider = MockImageGenProvider(width=32, height=32)
        result = await provider.txt2img(prompt="test", width=32, height=32)
        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_upscale_returns_larger(self):
        provider = MockImageGenProvider(width=64, height=64)
        original = await provider.txt2img(prompt="test", width=64, height=64)
        upscaled = await provider.upscale(original, scale=4)
        assert isinstance(upscaled, bytes)
        assert len(upscaled) > 0

    @pytest.mark.asyncio
    async def test_remove_background_returns_bytes(self):
        provider = MockImageGenProvider()
        img = await provider.txt2img(prompt="test")
        result = await provider.remove_background(img)
        assert isinstance(result, bytes)


class TestComfyUIProvider:
    @pytest.mark.asyncio
    async def test_txt2img_raises_on_connection_error(self):
        provider = ComfyUIProvider(base_url="http://localhost:1")
        with pytest.raises(ImageGenError):
            await provider.txt2img(prompt="test", width=64, height=64)

    def test_build_workflow_creates_valid_structure(self):
        provider = ComfyUIProvider()
        workflow = provider._build_txt2img_workflow("test cat", width=512, height=512)
        assert "3" in workflow
        assert workflow["3"]["class_type"] == "KSampler"
        assert workflow["6"]["inputs"]["text"] == "test cat"
        assert workflow["5"]["inputs"]["width"] == 512


class TestReplicateProvider:
    @pytest.mark.asyncio
    async def test_txt2img_raises_without_token(self):
        provider = ReplicateProvider(api_token="")
        with pytest.raises(ImageGenError, match="REPLICATE_API_TOKEN not configured"):
            await provider.txt2img(prompt="test")


class TestCreateProvider:
    def test_creates_mock_by_default(self):
        with patch("app.services.image_gen.settings") as mock_settings:
            mock_settings.image_gen_provider = ""
            provider = create_image_gen_provider("")
            assert isinstance(provider, MockImageGenProvider)

    def test_creates_comfyui(self):
        provider = create_image_gen_provider("comfyui")
        assert isinstance(provider, ComfyUIProvider)

    def test_creates_replicate(self):
        provider = create_image_gen_provider("replicate")
        assert isinstance(provider, ReplicateProvider)

    def test_creates_mock(self):
        provider = create_image_gen_provider("mock")
        assert isinstance(provider, MockImageGenProvider)

    def test_unknown_falls_back_to_mock(self):
        provider = create_image_gen_provider("nonexistent")
        assert isinstance(provider, MockImageGenProvider)


# ─── Prompt Enhancement Tests ──────────────────────────────────────

@pytest.mark.asyncio
async def test_enhance_prompt_returns_enhanced_text():
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="A majestic cat with glowing eyes, cinematic lighting")
    result = await enhance_prompt("a cat", mock_llm)
    assert "cat" in result
    assert len(result) > len("a cat")


@pytest.mark.asyncio
async def test_enhance_prompt_fallback_on_error():
    with patch("app.llm.model_manager.ModelManager.generate", side_effect=Exception("LLM fail")):
        result = await enhance_prompt("a dog")
        assert result == "a dog"


# ─── ImageGenTool Tests ────────────────────────────────────────────

class TestImageGenTool:
    @pytest.mark.asyncio
    async def test_txt2img_returns_base64_image(self):
        tool = ImageGenTool()
        result = await tool.execute(action="txt2img", prompt="test cat", enhance=False)
        assert "image" in result
        assert result["format"] == "png"
        # Verify valid base64
        decoded = base64.b64decode(result["image"])
        assert len(decoded) > 0

    @pytest.mark.asyncio
    async def test_txt2img_requires_prompt(self):
        tool = ImageGenTool()
        result = await tool.execute(action="txt2img", prompt="")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_upscale_requires_image_data(self):
        tool = ImageGenTool()
        result = await tool.execute(action="upscale")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_upscale_with_data(self):
        tool = ImageGenTool()
        dummy_img = base64.b64encode(b"MOCK_PNG_DATA").decode()
        result = await tool.execute(action="upscale", image_data=dummy_img)
        assert "image" in result

    @pytest.mark.asyncio
    async def test_remove_background_requires_data(self):
        tool = ImageGenTool()
        result = await tool.execute(action="remove_background")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_unknown_action(self):
        tool = ImageGenTool()
        result = await tool.execute(action="invalid_action")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_txt2img_with_enhance(self):
        tool = ImageGenTool()
        with patch("app.tools.image_gen_tool.enhance_prompt", new=AsyncMock(return_value="enhanced cat")):
            result = await tool.execute(action="txt2img", prompt="cat", enhance=True)
            assert "image" in result


# ─── ImageGenWorkflow Tests ────────────────────────────────────────

class TestImageGenWorkflow:
    @pytest.mark.asyncio
    async def test_analyze_concept_returns_params(self):
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value='{"subject":"cat","style":"photorealistic","mood":"calm"}')
        workflow = ImageGenWorkflow(llm=mock_llm)
        result = await workflow.analyze_concept("a calm cat")
        assert result["subject"] == "cat"
        assert result["style"] == "photorealistic"

    @pytest.mark.asyncio
    async def test_analyze_concept_fallback_on_bad_json(self):
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value="not json")
        workflow = ImageGenWorkflow(llm=mock_llm)
        result = await workflow.analyze_concept("test")
        assert "subject" in result

    @pytest.mark.asyncio
    async def test_generate_returns_image(self):
        workflow = ImageGenWorkflow(llm=MagicMock())
        result = await workflow.generate("test cat", {"aspect_ratio": "square"})
        assert "image" in result
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_refine_returns_image(self):
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value="refined cat prompt")
        workflow = ImageGenWorkflow(llm=mock_llm)
        previous = {"prompt": "original cat", "aspect_ratio": "square"}
        result = await workflow.refine(previous, "more detail")
        assert "image" in result
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_full_flow(self):
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value='{"subject":"cat","style":"photorealistic"}')
        workflow = ImageGenWorkflow(llm=mock_llm)
        result = await workflow.execute("a cat")
        assert result["status"] == "completed"
        assert "concept_analysis" in result
        assert "result" in result

    @pytest.mark.asyncio
    async def test_execute_with_feedback_rounds(self):
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value='{"subject":"cat"}')
        workflow = ImageGenWorkflow(llm=mock_llm)
        result = await workflow.execute("a cat", {"feedback_rounds": 1, "feedback_0": "more color"})
        assert result["status"] == "completed"


# ─── Tool Registry Integration Test ────────────────────────────────

class TestToolRegistryIntegration:
    @pytest.mark.asyncio
    async def test_image_gen_registered(self):
        from app.tools import tool_registry
        tool = tool_registry.get("image_gen")
        assert tool is not None
        assert tool.name == "image_gen"

    @pytest.mark.asyncio
    async def test_image_gen_listed(self):
        from app.tools import tool_registry
        tools = tool_registry.list()
        ids = [t["id"] for t in tools]
        assert "image_gen" in ids


# ─── Workflow Registry Integration Test ────────────────────────────

class TestWorkflowRegistryIntegration:
    def test_image_gen_workflow_registered(self):
        from app.workflows import get_workflow
        wf = get_workflow("image_gen")
        assert wf is not None
        assert wf.name == "image_gen"
