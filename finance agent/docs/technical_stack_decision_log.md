# Technical Stack & Decision Log

## LLM Chosen

Primary model: **Gemini 1.5 Flash via Google Gemini API**.

Rationale:

- Gemini has a free-tier path suitable for internship prototyping.
- It is fast enough for short professional email generation.
- It supports structured prompting and JSON-style responses.
- It avoids relying on paid ChatGPT/OpenAI models for basic demo usage.

Fallback:

- If no `GEMINI_API_KEY` is available, the project uses deterministic stage-based templates.
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
- The pipeline can later add caching for repeated LLM generations during development.

