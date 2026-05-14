# Security Risk Mitigations

## Prompt Injection

Risk: A malicious invoice field could attempt to manipulate the LLM, for example by inserting instructions into a client name or payment note.

Mitigations:

- Invoice data is validated through Pydantic before email generation.
- The LLM prompt tells the model to use only supplied invoice facts.
- Generated output is parsed into a structured `EmailDraft` model.
- A personalization validator checks that required invoice facts are present.
- The agent does not allow invoice data to change system behavior.

## Data Privacy / PII

Risk: Invoice records contain client names, contact emails, and payment details.

Mitigations:

- The prototype processes data locally.
- Logs are written locally to `outputs/`.
- The sample dataset uses fake client emails.
- Production usage should mask or minimize PII before sending it to any cloud LLM.
- Only fields required for the email are included in prompts.

## API Key Exposure

Risk: LLM or email credentials could be leaked in source code.

Mitigations:

- `.env` is ignored by Git.
- `.env.example` documents required variables without secrets.
- No API keys are hardcoded in code.
- Production deployments should use a secrets manager.

## Hallucination Risk

Risk: The LLM may generate wrong invoice numbers, amounts, dates, or payment links.

Mitigations:

- Invoice facts come from validated source records, not from the model.
- The LLM receives explicit guardrails to not invent facts.
- Output is validated with Pydantic.
- A personalization validator checks required fields after generation.
- If validation fails, the system raises an error instead of logging a sendable email.

## Unauthorized Access

Risk: Anyone could trigger the agent if exposed as an API or dashboard.

Mitigations:

- This prototype runs locally by default.
- If exposed through an API, add API key or OAuth authentication.
- Add rate limiting and role-based access for production.
- Restrict write access to audit logs.

## Email Spoofing

Risk: Real emails may appear to come from an unauthorized sender.

Mitigations:

- Real sending is disabled in this prototype.
- `DRY_RUN=true` is the default.
- Production sending should use a verified sender domain.
- SPF, DKIM, and DMARC must be configured before enabling real sends.

## Accidental Client Emails

Risk: During testing, the agent could send emails to real clients.

Mitigations:

- Dry-run mode is the default behavior.
- The sender returns `DRY_RUN` status instead of connecting to SMTP.
- Real sending requires code changes and verified credentials.
- Sample data uses example addresses.

