from __future__ import annotations

from datetime import date
from typing import Any, TypedDict

from .email_generator import EmailGenerator
from .escalation import decide_escalation
from .models import EmailDraft, EscalationDecision, InvoiceRecord, SendStatus
from .sender import EmailSender


class InvoiceWorkflowState(TypedDict, total=False):
    invoice: InvoiceRecord
    today: date | None
    decision: EscalationDecision
    draft: EmailDraft | None
    status: SendStatus
    subject: str | None
    body: str | None
    reason: str
    generation_method: str


def run_invoice_workflow(
    invoice: InvoiceRecord,
    generator: EmailGenerator,
    sender: EmailSender,
    today: date | None = None,
) -> InvoiceWorkflowState:
    graph = _build_langgraph_workflow(generator, sender)
    initial_state: InvoiceWorkflowState = {"invoice": invoice, "today": today}

    if graph is None:
        return _run_sequential_workflow(initial_state, generator, sender)

    return graph.invoke(initial_state)


def _build_langgraph_workflow(generator: EmailGenerator, sender: EmailSender) -> Any | None:
    try:
        from langgraph.graph import END, StateGraph
    except Exception:
        return None

    def decide_node(state: InvoiceWorkflowState) -> InvoiceWorkflowState:
        state["decision"] = decide_escalation(state["invoice"], state.get("today"))
        return state

    def route_after_decision(state: InvoiceWorkflowState) -> str:
        decision = state["decision"]
        if decision.stage == 0:
            return "skip"
        if decision.requires_manual_review:
            return "escalate"
        return "generate"

    def skip_node(state: InvoiceWorkflowState) -> InvoiceWorkflowState:
        state["draft"] = None
        state["subject"] = None
        state["body"] = None
        state["status"] = SendStatus.SKIPPED
        state["reason"] = "Invoice is not overdue."
        state["generation_method"] = "NO_EMAIL"
        return state

    def escalate_node(state: InvoiceWorkflowState) -> InvoiceWorkflowState:
        state["draft"] = None
        state["subject"] = None
        state["body"] = None
        state["status"] = SendStatus.ESCALATED
        state["reason"] = "Invoice is over 30 days overdue; flagged for finance/legal review."
        state["generation_method"] = "NO_EMAIL_ESCALATED"
        return state

    def generate_node(state: InvoiceWorkflowState) -> InvoiceWorkflowState:
        draft = generator.generate(state["invoice"], state["decision"])
        status = sender.send(draft)
        state["draft"] = draft
        state["subject"] = draft.subject
        state["body"] = draft.body
        state["status"] = status
        state["generation_method"] = generator.last_generation_method
        state["reason"] = (
            "Email generated and logged in dry-run mode."
            if status == SendStatus.DRY_RUN
            else "Email sent."
        )
        return state

    workflow = StateGraph(InvoiceWorkflowState)
    workflow.add_node("decide", decide_node)
    workflow.add_node("skip", skip_node)
    workflow.add_node("escalate", escalate_node)
    workflow.add_node("generate", generate_node)
    workflow.set_entry_point("decide")
    workflow.add_conditional_edges(
        "decide",
        route_after_decision,
        {"skip": "skip", "escalate": "escalate", "generate": "generate"},
    )
    workflow.add_edge("skip", END)
    workflow.add_edge("escalate", END)
    workflow.add_edge("generate", END)
    return workflow.compile()


def _run_sequential_workflow(
    state: InvoiceWorkflowState,
    generator: EmailGenerator,
    sender: EmailSender,
) -> InvoiceWorkflowState:
    invoice = state["invoice"]
    decision = decide_escalation(invoice, state.get("today"))
    state["decision"] = decision

    if decision.stage == 0:
        state["draft"] = None
        state["subject"] = None
        state["body"] = None
        state["status"] = SendStatus.SKIPPED
        state["reason"] = "Invoice is not overdue."
        state["generation_method"] = "NO_EMAIL"
        return state

    if decision.requires_manual_review:
        state["draft"] = None
        state["subject"] = None
        state["body"] = None
        state["status"] = SendStatus.ESCALATED
        state["reason"] = "Invoice is over 30 days overdue; flagged for finance/legal review."
        state["generation_method"] = "NO_EMAIL_ESCALATED"
        return state

    draft = generator.generate(invoice, decision)
    status = sender.send(draft)
    state["draft"] = draft
    state["subject"] = draft.subject
    state["body"] = draft.body
    state["status"] = status
    state["generation_method"] = generator.last_generation_method
    state["reason"] = (
        "Email generated and logged in dry-run mode."
        if status == SendStatus.DRY_RUN
        else "Email sent."
    )
    return state
