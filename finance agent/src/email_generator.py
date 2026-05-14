from __future__ import annotations

import json
from textwrap import dedent

from .cache import LLMCache
from .models import EmailDraft, EscalationDecision, InvoiceRecord
from .validators import validate_email_personalization


class EmailGenerator:
    def __init__(
        self,
        gemini_api_key: str | None = None,
        gemini_model: str = "gemini-2.0-flash",
        cache: LLMCache | None = None,
    ) -> None:
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model
        self.cache = cache
        self.last_generation_method = "NONE"
        self._gemini_disabled_reason: str | None = None

    def generate(self, invoice: InvoiceRecord, decision: EscalationDecision) -> EmailDraft:
        if not decision.should_email:
            raise ValueError("Email generation requested for a non-email escalation decision.")

        self.last_generation_method = "NONE"
        draft = (
            self._generate_with_gemini(invoice, decision)
            if self.gemini_api_key and not self._gemini_disabled_reason
            else None
        )
        if draft is None:
            draft = self._generate_template_email(invoice, decision)
            self.last_generation_method = "TEMPLATE_FALLBACK"

        missing = validate_email_personalization(invoice, decision, draft)
        if missing:
            raise ValueError(
                f"Generated email failed personalization validation. Missing: {', '.join(missing)}"
            )
        return draft

    def _generate_with_gemini(
        self, invoice: InvoiceRecord, decision: EscalationDecision
    ) -> EmailDraft | None:
        try:
            import google.generativeai as genai
        except ImportError:
            return None

        genai.configure(api_key=self.gemini_api_key)
        model = genai.GenerativeModel(self.gemini_model)
        prompt = self._build_prompt(invoice, decision)
        cached_response = self.cache.get(prompt) if self.cache else None
        if cached_response:
            self.last_generation_method = "GEMINI_CACHE"
            return EmailDraft.model_validate(json.loads(cached_response))
        try:
            response = model.generate_content(prompt)
        except Exception as exc:
            self._gemini_disabled_reason = _summarize_gemini_error(exc, self.gemini_model)
            print(f"Gemini unavailable: {self._gemini_disabled_reason}. Using TEMPLATE_FALLBACK.")
            return None
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            raw_text = raw_text.removeprefix("json").strip()
        payload = json.loads(raw_text)
        draft = EmailDraft.model_validate(payload)
        if self.cache:
            self.cache.set(prompt, draft.model_dump_json())
        self.last_generation_method = "GEMINI"
        return draft

    def _build_prompt(self, invoice: InvoiceRecord, decision: EscalationDecision) -> str:
        return dedent(
            f"""
            You are a finance collections assistant. Generate exactly one professional payment
            follow-up email as valid JSON with these keys: invoice_no, recipient, subject, body,
            tone, stage.

            Guardrails:
            - Use only the facts provided below. Do not invent amounts, dates, contacts, or payment terms.
            - Include client name, invoice number, amount due, due date, days overdue, and payment link.
            - Match the requested tone and CTA.
            - Do not include markdown fences or commentary.

            Invoice facts:
            invoice_no: {invoice.invoice_no}
            client_name: {invoice.client_name}
            contact_name: {invoice.contact_name}
            contact_email: {invoice.contact_email}
            amount: {invoice.amount:g} {invoice.currency}
            due_date: {invoice.due_date.isoformat()}
            days_overdue: {decision.days_overdue}
            payment_link: {invoice.payment_link}

            Escalation:
            stage: {decision.stage}
            tone: {decision.tone}
            key_message: {decision.key_message}
            cta: {decision.cta}
            """
        ).strip()

    def _generate_template_email(
        self, invoice: InvoiceRecord, decision: EscalationDecision
    ) -> EmailDraft:
        amount = f"{invoice.currency} {invoice.amount:g}"
        base = {
            1: (
                f"Quick Reminder - Invoice #{invoice.invoice_no} | {amount} Due",
                f"Hi {invoice.contact_name},\n\n"
                f"I hope you are doing well. This is a friendly reminder for {invoice.client_name} "
                f"that Invoice #{invoice.invoice_no} for {amount} was due on "
                f"{invoice.due_date.isoformat()} and is now {decision.days_overdue} days overdue.\n\n"
                f"If this has already been processed, please disregard this note. Otherwise, you can "
                f"complete the payment here: {invoice.payment_link}.\n\n"
                f"Thank you,\nFinance Team",
            ),
            2: (
                f"Payment Confirmation Requested - Invoice #{invoice.invoice_no}",
                f"Hi {invoice.contact_name},\n\n"
                f"Our records show that {invoice.client_name}'s Invoice #{invoice.invoice_no} for "
                f"{amount}, due on {invoice.due_date.isoformat()}, remains unpaid and is now "
                f"{decision.days_overdue} days overdue.\n\n"
                f"Please confirm the expected payment date, or use this payment link to settle the "
                f"invoice: {invoice.payment_link}.\n\n"
                f"Regards,\nFinance Team",
            ),
            3: (
                f"IMPORTANT: Outstanding Payment - Invoice #{invoice.invoice_no} ({decision.days_overdue} Days Overdue)",
                f"Dear {invoice.contact_name},\n\n"
                f"Despite earlier follow-ups, {invoice.client_name}'s Invoice #{invoice.invoice_no} "
                f"for {amount}, due on {invoice.due_date.isoformat()}, remains unpaid and is now "
                f"{decision.days_overdue} days overdue.\n\n"
                f"We request your immediate attention. Continued non-payment may impact credit terms. "
                f"Please respond within 48 hours or complete payment here: {invoice.payment_link}.\n\n"
                f"Regards,\nFinance Team",
            ),
            4: (
                f"FINAL NOTICE - Invoice #{invoice.invoice_no} - Immediate Action Required",
                f"Dear {invoice.contact_name},\n\n"
                f"This is the final reminder for {invoice.client_name}'s Invoice #{invoice.invoice_no} "
                f"for {amount}. The invoice was due on {invoice.due_date.isoformat()} and is now "
                f"{decision.days_overdue} days overdue.\n\n"
                f"Please pay immediately using {invoice.payment_link} or contact us today. Failure to "
                f"remit payment may result in escalation to the finance/legal review process.\n\n"
                f"Regards,\nFinance Team",
            ),
        }
        subject, body = base[decision.stage]
        return EmailDraft(
            invoice_no=invoice.invoice_no,
            recipient=invoice.contact_email,
            subject=subject,
            body=body,
            tone=decision.tone,
            stage=decision.stage,
        )


def _summarize_gemini_error(exc: Exception, model_name: str) -> str:
    message = str(exc)
    if "429" in message or "quota" in message.lower():
        return f"quota exceeded for model '{model_name}'"
    if "404" in message or "not found" in message.lower():
        return "configured model is unavailable for this API key"
    return exc.__class__.__name__
