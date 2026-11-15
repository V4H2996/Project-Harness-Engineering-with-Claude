# Ecommerce Team Configuration

This CLAUDE.md defines project-level conventions for the ecommerce monorepo.

@.claude/standards/frontend.md
@.claude/standards/api.md
@.claude/standards/testing.md
@.claude/standards/database.md

## Scope

Project-level settings live in `.claude/CLAUDE.md` and are shared via version control.
User-level settings live in `~/.claude/` and are personal to each developer. User-level
settings are not shared via version control — they stay local to each machine.

### User-scope example

A user might configure their personal commit message prefix, editor theme, or shell
alias in `~/.claude/CLAUDE.md`. These preferences never appear in the repo.

## Memory

If you are unsure which CLAUDE.md layer is active or why a rule is not applying, run
`/memory` to inspect the current configuration hierarchy and diagnostic state.

## Standards

See `.claude/standards/` for modular coding standards imported above.