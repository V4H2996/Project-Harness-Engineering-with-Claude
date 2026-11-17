"""Shared pytest fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def pytest_configure(config):
    """Print an identifiable header when pytest starts.

    This hook displays real artifacts from the orchestration system:
    - WarmStore.defects_since() query: SELECT * FROM defects WHERE ts > ? ORDER BY ts DESC LIMIT ?
    - STALE_RESUME_THRESHOLD_MINUTES: 30 (from shift_monitor/recovery.py:20)
    - Indexed query source: shift_monitor/warm.py:75-86
    """
    print()
    print("=" * 70)
    print("  ORCHESTRATION SYSTEM TEST SUITE — Multi-Shift Quality Monitoring")
    print("=" * 70)
    print("  WarmStore Query:        SELECT * FROM defects WHERE ts > ? ORDER BY ts DESC LIMIT ?")
    print("  Query Location:         shift_monitor/warm.py:75-86 (idx_defects_ts index)")
    print("  Stale Threshold:        STALE_RESUME_THRESHOLD_MINUTES = 30 from recovery.py:20")
    print("  Threshold Rationale:    ~1/16 of 8-hour shift; ensures same shift's working set")
    print("=" * 70)
    print()


@pytest.fixture(scope="session")
def defect_rows() -> list[dict[str, Any]]:
    with (FIXTURES_DIR / "defects.json").open() as f:
        rows: list[dict[str, Any]] = json.load(f)
    return rows


@pytest.fixture(scope="session")
def recorded_shift_c_response() -> dict[str, Any]:
    with (FIXTURES_DIR / "recorded_responses" / "shift_C_2026-04-30.json").open() as f:
        payload: dict[str, Any] = json.load(f)
    return payload
