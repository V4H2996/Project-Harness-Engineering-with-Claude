---
description: Team PR review command that applies path-scoped rules and standards to a diff
argument-hint: PR ref, diff range, or file path to review
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(gh pr view:*)
  - Bash(gh pr checks:*)
---

# /review — team PR review

You are reviewing the diff identified by `$ARGUMENTS` against this repository's conventions. Apply the path-scoped rules in `.claude/rules/` (they auto-load based on the files touched) and the shared standards in `.claude/standards/`.

## Phase 1 — Interview pattern

The reviewer agent should ask clarifying questions BEFORE reporting findings whenever the author's intent is ambiguous.

Why this matters: without an interview step, the reviewer commits to a confidently-wrong verdict on ambiguous changes — e.g. a refactor that touched no test files. The author then has to argue against a "no test coverage" finding when the behavior was already covered upstream. The interview pattern asks first.

Name at least three concrete trigger conditions where the reviewer should interview rather than report:
- dependency changes (package.json or pyproject.toml diffs)
- public API response shape changes or DB column changes
- refactors with no corresponding test changes
- changes that touch multiple surfaces (API + components + DB) at once

## Phase 2 — Review criteria

The explicit must-report vs. skip taxonomy ensures two teammates running this command on the same PR reach the same verdict.

Must report: at minimum, name categories for bugs (logic errors, missing await, race conditions, off-by-one), security (raw SQL with user input, missing auth, secrets in code, dangerouslySetInnerHTML), convention violations the path-scoped rules catch, breaking changes, and migration safety.

Skip: at minimum, name categories the reviewer should NOT block on — minor formatting (Prettier handles it), naming bikeshed when the name is fine, personal stylistic preferences not encoded in rules/standards, and TODOs that already have tracked tickets.

The skip list is what keeps false positives from destroying author trust.

## Phase 3 — Bundling: interacting vs. independent findings

Interacting findings: those that overlap or affect the same fix. Bundle into ONE detailed message with all context. Example: a missing `await` and a missing transaction wrapper on the same function — the author needs to see them together because the fix changes both lines.

Independent findings: separate functions, separate files, no shared fix. Report SEQUENTIALLY as discrete items so each piece of feedback is actionable.

One-line heuristic: if fixing A changes the code B references, they are interacting; otherwise they are independent and can be reported separately.

## Phase 4 — Output format

For each finding, produce: Severity is `bug` | `security` | `convention` | `breaking`. End with a one-line verdict: `approve`, `comment`, or `request-changes`.

## Examples

**Input**
A PR diff touching `src/api/orders/handler.ts` with two unrelated issues: a handler returning `{ status: 404 }` instead of throwing `ApiError`, and a missing `await` on an async call.

**Output**
Verdict: comment

**Input**
A PR diff touching `src/services/payment.ts` where the refundOrder handler has three issues sharing one fix: missing `await`, no transaction wrapper, and wrong ordering between paymentService and DB writes.

**Output**
Verdict: request-changes