"""Chat API routes — natural language interface with multi-model support."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import check_usage_limit, get_current_user
from app.consensus.engine import ConsensusEngine
from app.db.models import User
from app.db.session import get_db
from app.errors import LLMConnectionError
from app.llm.model_manager import ModelManager
from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger
from app.rag.injector import build_rag_context


# Request validation models
class ChatCompletionRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    model: str = Field(default="", description="Target model name")
    use_rag: bool = Field(default=False, description="Inject RAG context")
    use_consensus: bool = Field(default=False, description="Use consensus engine")
    consensus_rounds: int = Field(default=2, ge=1, le=20, description="Max consensus rounds")


class ChatMultiModelRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    models: list[str] = Field(default_factory=list, description="Model names to query")


class ChatStreamRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    model: str = Field(default="", description="Target model name")
    use_rag: bool = Field(default=False, description="Inject RAG context")


router = APIRouter()
llm = OllamaClient()
model_manager = ModelManager()
engine = ConsensusEngine()


async def _track_usage(user: User | None, db: AsyncSession):
    if user is not None:
        user.message_count += 1
        db.add(user)
        await db.commit()


@router.post("/completions")
async def chat_completion(
    request: ChatCompletionRequest,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Chat completion with optional RAG and consensus."""
    message = request.message
    model = request.model
    use_rag = request.use_rag

    if user is not None:
        await check_usage_limit(user, db)

    try:
        # Optionally inject RAG context
        rag_context = ""
        if use_rag:
            rag_context = await build_rag_context(message)

        # Route "syzygy" model through the consensus engine
        if model == "syzygy" or request.use_consensus:
            CONSENSUS_TIMEOUT = 600.0
            try:
                augmented_task = message
                if rag_context:
                    augmented_task = f"{rag_context}\n\nUser question: {message}"
                session = await asyncio.wait_for(
                    engine.run_consensus(
                        task=augmented_task,
                        max_rounds=request.consensus_rounds,
                    ),
                    timeout=CONSENSUS_TIMEOUT,
                )
                await _track_usage(user, db)
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
                        "message": f"Consensus engine took longer than {CONSENSUS_TIMEOUT}s. Try a simpler query or select a specific model.",
                    },
                )

        # Direct LLM response with optional RAG context
        messages = []
        if rag_context:
            messages.append({"role": "system", "content": rag_context})
        messages.append({"role": "user", "content": message})

        response = await llm.chat(
            messages=messages,
            model=model or "",
        )
        await _track_usage(user, db)
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
):
    """Query multiple models in parallel and return all responses."""
    message = request.message
    models = request.models

    if not models:
        models = model_manager.get_all_model_names()

    if user is not None:
        await check_usage_limit(user, db)

    logger.info("Multi-model chat requested", models=models)

    results = await model_manager.generate_multi_model(
        prompt=message,
        models=models,
    )
    if user is not None:
        await _track_usage(user, db)
    return {"responses": results}


@router.get("/models")
async def list_configured_models():
    """Return all configured model names and their roles."""
    roles = {}
    for role in ModelManager.MODEL_ROLES:
        roles[role] = model_manager.get_model_for_role(role)

    available = await model_manager.list_available_models()
    available_names = [m.get("name") for m in available]

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
):
    """SSE streaming chat completion with optional RAG context injection."""
    message = request.message
    model = request.model
    use_rag = request.use_rag

    if user is not None:
        await check_usage_limit(user, db)
        await _track_usage(user, db)

    async def event_generator():
        try:
            full_response = ""
            rag_context = ""

            if use_rag:
                rag_context = await build_rag_context(message)
                if rag_context:
                    yield f"data: {json.dumps({'rag_context': True})}\n\n"

            augmented_prompt = message
            if rag_context:
                augmented_prompt = f"{rag_context}\n\nUser question: {message}"

            async for token in llm.generate_stream(
                prompt=augmented_prompt,
                model=model or llm.default_model,
            ):
                full_response += token
                yield f"data: {json.dumps({'token': token})}\n\n"

            yield f"data: {json.dumps({'done': True, 'full': full_response, 'rag_context_used': bool(rag_context)})}\n\n"
        except LLMConnectionError as e:
            yield f"data: {json.dumps({'error': e.message})}\n\n"
        except Exception as e:
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
