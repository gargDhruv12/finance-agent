# Prompt Design Summary

The full local prompt files are stored under `prompts/`, which is intentionally ignored by Git. This document records the prompt design approach without exposing the full working prompts.

## Prompt Goals

- Generate one professional follow-up email for one invoice record.
- Match the escalation tone selected by the deterministic escalation engine.
- Include all mandatory personalization fields.
- Return structured JSON that can be validated by Pydantic.

## Prompt Inputs

The email generation prompt receives:

- invoice number
- client name
- contact name
- contact email
- amount and currency
- due date
- days overdue
- payment link
- escalation stage
- tone
- key message
- CTA

## Guardrails

The prompt instructs the model to:

- Use only the provided invoice facts.
- Never invent payment terms, dates, amounts, or contacts.
- Return only valid JSON.
- Include every mandatory personalization field.
- Avoid markdown formatting and extra commentary.

## Prompt Iteration Notes

Iteration 1:

- Basic email prompt with tone guidance.
- Issue: output could be plain text and hard to parse.

Iteration 2:

- Required JSON keys were added.
- Improvement: easier Pydantic validation.

Iteration 3:

- Explicit anti-hallucination guardrails were added.
- Improvement: invoice facts became more reliable.

Iteration 4:

- Mandatory personalization checklist was added.
- Improvement: generated emails consistently include invoice number, amount, due date, days overdue, and payment link.

