"""Email service abstraction — SendGrid, SES, or console fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger("syzygy.email")


@dataclass
class EmailMessage:
    to: str
    subject: str
    text_body: str
    html_body: str | None = None


class EmailSender(Protocol):
    """Protocol for email sender implementations."""

    async def send(self, message: EmailMessage) -> None: ...


class ConsoleEmailSender:
    """Logs emails to console — used in development."""

    async def send(self, message: EmailMessage) -> None:
        logger.info(
            "--- EMAIL ---\nTo: %s\nSubject: %s\nBody:\n%s\n-------------",
            message.to,
            message.subject,
            message.html_body or message.text_body,
        )


class SendGridEmailSender:
    """Sends emails via SendGrid API."""

    def __init__(self, api_key: str, from_address: str, from_name: str) -> None:
        self.api_key = api_key
        self.from_address = from_address
        self.from_name = from_name

    async def send(self, message: EmailMessage) -> None:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "personalizations": [{"to": [{"email": message.to}]}],
                    "from": {"email": self.from_address, "name": self.from_name},
                    "subject": message.subject,
                    "content": [
                        {"type": "text/plain", "value": message.text_body},
                        *([{"type": "text/html", "value": message.html_body}] if message.html_body else []),
                    ],
                },
            )
            resp.raise_for_status()


class SESEmailSender:
    """Sends emails via AWS SES."""

    def __init__(self, region: str, access_key_id: str, secret_access_key: str, from_address: str, from_name: str) -> None:
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.from_address = from_address
        self.from_name = from_name

    async def send(self, message: EmailMessage) -> None:
        try:
            import aioboto3
        except ImportError:
            logger.warning("aioboto3 not installed — falling back to console email")
            sender = ConsoleEmailSender()
            return await sender.send(message)

        session = aioboto3.Session(
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region,
        )
        async with session.client("ses") as client:
            await client.send_email(
                Source=f"{self.from_name} <{self.from_address}>",
                Destination={"ToAddresses": [message.to]},
                Message={
                    "Subject": {"Data": message.subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": message.text_body, "Charset": "UTF-8"},
                        **(
                            {"Html": {"Data": message.html_body, "Charset": "UTF-8"}}
                            if message.html_body
                            else {}
                        ),
                    },
                },
            )


def create_email_sender(
    provider: str = "console",
    sendgrid_api_key: str = "",
    ses_region: str = "us-east-1",
    ses_access_key_id: str = "",
    ses_secret_access_key: str = "",
    from_address: str = "noreply@syzygy.local",
    from_name: str = "Syzygy Intelligence",
) -> EmailSender:
    if provider == "sendgrid" and sendgrid_api_key:
        return SendGridEmailSender(sendgrid_api_key, from_address, from_name)
    if provider == "ses" and ses_access_key_id:
        return SESEmailSender(ses_region, ses_access_key_id, ses_secret_access_key, from_address, from_name)
    return ConsoleEmailSender()
