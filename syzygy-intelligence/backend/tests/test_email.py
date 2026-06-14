"""Tests for email service — Console, SendGrid, SES senders."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.email import (
    ConsoleEmailSender,
    EmailMessage,
    SESEmailSender,
    SendGridEmailSender,
    create_email_sender,
)


class TestEmailMessage:
    def test_create_basic(self):
        msg = EmailMessage(to="test@example.com", subject="Hello", text_body="World")
        assert msg.to == "test@example.com"
        assert msg.subject == "Hello"
        assert msg.text_body == "World"
        assert msg.html_body is None

    def test_create_with_html(self):
        msg = EmailMessage(to="a@b.com", subject="S", text_body="T", html_body="<p>H</p>")
        assert msg.html_body == "<p>H</p>"


class TestConsoleEmailSender:
    @pytest.mark.asyncio
    async def test_send_logs_message(self):
        import logging
        logger = logging.getLogger("syzygy.email")
        original_level = logger.level
        logger.setLevel(logging.INFO)
        try:
            with patch.object(logger, "info") as mock_info:
                sender = ConsoleEmailSender()
                msg = EmailMessage(to="test@test.com", subject="Subj", text_body="Body text")
                await sender.send(msg)
                mock_info.assert_called_once()
                args, _ = mock_info.call_args
                assert "test@test.com" in args[0] % args[1:]
        finally:
            logger.setLevel(original_level)

    @pytest.mark.asyncio
    async def test_send_with_html(self):
        import logging
        logger = logging.getLogger("syzygy.email")
        original_level = logger.level
        logger.setLevel(logging.INFO)
        try:
            with patch.object(logger, "info") as mock_info:
                sender = ConsoleEmailSender()
                msg = EmailMessage(to="a@b.com", subject="S", text_body="T", html_body="<h1>HTML</h1>")
                await sender.send(msg)
                mock_info.assert_called_once()
                args, _ = mock_info.call_args
                assert "<h1>HTML</h1>" in args[0] % args[1:]
        finally:
            logger.setLevel(original_level)


class TestSendGridEmailSender:
    @pytest.mark.asyncio
    async def test_send_success(self):
        sender = SendGridEmailSender(
            api_key="sg-key", from_address="from@test.com", from_name="Tester",
        )
        msg = EmailMessage(to="to@test.com", subject="Hi", text_body="Content")
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_post = AsyncMock()
            mock_client.post = mock_post
            mock_post.return_value.raise_for_status = MagicMock()
            await sender.send(msg)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert args[0] == "https://api.sendgrid.com/v3/mail/send"
            assert "Bearer sg-key" in kwargs["headers"]["Authorization"]
            assert kwargs["json"]["personalizations"][0]["to"][0]["email"] == "to@test.com"

    @pytest.mark.asyncio
    async def test_send_with_html_body(self):
        sender = SendGridEmailSender(api_key="k", from_address="f@t.com", from_name="N")
        msg = EmailMessage(to="t@t.com", subject="S", text_body="T", html_body="<b>HTML</b>")
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock()
            await sender.send(msg)
            _, kwargs = mock_client.post.call_args
            content_types = [c["type"] for c in kwargs["json"]["content"]]
            assert "text/html" in content_types

    @pytest.mark.asyncio
    async def test_send_raises_on_http_error(self):
        sender = SendGridEmailSender(api_key="k", from_address="f@t.com", from_name="N")
        msg = EmailMessage(to="t@t.com", subject="S", text_body="T")
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("HTTP 401")
            mock_client.post = AsyncMock(return_value=mock_response)
            with pytest.raises(Exception, match="HTTP 401"):
                await sender.send(msg)


class TestSESEmailSenderAioboto3:
    """SES sender tests with mocked aioboto3 available."""

    @pytest.fixture(autouse=True)
    def _patch_aioboto3(self):
        mock_mod = MagicMock()
        self._mock_session_cls = MagicMock()
        self._mock_client = AsyncMock()
        self._mock_session = MagicMock()
        self._mock_session.client.return_value.__aenter__.return_value = self._mock_client
        self._mock_session_cls.return_value = self._mock_session
        mock_mod.Session = self._mock_session_cls
        with patch.dict("sys.modules", {"aioboto3": mock_mod}):
            yield

    @pytest.mark.asyncio
    async def test_send_via_aioboto3(self):
        sender = SESEmailSender("us-east-1", "AKID", "SAK", "f@t.com", "N")
        msg = EmailMessage(to="t@t.com", subject="S", text_body="T")
        await sender.send(msg)
        self._mock_session_cls.assert_called_once_with(
            aws_access_key_id="AKID", aws_secret_access_key="SAK", region_name="us-east-1",
        )
        self._mock_client.send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_with_html_body(self):
        sender = SESEmailSender("us-east-1", "AKID", "SAK", "f@t.com", "N")
        msg = EmailMessage(to="t@t.com", subject="S", text_body="T", html_body="<p>H</p>")
        await sender.send(msg)
        _, kwargs = self._mock_client.send_email.call_args
        assert "Html" in kwargs["Message"]["Body"]


class TestSESEmailSenderFallback:
    """SES sender fallback when aioboto3 is not installed."""

    @pytest.mark.asyncio
    async def test_fallback_when_aioboto3_missing(self, caplog):
        import logging
        caplog.set_level(logging.WARNING)
        sender = SESEmailSender("us-east-1", "AKID", "SAK", "f@t.com", "N")
        msg = EmailMessage(to="t@t.com", subject="S", text_body="T")
        with patch("app.services.email.ConsoleEmailSender.send", new_callable=AsyncMock) as mock_console:
            # Ensure aioboto3 is not in sys.modules
            saved = {}
            if "aioboto3" in sys.modules:
                saved["aioboto3"] = sys.modules.pop("aioboto3")
            import builtins
            original_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == "aioboto3":
                    raise ImportError("No module named 'aioboto3'")
                return original_import(name, *args, **kwargs)

            builtins.__import__ = mock_import
            try:
                await sender.send(msg)
                mock_console.assert_called_once()
            finally:
                builtins.__import__ = original_import
                for k, v in saved.items():
                    sys.modules[k] = v


class TestCreateEmailSender:
    def test_console_default(self):
        sender = create_email_sender()
        assert isinstance(sender, ConsoleEmailSender)

    def test_sendgrid(self):
        sender = create_email_sender(
            provider="sendgrid", sendgrid_api_key="sg-key",
            from_address="f@t.com", from_name="N",
        )
        assert isinstance(sender, SendGridEmailSender)
        assert sender.api_key == "sg-key"

    def test_sendgrid_no_key_falls_to_console(self):
        sender = create_email_sender(provider="sendgrid")
        assert isinstance(sender, ConsoleEmailSender)

    def test_ses(self):
        sender = create_email_sender(
            provider="ses", ses_access_key_id="AKID", ses_secret_access_key="SAK",
            from_address="f@t.com", from_name="N",
        )
        assert isinstance(sender, SESEmailSender)

    def test_ses_no_key_falls_to_console(self):
        sender = create_email_sender(provider="ses")
        assert isinstance(sender, ConsoleEmailSender)

    def test_unknown_provider_uses_console(self):
        sender = create_email_sender(provider="unknown")
        assert isinstance(sender, ConsoleEmailSender)
