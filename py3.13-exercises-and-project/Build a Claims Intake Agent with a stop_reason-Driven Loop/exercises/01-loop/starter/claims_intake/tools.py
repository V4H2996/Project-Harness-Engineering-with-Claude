"""Tool schemas and dispatcher.

Seven tools, registered with Anthropic tool-use shape. The dispatcher returns
serialized JSON strings to be wrapped as `tool_result` content. Errors follow
the "Graceful Tool Failure" shape:

    {"is_error": true,
     "error_category": "transient"|"permanent",
     "is_retryable": bool,
     "message": "..."}

Errors are never raised to the loop.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from claims_intake.session import ClaimSession

CLAIM_TYPES = ["property_damage", "theft", "liability", "auto"]
SEVERITIES = ["low", "medium", "high"]

# ---------------------------------------------------------------------------
# Schemas — passed verbatim to the Anthropic Messages API as the `tools` arg.
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "lookup_policy",
        "description": "Look up an insurance policy by policy_id to verify coverage and holder details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_id": {
                    "type": "string",
                    "description": "The policy ID to look up.",
                },
            },
            "required": ["policy_id"],
        },
    },
    {
        "name": "record_claim_fact",
        "description": "Record one normalized fact about the claim (e.g. incident_date, location, items_lost).",
        "input_schema": {
            "type": "object",
            "properties": {
                "field": {
                    "type": "string",
                    "description": "The fact field name.",
                },
                "value": {
                    "type": "string",
                    "description": "The fact value.",
                },
            },
            "required": ["field", "value"],
        },
    },
    {
        "name": "classify_claim",
        "description": "Commit to a claim type with a confidence score and rationale.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_type": {
                    "type": "string",
                    "enum": CLAIM_TYPES,
                    "description": "The classified claim type.",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence score between 0 and 1.",
                },
                "rationale": {
                    "type": "string",
                    "description": "Reasoning for the classification.",
                },
            },
            "required": ["claim_type", "confidence", "rationale"],
        },
    },
    {
        "name": "assess_severity",
        "description": "Commit to a severity bucket with a rationale.",
        "input_schema": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": SEVERITIES,
                    "description": "The severity bucket.",
                },
                "rationale": {
                    "type": "string",
                    "description": "Reasoning for the severity assessment.",
                },
            },
            "required": ["severity", "rationale"],
        },
    },
    {
        "name": "request_clarification",
        "description": "Ask the claimant a clarifying question to resolve ambiguity between claim types.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The clarifying question to ask.",
                },
                "ambiguity_between": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": CLAIM_TYPES,
                    },
                    "description": "The claim types between which the model is uncertain.",
                },
            },
            "required": ["question", "ambiguity_between"],
        },
    },
    {
        "name": "route_to_adjuster",
        "description": "Route the classified claim to the appropriate adjuster queue (terminal action).",
        "input_schema": {
            "type": "object",
            "properties": {
                "queue": {
                    "type": "string",
                    "enum": CLAIM_TYPES,
                    "description": "The adjuster queue to route to.",
                },
                "claim_summary": {
                    "type": "string",
                    "description": "A short summary of the claim for routing.",
                },
            },
            "required": ["queue", "claim_summary"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate the claim to a human adjuster with a structured summary (terminal action).",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Why the claim needs human review.",
                },
                "structured_summary": {
                    "type": "object",
                    "description": "Structured summary of the case for the human adjuster.",
                },
            },
            "required": ["reason", "structured_summary"],
        },
    },
]


# ---------------------------------------------------------------------------
# Errors — Graceful Tool Failure shape
# ---------------------------------------------------------------------------


def _err(category: str, retryable: bool, message: str) -> str:
    return json.dumps(
        {
            "is_error": True,
            "error_category": category,
            "is_retryable": retryable,
            "message": message,
        }
    )


def _ok(payload: dict[str, Any]) -> str:
    return json.dumps(payload)


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def _t_lookup_policy(session: ClaimSession, inp: dict[str, Any]) -> str:
    policy_id = inp.get("policy_id")
    if not isinstance(policy_id, str):
        return _err("permanent", False, "policy_id must be a string")
    policy = session.policies.get(policy_id)
    if policy is None:
        return _err("permanent", False, f"policy {policy_id} not found")
    return _ok(policy)


def _t_record_claim_fact(session: ClaimSession, inp: dict[str, Any]) -> str:
    field = inp.get("field")
    value = inp.get("value")
    if not isinstance(field, str) or not field:
        return _err("permanent", False, "field must be a non-empty string")
    if not isinstance(value, str) or not value:
        return _err("permanent", False, "value must be a non-empty string")
    session.case_facts[field] = value
    return _ok({"recorded": True, "field": field, "value": value})


def _t_classify_claim(session: ClaimSession, inp: dict[str, Any]) -> str:
    claim_type = inp.get("claim_type")
    confidence = inp.get("confidence")
    rationale = inp.get("rationale")
    if claim_type not in CLAIM_TYPES:
        return _err("permanent", False, f"claim_type must be one of {CLAIM_TYPES}")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not (0 <= confidence <= 1):
        return _err("permanent", False, "confidence must be a number between 0 and 1")
    if not isinstance(rationale, str) or not rationale:
        return _err("permanent", False, "rationale must be a non-empty string")
    session.classification = {
        "claim_type": claim_type,
        "confidence": confidence,
        "rationale": rationale,
    }
    return _ok(session.classification)


def _t_assess_severity(session: ClaimSession, inp: dict[str, Any]) -> str:
    severity = inp.get("severity")
    rationale = inp.get("rationale")
    if severity not in SEVERITIES:
        return _err("permanent", False, f"severity must be one of {SEVERITIES}")
    if not isinstance(rationale, str) or not rationale:
        return _err("permanent", False, "rationale must be a non-empty string")
    session.severity = {"severity": severity, "rationale": rationale}
    return _ok(session.severity)


def _t_request_clarification(session: ClaimSession, inp: dict[str, Any]) -> str:
    question = inp.get("question")
    ambiguity_between = inp.get("ambiguity_between")
    if not isinstance(question, str) or not question:
        return _err("permanent", False, "question must be a non-empty string")
    if not isinstance(ambiguity_between, list) or not all(
        t in CLAIM_TYPES for t in ambiguity_between
    ):
        return _err("permanent", False, f"ambiguity_between must be a list of claim types from {CLAIM_TYPES}")

    question_lower = question.lower()
    matched_reply = None
    for key, reply in session.clarification_responses.items():
        if key.lower() in question_lower:
            matched_reply = reply
            break

    session.clarifications_asked.append(
        {
            "question": question,
            "ambiguity_between": ambiguity_between,
            "claimant_reply": matched_reply or "NO_RESPONSE",
        }
    )

    return _ok({"claimant_reply": matched_reply if matched_reply is not None else "NO_RESPONSE"})


def _t_route_to_adjuster(session: ClaimSession, inp: dict[str, Any]) -> str:
    if session.terminal_called:
        return _err("permanent", False, "terminal action already called")

    queue = inp.get("queue")
    claim_summary = inp.get("claim_summary")
    if queue not in CLAIM_TYPES:
        return _err("permanent", False, f"queue must be one of {CLAIM_TYPES}")
    if not isinstance(claim_summary, str) or not claim_summary:
        return _err("permanent", False, "claim_summary must be a non-empty string")
    if session.classification is None:
        return _err("permanent", False, "classify_claim must be called before route_to_adjuster")
    if session.severity is None:
        return _err("permanent", False, "assess_severity must be called before route_to_adjuster")

    record = {
        "claim_id": session.claim_id,
        "policy_id": session.policy_id,
        "claim_type": session.classification["claim_type"],
        "severity": session.severity["severity"],
        "confidence": session.classification["confidence"],
        "rationale": session.classification["rationale"],
        "claim_summary": claim_summary,
        "case_facts": dict(session.case_facts),
    }
    session.routing = record

    queue_file = session.run_dir / "queues" / f"{queue}.jsonl"
    _append_jsonl(queue_file, record)

    return _ok({"routed": True, "queue": queue})


def _t_escalate_to_human(session: ClaimSession, inp: dict[str, Any]) -> str:
    if session.terminal_called:
        return _err("permanent", False, "terminal action already called")

    reason = inp.get("reason")
    structured_summary = inp.get("structured_summary")
    if not isinstance(reason, str) or not reason:
        return _err("permanent", False, "reason must be a non-empty string")
    if not isinstance(structured_summary, dict):
        return _err("permanent", False, "structured_summary must be a dict")

    required_keys = [
        "policy_id",
        "root_cause",
        "candidate_claim_types",
        "case_facts",
        "recommended_action",
        "confidence",
    ]
    missing = [k for k in required_keys if k not in structured_summary]
    if missing:
        return _err(
            "permanent", False, f"missing structured_summary fields: {', '.join(missing)}"
        )

    record = {
        "claim_id": session.claim_id,
        "policy_id": session.policy_id,
        "reason": reason,
        **structured_summary,
        "case_facts_at_escalation": dict(session.case_facts),
    }
    session.escalation = record

    esc_file = session.run_dir / "escalations.jsonl"
    _append_jsonl(esc_file, record)

    return _ok({"escalated": True})


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_DISPATCH = {
    "lookup_policy": _t_lookup_policy,
    "record_claim_fact": _t_record_claim_fact,
    "classify_claim": _t_classify_claim,
    "assess_severity": _t_assess_severity,
    "request_clarification": _t_request_clarification,
    "route_to_adjuster": _t_route_to_adjuster,
    "escalate_to_human": _t_escalate_to_human,
}


def make_executor(session: ClaimSession):
    """Return a ToolExecutor callable bound to this session."""

    def execute(name: str, tool_input: dict[str, Any]) -> str:
        handler = _DISPATCH.get(name)
        if handler is None:
            return _err("permanent", False, f"unknown tool: {name}")
        try:
            return handler(session, tool_input)
        except Exception as exc:
            # Defensive: anything raised inside a handler becomes a graceful error,
            # never crashes the loop.
            return _err("transient", True, f"{type(exc).__name__}: {exc}")

    return execute


# Type alias for clarity; the loop only sees a Callable.
Executor = Any


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")