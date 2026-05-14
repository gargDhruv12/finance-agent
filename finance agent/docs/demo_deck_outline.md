# Demo Deck Outline

## Slide 1: Title

Finance Credit Follow-Up Email Agent

## Slide 2: Business Problem

Finance teams spend time manually chasing overdue invoices, leading to inconsistent tone, delayed follow-ups, and limited auditability.

## Slide 3: Solution

An AI-assisted agent reads invoice data, selects the correct escalation stage, generates personalized emails, and logs every action.

## Slide 4: Escalation Matrix

Show the five required stages from warm reminder to legal/finance review flag.

## Slide 5: Architecture

Show ingestion, validation, escalation, generation, dry-run sender, and audit log.

## Slide 6: Demo Data

Show sample CSV with invoices across Stage 1, Stage 2, Stage 3, Stage 4, escalation flag, and not-overdue cases.

## Slide 7: Results

Show sample generated emails and audit log output.

## Slide 8: Security

Cover dry-run default, secret handling, prompt injection protection, hallucination checks, and email spoofing prevention.

## Slide 9: Tech Stack Decisions

Gemini free-tier, Python, Pydantic, pandas, SQLite, Streamlit, and dry-run sender.

## Slide 10: Learnings & Future Improvements

Add real email provider, authentication, approval workflow, scheduler, caching, and observability tracing.

