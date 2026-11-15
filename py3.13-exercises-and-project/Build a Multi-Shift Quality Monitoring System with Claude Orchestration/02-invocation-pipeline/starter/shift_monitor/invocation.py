"""Three invocation shapes.

thin     — prompt only.
rich     — hot state + new defects.
resumed  — prior partial findings + new defects since the last manifest step.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from .state import HotState

InvocationShape = Literal["thin", "rich", "resumed"]


@dataclass(frozen=True)
class Invocation:
    shape: InvocationShape
    prompt: str


def thin(prompt: str) -> Invocation:
    """Return an Invocation with shape="thin" and the prompt unchanged.

    The thin shape is for one-shot calls that don't need any project state.
    """
    return Invocation(shape="thin", prompt=prompt)


def rich(
    role: str, hot_state: HotState, new_defects: Sequence[Mapping[str, Any]]
) -> Invocation:
    """Build a rich prompt that includes:

    - A one-line role framing ("You are the on-call {role} for Northridge Plant 3.")
    - A "## Current hot state" section listing recent_defect_hashes,
      current_shift_summary, active_alerts, threshold_statuses.
    - A "## New defects since last shift" section enumerating each new defect
      (id / ts / shift / component / severity / description).
    - A trailing instruction asking for: Summary, Findings, Recommended
      actions, and an Updated hot state proposal as a JSON block.

    Return an Invocation with shape="rich" and the rendered prompt.
    """
    lines: list[str] = []
    lines.append(f"You are the on-call {role} for Northridge Plant 3.")
    lines.append("")
    lines.append("## Current hot state")
    lines.append(f"- recent_defect_hashes: {', '.join(hot_state.recent_defect_hashes)}")
    lines.append(f"- current_shift_summary: {hot_state.current_shift_summary}")
    lines.append(f"- active_alerts: {', '.join(hot_state.active_alerts)}")
    lines.append(f"- threshold_statuses: {hot_state.threshold_statuses}")
    lines.append("")
    lines.append("## New defects since last shift")
    for d in new_defects:
        lines.append(
            f"- {d.get('id', '?')} | {d.get('ts', '?')} | {d.get('shift', '?')} | "
            f"{d.get('component', '?')} | {d.get('severity', '?')} | {d.get('description', '?')}"
        )
    lines.append("")
    lines.append("## Instruction")
    lines.append("Please provide:")
    lines.append("- Summary")
    lines.append("- Findings")
    lines.append("- Recommended actions")
    lines.append("- An Updated hot state proposal as a JSON block.")
    prompt = "\n".join(lines)
    return Invocation(shape="rich", prompt=prompt)


def resumed(
    session_id: str,
    summary: str,
    latest_message: str,
    prior_steps: Sequence[Mapping[str, Any]],
    new_defects: Sequence[Mapping[str, Any]],
) -> Invocation:
    """Build a resumed prompt with three required sections:

    - "## Prior partial findings" — one line per prior step, showing its
      `name` and a truncated representation of its `payload`.
    - "## Prior summary" — the supplied summary string.
    - "## New defects since last partial step" — enumerate new_defects
      (id / ts / component / severity / description), or "- (none)" if empty.

    Close with the latest_message under "## Latest instruction".

    Return an Invocation with shape="resumed".
    """
    lines: list[str] = []
    lines.append(f"## Session: {session_id}")
    lines.append("")
    lines.append("## Prior partial findings")
    for step in prior_steps:
        name = step.get("name", "?")
        payload = step.get("payload", {})
        payload_str = str(payload)[:80]
        lines.append(f"- {name}: {payload_str}")
    lines.append("")
    lines.append("## Prior summary")
    lines.append(summary)
    lines.append("")
    lines.append("## New defects since last partial step")
    if new_defects:
        for d in new_defects:
            lines.append(
                f"- {d.get('id', '?')} | {d.get('ts', '?')} | {d.get('component', '?')} | "
                f"{d.get('severity', '?')} | {d.get('description', '?')}"
            )
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Latest instruction")
    lines.append(latest_message)
    prompt = "\n".join(lines)
    return Invocation(shape="resumed", prompt=prompt)