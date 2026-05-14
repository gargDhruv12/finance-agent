from __future__ import annotations

from datetime import date
from typing import Any, TypedDict

from .approval import ApprovalStore
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
    approval_status: str


def run_invoice_workflow(
    invoice: InvoiceRecord,
    generator: EmailGenerator,
    sender: EmailSender,
    today: date | None = None,
    approval_store: ApprovalStore | None = None,
    require_approval: bool = True,
) -> InvoiceWorkflowState:
    graph = _build_langgraph_workflow(generator, sender, approval_store, require_approval)
    initial_state: InvoiceWorkflowState = {"invoice": invoice, "today": today}

    if graph is None:
        return _run_sequential_workflow(initial_state, generator, sender, approval_store, require_approval)

    return graph.invoke(initial_state)


def _build_langgraph_workflow(
    generator: EmailGenerator,
    sender: EmailSender,
    approval_store: ApprovalStore | None,
    require_approval: bool,
) -> Any | None:
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
        state["approval_status"] = "NOT_REQUIRED"
        return state

    def escalate_node(state: InvoiceWorkflowState) -> InvoiceWorkflowState:
        state["draft"] = None
        state["subject"] = None
        state["body"] = None
        state["status"] = SendStatus.ESCALATED
        state["reason"] = "Invoice is over 30 days overdue; flagged for finance/legal review."
        state["generation_method"] = "NO_EMAIL_ESCALATED"
        state["approval_status"] = "MANUAL_REVIEW"
        return state

    def generate_node(state: InvoiceWorkflowState) -> InvoiceWorkflowState:
        draft = generator.generate(state["invoice"], state["decision"])
        approval_status = _approval_status(state["invoice"], draft, approval_store, require_approval)
        if approval_status == "PENDING":
            status = SendStatus.PENDING_APPROVAL
        elif approval_status == "REJECTED":
            status = SendStatus.REJECTED
        else:
            status = sender.send(draft)
        state["draft"] = draft
        state["subject"] = draft.subject
        state["body"] = draft.body
        state["status"] = status
        state["approval_status"] = approval_status
        state["generation_method"] = generator.last_generation_method
        state["reason"] = _reason_for_status(status)
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
    approval_store: ApprovalStore | None,
    require_approval: bool,
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
        state["approval_status"] = "NOT_REQUIRED"
        return state

    if decision.requires_manual_review:
        state["draft"] = None
        state["subject"] = None
        state["body"] = None
        state["status"] = SendStatus.ESCALATED
        state["reason"] = "Invoice is over 30 days overdue; flagged for finance/legal review."
        state["generation_method"] = "NO_EMAIL_ESCALATED"
        state["approval_status"] = "MANUAL_REVIEW"
        return state

    draft = generator.generate(invoice, decision)
    approval_status = _approval_status(invoice, draft, approval_store, require_approval)
    if approval_status == "PENDING":
        status = SendStatus.PENDING_APPROVAL
    elif approval_status == "REJECTED":
        status = SendStatus.REJECTED
    else:
        status = sender.send(draft)
    state["draft"] = draft
    state["subject"] = draft.subject
    state["body"] = draft.body
    state["status"] = status
    state["approval_status"] = approval_status
    state["generation_method"] = generator.last_generation_method
    state["reason"] = _reason_for_status(status)
    return state


def _approval_status(
    invoice: InvoiceRecord,
    draft: EmailDraft,
    approval_store: ApprovalStore | None,
    require_approval: bool,
) -> str:
    if not require_approval:
        return "NOT_REQUIRED"
    if approval_store is None:
        return "PENDING"
    approval_store.ensure_pending(invoice, draft)
    return approval_store.status_for(invoice).status


def _reason_for_status(status: SendStatus) -> str:
    if status == SendStatus.DRY_RUN:
        return "Email generated and logged in dry-run mode."
    if status == SendStatus.SENT:
        return "Email sent through configured SMTP provider."
    if status == SendStatus.PENDING_APPROVAL:
        return "Email generated and queued for finance approval before sending."
    if status == SendStatus.REJECTED:
        return "Email generated but rejected by finance reviewer."
    if status == SendStatus.FAILED:
        return "Email generation completed but sending failed due to missing or invalid SMTP configuration."
    return "Workflow completed."
