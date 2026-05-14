from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import PROJECT_ROOT
from src.main import process_invoices


st.set_page_config(page_title="Finance Follow-Up Agent", layout="wide")
st.title("Finance Credit Follow-Up Email Agent")

default_path = PROJECT_ROOT / "data" / "sample_invoices.csv"
input_path = st.text_input("Invoice data path", value=str(default_path))
today = st.date_input("Demo date", value=date(2026, 5, 14))

if st.button("Run dry-run agent"):
    entries = process_invoices(Path(input_path), today=today)
    data = [entry.model_dump(mode="json") for entry in entries]
    st.success(f"Processed {len(entries)} records.")

    frame = pd.DataFrame(data)
    sent_count = int((frame["status"] == "DRY_RUN").sum())
    escalated_count = int((frame["status"] == "ESCALATED").sum())
    skipped_count = int((frame["status"] == "SKIPPED").sum())

    col1, col2, col3 = st.columns(3)
    col1.metric("Dry-run emails", sent_count)
    col2.metric("Escalated", escalated_count)
    col3.metric("Skipped", skipped_count)

    st.dataframe(frame[["invoice_no", "client_name", "days_overdue", "stage", "tone", "status", "subject"]])

    st.subheader("Generated Email Bodies")
    for entry in entries:
        if entry.body:
            with st.expander(f"{entry.invoice_no} - Stage {entry.stage}"):
                st.write(entry.subject)
                st.text(entry.body)

