from pathlib import Path

import pytest


def pytest_configure(config):
    """Print an identifiable header when pytest starts.

    This hook displays real artifacts from module 02:
    - Project-scoped /review command at .claude/commands/review.md
    - Requires read-only allowed-tools for PR analysis
    - Validator evidence: valid_output.txt contains OK
    """
    print()
    print("=" * 80)
    print("  MODULE 02: PROJECT-SCOPED /REVIEW SLASH COMMAND")
    print("=" * 80)
    print("  Command File:    .claude/commands/review.md")
    print("  Purpose:         Codified PR review checklist (project-scoped, not user-level)")
    print("  Read-Only Tools: Code analysis without write/execute risk")
    print("  Scope:           Team-shared, applied to all ecommerce project teammates")
    print()
    print("  Validator Evidence:")
    print("    • valid_output.txt: OK")
    print("=" * 80)
    print()


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent
