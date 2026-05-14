from datetime import date

from src.email_generator import EmailGenerator
from src.escalation import decide_escalation
from src.models import EmailDraft, InvoiceRecord
from src.validators import validate_email_personalization


def invoice() -> InvoiceRecord:
    return InvoiceRecord(
        invoice_no="INV-2026-001",
        client_name="Kapoor Textiles",
        contact_name="Rajesh Kapoor",
        contact_email="rajesh.kapoor@example.com",
        amount=45000,
        currency="INR",
        due_date=date(2026, 5, 10),
        follow_up_count=0,
        payment_link="https://payments.example.com/pay/INV-2026-001",
        account_manager_email="manager@example.com",
    )


def test_template_email_contains_required_personalization_fields():
    record = invoice()
    decision = decide_escalation(record, today=date(2026, 5, 14))
    draft = EmailGenerator().generate(record, decision)

    assert validate_email_personalization(record, decision, draft) == []


def test_validator_reports_missing_fields():
    record = invoice()
    decision = decide_escalation(record, today=date(2026, 5, 14))
    draft = EmailDraft(
        invoice_no=record.invoice_no,
        recipient=record.contact_email,
        subject="Payment reminder",
        body="Please pay soon.",
        tone=decision.tone,
        stage=decision.stage,
    )

    missing = validate_email_personalization(record, decision, draft)

    assert "invoice number" in missing
    assert "payment link" in missing

