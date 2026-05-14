from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SendStatus(str, Enum):
    DRY_RUN = "DRY_RUN"
    SENT = "SENT"
    ESCALATED = "ESCALATED"
    SKIPPED = "SKIPPED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class InvoiceRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    invoice_no: str = Field(min_length=1)
    client_name: str = Field(min_length=1)
    contact_name: str = Field(min_length=1)
    contact_email: str = Field(min_length=3)
    amount: float = Field(gt=0)
    currency: str = Field(default="INR", min_length=1)
    due_date: date
    follow_up_count: int = Field(default=0, ge=0)
    payment_link: str = Field(min_length=1)
    account_manager_email: str = Field(min_length=3)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("contact_email", "account_manager_email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email address")
        return value.lower()


class EscalationDecision(BaseModel):
    invoice_no: str
    days_overdue: int
    stage: Literal[0, 1, 2, 3, 4, 5]
    tone: str
    trigger: str
    key_message: str
    cta: str
    should_email: bool
    requires_manual_review: bool = False


class EmailDraft(BaseModel):
    invoice_no: str
    recipient: str = Field(min_length=3)
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)
    tone: str
    stage: int

    @field_validator("recipient")
    @classmethod
    def validate_recipient(cls, value: str) -> str:
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email address")
        return value.lower()


class AuditEntry(BaseModel):
    timestamp: datetime
    invoice_no: str
    client_name: str
    contact_email: str
    amount: float
    currency: str
    due_date: date
    days_overdue: int
    stage: int
    tone: str
    status: SendStatus
    generation_method: str
    approval_status: str = "NOT_REQUIRED"
    assigned_to: str | None = None
    subject: str | None = None
    body: str | None = None
    reason: str
