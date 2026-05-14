from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

from .models import AuditEntry


def write_audit_outputs(entries: list[AuditEntry], output_dir: str | Path, db_path: str | Path) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_path = output_path / "sample_email_log.json"
    csv_path = output_path / "sample_email_log.csv"

    payload = [entry.model_dump(mode="json") for entry in entries]
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if payload:
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(payload[0].keys()))
            writer.writeheader()
            writer.writerows(payload)

    write_sqlite(entries, db_path)


def write_sqlite(entries: list[AuditEntry], db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                timestamp TEXT NOT NULL,
                invoice_no TEXT NOT NULL,
                client_name TEXT NOT NULL,
                contact_email TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                due_date TEXT NOT NULL,
                days_overdue INTEGER NOT NULL,
                stage INTEGER NOT NULL,
                tone TEXT NOT NULL,
                status TEXT NOT NULL,
                subject TEXT,
                body TEXT,
                reason TEXT NOT NULL
            )
            """
        )
        connection.execute("DELETE FROM audit_log")
        connection.executemany(
            """
            INSERT INTO audit_log VALUES (
                :timestamp, :invoice_no, :client_name, :contact_email, :amount, :currency,
                :due_date, :days_overdue, :stage, :tone, :status, :subject, :body, :reason
            )
            """,
            [entry.model_dump(mode="json") for entry in entries],
        )

