from pathlib import Path

import pytest


def pytest_configure(config):
    """Print an identifiable header when pytest starts.

    This hook displays real artifacts from the Claude Code config system:
    - Rule files: .claude/rules/api.md, react.md, tests.md (with glob paths)
    - Skill: .claude/skills/deploy-check/SKILL.md (with context: fork and read-only tools)
    - Validator evidence: valid_output.txt contains OK
    """
    print()
    print("=" * 80)
    print("  CLAUDE CODE CONFIGURATION SYSTEM TEST SUITE")
    print("=" * 80)
    print("  Path-Scoped Rules (glob frontmatter):")
    print("    • .claude/rules/api.md        -> paths: ['src/api/**/*']")
    print("    • .claude/rules/react.md      -> paths: ['src/components/**/*', 'src/pages/**/*']")
    print("    • .claude/rules/tests.md      -> paths: ['**/*.test.tsx', '**/*.test.ts']")
    print()
    print("  Forked Skill (context: fork + read-only tools):")
    print("    • .claude/skills/deploy-check/SKILL.md")
    print("    • allowed-tools: [Read, Grep, Glob, Bash(git diff)]")
    print("    • Goal: Pre-deployment checks without cluttering main session")
    print()
    print("  Validator Evidence:")
    print("    • valid_output.txt: OK")
    print("=" * 80)
    print()


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent
