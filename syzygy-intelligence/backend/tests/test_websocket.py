"""Tests for WebSocket handler — ConnectionManager and ws_handler."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.consensus.engine import ConsensusRound, ConsensusSession

# Build minimal test app with WebSocket route
test_app = FastAPI()


def _fake_session(task="Test task"):
    r1 = ConsensusRound(round_number=1)
    r1.proposals = {"a1": "Proposal A"}
    r1.critiques = {"a1": "Critique A"}
    r1.refinements = {"a1": "Refined A"}
    r1.scores = {"a1": 0.85}
    r1.convergence_score = 0.92
    r1.polarity_balance = 0.55
    r1.completed = True
    return ConsensusSession(
        task=task,
        agents=[],
        rounds=[r1],
        current_round=1,
        status="completed",
        final_synthesis="Synthesis result",
        polarity_fusion_report={
            "masculine_forces": [],
            "feminine_forces": [],
            "unified_perspective": [],
            "polarity_balance_scores": [0.55],
            "rounds_completed": 1,
            "individuation_notes": "",
        },
    )


# ===================================================================
# ConnectionManager (client_id-based, from websockets/__init__.py)
# ===================================================================

class TestConnectionManager:
    @pytest.mark.asyncio
    async def test_connect_assigns_client_id(self):
        from app.api.websockets import ConnectionManager
        ws = AsyncMock()
        ws.send_json = AsyncMock()

        mgr = ConnectionManager()
        cid = await mgr.connect(ws, "test-cid")
        assert cid == "test-cid"
        assert mgr.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_connect_generates_id(self):
        from app.api.websockets import ConnectionManager
        ws = AsyncMock()

        mgr = ConnectionManager()
        cid = await mgr.connect(ws)
        assert cid.startswith("ws_")
        assert mgr.get_connection_count() == 1

    def test_disconnect_cleans_up(self):
        from app.api.websockets import ConnectionManager
        ws = MagicMock()

        mgr = ConnectionManager()
        mgr.active_connections["test-cid"] = ws
        mgr._connection_health["test-cid"] = 0
        mgr.disconnect("test-cid")
        assert mgr.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_send_to_success(self):
        from app.api.websockets import ConnectionManager
        ws = AsyncMock()
        ws.send_json = AsyncMock()

        mgr = ConnectionManager()
        mgr.active_connections["test-cid"] = ws
        result = await mgr.send_to("test-cid", {"type": "test"})
        assert result is True
        ws.send_json.assert_called_once_with({"type": "test"})

    @pytest.mark.asyncio
    async def test_send_to_missing_client(self):
        from app.api.websockets import ConnectionManager
        mgr = ConnectionManager()
        result = await mgr.send_to("nonexistent", {"type": "test"})
        assert result is False

    @pytest.mark.asyncio
    async def test_send_to_disconnects_on_error(self):
        from app.api.websockets import ConnectionManager
        ws = AsyncMock()
        ws.send_json = AsyncMock(side_effect=RuntimeError("WS closed"))

        mgr = ConnectionManager()
        mgr.active_connections["test-cid"] = ws
        result = await mgr.send_to("test-cid", {"type": "test"})
        assert result is False
        assert "test-cid" not in mgr.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self):
        from app.api.websockets import ConnectionManager
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2.send_json = AsyncMock()

        mgr = ConnectionManager()
        mgr.active_connections["cid1"] = ws1
        mgr.active_connections["cid2"] = ws2
        await mgr.broadcast({"type": "broadcast"})
        ws1.send_json.assert_called_once_with({"type": "broadcast"})
        ws2.send_json.assert_called_once_with({"type": "broadcast"})

    @pytest.mark.asyncio
    async def test_broadcast_disconnects_on_failure(self):
        from app.api.websockets import ConnectionManager
        ws1 = AsyncMock()
        ws1.send_json = AsyncMock(side_effect=Exception("closed"))
        mgr = ConnectionManager()
        mgr.active_connections["cid1"] = ws1
        await mgr.broadcast({"type": "broadcast"})
        assert mgr.get_connection_count() == 0

    def test_get_connection_ids(self):
        from app.api.websockets import ConnectionManager
        mgr = ConnectionManager()
        mgr.active_connections["a"] = MagicMock()
        mgr.active_connections["b"] = MagicMock()
        ids = mgr.get_connection_ids()
        assert "a" in ids
        assert "b" in ids

    @pytest.mark.asyncio
    async def test_notification_send_via_registered_callback(self):
        from app.api.websockets import ConnectionManager
        from app.notifications import notification_manager

        mgr = ConnectionManager()
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        cid = await mgr.connect(ws, "test-cid")

        send_func = notification_manager._ws_connections.get(cid)
        assert send_func is not None
        await send_func({"type": "test"})
        ws.send_json.assert_called_once_with({"type": "test"})


# ===================================================================
# WebSocket handler — ws_handler
# ===================================================================

if not any(r.path == "/ws" for r in test_app.routes):
    from app.api.websockets import ws_handler
    test_app.add_api_websocket_route("/ws", ws_handler)


class TestWebSocketHandler:
    @pytest.fixture(autouse=True)
    def _patch_deps(self):
        with (
            patch("app.api.websockets.run_consensus_with_memory", new_callable=AsyncMock) as mock_run,
            patch("app.api.websockets.agent_registry") as mock_registry,
            patch("app.api.websockets.notification_manager") as mock_notif,
        ):
            mock_run.return_value = _fake_session()
            mock_registry.create_default_team = MagicMock(return_value=[])
            mock_notif.register_ws = MagicMock()
            mock_notif.unregister_ws = MagicMock()
            mock_notif.notify = AsyncMock()
            yield

    def test_ping_pong(self, _patch_deps):
        with TestClient(test_app).websocket_connect("/ws") as ws:
            ws.send_json({"action": "ping"})
            resp = ws.receive_json()
            assert resp["type"] == "pong"
            assert "timestamp" in resp

    def test_get_status(self, _patch_deps):
        with TestClient(test_app).websocket_connect("/ws") as ws:
            ws.send_json({"action": "get_status"})
            resp = ws.receive_json()
            assert resp["type"] == "status"
            assert resp["connection_count"] >= 1
            assert "connection_id" in resp

    def test_subscribe(self, _patch_deps):
        with TestClient(test_app).websocket_connect("/ws") as ws:
            ws.send_json({"action": "subscribe", "event_types": ["consensus.*"]})
            resp = ws.receive_json()
            assert resp["type"] == "subscribed"
            assert resp["event_types"] == ["consensus.*"]

    def test_run_consensus_success(self, _patch_deps):
        with TestClient(test_app).websocket_connect("/ws") as ws:
            ws.send_json({"action": "run_consensus", "task": "Test task"})

            started = ws.receive_json()
            assert started["type"] == "consensus_started"
            assert started["task"] == "Test task"

            complete = ws.receive_json()
            assert complete["type"] == "consensus_complete"
            assert complete["synthesis"] == "Synthesis result"
            assert complete["session_id"] is not None
            assert complete["total_rounds"] == 1
            assert "fusion_report" in complete

    def test_run_consensus_missing_task(self, _patch_deps):
        with TestClient(test_app).websocket_connect("/ws") as ws:
            ws.send_json({"action": "run_consensus", "task": ""})
            resp = ws.receive_json()
            assert resp["type"] == "error"
            assert resp["message"] == "Task is required"

    def test_unknown_action_does_not_crash(self, _patch_deps):
        with TestClient(test_app).websocket_connect("/ws") as ws:
            ws.send_json({"action": "unknown_action"})
            ws.send_json({"action": "ping"})
            resp = ws.receive_json()
            assert resp["type"] == "pong"

    def test_run_consensus_passes_on_event(self, _patch_deps):
        with TestClient(test_app).websocket_connect("/ws") as ws:
            ws.send_json({"action": "run_consensus", "task": "Test"})
            ws.receive_json()
            ws.receive_json()

            from app.api.websockets import run_consensus_with_memory
            _, kwargs = run_consensus_with_memory.call_args
            assert kwargs["on_event"] is not None
            assert callable(kwargs["on_event"])

    def test_run_consensus_on_event_callback(self, _patch_deps):
        from app.api.websockets import run_consensus_with_memory
        with TestClient(test_app).websocket_connect("/ws") as ws:
            ws.send_json({"action": "run_consensus", "task": "Test"})
            ws.receive_json()
            ws.receive_json()

            _, kwargs = run_consensus_with_memory.call_args
            on_event = kwargs["on_event"]

            import asyncio
            asyncio.run(on_event("round_update", {"round": 1, "score": 0.85}))

            msg = ws.receive_json()
            assert msg["type"] == "consensus_round_update"
            assert msg["round"] == 1
            assert msg["score"] == 0.85

    def test_run_consensus_uses_default_team(self, _patch_deps):
        mock_agents = [MagicMock(), MagicMock()]
        from app.api.websockets import agent_registry
        agent_registry.create_default_team = MagicMock(return_value=mock_agents)

        with TestClient(test_app).websocket_connect("/ws") as ws:
            ws.send_json({"action": "run_consensus", "task": "Test"})
            ws.receive_json()
            ws.receive_json()

            from app.api.websockets import run_consensus_with_memory
            _, kwargs = run_consensus_with_memory.call_args
            assert kwargs["agents"] == mock_agents

    @pytest.mark.asyncio
    async def test_invalid_json_decode_error(self):
        """Directly invoke ws_handler with invalid JSON — handler disconnects."""
        from app.api.websockets import ws_handler

        ws = AsyncMock()
        ws.receive_text = AsyncMock(return_value="not json")
        ws.send_json = AsyncMock()

        await ws_handler(ws)
        # Handler catches JSONDecodeError, logs warning, disconnects, returns
        send_calls = [c[0][0] for c in ws.send_json.call_args_list]
        assert all(c.get("type") != "pong" for c in send_calls)

    @pytest.mark.asyncio
    async def test_generic_exception(self):
        """Directly invoke ws_handler with a generic exception path."""
        from app.api.websockets import ws_handler, manager

        ws = AsyncMock()
        ws.receive_text = AsyncMock(side_effect=RuntimeError("unexpected"))
        ws.send_json = AsyncMock()

        await ws_handler(ws)

    @pytest.mark.asyncio
    async def test_websocket_disconnect(self):
        """Directly invoke ws_handler with WebSocketDisconnect."""
        from app.api.websockets import ws_handler
        from fastapi import WebSocketDisconnect

        ws = AsyncMock()
        ws.receive_text = AsyncMock(side_effect=WebSocketDisconnect(code=1000))
        ws.send_json = AsyncMock()

        await ws_handler(ws)
