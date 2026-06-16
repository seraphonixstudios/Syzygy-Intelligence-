"""Tests for checkpointing system."""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestCheckpointManager:
    @pytest.mark.asyncio
    async def test_load_checkpoint_nonexistent_session(self, tmp_path):
        from app.orchestration.checkpointing import CheckpointManager

        with patch("app.orchestration.checkpointing.settings") as ms:
            ms.data_dir = str(tmp_path)
            cm = CheckpointManager()
            result = await cm.load_checkpoint("nonexistent-session", 1)
            assert result is None

    @pytest.mark.asyncio
    async def test_load_checkpoint_no_matching_round(self, tmp_path):
        from app.orchestration.checkpointing import CheckpointManager

        with patch("app.orchestration.checkpointing.settings") as ms:
            ms.data_dir = str(tmp_path)
            cm = CheckpointManager()
            await cm.save_checkpoint("session-a", 1, {"state": "data"})
            result = await cm.load_checkpoint("session-a", 2)
            assert result is None

    @pytest.mark.asyncio
    async def test_replay_to_round_delegates(self, tmp_path):
        from app.orchestration.checkpointing import CheckpointManager

        with patch("app.orchestration.checkpointing.settings") as ms:
            ms.data_dir = str(tmp_path)
            cm = CheckpointManager()
            result = await cm.replay_to_round("nonexistent", 1)
            assert result is None
