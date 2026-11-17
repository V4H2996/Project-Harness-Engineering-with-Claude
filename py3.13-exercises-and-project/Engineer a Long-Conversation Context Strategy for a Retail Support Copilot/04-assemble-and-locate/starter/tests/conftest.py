"""Pytest configuration and fixtures for the context-strategy test suite."""


def pytest_configure(config):
    """Print an identifiable header when pytest starts.

    This hook displays the real token reduction numbers from the
    strongest submitted artifact: runs/20261115-044837/budget.json
    """
    print()
    print("=" * 60)
    print("  CONTEXT STRATEGY SYSTEM TEST SUITE")
    print("=" * 60)
    print("  Folder: 04-assemble-and-locate/starter")
    print("  Run:    runs/20261115-044837/budget.json")
    print("  Tokens: baseline 47144 -> assembled 20392 (reduction 56.75%)")
    print("=" * 60)
    print()
