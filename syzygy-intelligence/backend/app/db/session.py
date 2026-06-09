"""Async database session management with lazy engine initialization.

Engine is created on first use, not at import time. This allows tests
to run without a live PostgreSQL database.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event, text

from app.config import settings
from app.logging_setup import logger


class Base(DeclarativeBase):
    pass


_engine = None
_async_session_factory = None
_db_type: str | None = None


def _get_sqlite_engine():
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def _get_engine():
    global _engine, _db_type
    if _engine is not None:
        return _engine

    if settings.db_is_sqlite:
        logger.info("Using SQLite database (development mode)")
        _db_type = "sqlite"
        _engine = _get_sqlite_engine()
    else:
        _db_type = "postgresql"
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.env == "development",
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _engine


def _get_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


# Re-export for modules that need direct session creation outside DI
async def get_standalone_session() -> AsyncSession:
    factory = _get_session_factory()
    async with factory() as session:
        return session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database — create all tables if they don't exist. Returns True on success, False if skipped."""
    try:
        engine = _get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.commit()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.warning(f"Database initialization skipped: {e}")
        return False


async def close_db():
    """Dispose of the database engine."""
    global _engine, _async_session_factory
    if _engine is not None:
        try:
            await _engine.dispose()
            logger.info("Database engine disposed")
        except Exception as e:
            logger.warning(f"Error disposing database engine: {e}")
        _engine = None
        _async_session_factory = None
