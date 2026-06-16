"""Unit tests for Syzygy Notifications and Audit System."""

from unittest.mock import AsyncMock, patch

import pytest

from app.notifications import (
    MessageBus,
    Notification,
    NotificationManager,
    NotificationSeverity,
    NotificationType,
)


class TestNotification:
    def test_notification_creation(self):
        n = Notification(
            type=NotificationType.CONSENSUS_COMPLETE,
            title="Done",
            body="Consensus reached",
            severity=NotificationSeverity.INFO,
        )
        assert n.title == "Done"
        assert n.type == NotificationType.CONSENSUS_COMPLETE
        assert n.severity == NotificationSeverity.INFO

    def test_notification_to_dict(self):
        n = Notification(type=NotificationType.SYSTEM, title="Test")
        d = n.to_dict()
        assert d["title"] == "Test"
        assert d["type"] == "system"
        assert "id" in d
        assert "created_at" in d

    def test_notification_to_json(self):
        n = Notification(type=NotificationType.AGENT_ACTIVATED, title="Agent On")
        json_str = n.to_json()
        assert '"title": "Agent On"' in json_str

    def test_default_severity(self):
        n = Notification(type=NotificationType.SYSTEM, title="Default")
        assert n.severity == NotificationSeverity.INFO

    def test_all_types_have_values(self):
        for t in NotificationType:
            assert t.value

    def test_all_severities_have_values(self):
        for s in NotificationSeverity:
            assert s.value


class TestMessageBusHistory:
    @pytest.mark.asyncio
    async def test_history_truncation(self):
        bus = MessageBus()
        for i in range(1100):
            await bus.publish(Notification(type=NotificationType.SYSTEM, title=f"T{i}"))
        history = bus.get_history(limit=2000)
        assert len(history) == 1000
        assert history[0].title == "T100"

    @pytest.mark.asyncio
    async def test_sync_callback(self):
        bus = MessageBus()
        received = []

        def sync_handler(notification):
            received.append(notification)

        bus.subscribe("system", sync_handler)
        await bus.publish(Notification(type=NotificationType.SYSTEM, title="Sync"))
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_callback_exception_logged(self):
        bus = MessageBus()
        with patch("app.notifications.logger.error") as mock_err:

            async def failing_handler(n):
                raise RuntimeError("handler crashed")

            bus.subscribe("system", failing_handler)
            await bus.publish(Notification(type=NotificationType.SYSTEM, title="Fail"))
            mock_err.assert_called_once()
            assert "handler crashed" in str(mock_err.call_args)


class TestMessageBus:
    @pytest.mark.asyncio
    async def test_publish_subscribe(self):
        bus = MessageBus()
        received = []

        async def handler(notification):
            received.append(notification)

        bus.subscribe("system", handler)
        await bus.publish(Notification(type=NotificationType.SYSTEM, title="Test"))
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_wildcard_subscribe(self):
        bus = MessageBus()
        received = []

        async def handler(notification):
            received.append(notification)

        bus.subscribe("*", handler)
        await bus.publish(Notification(type=NotificationType.SYSTEM, title="T1"))
        await bus.publish(Notification(type=NotificationType.CONSENSUS_STARTED, title="T2"))
        assert len(received) == 2

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        bus = MessageBus()
        received = []

        async def handler(n):
            received.append(n)

        bus.subscribe("system", handler)
        bus.unsubscribe("system", handler)
        await bus.publish(Notification(type=NotificationType.SYSTEM, title="T"))
        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_history(self):
        bus = MessageBus()
        for i in range(5):
            await bus.publish(Notification(type=NotificationType.SYSTEM, title=f"T{i}"))
        history = bus.get_history(limit=3)
        assert len(history) == 3
        assert history[-1].title == "T4"

    @pytest.mark.asyncio
    async def test_history_limit(self):
        bus = MessageBus()
        for i in range(20):
            await bus.publish(Notification(type=NotificationType.SYSTEM, title=f"T{i}"))
        assert len(bus.get_history()) == 20

    @pytest.mark.asyncio
    async def test_clear_history(self):
        bus = MessageBus()
        await bus.publish(Notification(type=NotificationType.SYSTEM, title="T"))
        bus.clear_history()
        assert len(bus.get_history()) == 0

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self):
        bus = MessageBus()
        r1, r2 = [], []

        async def h1(n): r1.append(n)
        async def h2(n): r2.append(n)

        bus.subscribe("system", h1)
        bus.subscribe("system", h2)
        await bus.publish(Notification(type=NotificationType.SYSTEM, title="T"))
        assert len(r1) == 1
        assert len(r2) == 1


class TestNotificationManagerWsSend:
    @pytest.mark.asyncio
    async def test_notify_ws_broadcast_success(self):
        nm = NotificationManager()
        send = AsyncMock()
        nm.register_ws("cid1", send)

        with patch("app.notifications.audit_service.log", new_callable=AsyncMock):
            n = await nm.notify(
                type=NotificationType.SYSTEM,
                title="Broadcast",
                body="To all",
            )
        send.assert_awaited_once()
        assert send.call_args[0][0]["title"] == "Broadcast"

    @pytest.mark.asyncio
    async def test_notify_ws_broadcast_failure_disconnects(self):
        nm = NotificationManager()
        send_fail = AsyncMock(side_effect=RuntimeError("WS gone"))
        send_ok = AsyncMock()
        nm.register_ws("cid_fail", send_fail)
        nm.register_ws("cid_ok", send_ok)

        with patch("app.notifications.audit_service.log", new_callable=AsyncMock):
            with patch.object(nm, "unregister_ws") as mock_unreg:
                await nm.notify(
                    type=NotificationType.SYSTEM,
                    title="Test",
                )
        mock_unreg.assert_called_once_with("cid_fail")
        assert send_ok.await_count == 1


class TestNotificationManager:
    @pytest.mark.asyncio
    async def test_notify(self):
        nm = NotificationManager()
        n = await nm.notify(
            type=NotificationType.SYSTEM,
            title="Test Notification",
            body="Test body",
        )
        assert n.title == "Test Notification"
        assert n.body == "Test body"
        assert n.severity == NotificationSeverity.INFO

    @pytest.mark.asyncio
    async def test_notify_with_data(self):
        nm = NotificationManager()
        n = await nm.notify(
            type=NotificationType.CONSENSUS_COMPLETE,
            title="Done",
            data={"rounds": 4},
        )
        assert n.data == {"rounds": 4}

    @pytest.mark.asyncio
    async def test_notify_with_agent(self):
        nm = NotificationManager()
        n = await nm.notify(
            type=NotificationType.AGENT_ACTIVATED,
            title="Agent active",
            agent_id="agent_1",
        )
        assert n.target_agent_id == "agent_1"
