"""Ollama embedding generation for the RAG pipeline."""

import httpx

from app.config import settings
from app.logging_setup import logger


async def embed(
    texts: list[str],
    model: str = "qwen3:8b-gpu",
) -> list[list[float]]:
    """Generate embeddings via Ollama's ``/api/embed`` endpoint.

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
    """
    url = f"{settings.ollama_base_url.rstrip('/')}/api/embed"
    payload = {"model": model, "input": texts}

    logger.info(
        "Generating embeddings",
        model=model,
        num_texts=len(texts),
        total_chars=sum(len(t) for t in texts),
    )

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    embeddings = data.get("embeddings", [])
    logger.info(
        "Embeddings generated",
        model=model,
        count=len(embeddings),
        dim=len(embeddings[0]) if embeddings else 0,
    )
    return embeddings
