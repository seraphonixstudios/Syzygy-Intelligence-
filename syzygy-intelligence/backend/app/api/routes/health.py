"""Health check endpoint — reports connectivity status for DB, Redis, Ollama, Neo4j."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.db.session import _get_engine
from app.logging_setup import logger

router = APIRouter()

_start_time = time.time()


@router.get("/health")
async def health_check() -> dict[str, Any]:
    checks: dict[str, Any] = {}

    checks["database"] = await _check_database()
    checks["redis"] = await _check_redis()
    checks["ollama"] = await _check_ollama()
    checks["neo4j"] = await _check_neo4j()

    all_ok = all(c["status"] == "ok" for c in checks.values())
    any_ok = any(c["status"] == "ok" for c in checks.values())

    if all_ok:
        overall = "healthy"
    elif any_ok:
        overall = "degraded"
    else:
        overall = "unhealthy"

    return {
        "status": overall,
        "version": "0.1.0",
        "env": settings.env,
        "uptime_seconds": int(time.time() - _start_time),
        "checks": checks,
    }


async def _check_database() -> dict[str, Any]:
    start = time.monotonic()
    try:
        engine = _get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.commit()
        return {"status": "ok", "latency_ms": _ms(start)}
    except Exception as e:
        logger.warning("Health check: database unavailable", error=str(e))
        return {"status": "unavailable", "error": str(e)[:200]}


async def _check_redis() -> dict[str, Any]:
    start = time.monotonic()
    url = settings.redis_url
    if not url or url == "redis://localhost:6379/0" and settings.env == "development":
        return {"status": "ok", "latency_ms": _ms(start), "note": "using default dev URL"}

    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(url, socket_connect_timeout=3, socket_timeout=3)
        pong = await r.ping()
        await r.aclose()
        if pong:
            return {"status": "ok", "latency_ms": _ms(start)}
        return {"status": "unavailable", "error": "ping returned false"}
    except Exception as e:
        logger.warning("Health check: redis unavailable", error=str(e))
        return {"status": "unavailable", "error": str(e)[:200]}


async def _check_ollama() -> dict[str, Any]:
    start = time.monotonic()
    base_url = settings.ollama_base_url
    if not base_url:
        return {"status": "unavailable", "error": "no URL configured"}

    try:
        import httpx

        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{base_url}/api/tags")
            if resp.status_code == 200:
                return {"status": "ok", "latency_ms": _ms(start)}
            return {"status": "unavailable", "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        logger.warning("Health check: ollama unavailable", error=str(e))
        return {"status": "unavailable", "error": str(e)[:200]}


async def _check_neo4j() -> dict[str, Any]:
    start = time.monotonic()
    uri = settings.neo4j_uri
    if not uri or "localhost" in uri and settings.env == "development":
        return {"status": "ok", "latency_ms": _ms(start), "note": "using default dev URI"}

    try:
        from neo4j import AsyncGraphDatabase

        driver = AsyncGraphDatabase.driver(uri, auth=(settings.neo4j_user, settings.neo4j_password))
        async with driver:
            async with driver.session() as session:
                result = await session.run("RETURN 1 AS n")
                record = await result.single()
                if record and record["n"] == 1:
                    return {"status": "ok", "latency_ms": _ms(start)}
                return {"status": "unavailable", "error": "query returned unexpected result"}
    except Exception as e:
        logger.warning("Health check: neo4j unavailable", error=str(e))
        return {"status": "unavailable", "error": str(e)[:200]}


def _ms(start: float) -> float:
    return round((time.monotonic() - start) * 1000, 2)
