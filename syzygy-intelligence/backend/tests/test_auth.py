"""Tests for authentication utilities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAuthenticateApiKey:
    @pytest.mark.asyncio
    async def test_verify_password_mismatch_returns_none(self):
        from app.api.auth import authenticate_api_key

        mock_api_key = MagicMock()
        mock_api_key.id = "key-id-123"
        mock_api_key.hashed_key = "hashed-value"

        fut = AsyncMock()
        fut.scalar_one_or_none = MagicMock(return_value=mock_api_key)

        db = AsyncMock()
        db.execute = AsyncMock(return_value=fut)
        db.add = MagicMock()

        with (
            patch("app.api.auth._compute_searchable_hash", return_value="known-searchable-hash"),
            patch("app.api.auth.verify_password", return_value=False),
        ):
            result = await authenticate_api_key("syzygy_test-key", db)

        assert result is None
