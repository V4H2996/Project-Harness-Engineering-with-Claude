---
name: deploy-check
description: Run pre-deployment safety checks before shipping to production.
context: fork
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(git diff)
---

# Deploy Check Skill

Use this skill in a forked session to run pre-deployment checks without cluttering your main conversation. Keeping verbose check output out of the main session is the goal — the fork isolates the discovery work.

Context: fork is a Claude Code product feature analogous to the Branching Reality pattern — you get an isolated working set to investigate, then return to the main session with results.

Personal customization: install your own forked skills at `~/.claude/skills/` for project-specific checks.

Skill vs CLAUDE.md: A skill is on-demand and forked, loaded only when you invoke it. CLAUDE.md is always-loaded and applies to every session. Use a skill for task-specific checks like deploy verification; use CLAUDE.md for universal standards that apply in every session.

## Pre-Deployment Checks

### Check: Dependency Vulnerability Scan
- detect: Run `npm audit` or `pip-audit` and scan the output for high/critical vulnerabilities.
- pass: Zero high or critical severity findings.
- fail: One or more high or critical vulnerabilities detected.

### Check: Test Suite Pass Rate
- detect: Run the test suite and review the summary line for failures.
- pass: All tests green, zero failures.
- fail: Any test fails or errors.

### Check: Build Artifact Integrity
- detect: Verify the build output directory exists and contains the expected entrypoint file.
- pass: Build artifact present and non-empty.
- fail: Missing or empty build artifact.

## Decision Rubric

Use this skill when you need a focused, task-specific deployment review in a forked session. CLAUDE.md is always-loaded and universal — use it for standards that apply to every session, not just deploy checks.