from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from .approval import ApprovalStore
from .audit_log import write_audit_outputs
from .cache import LLMCache
from .config import PROJECT_ROOT, load_settings
from .email_generator import EmailGenerator
from .ingestion import load_invoice_records
from .models import AuditEntry
from .sender import EmailSender
from .tracing import TraceLogger
from .workflow import run_invoice_workflow


def process_invoices(input_path: Path, today: date | None = None) -> list[AuditEntry]:
    settings = load_settings()
    invoices = load_invoice_records(input_path)
    cache = LLMCache(settings.cache_db_path)
    generator = EmailGenerator(settings.gemini_api_key, settings.gemini_model, cache)
    sender = EmailSender(
        dry_run=settings.dry_run,
        sender_email=settings.sender_email,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_password=settings.smtp_password,
        smtp_use_tls=settings.smtp_use_tls,
    )
    approval_store = ApprovalStore(settings.approvals_path)
    tracer = TraceLogger(
        PROJECT_ROOT / "outputs",
        enable_local=settings.enable_local_tracing,
        langsmith_enabled=settings.langsmith_tracing,
        langsmith_api_key=settings.langsmith_api_key,
        langsmith_project=settings.langsmith_project,
    )
    entries: list[AuditEntry] = []

    for invoice in invoices:
        tracer.event("invoice_started", {"invoice_no": invoice.invoice_no, "client_name": invoice.client_name})
        state = run_invoice_workflow(
            invoice,
            generator,
            sender,
            today,
            approval_store=approval_store,
            require_approval=settings.require_approval and not settings.dry_run,
        )
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
                generation_method=state["generation_method"],
                approval_status=state["approval_status"],
                assigned_to=invoice.account_manager_email if decision.requires_manual_review else None,
                subject=subject,
                body=body,
                reason=reason,
            )
        )
        tracer.event(
            "invoice_completed",
            {
                "invoice_no": invoice.invoice_no,
                "stage": decision.stage,
                "status": status.value,
                "generation_method": state["generation_method"],
                "approval_status": state["approval_status"],
            },
        )

    write_audit_outputs(entries, PROJECT_ROOT / "outputs", settings.audit_db_path)
    tracer.flush()
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
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run on an APScheduler interval instead of once.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    today = date.fromisoformat(args.today) if args.today else None
    if args.schedule:
        from .scheduler import start_scheduler

        start_scheduler(Path(args.input), today=today)
        return
    entries = process_invoices(Path(args.input), today=today)

    print(f"Processed {len(entries)} invoice records.")
    for entry in entries:
        print(
            f"{entry.invoice_no}: stage={entry.stage}, days_overdue={entry.days_overdue}, "
            f"status={entry.status.value}, generation={entry.generation_method}, "
            f"approval={entry.approval_status}"
        )


if __name__ == "__main__":
    main()
