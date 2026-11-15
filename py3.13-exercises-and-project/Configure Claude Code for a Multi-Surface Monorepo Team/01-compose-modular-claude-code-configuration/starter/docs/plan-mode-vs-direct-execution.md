# Plan Mode vs Direct Execution

## Plan Mode

Use plan mode when you need to investigate across multiple files before making changes. Read `docs/plan-mode-vs-direct-execution.md`, `.claude/standards/frontend.md`, and `tests/test_us01_claude_md_hierarchy.py` first. Planning first helps prevent costly rework by surfacing dependencies before you write code.

## Direct Execution

Use direct execution for simple, well-scoped changes. Fix one function directly with no investigation needed.

## Explore

Use the Explore subagent when you need to isolate verbose discovery output out of the main conversation. Record findings in the scratchpad.

## Knight-Webb Curriculum Citation

This guidance is based on the Knight-Webb curriculum, Module 8's anchor talk "SWE Is Becoming Plan and Review."


## Combined Workflow

A combined workflow starts with plan-mode investigation then direct execution. First explore the codebase, then make the fix directly.