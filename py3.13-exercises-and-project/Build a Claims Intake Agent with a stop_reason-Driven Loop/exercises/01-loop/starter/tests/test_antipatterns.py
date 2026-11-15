"""Anti-pattern audit.

Verifies, by static AST analysis, that the agentic loop does NOT:
- use string-membership tests against text content to drive control flow
- use an integer-literal iteration cap as its primary stopping mechanism
- omit reference to `stop_reason` as the loop-breaking signal

And that the package broadly does not branch on `claim_type` equality
outside of the tool-schema definitions and the cost-estimate module.

Each test parses the relevant file with `ast` and walks the tree. There are
no runtime imports of claims_intake here — the audit is static, so it works
even if loop.py / tools.py do not run end-to-end.
"""

from __future__ import annotations

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "claims_intake"
LOOP_PY = PKG / "loop.py"


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _has_stop_reason_reference(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "stop_reason":
            return True
        if isinstance(node, ast.Name) and node.id == "stop_reason":
            return True
    return False


def _while_exits_on_stop_reason(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            body_text = "\n".join(ast.unparse(stmt) for stmt in node.body)
            has_stop_reason = "stop_reason" in body_text
            has_exit = "return" in body_text or "raise" in body_text
            if has_stop_reason and has_exit:
                return True
    return False


# ---------------------------------------------------------------------------
# Anti-pattern 1 — no string-membership tests against assistant text in the loop
# ---------------------------------------------------------------------------
def test_no_string_membership_against_text_in_loop() -> None:
    """No `"some_token" in <something>` expressions in loop.py.

    Heuristic: any `ast.Compare` node using `ast.In` whose `left` operand is a
    string `ast.Constant` is flagged. The loop has no legitimate reason to test
    for the presence of a magic string inside the model's output — that would be
    natural-language-driven control flow.
    """
    tree = _parse(LOOP_PY)
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            if any(isinstance(op, ast.In) for op in node.ops):
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                    offenders.append(ast.unparse(node))
    assert not offenders, (
        "Found string-membership tests against text in loop.py "
        "(natural-language control flow):\n" + "\n".join(offenders)
    )


# ---------------------------------------------------------------------------
# Anti-pattern 2 — no integer-literal iteration cap as the primary stop mechanism
# ---------------------------------------------------------------------------
def test_no_integer_literal_iteration_cap_in_loop() -> None:
    """No `for _ in range(<int literal>)` and no `while <var> < <int literal>` in loop.py.

    Token/wall-clock/config-sourced budgets are explicitly allowed because they
    read their cap from a `Budget` instance (an attribute access or a function
    arg), not from a literal. If you need a cap, pass it in.
    """
    tree = _parse(LOOP_PY)
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            iter_node = node.iter
            if (
                isinstance(iter_node, ast.Call)
                and isinstance(iter_node.func, ast.Name)
                and iter_node.func.id == "range"
                and any(
                    isinstance(a, ast.Constant) and isinstance(a.value, int)
                    for a in iter_node.args
                )
            ):
                offenders.append(ast.unparse(node))
        if isinstance(node, ast.While):
            if isinstance(node.test, ast.Compare):
                if any(
                    isinstance(c, ast.Constant) and isinstance(c.value, int)
                    for c in node.comparators
                ):
                    offenders.append(ast.unparse(node))
    assert not offenders, (
        "Found integer-literal iteration cap in loop.py — use a Budget instead:\n"
        + "\n".join(offenders)
    )


# ---------------------------------------------------------------------------
# Positive evidence — stop_reason is the value that breaks the while loop
# ---------------------------------------------------------------------------
def test_stop_reason_is_loop_control() -> None:
    """loop.py references `stop_reason` AND a `while` loop exits via return/raise on it."""
    tree = _parse(LOOP_PY)
    if not _has_stop_reason_reference(tree):
        raise AssertionError(
            "loop.py does not reference `stop_reason` — it must be the loop-breaking signal."
        )
    if not _while_exits_on_stop_reason(tree):
        raise AssertionError(
            "No `while` loop body mentions both `stop_reason` and an exit "
            "(`return`/`raise`). The loop must exit on stop_reason."
        )


# ---------------------------------------------------------------------------
# Decision-tree-in-Python — no `if claim_type == "..."` branches in the package
# ---------------------------------------------------------------------------
def test_no_claim_type_equality_branching_in_package() -> None:
    """Decision logic about claim type lives in the model, not in Python.

    tools.py is exempt (it defines the enum in input_schema).
    pricing.py is exempt (it may map claim_type to per-queue cost weights).
    """
    skip_names = {"tools.py", "pricing.py", "__init__.py"}
    offenders: list[str] = []
    for path in sorted(PKG.rglob("*.py")):
        if path.name in skip_names:
            continue
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare) and ast.Eq in node.ops:
                left = node.left
                is_claim_type = (
                    (isinstance(left, ast.Name) and left.id == "claim_type")
                    or (isinstance(left, ast.Attribute) and left.attr == "claim_type")
                )
                if is_claim_type and any(
                    isinstance(c, ast.Constant) and isinstance(c.value, str)
                    for c in node.comparators
                ):
                    rel = path.relative_to(PKG.parents[1])
                    offenders.append(f"{rel}:{node.lineno}: {ast.unparse(node)}")
    assert not offenders, (
        "Found `claim_type == \"...\"` branching outside of tool schemas / pricing — "
        "move the decision into the model via tool calls:\n" + "\n".join(offenders)
    )