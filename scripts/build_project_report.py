from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Finance_Credit_Follow_Up_Email_Agent_Project_Report.docx"

BLUE = RGBColor(46, 116, 181)
DARK_BLUE = RGBColor(31, 77, 120)
INK = RGBColor(11, 37, 69)
LIGHT_GRAY = "F2F4F7"
CALLOUT = "F4F6F9"


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_margins(table) -> None:
    tbl_pr = table._tbl.tblPr
    margins = tbl_pr.first_child_found_in("w:tblCellMar")
    if margins is None:
        margins = OxmlElement("w:tblCellMar")
        tbl_pr.append(margins)
    for side in ("top", "bottom", "start", "end"):
        node = margins.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            margins.append(node)
        node.set(qn("w:w"), "120" if side in {"start", "end"} else "80")
        node.set(qn("w:type"), "dxa")


def set_table_width(table) -> None:
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.first_child_found_in("w:tblW")
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), "9360")
    tbl_w.set(qn("w:type"), "dxa")


def add_table(document: Document, headers: list[str], rows: list[list[str]], widths: list[float]):
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    set_table_width(table)
    set_cell_margins(table)

    header_cells = table.rows[0].cells
    for idx, text in enumerate(headers):
        cell = header_cells[idx]
        cell.width = Inches(widths[idx])
        set_cell_shading(cell, LIGHT_GRAY)
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(text)
        run.bold = True
        run.font.size = Pt(9.5)
        run.font.color.rgb = INK
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    for row in rows:
        cells = table.add_row().cells
        for idx, text in enumerate(row):
            cells[idx].width = Inches(widths[idx])
            cells[idx].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            para = cells[idx].paragraphs[0]
            para.paragraph_format.space_after = Pt(0)
            run = para.add_run(text)
            run.font.size = Pt(9.2)
    document.add_paragraph()
    return table


def add_callout(document: Document, title: str, body: str) -> None:
    table = document.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_width(table)
    set_cell_margins(table)
    cell = table.cell(0, 0)
    set_cell_shading(cell, CALLOUT)
    para = cell.paragraphs[0]
    para.paragraph_format.space_after = Pt(3)
    run = para.add_run(title)
    run.bold = True
    run.font.color.rgb = DARK_BLUE
    run.font.size = Pt(10.5)
    body_para = cell.add_paragraph()
    body_para.paragraph_format.space_after = Pt(0)
    body_run = body_para.add_run(body)
    body_run.font.size = Pt(10)
    document.add_paragraph()


def add_bullet(document: Document, text: str) -> None:
    para = document.add_paragraph(style="List Bullet")
    para.paragraph_format.left_indent = Inches(0.5)
    para.paragraph_format.first_line_indent = Inches(-0.25)
    para.paragraph_format.space_after = Pt(4)
    para.paragraph_format.line_spacing = 1.167
    para.add_run(text)


def configure_document(document: Document) -> None:
    section = document.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.492)
    section.footer_distance = Inches(0.492)

    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.1

    title = styles["Title"]
    title.font.name = "Calibri"
    title.font.size = Pt(22)
    title.font.bold = True
    title.font.color.rgb = INK
    title.paragraph_format.space_after = Pt(6)

    subtitle = styles["Subtitle"]
    subtitle.font.name = "Calibri"
    subtitle.font.size = Pt(12)
    subtitle.font.color.rgb = DARK_BLUE

    h1 = styles["Heading 1"]
    h1.font.name = "Calibri"
    h1.font.size = Pt(16)
    h1.font.color.rgb = BLUE
    h1.paragraph_format.space_before = Pt(16)
    h1.paragraph_format.space_after = Pt(8)

    h2 = styles["Heading 2"]
    h2.font.name = "Calibri"
    h2.font.size = Pt(13)
    h2.font.color.rgb = BLUE
    h2.paragraph_format.space_before = Pt(12)
    h2.paragraph_format.space_after = Pt(6)

    h3 = styles["Heading 3"]
    h3.font.name = "Calibri"
    h3.font.size = Pt(12)
    h3.font.color.rgb = DARK_BLUE
    h3.paragraph_format.space_before = Pt(8)
    h3.paragraph_format.space_after = Pt(4)

    header = section.header.paragraphs[0]
    header.text = "Finance Credit Follow-Up Email Agent"
    header.alignment = WD_ALIGN_PARAGRAPH.LEFT
    header.runs[0].font.size = Pt(9)
    header.runs[0].font.color.rgb = DARK_BLUE

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run("Project Report | AI Enablement Internship")
    footer.runs[0].font.size = Pt(9)


def build() -> None:
    document = Document()
    configure_document(document)

    title = document.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("Finance Credit Follow-Up Email Agent")

    subtitle = document.add_paragraph(style="Subtitle")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run("Project Report for AI Enablement Internship - Task 2")

    meta = document.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.add_run("Submission Date: 14 May 2026 | Mode: GitHub / Source Code + Report")

    add_callout(
        document,
        "Executive Summary",
        "This project implements an AI-assisted finance agent that reads overdue invoice records, "
        "determines the correct follow-up stage, generates personalized payment reminder emails, "
        "runs in dry-run mode by default, and records every action in an audit trail. The prototype "
        "prioritizes safety, traceability, and cost-conscious tooling suitable for an internship submission.",
    )

    document.add_heading("1. Project Overview", level=1)
    document.add_paragraph(
        "Finance teams often spend significant time manually following up on overdue invoices. "
        "Manual follow-ups can be inconsistent in tone, delayed, and difficult to audit. The proposed "
        "agent automates the drafting and logging of payment follow-up emails while preserving control "
        "through deterministic escalation logic and dry-run execution."
    )
    document.add_paragraph(
        "The solution follows Task 2 from the AI Enablement Internship brief: Finance Credit Follow-Up Email Agent. "
        "It supports pending invoice ingestion, tone escalation, personalized email generation, mock sending, "
        "audit logging, and manual review flags for severely overdue accounts."
    )

    document.add_heading("2. Objectives", level=1)
    for item in [
        "Read invoice records from CSV or Excel with fields such as invoice number, client, amount, due date, contact email, and follow-up count.",
        "Identify overdue invoices and map them to the mandatory escalation matrix.",
        "Generate professional, personalized emails that include all required invoice details.",
        "Use dry-run mode to prevent accidental emails during testing and demos.",
        "Maintain a complete audit trail for generated emails, skipped records, and manual escalation flags.",
        "Document LLM choice, framework choice, prompt design, and security mitigations as required by the internship brief.",
    ]:
        add_bullet(document, item)

    document.add_heading("3. Methodology", level=1)
    document.add_paragraph(
        "The agent was designed as a controlled workflow rather than a fully autonomous system. "
        "The LLM is used only for language generation, while business-critical decisions such as overdue status, "
        "escalation stage, and send behavior are handled by deterministic Python logic. This reduces hallucination risk "
        "and makes the workflow easier to explain during review."
    )
    add_table(
        document,
        ["Step", "Component", "Purpose"],
        [
            ["1", "Data ingestion", "Load CSV or Excel invoice records and validate required fields."],
            ["2", "Trigger logic", "Calculate days overdue and skip invoices that are not overdue."],
            ["3", "Escalation engine", "Apply the required stage matrix from warm reminder to manual review."],
            ["4", "Email generation", "Use Gemini when available, otherwise deterministic templates."],
            ["5", "Personalization validation", "Confirm required fields appear in the generated email."],
            ["6", "Dry-run sender", "Log send intent without contacting real clients."],
            ["7", "Audit trail", "Write JSON, CSV, and SQLite records for review and compliance."],
        ],
        [0.55, 1.7, 4.1],
    )

    document.add_heading("4. Technical Stack", level=1)
    add_table(
        document,
        ["Layer", "Technology", "Reason"],
        [
            ["Language", "Python", "Simple, readable, and suitable for data processing workflows."],
            ["LLM", "Gemini API", "Free-tier-friendly option; configurable model in .env."],
            ["Framework", "LangGraph-capable workflow", "Provides clear node-based agent flow with fallback support."],
            ["Validation", "Pydantic", "Structured models for invoice records, decisions, drafts, and audits."],
            ["Data", "pandas CSV/Excel", "Common finance-friendly input format."],
            ["Sending", "Dry-run sender", "Prevents accidental real client emails during testing."],
            ["Logging", "JSON, CSV, SQLite", "Human-readable output plus persistent audit records."],
            ["UI", "Streamlit", "Optional dashboard for demo visibility."],
        ],
        [1.15, 1.75, 3.45],
    )

    document.add_heading("5. Escalation Matrix", level=1)
    add_table(
        document,
        ["Stage", "Trigger", "Tone", "Action"],
        [
            ["1", "1-7 days overdue", "Warm & Friendly", "Generate gentle reminder with payment link."],
            ["2", "8-14 days overdue", "Polite but Firm", "Request payment confirmation date."],
            ["3", "15-21 days overdue", "Formal & Serious", "Ask for response within 48 hours."],
            ["4", "22-30 days overdue", "Stern & Urgent", "Final reminder before escalation."],
            ["5", "30+ days overdue", "Escalation Flag", "No auto email; assign for manual finance/legal review."],
        ],
        [0.7, 1.5, 1.45, 2.9],
    )

    document.add_heading("6. Implementation Summary", level=1)
    for item in [
        "The GitHub repository is intended to be named finance-agent, with project files placed at the repository root for a clean submission view.",
        "The CLI entry point is python -m src.main --today 2026-05-14.",
        "The sample dataset includes Stage 1, Stage 2, Stage 3, Stage 4, escalation flag, and not-overdue records.",
        "The app uses DRY_RUN=true by default, so generated emails are logged but not sent.",
        "The prompts folder is intentionally ignored by Git. A safe prompt design summary is included in the docs.",
        "Gemini generation is configurable through GEMINI_MODEL. If quota is unavailable, the system falls back to templates and continues running.",
    ]:
        add_bullet(document, item)

    document.add_heading("7. Findings And Results", level=1)
    document.add_paragraph(
        "The sample run processed six invoice records using the demo date 14 May 2026. "
        "The output demonstrated all required behavioral cases: four dry-run emails, one manual escalation, "
        "and one skipped not-overdue invoice."
    )
    add_table(
        document,
        ["Invoice", "Days Overdue", "Stage", "Status", "Generation"],
        [
            ["INV-2026-001", "4", "1", "DRY_RUN", "Template fallback or Gemini when quota is available"],
            ["INV-2026-002", "11", "2", "DRY_RUN", "Template fallback or Gemini when quota is available"],
            ["INV-2026-003", "18", "3", "DRY_RUN", "Template fallback or Gemini when quota is available"],
            ["INV-2026-004", "25", "4", "DRY_RUN", "Template fallback or Gemini when quota is available"],
            ["INV-2026-005", "34", "5", "ESCALATED", "No email; manual review required"],
            ["INV-2026-006", "0", "0", "SKIPPED", "No email; invoice is not overdue"],
        ],
        [1.25, 1.0, 0.65, 1.0, 2.6],
    )

    document.add_heading("8. Security And Risk Mitigation", level=1)
    add_table(
        document,
        ["Risk", "Mitigation"],
        [
            ["Prompt injection", "Validated invoice fields, constrained prompts, and structured output parsing."],
            ["Data privacy / PII", "Local processing, fake sample data, minimized fields in prompts, and local logs."],
            ["API key exposure", ".env is ignored by Git; .env.example contains placeholders only."],
            ["Hallucination", "Invoice facts come from validated data; generated email content is checked for mandatory fields."],
            ["Unauthorized access", "Prototype runs locally; production deployment should add authentication and rate limits."],
            ["Email spoofing", "Real sending disabled; production requires verified sender domain, SPF, DKIM, and DMARC."],
            ["Accidental sending", "DRY_RUN=true by default and sender does not connect to SMTP in this prototype."],
        ],
        [1.65, 4.8],
    )

    document.add_heading("9. Deliverables", level=1)
    for item in [
        "Source code and documentation placed at the repository root for a clean GitHub submission.",
        "README with setup, run instructions, architecture, tech decisions, and security notes.",
        "Sample input dataset in data/sample_invoices.csv.",
        "Sample output logs in outputs/sample_email_log.json and outputs/sample_email_log.csv.",
        "Dedicated documents for technical stack, prompt design, security mitigations, architecture, and demo deck outline.",
        "Optional Streamlit dashboard through streamlit run app.py.",
    ]:
        add_bullet(document, item)

    document.add_heading("10. Implemented Enhancements", level=1)
    for item in [
        "Human approval queue before real email sending.",
        "Optional SMTP sender guarded by dry-run and approval settings.",
        "APScheduler support for recurring invoice scans.",
        "SQLite LLM response caching to reduce repeated Gemini calls.",
        "Local tracing plus optional LangSmith hooks.",
        "Expanded dashboard with filters, approval actions, generated email review, and trace visibility.",
    ]:
        add_bullet(document, item)

    document.add_heading("11. Next Production Steps", level=1)
    for item in [
        "Configure a verified sender domain with SPF, DKIM, and DMARC before real client sends.",
        "Add authentication and role-based access if the dashboard is deployed beyond local use.",
        "Connect the input source to the finance team's actual ERP, accounting system, or Google Sheet.",
        "Add PII redaction before enabling hosted tracing in production.",
    ]:
        add_bullet(document, item)

    document.add_heading("12. Conclusion", level=1)
    document.add_paragraph(
        "The Finance Credit Follow-Up Email Agent provides a practical, auditable prototype for automating overdue "
        "invoice follow-ups. It satisfies the internship task requirements while keeping real-world safety concerns "
        "front and center: dry-run mode is enabled by default, all decisions are traceable, and records beyond the "
        "Stage 4 threshold are flagged for human review instead of being emailed automatically."
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
