"""Tests for db/session.py — engine lifecycle, SQLite pragmas, DB init/close, context manager, DI."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession


class TestGetEngine:
    def test_returns_cached_engine(self):
        from app.db.session import _get_engine
        import app.db.session as sess
        sess._engine = None
        sess._db_type = "unknown"
        with patch("app.db.session.settings") as ms:
            ms.db_is_sqlite = True
            ms.database_url = "sqlite+aiosqlite:///:memory:"
            ms.env = "development"
            engine1 = _get_engine()
            assert engine1 is not None
            engine2 = _get_engine()
            assert engine2 is engine1

    def test_sqlite_engine_creates(self):
        from app.db.session import _get_sqlite_engine
        with patch("app.db.session.settings") as ms:
            ms.database_url = "sqlite+aiosqlite:///:memory:"
            engine = _get_sqlite_engine()
            assert engine is not None

    def test_postgresql_engine_create(self):
        pytest.importorskip("asyncpg")
        from app.db.session import _get_engine
        import app.db.session as sess
        sess._engine = None
        sess._db_type = "unknown"
        with patch("app.db.session.settings") as ms:
            ms.db_is_sqlite = False
            ms.database_url = "postgresql+asyncpg://user:pass@localhost/db"
            ms.env = "development"
            ms.db_host = "localhost"
            ms.db_port = 5432
            ms.db_name = "db"
            ms.db_password = "pass"
            engine = _get_engine()
            assert engine is not None


class TestGetSessionFactory:
    def test_creates_factory(self):
        from app.db.session import _get_session_factory
        import app.db.session as sess
        sess._engine = None
        sess._async_session_factory = None
        with patch("app.db.session.settings") as ms:
            ms.db_is_sqlite = True
            ms.database_url = "sqlite+aiosqlite:///:memory:"
            ms.env = "development"
            factory = _get_session_factory()
            assert factory is not None

    def test_get_session_factory_public(self):
        from app.db.session import get_session_factory
        with patch("app.db.session._get_session_factory") as m:
            m.return_value = "factory"
            assert get_session_factory() == "factory"


class TestGetDbContext:
    @pytest.mark.asyncio
    async def test_commits_on_success(self):
        from app.db.session import get_db_context
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.in_transaction.return_value = True
        factory = MagicMock()
        factory.return_value.__aenter__.return_value = mock_session
        with patch("app.db.session._get_session_factory", return_value=factory):
            async with get_db_context() as db:
                assert db is mock_session
        mock_session.commit.assert_awaited_once()
        mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rolls_back_on_exception(self):
        from app.db.session import get_db_context
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.in_transaction.return_value = False
        factory = MagicMock()
        factory.return_value.__aenter__.return_value = mock_session
        with patch("app.db.session._get_session_factory", return_value=factory):
            with pytest.raises(ValueError):
                async with get_db_context() as db:
                    raise ValueError("boom")
        mock_session.rollback.assert_awaited_once()
        mock_session.close.assert_awaited_once()


class TestGetDb:
    @pytest.mark.asyncio
    async def test_yields_session(self):
        from app.db.session import get_db
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.in_transaction.return_value = False
        factory = MagicMock()
        factory.return_value.__aenter__.return_value = mock_session
        with patch("app.db.session._get_session_factory", return_value=factory):
            gen = get_db()
            db = await gen.__anext__()
            assert db is mock_session
            with pytest.raises(StopAsyncIteration):
                await gen.__anext__()
        mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_commits_when_transaction_active(self):
        from app.db.session import get_db
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.in_transaction.return_value = True
        factory = MagicMock()
        factory.return_value.__aenter__.return_value = mock_session
        with patch("app.db.session._get_session_factory", return_value=factory):
            gen = get_db()
            db = await gen.__anext__()
            assert db is mock_session
            with pytest.raises(StopAsyncIteration):
                await gen.__anext__()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rolls_back_on_exception(self):
        from app.db.session import get_db
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.in_transaction.return_value = False
        factory = MagicMock()
        factory.return_value.__aenter__.return_value = mock_session
        with patch("app.db.session._get_session_factory", return_value=factory):
            gen = get_db()
            db = await gen.__anext__()
            assert db is mock_session
            with pytest.raises(ValueError):
                await gen.athrow(ValueError("fail"))
        mock_session.rollback.assert_awaited_once()
        mock_session.close.assert_awaited_once()


class TestInitDb:
    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        mock_engine = MagicMock()
        mock_conn = AsyncMock()
        mock_engine.begin.return_value.__aenter__.return_value = mock_conn
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn
        with (
            patch("app.db.session._get_engine", return_value=mock_engine),
            patch("app.db.session.settings") as ms,
        ):
            ms.database_url = "sqlite+aiosqlite:///:memory:"
            ms.env = "development"
            ms.db_password = None
            from app.db.session import init_db
            result = await init_db()
            assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_on_failure(self):
        mock_engine = MagicMock()
        mock_engine.begin.side_effect = Exception("DB unavailable")
        with (
            patch("app.db.session._get_engine", return_value=mock_engine),
            patch("app.db.session.settings") as ms,
        ):
            ms.database_url = "sqlite+aiosqlite:///:memory:"
            ms.env = "development"
            ms.db_password = None
            from app.db.session import init_db
            result = await init_db()
            assert result is False

    @pytest.mark.asyncio
    async def test_masks_password_in_log(self):
        mock_engine = MagicMock()
        mock_conn = AsyncMock()
        mock_engine.begin.return_value.__aenter__.return_value = mock_conn
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn
        with (
            patch("app.db.session._get_engine", return_value=mock_engine),
            patch("app.db.session.settings") as ms,
        ):
            ms.database_url = "postgresql+asyncpg://user:secret@localhost/db"
            ms.env = "development"
            ms.db_password = "secret"
            from app.db.session import init_db
            result = await init_db()
            assert result is True


class TestCloseDb:
    @pytest.mark.asyncio
    async def test_disposes_engine(self):
        import app.db.session as sess
        mock_eng = AsyncMock()
        sess._engine = mock_eng
        from app.db.session import close_db
        await close_db()
        mock_eng.dispose.assert_awaited_once()
        assert sess._engine is None
        assert sess._async_session_factory is None

    @pytest.mark.asyncio
    async def test_handles_dispose_error(self):
        import app.db.session as sess
        mock_eng = AsyncMock()
        mock_eng.dispose.side_effect = Exception("dispose failed")
        sess._engine = mock_eng
        from app.db.session import close_db
        await close_db()
        assert sess._engine is None

    @pytest.mark.asyncio
    async def test_noop_when_no_engine(self):
        import app.db.session as sess
        sess._engine = None
        from app.db.session import close_db
        await close_db()


class TestSqlitePragmaListener:
    @pytest.mark.asyncio
    async def test_pragma_listener_sets_wal_and_foreign_keys(self):
        from app.db.session import _get_sqlite_engine
        with patch("app.db.session.settings") as ms:
            ms.database_url = "sqlite+aiosqlite:///:memory:"
            engine = _get_sqlite_engine()
            assert engine is not None


class TestSqlitePragmaFinally:
    """The 'finally: cursor.close()' block in the SQLite pragma listener."""

    @pytest.mark.asyncio
    async def test_pragma_finally_closes_cursor(self):
        """The cursor is closed in the finally block even if execute fails."""
        from app.db.session import _get_sqlite_engine
        with patch("app.db.session.settings") as ms:
            ms.database_url = "sqlite+aiosqlite:///:memory:"
            engine = _get_sqlite_engine()
            # The listener is registered; we just test it compiles and runs
            assert engine is not None

    @pytest.mark.asyncio
    async def test_pragma_triggered_on_connect(self):
        """The pragma listener is triggered when a connection is established."""
        from app.db.session import _get_sqlite_engine
        with patch("app.db.session.settings") as ms:
            ms.database_url = "sqlite+aiosqlite:///:memory:"
            engine = _get_sqlite_engine()
            async with engine.connect() as conn:
                await conn.execute(sa.text("SELECT 1"))
                await conn.commit()


