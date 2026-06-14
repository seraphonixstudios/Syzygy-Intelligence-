"""Chat API routes — natural language interface with multi-model support."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import check_usage_limit, get_current_user
from app.consensus.engine import ConsensusEngine
from app.db.models import User
from app.db.session import get_db
from app.errors import LLMConnectionError, ValidationError
from app.llm.model_manager import ModelManager
from app.logging_setup import logger
from app.rag.injector import build_rag_context
from app.config import settings


# Request validation models
class ChatCompletionRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    model: str = Field(default="", description="Target model name")
    use_rag: bool = Field(default=False, description="Inject RAG context")
    use_consensus: bool = Field(default=False, description="Use consensus engine")
    consensus_rounds: int = Field(default=2, ge=1, le=20, description="Max consensus rounds")
    provider: str = Field(default="", description="LLM provider to use")


class ChatMultiModelRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    models: list[str] = Field(default_factory=list, description="Model names to query")


class ChatStreamRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    model: str = Field(default="", description="Target model name")
    use_rag: bool = Field(default=False, description="Inject RAG context")
    provider: str = Field(default="", description="LLM provider to use")


router = APIRouter()
model_manager = ModelManager()
engine = ConsensusEngine()


def _sanitize_rag_context(rag_context: str) -> str:
    """Sanitize RAG context to prevent prompt injection."""
    # Use explicit delimiters to prevent injection
    return f"[RAG_CONTEXT_START]\n{rag_context}\n[RAG_CONTEXT_END]"


def _build_augmented_prompt(rag_context: str, user_message: str) -> str:
    """Build augmented prompt with clear separation between RAG and user input."""
    if rag_context:
        return f"{_sanitize_rag_context(rag_context)}\n\n[USER_MESSAGE]\n{user_message}\n[END_USER_MESSAGE]"
    return user_message


async def _track_usage(user: User | None, db: AsyncSession) -> None:
    """Track message usage for the current user."""
    if user is not None:
        user.message_count += 1  # type: ignore
        db.add(user)
        await db.commit()


@router.post("/completions")
async def chat_completion(
    request: ChatCompletionRequest,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Chat completion with optional RAG and consensus."""
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await check_usage_limit(user, db)
    await _track_usage(user, db)

    message = request.message
    model = request.model
    use_rag = request.use_rag

    try:
        # Optionally inject RAG context
        rag_context = ""
        if use_rag:
            rag_context = await build_rag_context(message)

        # Route "syzygy" model through the consensus engine
        if model == "syzygy" or request.use_consensus:
            CONSENSUS_TIMEOUT = settings.consensus_timeout if hasattr(settings, 'consensus_timeout') else 600.0
            try:
                augmented_task = _build_augmented_prompt(rag_context, message)
                session = await asyncio.wait_for(
                    engine.run_consensus(
                        task=augmented_task,
                        max_rounds=request.consensus_rounds,
                    ),
                    timeout=CONSENSUS_TIMEOUT,
                )
                return {
                    "response": session.final_synthesis,
                    "session_id": session.id,
                    "rounds": session.current_round,
                    "fusion_report": session.polarity_fusion_report,
                    "rag_context_used": bool(rag_context),
                }
            except TimeoutError:
                logger.error("Consensus timed out", timeout=CONSENSUS_TIMEOUT)
                raise HTTPException(
                    status_code=504,
                    detail={
                        "code": "CONSENSUS_TIMEOUT",
                        "message": (
                            f"Consensus engine took longer than {CONSENSUS_TIMEOUT}s. "
                            "Try a simpler query or select a specific model."
                        ),
                    },
                )

        # Direct LLM response with optional RAG context
        messages = []
        if rag_context:
            messages.append({"role": "system", "content": _sanitize_rag_context(rag_context)})
        messages.append({"role": "user", "content": message})

        provider = getattr(request, "provider", "") or None
        response = await model_manager.chat(
            messages=messages,
            model=model or "",
            provider=provider,
        )
        return {"response": response, "rag_context_used": bool(rag_context)}

    except LLMConnectionError as e:
        logger.error("Chat completion failed", model=model, error=e.message)
        raise HTTPException(
            status_code=503,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        )


@router.post("/multi-model")
async def chat_multi_model(
    request: ChatMultiModelRequest,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Query multiple models in parallel and return all responses."""
    # Track usage BEFORE LLM calls
    if user is not None:
        await check_usage_limit(user, db)
        await _track_usage(user, db)

    try:
        message = request.message
        models = request.models

        if not models:
            models = model_manager.get_all_model_names()

        logger.info("Multi-model chat requested", models=models)

        # Add timeout to prevent indefinite blocking
        MULTI_MODEL_TIMEOUT = settings.multi_model_timeout if hasattr(settings, 'multi_model_timeout') else 120.0
        results = await asyncio.wait_for(
            model_manager.generate_multi_model(
                prompt=message,
                models=models,
            ),
            timeout=MULTI_MODEL_TIMEOUT,
        )
        return {"responses": results}
    except asyncio.TimeoutError:
        logger.error("Multi-model request timed out", models=request.models)
        raise HTTPException(
            status_code=504,
            detail="Multi-model request exceeded timeout. Some models may be slow.",
        )
    except Exception as e:
        logger.error("Multi-model chat failed", error=str(e), models=request.models)
        raise HTTPException(status_code=500, detail=f"Multi-model request failed: {str(e)[:200]}")


@router.get("/models")
async def list_configured_models() -> dict[str, Any]:
    """Return all configured model names and their roles."""
    roles = {}
    for role in ModelManager.MODEL_ROLES:
        roles[role] = model_manager.get_model_for_role(role)

    try:
        available = await model_manager.list_available_models()
        available_names = [m.get("name") for m in available]
    except Exception:
        logger.warning("Failed to list available models from Ollama — returning empty")
        available_names = []

    return {
        "configured": roles,
        "available": available_names,
        "all_models": model_manager.get_all_model_names(),
    }


@router.post("/stream")
async def chat_stream(
    request: ChatStreamRequest,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """SSE streaming chat completion with optional RAG context injection."""
    # Track usage BEFORE streaming starts
    if user is not None:
        await check_usage_limit(user, db)
        await _track_usage(user, db)

    message = request.message
    model = request.model
    use_rag = request.use_rag

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            full_response = ""
            rag_context = ""

            if use_rag:
                rag_context = await build_rag_context(message)
                if rag_context:
                    yield f"data: {json.dumps({'rag_context': True})}\n\n"

            augmented_prompt = _build_augmented_prompt(rag_context, message)

            try:
                provider = getattr(request, "provider", "") or None
                async for token in model_manager.generate_stream(
                    prompt=augmented_prompt,
                    model=model or model_manager.get_model_for_role("default"),
                    provider=provider,
                ):
                    full_response += token
                    yield f"data: {json.dumps({'token': token})}\n\n"
            except Exception as stream_error:
                logger.error("Stream generation error", error=str(stream_error))
                raise

            yield f"data: {json.dumps({'done': True, 'full': full_response, 'rag_context_used': bool(rag_context)})}"
            yield "\n\n"
        except LLMConnectionError as e:
            yield f"data: {json.dumps({'error': e.message})}\n\n"
        except Exception as e:
            logger.error("Event generator error", error=str(e))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
