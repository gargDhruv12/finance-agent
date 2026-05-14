from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from src.approval import ApprovalStore
from src.config import PROJECT_ROOT
from src.main import process_invoices


st.set_page_config(page_title="Finance Follow-Up Agent", layout="wide")
st.title("Finance Credit Follow-Up Email Agent")

default_path = PROJECT_ROOT / "data" / "sample_invoices.csv"
input_path = st.text_input("Invoice data path", value=str(default_path))
today = st.date_input("Demo date", value=date(2026, 5, 14))
approval_store = ApprovalStore(PROJECT_ROOT / "outputs" / "approvals.json")

if st.button("Run dry-run agent"):
    entries = process_invoices(Path(input_path), today=today)
    st.session_state["entries"] = [entry.model_dump(mode="json") for entry in entries]

data = st.session_state.get("entries")
if data:
    frame = pd.DataFrame(data)
    st.success(f"Processed {len(frame)} records.")

    dry_run_count = int((frame["status"] == "DRY_RUN").sum())
    pending_count = int((frame["status"] == "PENDING_APPROVAL").sum())
    escalated_count = int((frame["status"] == "ESCALATED").sum())
    skipped_count = int((frame["status"] == "SKIPPED").sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Dry-run emails", dry_run_count)
    col2.metric("Pending approval", pending_count)
    col3.metric("Escalated", escalated_count)
    col4.metric("Skipped", skipped_count)

    stages = ["All"] + [str(stage) for stage in sorted(frame["stage"].unique())]
    statuses = ["All"] + sorted(frame["status"].unique().tolist())
    selected_stage = st.selectbox("Stage filter", stages)
    selected_status = st.selectbox("Status filter", statuses)

    filtered = frame.copy()
    if selected_stage != "All":
        filtered = filtered[filtered["stage"] == int(selected_stage)]
    if selected_status != "All":
        filtered = filtered[filtered["status"] == selected_status]

    columns = [
        "invoice_no",
        "client_name",
        "days_overdue",
        "stage",
        "tone",
        "status",
        "approval_status",
        "generation_method",
        "subject",
    ]
    st.dataframe(filtered[columns], use_container_width=True)

    st.subheader("Approval Queue")
    approval_candidates = frame[frame["body"].notna()]
    if approval_candidates.empty:
        st.info("No generated email drafts are available for approval.")
    else:
        invoice_no = st.selectbox("Invoice to review", approval_candidates["invoice_no"].tolist())
        selected = approval_candidates[approval_candidates["invoice_no"] == invoice_no].iloc[0]
        st.write(selected["subject"])
        st.text(selected["body"])
        reviewer = st.text_input("Reviewer email", value="finance.manager@example.com")
        reason = st.text_input("Review note", value="Reviewed from Streamlit dashboard.")
        approve_col, reject_col = st.columns(2)
        if approve_col.button("Approve draft"):
            approval_store.upsert(invoice_no, "APPROVED", reviewer, reason)
            st.success(f"{invoice_no} approved.")
        if reject_col.button("Reject draft"):
            approval_store.upsert(invoice_no, "REJECTED", reviewer, reason)
            st.warning(f"{invoice_no} rejected.")

    st.subheader("Generated Email Bodies")
    for _, entry in filtered.iterrows():
        if isinstance(entry.get("body"), str) and entry["body"]:
            with st.expander(f"{entry['invoice_no']} - Stage {entry['stage']}"):
                st.write(entry["subject"])
                st.text(entry["body"])

    trace_path = PROJECT_ROOT / "outputs" / "trace_events.json"
    if trace_path.exists():
        st.subheader("Local Trace Events")
        st.json(trace_path.read_text(encoding="utf-8"))
