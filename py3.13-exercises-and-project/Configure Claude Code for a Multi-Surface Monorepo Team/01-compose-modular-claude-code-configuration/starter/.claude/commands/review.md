---
description: Review code changes for quality and standards compliance.
argument-hint: <file-path or directory>
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(git diff)
---

# Review Command

Review the specified file or directory against team coding standards.

## Must Report vs Skip

You must-report: security vulnerabilities, broken tests, missing type annotations.
You must flag: any change that introduces a new dependency without approval.
Skip: generated files, lockfile changes, documentation-only edits.
Do not report: pre-existing issues not touched by this change.
Ignore: vendor/ and node_modules/ directories.

## Input / Output Examples

Input: `src/components/Cart/Cart.tsx`
Output: "3 issues found: missing prop types on CartItem, unused import, missing test file."

Input: `src/api/orders/handler.ts`
Output: "Pass: all endpoints have input validation and error handling."

## Interview Pattern

Ask clarifying questions before reviewing:
1. What is the intended behavior change?
2. Are there edge cases you already handled?
3. Do you want a full review or just a quick sanity check?

## Interacting vs Independent Issues

Bundle interacting issues into a single message — for example, a missing type import and the resulting type error are interacting and should be reported together.

Handle independent issues sequentially — one at a time — so the user can address each separately without confusion.