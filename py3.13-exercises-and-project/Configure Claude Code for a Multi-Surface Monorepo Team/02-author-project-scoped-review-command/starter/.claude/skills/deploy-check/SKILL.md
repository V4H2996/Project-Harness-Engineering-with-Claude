---
name: deploy-check
description: Pre-deployment verification skill that runs read-only checks before deployment in a forked context
context: fork
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(git diff:*)
  - Bash(git log:*)
---

# /deploy-check — pre-deployment verification

Run this skill in a fork before deploying to verify the change is safe. All tools are read-only; this skill never writes to the repository.

## Pre-deployment checks

### Check 1 — Dependency changes

- Detect how to check: scan `git diff` for changes to `package.json`, `pyproject.toml`, or `go.mod`
- Pass: no dependency version changes, or all changed dependencies are in the approved allowlist
- Fail: any dependency version bump not reviewed for breaking changes or security advisories

### Check 2 — Test coverage

- Detect how to check: confirm every changed source file has a corresponding test file change
- Pass: all source changes include matching test updates
- Fail: source files changed without any test coverage update

### Check 3 — Breaking API changes

- Detect how to check: search for changes to public function signatures, exported types, or DB column names
- Pass: no public API surface changes, or all changes are backward-compatible
- Fail: any breaking change to public APIs without a migration plan

## Rationale

The goal of running this skill in a fork is to keep verbose discovery output out of the main session context window. By isolating the pre-deployment investigation to a forked context, the main conversation stays focused on the deployment decision rather than the raw check output.

A fork is a Claude Code product feature analogous to the Branching Reality pattern: it lets you explore a codebase change in isolation without affecting the primary session state.

## Personal customization

This skill is project-scoped and lives in `.claude/skills/deploy-check/`. Team members can layer personal preferences by copying skills to `~/.claude/skills/` in their home directory — personal copies do not affect teammates.

## Skill vs CLAUDE.md

A skill is on-demand and forked: it loads only when invoked and runs in an isolated context. CLAUDE.md is always-loaded and universal: it applies to every session. Use a skill like deploy-check for task-specific, occasional verification; rely on CLAUDE.md for standards that should govern every conversation.