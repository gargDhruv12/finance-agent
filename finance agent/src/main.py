from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from .audit_log import write_audit_outputs
from .config import PROJECT_ROOT, load_settings
from .email_generator import EmailGenerator
from .ingestion import load_invoice_records
from .models import AuditEntry
from .sender import EmailSender
from .workflow import run_invoice_workflow


def process_invoices(input_path: Path, today: date | None = None) -> list[AuditEntry]:
    settings = load_settings()
    invoices = load_invoice_records(input_path)
    generator = EmailGenerator(settings.gemini_api_key)
    sender = EmailSender(dry_run=settings.dry_run)
    entries: list[AuditEntry] = []

    for invoice in invoices:
        state = run_invoice_workflow(invoice, generator, sender, today)
        decision = state["decision"]
        status = state["status"]
        subject = state.get("subject")
        body = state.get("body")
        reason = state["reason"]

        entries.append(
            AuditEntry(
                timestamp=datetime.now(),
                invoice_no=invoice.invoice_no,
                client_name=invoice.client_name,
                contact_email=invoice.contact_email,
                amount=invoice.amount,
                currency=invoice.currency,
                due_date=invoice.due_date,
                days_overdue=decision.days_overdue,
                stage=decision.stage,
                tone=decision.tone,
                status=status,
                subject=subject,
                body=body,
                reason=reason,
            )
        )

    write_audit_outputs(entries, PROJECT_ROOT / "outputs", settings.audit_db_path)
    return entries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Finance Credit Follow-Up Email Agent")
    parser.add_argument(
        "--input",
        default=str(PROJECT_ROOT / "data" / "sample_invoices.csv"),
        help="Path to CSV or Excel invoice data.",
    )
    parser.add_argument(
        "--today",
        default=None,
        help="Override today's date as YYYY-MM-DD for reproducible demos.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    today = date.fromisoformat(args.today) if args.today else None
    entries = process_invoices(Path(args.input), today=today)

    print(f"Processed {len(entries)} invoice records.")
    for entry in entries:
        print(
            f"{entry.invoice_no}: stage={entry.stage}, days_overdue={entry.days_overdue}, "
            f"status={entry.status.value}"
        )


if __name__ == "__main__":
    main()
