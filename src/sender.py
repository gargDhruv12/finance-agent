from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .models import EmailDraft, SendStatus


class EmailSender:
    def __init__(
        self,
        dry_run: bool = True,
        sender_email: str = "finance@example.com",
        smtp_host: str | None = None,
        smtp_port: int = 587,
        smtp_username: str | None = None,
        smtp_password: str | None = None,
        smtp_use_tls: bool = True,
    ) -> None:
        self.dry_run = dry_run
        self.sender_email = sender_email
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.smtp_use_tls = smtp_use_tls

    def send(self, draft: EmailDraft) -> SendStatus:
        if self.dry_run:
            return SendStatus.DRY_RUN

        if not self.smtp_host:
            return SendStatus.FAILED

        message = EmailMessage()
        message["From"] = self.sender_email
        message["To"] = draft.recipient
        message["Subject"] = draft.subject
        message.set_content(draft.body)

        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as smtp:
            if self.smtp_use_tls:
                smtp.starttls()
            if self.smtp_username and self.smtp_password:
                smtp.login(self.smtp_username, self.smtp_password)
            smtp.send_message(message)
        return SendStatus.SENT
