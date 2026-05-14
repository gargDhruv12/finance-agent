from datetime import date

from src.escalation import decide_escalation
from src.models import InvoiceRecord


def invoice(due_date: date) -> InvoiceRecord:
    return InvoiceRecord(
        invoice_no="INV-TEST",
        client_name="Test Client",
        contact_name="Test User",
        contact_email="test@example.com",
        amount=1000,
        currency="INR",
        due_date=due_date,
        follow_up_count=0,
        payment_link="https://payments.example.com/pay/INV-TEST",
        account_manager_email="manager@example.com",
    )


def test_escalation_stages_match_required_matrix():
    today = date(2026, 5, 14)
    cases = [
        (date(2026, 5, 14), 0, False),
        (date(2026, 5, 11), 1, True),
        (date(2026, 5, 4), 2, True),
        (date(2026, 4, 26), 3, True),
        (date(2026, 4, 19), 4, True),
        (date(2026, 4, 10), 5, False),
    ]

    for due_date, expected_stage, should_email in cases:
        decision = decide_escalation(invoice(due_date), today=today)
        assert decision.stage == expected_stage
        assert decision.should_email is should_email


def test_over_30_days_requires_manual_review():
    decision = decide_escalation(invoice(date(2026, 4, 10)), today=date(2026, 5, 14))

    assert decision.stage == 5
    assert decision.requires_manual_review is True
    assert decision.should_email is False

