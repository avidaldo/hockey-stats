from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


class SmtpEmailSender:
    def __init__(self) -> None:
        self.host = os.getenv("HOCKEY_SMTP_HOST", "")
        self.port = int(os.getenv("HOCKEY_SMTP_PORT", "587"))
        self.user = os.getenv("HOCKEY_SMTP_USER", "")
        self.password = os.getenv("HOCKEY_SMTP_PASSWORD", "")
        self.from_addr = os.getenv("HOCKEY_SMTP_FROM", self.user)
        self.use_tls = os.getenv("HOCKEY_SMTP_TLS", "true").lower() != "false"

    def is_configured(self) -> bool:
        return bool(self.host and self.from_addr)

    def send(self, subject: str, body: str, recipients: list[str]) -> tuple[bool, str]:
        message = EmailMessage()
        message["From"] = self.from_addr
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=20) as smtp:
                if self.use_tls:
                    smtp.starttls()
                if self.user and self.password:
                    smtp.login(self.user, self.password)
                smtp.send_message(message)
            return True, "Sent via SMTP"
        except Exception as exc:  # noqa: BLE001
            return False, f"SMTP send failed: {exc}"


class MockEmailSender:
    def send(self, subject: str, body: str, recipients: list[str]) -> tuple[bool, str]:
        preview = body[:200].replace("\n", " ")
        return True, f"Mock send to {len(recipients)} recipient(s). Preview: {preview}"


class AutoEmailSender:
    def __init__(self) -> None:
        self.smtp = SmtpEmailSender()
        self.mock = MockEmailSender()

    def send(self, subject: str, body: str, recipients: list[str]) -> tuple[bool, str]:
        if self.smtp.is_configured():
            return self.smtp.send(subject, body, recipients)
        return self.mock.send(subject, body, recipients)
