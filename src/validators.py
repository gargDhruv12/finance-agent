from __future__ import annotations

from .models import EmailDraft, EscalationDecision, InvoiceRecord


def validate_email_personalization(
    invoice: InvoiceRecord, decision: EscalationDecision, draft: EmailDraft
) -> list[str]:
    text = f"{draft.subject}\n{draft.body}".lower()
    required_values = {
        "client name": invoice.client_name,
        "invoice number": invoice.invoice_no,
        "amount": _format_amount(invoice.amount),
        "due date": invoice.due_date.isoformat(),
        "days overdue": str(decision.days_overdue),
        "payment link": invoice.payment_link,
    }

    missing: list[str] = []
    for label, value in required_values.items():
        normalized_value = str(value).lower()
        if label == "amount":
            amount_variants = {normalized_value, str(int(invoice.amount)).lower()}
            if not any(variant in text for variant in amount_variants):
                missing.append(label)
        elif normalized_value not in text:
            missing.append(label)
    return missing


def _format_amount(amount: float) -> str:
    return str(int(amount)) if amount.is_integer() else str(amount)

