from __future__ import annotations

from pathlib import Path

import pandas as pd

from .models import InvoiceRecord


REQUIRED_COLUMNS = {
    "invoice_no",
    "client_name",
    "contact_name",
    "contact_email",
    "amount",
    "currency",
    "due_date",
    "follow_up_count",
    "payment_link",
    "account_manager_email",
}


def load_invoice_records(path: str | Path) -> list[InvoiceRecord]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Input file not found: {source}")

    if source.suffix.lower() == ".csv":
        frame = pd.read_csv(source)
    elif source.suffix.lower() in {".xlsx", ".xls"}:
        frame = pd.read_excel(source)
    else:
        raise ValueError("Supported input formats: .csv, .xlsx, .xls")

    frame.columns = [str(column).strip().lower() for column in frame.columns]
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    records: list[InvoiceRecord] = []
    for row_number, row in frame.iterrows():
        try:
            records.append(InvoiceRecord.model_validate(row.to_dict()))
        except Exception as exc:
            raise ValueError(f"Invalid invoice record at row {row_number + 2}: {exc}") from exc
    return records

