"""Syzygy Intelligence — FastAPI entry point with logging, error handling, and audit."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    admin,
    agents,
    audit,
    auth,
    chat,
    consensus,
    memory,
    meta,
    oauth,
    payments,
    sessions,
    tools,
    uploads,
    workflows,
)
from app.api.routes import rag as rag_route
from app.api.websockets import ws_handler
from app.config import settings
from app.db.session import close_db, init_db
from app.errors import setup_error_handlers
from app.logging_setup import logger
from app.middleware.rate_limiter import setup_rate_limiter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db_type = "SQLite" if settings.db_is_sqlite else "PostgreSQL"
    logger.info(
        "Syzygy Intelligence starting",
        env=settings.env,
        db=db_type,
        db_url=settings.database_url.replace(settings.db_password, "****"),
        version="0.1.0",
    )

    # Check critical dependencies
    missing = []
    try:
        import sqlalchemy
        logger.info("sqlalchemy", version=sqlalchemy.__version__)
    except ImportError:
        missing.append("sqlalchemy")
    try:
        import httpx
        logger.info("httpx", version=httpx.__version__)
    except ImportError:
        missing.append("httpx")
    try:
        import bcrypt
        logger.info("bcrypt", version=bcrypt.__version__)  # type: ignore[attr-defined]
    except ImportError:
        missing.append("bcrypt")
    try:
        import jwt
        logger.info("PyJWT", version=jwt.__version__)
    except ImportError:
        missing.append("PyJWT")

    if missing:
        logger.warning(f"Missing dependencies: {', '.join(missing)} — install with: pip install {' '.join(missing)}")

    try:
        ok = await init_db()
        if ok:
            logger.info("Database initialized successfully")
        else:
            logger.warning("Database unavailable — features requiring DB will fail")
    except Exception as e:
        logger.warning(f"Database initialization error: {e}")

    yield
    logger.info("Syzygy Intelligence shutting down")
    await close_db()


app = FastAPI(
    title="Syzygy Intelligence API",
    description="Multi-agent platform with polarity-aware consensus and Jungian archetypes",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

setup_error_handlers(app)
setup_rate_limiter(app)

app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(consensus.router, prefix="/api/consensus", tags=["Consensus"])
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
app.include_router(tools.router, prefix="/api/tools", tags=["Tools"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(oauth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(meta.router, prefix="/api/meta", tags=["Meta"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["Uploads"])
app.include_router(rag_route.router, prefix="/api/rag", tags=["RAG"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])

app.add_api_websocket_route("/ws", ws_handler)


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "service": "Syzygy Intelligence",
        "version": "0.1.0",
        "tagline": "Aligning opposites into unified intelligence",
        "status": "operational",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "env": settings.env}

@app.get("/debug/config")
async def debug_config() -> dict[str, Any]:
    """Expose non-sensitive config for debugging (only in dev/testing)."""
    if settings.env == "production":
        return {"error": "Not available in production"}
    return {
        "env": settings.env,
        "db_type": "SQLite" if settings.db_is_sqlite else "PostgreSQL",
        "db_host": settings.db_host,
        "db_port": settings.db_port,
        "db_name": settings.db_name,
        "db_user": settings.db_user,
        "db_is_sqlite": settings.db_is_sqlite,
        "ollama_base_url": settings.ollama_base_url,
        "rate_limit_enabled": settings.rate_limit_enabled,
        "litellm_enabled": settings.litellm_enabled,
        "cors_origins": settings.cors_origins,
    }
