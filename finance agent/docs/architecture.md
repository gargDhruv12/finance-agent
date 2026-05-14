# Architecture

## Overview

The Finance Credit Follow-Up Email Agent is designed as a controlled automation pipeline. It does not let the LLM decide payment status, escalation stage, or send behavior. Those decisions are handled by deterministic code and validated data models.

## Flow

```mermaid
flowchart TD
  A["Load CSV / Excel"] --> B["Validate InvoiceRecord"]
  B --> C["Calculate Days Overdue"]
  C --> D["Select Escalation Stage"]
  D --> E{"Stage 5?"}
  E -- "Yes" --> F["Create Manual Review Audit Entry"]
  E -- "No" --> G["Generate EmailDraft"]
  G --> H["Validate Personalization"]
  H --> I{"Real Send Requires Approval?"}
  I -- "Pending / Rejected" --> J["Approval Queue"]
  I -- "Approved or Dry Run" --> K["Dry-Run or SMTP Sender"]
  J --> L["Audit + Trace Outputs"]
  K --> L
  F --> L
```

## Agent Responsibilities

- Ingestion validates source data.
- Escalation logic enforces the mandatory matrix.
- Email generation handles tone and wording.
- Validation prevents generic or incomplete emails.
- Approval queue gates real sends.
- Sender ensures dry-run behavior by default and supports optional SMTP.
- Audit logging and tracing record every action.

## Why This Architecture

Finance automation needs predictable behavior. A fully autonomous agent could be risky because it might over-escalate, send incorrect information, or email real clients during testing. This design uses the LLM only where it adds value: writing human-friendly emails.
