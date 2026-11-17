from pathlib import Path

import pytest


def pytest_configure(config):
    """Print an identifiable header when pytest starts.

    This hook displays real artifacts from module 03:
    - Forked /deploy-check skill at .claude/skills/deploy-check/SKILL.md
    - context: fork isolates output from main session
    - allowed-tools restricted to read-only: [Read, Grep, Glob, Bash(git diff)]
    - Validator evidence: valid_output.txt contains OK
    """
    print()
    print("=" * 80)
    print("  MODULE 03: FORKED /DEPLOY-CHECK SKILL")
    print("=" * 80)
    print("  Skill File:      .claude/skills/deploy-check/SKILL.md")
    print("  Context:         fork (isolated session, keeps verbose checks out of main)")
    print("  Allowed-Tools:   [Read, Grep, Glob, Bash(git diff)] — read-only only")
    print("  Purpose:         Pre-deployment validation without main session pollution")
    print("  Pattern:         Branching Reality — investigate in fork, return results to main")
    print()
    print("  Validator Evidence:")
    print("    • valid_output.txt: OK")
    print("=" * 80)
    print()


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent
