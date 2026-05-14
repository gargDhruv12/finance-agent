from __future__ import annotations

from .models import EmailDraft, SendStatus


class EmailSender:
    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    def send(self, draft: EmailDraft) -> SendStatus:
        if self.dry_run:
            return SendStatus.DRY_RUN

        # Real SMTP/SendGrid/Mailgun integration can be added here once verified
        # sender domains and credentials are configured.
        raise NotImplementedError("Real email sending is disabled in this prototype.")

