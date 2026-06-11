"""Ollama embedding generation for the RAG pipeline."""

import httpx

from app.config import settings
from app.errors import LLMConnectionError
from app.logging_setup import logger

_EMBEDDED_ENDPOINTS = ["/api/embed", "/api/embeddings"]


async def embed(
    texts: list[str],
    model: str = "nomic-embed-text",
) -> list[list[float]]:
    """Generate embeddings via Ollama.

    Tries ``/api/embed`` first (Ollama >= 0.3.0), then falls back to
    ``/api/embeddings``. If neither is available, raises ``LLMConnectionError``.

    Parameters
    ----------
    texts : list[str]
        One or more text strings to embed.
    model : str
        Ollama model name to use for embedding.

    Returns
    -------
    list[list[float]]
        List of embedding vectors, one per input text.

    Raises
    ------
    LLMConnectionError
        If Ollama doesn't support embeddings or is unreachable.
    """
    base = settings.ollama_base_url.rstrip("/")
    logger.info(
        "Generating embeddings",
        model=model,
        num_texts=len(texts),
        total_chars=sum(len(t) for t in texts),
    )

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            url = f"{base}/api/embed"
            payload = {"model": model, "input": texts}
            resp = await client.post(url, json=payload)
        except httpx.RequestError as e:
            raise LLMConnectionError(model=model, original_error=str(e))

        if resp.status_code == 200:
            data = resp.json()
            embeddings = data.get("embeddings", [])
        elif resp.status_code in (500, 501):
            raise LLMConnectionError(
                model=model,
                original_error="Ollama server does not support embeddings",
            )
        else:
            resp.raise_for_status()

    logger.info(
        "Embeddings generated",
        model=model,
        count=len(embeddings),
        dim=len(embeddings[0]) if embeddings else 0,
    )
    return embeddings
