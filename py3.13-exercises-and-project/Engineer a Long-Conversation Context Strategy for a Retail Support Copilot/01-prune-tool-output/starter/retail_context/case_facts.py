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
from retail_context.system_prompt import _SYSTEM_PROMPT
from retail_context.transcript import Transcript

# TODO (Exercise 2): Replace with the 12-field contract for the case-facts block.
# Order matters — the to_markdown() rendering uses this order so the block is
# reviewer-readable and the model can re-find a value by name. Each name appears
# verbatim in the extraction system prompt as the JSON key the LLM must return.
#
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


# TODO (Exercise 2): Replace with a dataclass that carries the 12 fields above
# with explicit Python types (str for IDs / status tokens / last4 strings,
# float for refund_amount_usd). Then implement to_markdown(self) -> str so the
# block renders with a level-1 `# Case Facts` header and the four groups
# (Customer / Refund (resolved) / Subscription (resolved) / Payment update
# (active)) as bold inline labels. The rendering is part of the contract:
# fixed key order, bold group labels, reviewer-readable.
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


# The extraction system prompt (strict JSON-only contract for the 12-field case-facts block).
# Imported from system_prompt.py so both files share the same prompt.
from retail_context.system_prompt import _SYSTEM_PROMPT


def _parse_json(raw: str) -> dict[str, Any]:
    raw = raw.strip()
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
    # 1. Build the user message.
    user_message = f"Transcript:\n\n{transcript.full_text}"

    # 2. Call complete_with_system(_SYSTEM_PROMPT, user, model=model,
    #    max_tokens=2048). It returns (text, input_tokens, output_tokens).
    raw_text, input_tokens, output_tokens = complete_with_system(
        _SYSTEM_PROMPT, user_message, model=model, max_tokens=2048
    )

    # 3. Parse the response text with _parse_json (handles a stray ``` fence).
    parsed = _parse_json(raw_text)

    # 4. If a `log_path` was given, write a JSON log.
    if log_path is not None:
        log_path.write_text(
            json.dumps(
                {
                    "model": get_model(),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "raw": parsed,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    # 5. Validate that every name in REQUIRED_FIELDS is present and not None/empty.
    missing = [
        f for f in REQUIRED_FIELDS if f not in parsed or parsed[f] in (None, "")
    ]
    if missing:
        raise CaseFactExtractionError(missing=missing, raw=parsed)

    # 6. Construct and return a CaseFacts with explicit casts.
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
