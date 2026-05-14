from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from .models import EmailDraft, InvoiceRecord


ApprovalStatus = Literal["APPROVED", "REJECTED", "PENDING"]


class ApprovalRecord(BaseModel):
    invoice_no: str
    status: ApprovalStatus
    reviewer: str = "finance.manager@example.com"
    reason: str = ""
    updated_at: datetime


class ApprovalStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def status_for(self, invoice: InvoiceRecord) -> ApprovalRecord:
        records = self._load()
        payload = records.get(invoice.invoice_no)
        if payload is None:
            return ApprovalRecord(
                invoice_no=invoice.invoice_no,
                status="PENDING",
                reviewer=invoice.account_manager_email,
                reason="Awaiting finance approval before real send.",
                updated_at=datetime.now(),
            )
        return ApprovalRecord.model_validate(payload)

    def upsert(
        self,
        invoice_no: str,
        status: ApprovalStatus,
        reviewer: str,
        reason: str,
    ) -> ApprovalRecord:
        record = ApprovalRecord(
            invoice_no=invoice_no,
            status=status,
            reviewer=reviewer,
            reason=reason,
            updated_at=datetime.now(),
        )
        records = self._load()
        records[invoice_no] = record.model_dump(mode="json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(records, indent=2), encoding="utf-8")
        return record

    def ensure_pending(self, invoice: InvoiceRecord, draft: EmailDraft) -> None:
        records = self._load()
        if invoice.invoice_no in records:
            return
        records[invoice.invoice_no] = ApprovalRecord(
            invoice_no=invoice.invoice_no,
            status="PENDING",
            reviewer=invoice.account_manager_email,
            reason=f"Review generated email before sending to {draft.recipient}.",
            updated_at=datetime.now(),
        ).model_dump(mode="json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def _load(self) -> dict[str, dict[str, object]]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

