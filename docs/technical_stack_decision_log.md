# Technical Stack & Decision Log

## LLM Chosen

Primary model: **Gemini 2.0 Flash via Google Gemini API**.

Rationale:

- Gemini has a free-tier path suitable for internship prototyping.
- It is fast enough for short professional email generation.
- It supports structured prompting and JSON-style responses.
- It avoids relying on paid ChatGPT/OpenAI models for basic demo usage.

Fallback:

- If no `GEMINI_API_KEY` is available, the project uses deterministic stage-based templates.
- If the configured Gemini model is unavailable for the current API key, the project logs the issue and uses deterministic stage-based templates.
- This keeps the demo reliable and cost-free while preserving the same validation, dry-run, and audit flow.

## Agent Framework

Planned framework: **LangGraph / LangChain-style workflow**.

The code is organized as a deterministic agent pipeline:

1. Ingestion node
2. Validation node
3. Trigger logic node
4. Escalation decision node
5. Email generation node
6. Personalization validation node
7. Dry-run send node
8. Audit logging node

This architecture is intentionally simple for a one-week internship prototype. It favors explainability and auditability over a complex autonomous loop.

## Data Source

Primary data source: CSV.

Supported formats:

- `.csv`
- `.xlsx`
- `.xls`

CSV was chosen first because it is easy to review in a demo and maps directly to the task brief fields.

## Structured Output

The project uses Pydantic models for:

- `InvoiceRecord`
- `EscalationDecision`
- `EmailDraft`
- `AuditEntry`

This reduces parsing errors and protects against malformed generated email data.

## Email Sending

Default mode: `DRY_RUN=true`.

The system logs emails instead of sending them. Real SMTP/SendGrid/Mailgun integration is intentionally disabled in the prototype until sender credentials, verified domains, SPF, DKIM, and DMARC are configured.

## Logging

Audit outputs:

- JSON for easy review
- CSV for spreadsheet inspection
- SQLite for persistent local audit records

Each audit row includes timestamp, invoice details, stage, tone, send status, subject, body, and reason.

## Cost Control

- Gemini free-tier is preferred.
- Template fallback avoids unnecessary API calls.
- Dry-run mode avoids paid email infrastructure.
- SQLite caching stores repeated LLM generations during development to reduce cost.

## Approval Workflow

The project now includes a finance approval queue. When `DRY_RUN=false` and `REQUIRE_APPROVAL=true`, generated drafts are marked `PENDING_APPROVAL` instead of being sent. Reviewers can approve or reject drafts through the Streamlit dashboard or the local `outputs/approvals.json` file.

## Email Sending

SMTP support is implemented but disabled unless `DRY_RUN=false` and SMTP settings are configured. This keeps the internship demo safe while showing a production-ready extension path.

## Scheduling

APScheduler is wired through the `--schedule` CLI flag. The interval is controlled by `SCHEDULER_INTERVAL_HOURS`.

## Observability

Local tracing writes event records to `outputs/trace_events.json`. Optional LangSmith hooks are included and activated only when credentials are configured. LangSmith was chosen because the project uses a LangGraph-capable workflow, making it the most natural observability fit.
