"""Case-facts extraction into a persistent block at the top of context.

Extraction is LLM-driven: one Claude call against the full transcript that returns
strict JSON for the 12 required fields. This is commonly called a *scratchpad* — same
concept, different word: a dense structured block that survives compression and is
placed at the top boundary of context so the model can recover transactional facts
without scanning thousands of tokens of narrative.

Missing-field behavior raises `CaseFactExtractionError` listing the gaps — silent
null-fill is forbidden.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from retail_context.client import complete_with_system, get_model
from retail_context.transcript import Transcript

# Required fields (12 total): customer_id; refund_order_id, refund_amount_usd,
# refund_status; subscription_id, subscription_plan, subscription_cancel_reason,
# subscription_status; active_payment_method_last4, new_payment_method_last4,
# payment_update_failure_code, payment_update_status.
REQUIRED_FIELDS: tuple[str, ...] = (
    "customer_id",
    "refund_order_id",
    "refund_amount_usd",
    "refund_status",
    "subscription_id",
    "subscription_plan",
    "subscription_cancel_reason",
    "subscription_status",
    "active_payment_method_last4",
    "new_payment_method_last4",
    "payment_update_failure_code",
    "payment_update_status",
)


@dataclass
class CaseFacts:
    customer_id: str
    refund_order_id: str
    refund_amount_usd: float
    refund_status: str
    subscription_id: str
    subscription_plan: str
    subscription_cancel_reason: str
    subscription_status: str
    active_payment_method_last4: str
    new_payment_method_last4: str
    payment_update_failure_code: str
    payment_update_status: str

    def to_markdown(self) -> str:
        lines = ["# Case Facts", ""]
        lines.append("**Customer**")
        lines.append(f"- customer_id: {self.customer_id}")
        lines.append("")
        lines.append("**Refund (resolved)**")
        lines.append(f"- refund_order_id: {self.refund_order_id}")
        lines.append(f"- refund_amount_usd: {self.refund_amount_usd}")
        lines.append(f"- refund_status: {self.refund_status}")
        lines.append("")
        lines.append("**Subscription (resolved)**")
        lines.append(f"- subscription_id: {self.subscription_id}")
        lines.append(f"- subscription_plan: {self.subscription_plan}")
        lines.append(f"- subscription_cancel_reason: {self.subscription_cancel_reason}")
        lines.append(f"- subscription_status: {self.subscription_status}")
        lines.append("")
        lines.append("**Payment update (active)**")
        lines.append(f"- active_payment_method_last4: {self.active_payment_method_last4}")
        lines.append(f"- new_payment_method_last4: {self.new_payment_method_last4}")
        lines.append(f"- payment_update_failure_code: {self.payment_update_failure_code}")
        lines.append(f"- payment_update_status: {self.payment_update_status}")
        return "\n".join(lines)


class CaseFactExtractionError(ValueError):
    def __init__(self, missing: list[str], raw: dict[str, Any]):
        super().__init__(f"case-facts extraction missing required fields: {missing}")
        self.missing = missing
        self.raw = raw


_SYSTEM_PROMPT = """You extract case facts from a retail support transcript. Return exactly one JSON object and nothing else — no prose, no markdown, no code fences, no preamble, no closing remarks.

Keys (all 12 required, exact names, exact types):
- customer_id: string — the customer's account ID
- refund_order_id: string — order id of the refunded order
- refund_amount_usd: number — refund amount in US dollars (e.g., 22.14), not a string
- refund_status: string — status token of the refund issue, verbatim
- subscription_id: string — the subscription id
- subscription_plan: string — the subscription plan name
- subscription_cancel_reason: string — reason for cancellation, verbatim
- subscription_status: string — status token of the subscription issue, verbatim
- active_payment_method_last4: string — last 4 digits of the card on file, zero-padded (e.g., "4242")
- new_payment_method_last4: string — last 4 digits of the card being added, zero-padded (e.g., "7782")
- payment_update_failure_code: string — gateway failure code verbatim (e.g., AVS_MISMATCH), null if none
- payment_update_status: string — status token of the payment-update ISSUE (not the card attempt). Since the payment-update segment is still active/open in the transcript, this is "in_progress", not "failed". The card attempt failed, but the issue itself remains in progress.

Rules:
- Preserve identifiers, amounts, and status tokens exactly as written in the transcript.
- Distinguish payment_update_failure_code (the card/gateway failure: AVS_MISMATCH) from payment_update_status (the overall issue status: in_progress because the issue is still active).
- If a fact is not stated in the transcript, set its value to null. Do not infer, guess, or fill in values.
- Output must be valid JSON and contain every one of the 12 keys above."""


def _parse_json(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if not raw:
        raise ValueError("LLM returned empty response; cannot parse JSON.")
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.rstrip().endswith("```"):
            raw = raw.rsplit("```", 1)[0]
    return json.loads(raw)


def extract(
    transcript: Transcript,
    *,
    model: str | None = None,
    log_path: Path | None = None,
) -> CaseFacts:
    # 1. User message carries the full transcript.
    user = f"Transcript:\n\n{transcript.full_text}"

    # 2. Single Claude call: system prompt + transcript.
    text, input_tokens, output_tokens = complete_with_system(
        _SYSTEM_PROMPT, user, model=model, max_tokens=2048
    )

    # 3. Parse (strips a stray ``` fence if the model adds one).
    parsed = _parse_json(text)

    # 4. Audit log: model name + usage + raw parsed dict.
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            json.dumps(
                {
                    "model": get_model(),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "raw": parsed,
                },
                indent=2,
            )
        )

    # 5. Validate: all required fields present, non-null, non-empty.
    missing = [
        name
        for name in REQUIRED_FIELDS
        if name not in parsed or parsed[name] is None or parsed[name] == ""
    ]
    if missing:
        raise CaseFactExtractionError(missing=missing, raw=parsed)

    # 6. Construct CaseFacts with explicit type casts.
    return CaseFacts(
        customer_id=str(parsed["customer_id"]),
        refund_order_id=str(parsed["refund_order_id"]),
        refund_amount_usd=float(parsed["refund_amount_usd"]),
        refund_status=str(parsed["refund_status"]),
        subscription_id=str(parsed["subscription_id"]),
        subscription_plan=str(parsed["subscription_plan"]),
        subscription_cancel_reason=str(parsed["subscription_cancel_reason"]),
        subscription_status=str(parsed["subscription_status"]),
        active_payment_method_last4=str(parsed["active_payment_method_last4"]),
        new_payment_method_last4=str(parsed["new_payment_method_last4"]),
        payment_update_failure_code=str(parsed["payment_update_failure_code"]),
        payment_update_status=str(parsed["payment_update_status"]),
    )


def to_dict(facts: CaseFacts) -> dict[str, Any]:
    return asdict(facts)