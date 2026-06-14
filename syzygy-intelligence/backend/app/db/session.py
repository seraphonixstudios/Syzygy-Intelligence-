"""Async database session management with lazy initialization.

Best practices:
- Lazy engine initialization: tests can run without live database
- Proper transaction handling: commit only on success, rollback on failure
- Resource cleanup: explicit context managers ensure disposal
- Connection pooling: optimized for async operations
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.logging_setup import logger


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None
_db_type: str = "unknown"  # Initialize to avoid unset variable errors


def _get_sqlite_engine() -> AsyncEngine:
    """Create SQLite async engine with optimizations."""
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
        """Set SQLite pragmas for WAL mode and foreign key constraints."""
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

    return engine


def _get_engine() -> AsyncEngine:
    """Get or create the async database engine."""
    global _engine, _db_type

    if _engine is not None:
        return _engine

    if settings.db_is_sqlite:
        logger.info("Database backend: SQLite (development mode)")
        _db_type = "sqlite"
        _engine = _get_sqlite_engine()
    else:
        _db_type = "postgresql"
        # Calculate optimal pool size based on number of workers
        # Rule of thumb: pool_size = (db_connections / num_workers)
        # With 4 workers, allocate ~3 connections per worker (12 total)
        # max_overflow allows burst beyond pool_size
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.env == "development",
            pool_size=12,
            max_overflow=5,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={
                "timeout": 10,
                "server_settings": {
                    "application_name": "syzygy-backend",
                    "jit": "off",
                },
            } if "postgresql" in settings.database_url else {},
        )
        logger.info(
            "Database backend: PostgreSQL",
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            pool_size=12,
            max_overflow=5,
        )

    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory."""
    global _async_session_factory

    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    return _async_session_factory


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the async session factory for manual session creation.

    Caller is responsible for cleanup with context manager or explicit close.
    """
    return _get_session_factory()


@asynccontextmanager
async def get_db_context() -> AsyncIterator[AsyncSession]:
    """Async context manager for DB sessions outside FastAPI DI.

    Usage:
        async with get_db_context() as session:
            result = await session.execute(select(User))

    Behavior:
        - On successful exit: commits the transaction if one is active
        - On exception: rolls back automatically
        - Always closes the session in finally block
    """
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception as exc:
            await session.rollback()
            logger.error(
                "Database session error — rolling back",
                error_type=type(exc).__name__,
                error=str(exc),
            )
            raise
        else:
            # Only commit if a transaction is active (not already committed)
            if session.in_transaction():
                await session.commit()
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection function for FastAPI endpoints.

    Usage in FastAPI:
        @app.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()

    Behavior:
        - On successful yield: commits the transaction if one is active
        - On exception: rolls back automatically
        - Always closes the session in finally block
    """
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception as exc:
            await session.rollback()
            logger.error(
                "Database session error — rolling back",
                error_type=type(exc).__name__,
                error=str(exc),
            )
            raise
        else:
            # Only commit if a transaction is active (not already committed)
            if session.in_transaction():
                await session.commit()
        finally:
            await session.close()


async def init_db() -> bool:
    """Initialize database: create all tables if they don't exist.

    Returns:
        True if initialization succeeded, False if skipped/failed.

    Raises:
        Does not raise; logs errors and returns False instead.
        This allows the app to start even if DB is unavailable.
    """
    safe_url = (
        settings.database_url.replace(settings.db_password, "****")
        if settings.db_password
        else settings.database_url
    )
    logger.info(
        "Initializing database",
        url=safe_url,
        environment=settings.env,
    )

    try:
        engine = _get_engine()

        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Verify connection works
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        logger.info("Database initialized successfully", db_type=_db_type or "unknown")
        return True

    except Exception as exc:
        logger.warning(
            "Database initialization failed — app will start without DB features",
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return False


async def close_db() -> None:
    """Dispose of the database engine.

    Called during application shutdown. Closes all active connections
    and releases resources.
    """
    global _engine, _async_session_factory

    if _engine is not None:
        try:
            await _engine.dispose()
            logger.info("Database engine disposed")
        except Exception as exc:
            logger.warning(
                "Error disposing database engine",
                error_type=type(exc).__name__,
                error=str(exc),
            )
        finally:
            _engine = None
            _async_session_factory = None
