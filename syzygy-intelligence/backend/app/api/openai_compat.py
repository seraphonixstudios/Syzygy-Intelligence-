"""Syzygy Intelligence — API for multi-agent consensus platform.

This module exposes an OpenAI-compatible API endpoint.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.consensus.engine import ConsensusEngine
from app.errors import LLMConnectionError
from app.llm.model_manager import ModelManager
from app.logging_setup import logger

router = APIRouter(prefix="/v1", tags=["OpenAI Compatible"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "syzygy-consensus"
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False
    syzygy_polarity_balance: float = 0.7
    syzygy_consensus_rounds: int = 4


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, Any]


@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest) -> dict[str, Any]:
    """OpenAI-compatible chat completions endpoint with Syzygy enhancements."""
    import time

    user_message = ""
    for msg in request.messages:
        if msg.role == "user":
            user_message = msg.content

    if not user_message:
        raise HTTPException(400, "No user message found")

    # Use consensus engine for syzygy model
    if "syzygy" in request.model.lower():
        try:
            engine = ConsensusEngine()
            session = await engine.run_consensus(
                task=user_message,
                max_rounds=request.syzygy_consensus_rounds,
            )
        except TimeoutError:
            raise HTTPException(504, detail={
                "code": "CONSENSUS_TIMEOUT",
                "message": "Consensus engine timed out",
            })
        except Exception as e:
            logger.error("Consensus engine failed", error=str(e))
            raise HTTPException(500, detail={
                "code": "CONSENSUS_ERROR",
                "message": "Consensus engine failed",
            })

        content = session.final_synthesis
        content += "\n\n---\n*Syzygy Polarity Fusion Report:*\n"
        content += f"Rounds completed: {session.current_round}\n"
        content += f"Polarity balance: {session.polarity_fusion_report.get('individuation_notes', '')}"
    else:
        try:
            mm = ModelManager()
            content = await mm.chat(
                messages=[m.model_dump() for m in request.messages],
                model=request.model,
                temperature=request.temperature,
                provider="openai_compat" if not request.model.startswith("qwen") else None,
            )
        except LLMConnectionError as e:
            raise HTTPException(503, detail={
                "code": "LLM_CONNECTION_ERROR",
                "message": str(e),
            })
        except Exception as e:
            logger.error("LLM request failed", error=str(e))
            raise HTTPException(500, detail={
                "code": "LLM_ERROR",
                "message": "LLM request failed",
            })

    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(user_message) // 4,
            "completion_tokens": len(content) // 4,
            "total_tokens": (len(user_message) + len(content)) // 4,
        },
    }
