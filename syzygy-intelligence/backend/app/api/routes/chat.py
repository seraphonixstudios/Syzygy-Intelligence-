"""Chat API routes — natural language interface with multi-model support."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from app.consensus.engine import ConsensusEngine
from app.agents.registry import agent_registry
from app.errors import LLMConnectionError
from app.llm.model_manager import ModelManager
from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger

router = APIRouter()
llm = OllamaClient()
model_manager = ModelManager()
engine = ConsensusEngine()


@router.post("/completions")
async def chat_completion(data: dict):
    message = data.get("message", "")
    model = data.get("model", "")

    try:
        # Route "syzygy" model through the consensus engine
        if model == "syzygy" or data.get("use_consensus", False):
            CONSENSUS_TIMEOUT = 300.0
            try:
                session = await asyncio.wait_for(
                    engine.run_consensus(
                        task=message,
                        max_rounds=data.get("consensus_rounds", 2),
                    ),
                    timeout=CONSENSUS_TIMEOUT,
                )
                return {
                    "response": session.final_synthesis,
                    "session_id": session.id,
                    "rounds": session.current_round,
                    "fusion_report": session.polarity_fusion_report,
                }
            except asyncio.TimeoutError:
                logger.error("Consensus timed out", timeout=CONSENSUS_TIMEOUT)
                raise HTTPException(
                    status_code=504,
                    detail={
                        "code": "CONSENSUS_TIMEOUT",
                        "message": f"Consensus engine took longer than {CONSENSUS_TIMEOUT}s. Try a simpler query or select a specific model.",
                    },
                )

        # Direct LLM response
        response = await llm.chat(
            messages=[{"role": "user", "content": message}],
            model=model or "",
        )
        return {"response": response}

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
async def chat_multi_model(data: dict):
    """Query multiple models in parallel and return all responses."""
    message = data.get("message", "")
    models = data.get("models", [])

    if not message:
        raise HTTPException(400, "Message is required")
    if not models:
        models = model_manager.get_all_model_names()

    logger.info("Multi-model chat requested", models=models)

    results = await model_manager.generate_multi_model(
        prompt=message,
        models=models,
    )
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
async def chat_stream(data: dict):
    return {"type": "stream", "status": "streaming_started"}
