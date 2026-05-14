from __future__ import annotations

from datetime import date

from .models import EscalationDecision, InvoiceRecord


def calculate_days_overdue(due_date: date, today: date | None = None) -> int:
    current_day = today or date.today()
    return max((current_day - due_date).days, 0)


def decide_escalation(invoice: InvoiceRecord, today: date | None = None) -> EscalationDecision:
    days = calculate_days_overdue(invoice.due_date, today)

    if days == 0:
        return EscalationDecision(
            invoice_no=invoice.invoice_no,
            days_overdue=0,
            stage=0,
            tone="Not overdue",
            trigger="Not overdue",
            key_message="Invoice is not overdue.",
            cta="No action required",
            should_email=False,
        )

    if 1 <= days <= 7:
        return EscalationDecision(
            invoice_no=invoice.invoice_no,
            days_overdue=days,
            stage=1,
            tone="Warm & Friendly",
            trigger="1-7 days overdue",
            key_message="Gentle reminder, assume oversight",
            cta="Pay now link / bank details",
            should_email=True,
        )

    if 8 <= days <= 14:
        return EscalationDecision(
            invoice_no=invoice.invoice_no,
            days_overdue=days,
            stage=2,
            tone="Polite but Firm",
            trigger="8-14 days overdue",
            key_message="Payment still pending; request confirmation",
            cta="Confirm payment date",
            should_email=True,
        )

    if 15 <= days <= 21:
        return EscalationDecision(
            invoice_no=invoice.invoice_no,
            days_overdue=days,
            stage=3,
            tone="Formal & Serious",
            trigger="15-21 days overdue",
            key_message="Escalating concern; mention impact",
            cta="Respond within 48 hrs",
            should_email=True,
        )

    if 22 <= days <= 30:
        return EscalationDecision(
            invoice_no=invoice.invoice_no,
            days_overdue=days,
            stage=4,
            tone="Stern & Urgent",
            trigger="22-30 days overdue",
            key_message="Final reminder before escalation",
            cta="Pay immediately or call us",
            should_email=True,
        )

    return EscalationDecision(
        invoice_no=invoice.invoice_no,
        days_overdue=days,
        stage=5,
        tone="Escalation Flag",
        trigger="30+ days overdue",
        key_message="Human review required; no auto email",
        cta="Assign to finance manager",
        should_email=False,
        requires_manual_review=True,
    )

