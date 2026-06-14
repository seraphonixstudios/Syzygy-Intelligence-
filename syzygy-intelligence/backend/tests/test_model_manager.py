"""Tests for ModelManager — provider routing, model selection, fallback."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _patch_settings():
    """Pin settings values so tests are deterministic."""
    import app.config as cfg

    originals = {}
    overrides = {
        "default_llm_provider": "ollama",
        "openai_compat_enabled": True,
        "litellm_enabled": True,
        "default_model": "qwen3:8b-gpu",
        "critic_model": "critic-model",
        "synthesis_model": "synthesis-model",
        "coding_model": "coding-model",
        "creative_model": "creative-model",
        "vision_model": "vision-model",
        "gpu_model": "gpu-model",
        "fast_model": "fast-model",
    }
    for key, val in overrides.items():
        originals[key] = getattr(cfg.settings, key, None)
        setattr(cfg.settings, key, val)
    yield originals
    for key, val in originals.items():
        if val is None:
            if hasattr(cfg.settings, key):
                delattr(cfg.settings, key)
        else:
            setattr(cfg.settings, key, val)


@pytest.fixture
def mock_providers():
    """Create ModelManager with all three providers mocked."""
    import app.config as cfg

    # Ensure settings are patched for this fixture
    cfg.settings.coding_model = "coding-model"
    cfg.settings.critic_model = "critic-model"
    cfg.settings.creative_model = "creative-model"
    cfg.settings.vision_model = "vision-model"
    cfg.settings.fast_model = "fast-model"
    cfg.settings.synthesis_model = "synthesis-model"
    cfg.settings.gpu_model = "gpu-model"
    cfg.settings.default_model = "qwen3:8b-gpu"
    cfg.settings.default_llm_provider = "ollama"
    cfg.settings.litellm_enabled = True
    cfg.settings.openai_compat_enabled = True
    with (
        patch("app.llm.model_manager.OllamaClient") as mock_ollama_cls,
        patch("app.llm.model_manager.LiteLLMClient") as mock_litellm_cls,
        patch("app.llm.model_manager.OpenAICompatClient") as mock_openai_cls,
    ):
        mock_ollama = MagicMock()
        mock_litellm = MagicMock()
        mock_openai = MagicMock()
        mock_ollama_cls.return_value = mock_ollama
        mock_litellm_cls.return_value = mock_litellm
        mock_openai_cls.return_value = mock_openai

        from app.llm.model_manager import ModelManager

        mm = ModelManager()
        yield mm, mock_ollama, mock_litellm, mock_openai


class TestInit:
    """ModelManager construction."""

    def test_creates_providers(self):
        with (
            patch("app.llm.model_manager.OllamaClient") as mock_ollama_cls,
            patch("app.llm.model_manager.LiteLLMClient") as mock_litellm_cls,
            patch("app.llm.model_manager.OpenAICompatClient") as mock_openai_cls,
        ):
            from app.llm.model_manager import ModelManager

            mm = ModelManager()
            mock_ollama_cls.assert_called_once()
            mock_litellm_cls.assert_called_once()
            mock_openai_cls.assert_called_once()
            assert "ollama" in mm._providers
            assert "litellm" in mm._providers
            assert "openai_compat" in mm._providers

    def test_openai_compat_disabled(self):
        import app.config as cfg
        cfg.settings.openai_compat_enabled = False
        with (
            patch("app.llm.model_manager.OllamaClient"),
            patch("app.llm.model_manager.LiteLLMClient"),
            patch("app.llm.model_manager.OpenAICompatClient"),
        ):
            from app.llm.model_manager import ModelManager

            mm = ModelManager()
            assert "openai_compat" not in mm._providers


class TestGetProvider:
    """ModelManager.get_provider."""

    def test_returns_by_name(self, mock_providers):
        mm, _, _, mock_openai = mock_providers
        assert mm.get_provider("openai_compat") is mock_openai

    def test_returns_default_when_none(self, mock_providers):
        mm, mock_ollama, _, _ = mock_providers
        assert mm.get_provider() is mock_ollama

    def test_unknown_provider_falls_back_to_ollama(self, mock_providers):
        mm, mock_ollama, _, _ = mock_providers
        assert mm.get_provider("nonexistent") is mock_ollama


class TestGetModelForRole:
    """ModelManager.get_model_for_role."""

    def test_returns_default_model(self, mock_providers):
        mm = mock_providers[0]
        assert mm.get_model_for_role("default") == "qwen3:8b-gpu"

    def test_returns_critic_model(self, mock_providers):
        mm = mock_providers[0]
        assert mm.get_model_for_role("critic") == "critic-model"

    def test_unknown_role_falls_to_default(self, mock_providers):
        mm = mock_providers[0]
        assert mm.get_model_for_role("unknown_role") == "qwen3:8b-gpu"


class TestGetModelForTask:
    """ModelManager.get_model_for_task."""

    def test_vision_task(self, mock_providers):
        mm = mock_providers[0]
        assert mm.get_model_for_task("analyze image") == "vision-model"

    def test_coding_task(self, mock_providers):
        mm = mock_providers[0]
        assert mm.get_model_for_task("write some code") == "coding-model"

    def test_reasoning_task(self, mock_providers):
        mm = mock_providers[0]
        assert mm.get_model_for_task("reason about") == "critic-model"

    def test_fast_task(self, mock_providers):
        mm = mock_providers[0]
        assert mm.get_model_for_task("quick summary") == "fast-model"

    def test_unmatched_task_falls_to_default(self, mock_providers):
        mm = mock_providers[0]
        assert mm.get_model_for_task("hello world") == "qwen3:8b-gpu"


class TestGetModelsForTask:
    """ModelManager.get_models_for_task."""

    def test_single_match(self, mock_providers):
        mm = mock_providers[0]
        models = mm.get_models_for_task("code review")
        assert "coding-model" in models
        assert len(models) == 1

    def test_multiple_matches_dedup(self, mock_providers):
        mm = mock_providers[0]
        models = mm.get_models_for_task("analyze and code")
        assert "critic-model" in models
        assert "coding-model" in models

    def test_no_match_returns_default(self, mock_providers):
        mm = mock_providers[0]
        assert mm.get_models_for_task("random text") == ["qwen3:8b-gpu"]


class TestGetAllModelNames:
    """ModelManager.get_all_model_names."""

    def test_returns_unique_models(self, mock_providers):
        mm = mock_providers[0]
        names = mm.get_all_model_names()
        assert "qwen3:8b-gpu" in names
        assert "coding-model" in names
        assert "critic-model" in names
        assert len(names) == len(set(names))


class TestGetAllProviders:
    """ModelManager.get_all_providers."""

    def test_returns_provider_dict(self, mock_providers):
        mm = mock_providers[0]
        providers = mm.get_all_providers()
        assert "ollama" in providers
        assert "litellm" in providers
        assert "openai_compat" in providers


class TestGenerate:
    """ModelManager.generate."""

    @pytest.mark.asyncio
    async def test_generate_with_model(self, mock_providers):
        mm, mock_ollama, _, _ = mock_providers
        mock_ollama.generate = AsyncMock(return_value="response")
        result = await mm.generate(prompt="hello", model="test-model")
        assert result == "response"
        mock_ollama.generate.assert_called_once_with(
            prompt="hello", system="", model="test-model",
            temperature=0.7, max_tokens=2048,
        )

    @pytest.mark.asyncio
    async def test_generate_resolves_via_task_hint(self, mock_providers):
        mm, mock_ollama, _, _ = mock_providers
        mock_ollama.generate = AsyncMock(return_value="resp")
        await mm.generate(prompt="write poetry", task_hint="creative")
        _, kwargs = mock_ollama.generate.call_args
        assert kwargs["model"] == "creative-model"

    @pytest.mark.asyncio
    async def test_generate_resolves_via_role(self, mock_providers):
        mm, mock_ollama, _, _ = mock_providers
        mock_ollama.generate = AsyncMock(return_value="resp")
        await mm.generate(prompt="test", role="coding")
        _, kwargs = mock_ollama.generate.call_args
        assert kwargs["model"] == "coding-model"

    @pytest.mark.asyncio
    async def test_generate_with_specific_provider(self, mock_providers):
        mm, _, _, mock_openai = mock_providers
        mock_openai.generate = AsyncMock(return_value="resp")
        await mm.generate(prompt="hello", model="m", provider="openai_compat")
        mock_openai.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_fallback_on_llm_error(self, mock_providers):
        import app.config as cfg
        cfg.settings.litellm_enabled = True
        mm, mock_ollama, mock_litellm, _ = mock_providers
        from app.errors import LLMConnectionError

        mock_ollama.generate = AsyncMock(side_effect=LLMConnectionError(model="m"))
        mock_litellm.generate = AsyncMock(return_value="fallback response")

        result = await mm.generate(prompt="hello", model="m")
        assert result == "fallback response"

    @pytest.mark.asyncio
    async def test_generate_no_fallback_when_provider_specified(self, mock_providers):
        mm, mock_ollama, _, _ = mock_providers
        from app.errors import LLMConnectionError

        mock_ollama.generate = AsyncMock(side_effect=LLMConnectionError(model="m"))
        with pytest.raises(LLMConnectionError):
            await mm.generate(prompt="hello", model="m", provider="ollama")

    @pytest.mark.asyncio
    async def test_generate_no_fallback_when_litellm_disabled(self, mock_providers):
        import app.config as cfg
        cfg.settings.litellm_enabled = False
        mm, mock_ollama, _, _ = mock_providers
        from app.errors import LLMConnectionError

        mock_ollama.generate = AsyncMock(side_effect=LLMConnectionError(model="m"))
        with pytest.raises(LLMConnectionError):
            await mm.generate(prompt="hello", model="m")


class TestChat:
    """ModelManager.chat."""

    @pytest.mark.asyncio
    async def test_chat_delegates_to_provider(self, mock_providers):
        mm, mock_ollama, _, _ = mock_providers
        mock_ollama.chat = AsyncMock(return_value="chat response")
        result = await mm.chat(messages=[{"role": "user", "content": "hi"}])
        assert result == "chat response"
        mock_ollama.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_role_model(self, mock_providers):
        mm, mock_ollama, _, _ = mock_providers
        mock_ollama.chat = AsyncMock(return_value="resp")
        await mm.chat(messages=[{"role": "user", "content": "hi"}], role="critic")
        _, kwargs = mock_ollama.chat.call_args
        assert kwargs["model"] == "critic-model"

    @pytest.mark.asyncio
    async def test_chat_with_provider(self, mock_providers):
        mm, _, _, mock_openai = mock_providers
        mock_openai.chat = AsyncMock(return_value="resp")
        await mm.chat(messages=[{"role": "user", "content": "hi"}], provider="openai_compat")
        mock_openai.chat.assert_called_once()


class TestGenerateStream:
    """ModelManager.generate_stream."""

    @pytest.mark.asyncio
    async def test_generate_stream_yields_chunks(self, mock_providers):
        mm, mock_ollama, _, _ = mock_providers

        async def mock_stream(*_a, **_kw):
            for t in ["a", "b", "c"]:
                yield t

        mock_ollama.generate_stream = mock_stream
        chunks = []
        async for chunk in mm.generate_stream(prompt="test", role="default"):
            chunks.append(chunk)
        assert chunks == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_generate_stream_with_role(self, mock_providers):
        mm, mock_ollama, _, _ = mock_providers

        async def mock_stream(*_a, **_kw):
            yield "ok"
            yield _kw.get("model")

        mock_ollama.generate_stream = mock_stream
        chunks = []
        async for chunk in mm.generate_stream(prompt="test", role="fast"):
            chunks.append(chunk)
        assert "fast-model" in chunks

    @pytest.mark.asyncio
    async def test_generate_stream_with_provider(self, mock_providers):
        mm, _, _, mock_openai = mock_providers

        async def mock_stream(*_a, **_kw):
            yield "ok"

        mock_openai.generate_stream = mock_stream
        chunks = []
        async for chunk in mm.generate_stream(prompt="test", provider="openai_compat"):
            chunks.append(chunk)
        assert chunks == ["ok"]


class TestGenerateMultiModel:
    """ModelManager.generate_multi_model."""

    @pytest.mark.asyncio
    async def test_delegates_to_ollama(self, mock_providers):
        mm, mock_ollama, _, _ = mock_providers
        mock_ollama.generate_multi = AsyncMock(return_value={"m1": "resp1"})
        result = await mm.generate_multi_model(
            prompt="test", models=["m1", "m2"], system="sys", temperature=0.5, max_tokens=100,
        )
        assert result == {"m1": "resp1"}
        mock_ollama.generate_multi.assert_called_once_with(
            prompt="test", models=["m1", "m2"], system="sys", temperature=0.5, max_tokens=100,
        )


class TestListAvailableModels:
    """ModelManager.list_available_models."""

    @pytest.mark.asyncio
    async def test_aggregates_across_providers(self, mock_providers):
        mm, mock_ollama, mock_litellm, mock_openai = mock_providers
        mock_ollama.list_models = AsyncMock(return_value=[{"name": "ollama-model"}])
        mock_litellm.list_models = AsyncMock(return_value=[{"name": "litellm-model"}])
        mock_openai.list_models = AsyncMock(return_value=[{"name": "openai-model"}])

        models = await mm.list_available_models()
        names = [m["name"] for m in models]
        assert "ollama-model" in names
        assert "litellm-model" in names
        assert "openai-model" in names
        # Each model dict gets provider tag
        assert any(m["provider"] == "ollama" for m in models)

    @pytest.mark.asyncio
    async def test_handles_provider_exception_gracefully(self, mock_providers):
        mm, mock_ollama, mock_litellm, mock_openai = mock_providers
        mock_ollama.list_models = AsyncMock(side_effect=RuntimeError("Ollama down"))
        mock_litellm.list_models = AsyncMock(return_value=[{"name": "l-model"}])
        mock_openai.list_models = AsyncMock(return_value=[{"name": "o-model"}])

        models = await mm.list_available_models()
        names = [m["name"] for m in models]
        assert "ollama-model" not in names  # skipped
        assert "l-model" in names
        assert "o-model" in names

    @pytest.mark.asyncio
    async def test_all_providers_fail_returns_empty(self, mock_providers):
        mm, mock_ollama, mock_litellm, mock_openai = mock_providers
        mock_ollama.list_models = AsyncMock(side_effect=RuntimeError("down"))
        mock_litellm.list_models = AsyncMock(side_effect=RuntimeError("down"))
        mock_openai.list_models = AsyncMock(side_effect=RuntimeError("down"))

        models = await mm.list_available_models()
        assert models == []


class TestIsModelAvailable:
    """ModelManager.is_model_available."""

    @pytest.mark.asyncio
    async def test_model_is_available(self, mock_providers):
        mm, mock_ollama, _, _ = mock_providers
        mock_ollama.list_models = AsyncMock(return_value=[{"name": "qwen3:8b-gpu"}])

        assert await mm.is_model_available("qwen3:8b-gpu") is True

    @pytest.mark.asyncio
    async def test_model_not_available(self, mock_providers):
        mm, mock_ollama, _, _ = mock_providers
        mock_ollama.list_models = AsyncMock(return_value=[{"name": "other-model"}])

        assert await mm.is_model_available("missing-model") is False
