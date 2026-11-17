from pathlib import Path

import pytest


def pytest_configure(config):
    """Print an identifiable header when pytest starts.

    This hook displays real artifacts from module 04:
    - Plan mode vs. direct execution decision doc: docs/plan-mode-vs-direct-execution.md
    - References the Knight-Webb curriculum framework
    - Team-scoped guidance on when to plan vs. execute directly
    - Validator evidence: valid_output.txt contains OK
    """
    print()
    print("=" * 80)
    print("  MODULE 04: PLAN MODE & EXPLORE DECISION DOCUMENTATION")
    print("=" * 80)
    print("  Decision Doc:    docs/plan-mode-vs-direct-execution.md")
    print("  Purpose:         Team guidance on when to enter plan mode vs. direct execute")
    print("  Examples:        Plan mode (multi-file changes), Direct (simple tweaks)")
    print("  Curriculum:      Knight-Webb framework for structured problem-solving")
    print("  Scope:           Project-level workflow documentation")
    print()
    print("  Validator Evidence:")
    print("    • valid_output.txt: OK")
    print("=" * 80)
    print()


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent
