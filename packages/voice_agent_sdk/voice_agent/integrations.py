"""Outbound side-effect adapters: SMS and email.

Each is a small Protocol plus a reference implementation and a console stub. The
stub pattern is deliberate and load-bearing: in the original code, missing
Twilio/SMTP creds logged a line and returned success so local dev never
crashed mid-call. We keep that contract here.

Wire these to a Tool handler (see examples) — the agent never imports them
directly.
"""
from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger("voice_agent.integrations")


@runtime_checkable
class SmsSender(Protocol):
    def send(self, to: str, message: str) -> dict: ...


@runtime_checkable
class EmailSender(Protocol):
    def send(self, to: str, subject: str, body: str) -> dict: ...


class ConsoleSmsSender:
    """No-op sender that logs what *would* have been sent. Default for dev."""

    def send(self, to: str, message: str) -> dict:
        logger.info("[SMS STUB] to=%s | %s", to, (message or "")[:160])
        return {"success": True, "sid": "stub", "stubbed": True}


class TwilioSmsSender:
    """Sends via Twilio; degrades to a console stub if creds are incomplete."""

    def __init__(self, account_sid: str, auth_token: str, from_number: str) -> None:
        self.sid = (account_sid or "").strip()
        self.token = (auth_token or "").strip()
        self.from_number = (from_number or "").strip()

    def send(self, to: str, message: str) -> dict:
        if not (self.sid and self.token and self.from_number):
            return ConsoleSmsSender().send(to, message)
        try:
            from twilio.rest import Client  # noqa: WPS433
            client = Client(self.sid, self.token)
            result = client.messages.create(body=message, from_=self.from_number, to=to)
            logger.info("[SMS SENT] to=%s sid=%s", to, result.sid)
            return {"success": True, "sid": result.sid}
        except Exception as exc:  # noqa: BLE001 — surface as a structured failure, never raise into a live call
            logger.error("[SMS ERROR] to=%s err=%s", to, exc)
            return {"success": False, "error": str(exc)}


class ConsoleEmailSender:
    def send(self, to: str, subject: str, body: str) -> dict:
        if not (to or "").strip():
            return {"success": False, "error": "Missing recipient email."}
        logger.info("[EMAIL STUB] to=%s subject=%s", to, subject)
        logger.info("[EMAIL STUB BODY] %s", (body or "")[:400])
        return {"success": True, "stubbed": True}


class SmtpEmailSender:
    """Stdlib SMTP sender (works with Resend/SendGrid/Postmark/Gmail SMTP).
    Falls back to the console stub when host/user aren't configured."""

    def __init__(self, host: str = "", user: str = "", password: str = "",
                 from_addr: str = "", port: int = 587, use_tls: bool = True) -> None:
        self.host = (host or "").strip()
        self.user = (user or "").strip()
        self.password = password or ""
        self.from_addr = (from_addr or self.user or "no-reply@localhost").strip()
        self.port = port
        self.use_tls = use_tls

    def send(self, to: str, subject: str, body: str) -> dict:
        to = (to or "").strip()
        if not to:
            return {"success": False, "error": "Missing recipient email."}
        if not (self.host and self.user):
            return ConsoleEmailSender().send(to, subject, body)
        try:
            import smtplib
            from email.message import EmailMessage
            msg = EmailMessage()
            msg["From"] = self.from_addr
            msg["To"] = to
            msg["Subject"] = subject
            msg.set_content(body)
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            logger.info("[EMAIL SENT] to=%s subject=%s", to, subject)
            return {"success": True}
        except Exception as exc:  # noqa: BLE001
            logger.error("[EMAIL ERROR] to=%s err=%s", to, exc)
            return {"success": False, "error": str(exc)}
