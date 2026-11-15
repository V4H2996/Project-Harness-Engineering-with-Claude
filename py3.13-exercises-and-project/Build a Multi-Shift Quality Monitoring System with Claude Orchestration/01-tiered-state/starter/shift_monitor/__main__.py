"""Command-line entry point: python -m shift_monitor --shift C --warm-db ..."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shift_monitor.warm import WarmStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="shift_monitor",
        description="Multi-Shift Quality Monitoring — warm-tier inspection.",
    )
    parser.add_argument("--shift", required=True, help="Shift identifier (e.g., C)")
    parser.add_argument(
        "--warm-db",
        required=True,
        help="Path to the SQLite warm database file.",
    )
    parser.add_argument(
        "--since",
        required=True,
        help="ISO timestamp; return defects recorded after this time.",
    )
    parser.add_argument(
        "--recorded-response",
        required=True,
        help="JSON file containing recorded defect rows to insert.",
    )
    args = parser.parse_args(argv)

    store = WarmStore(Path(args.warm_db))
    store.initialize()

    with open(args.recorded_response, encoding="utf-8") as f:
        rows = json.load(f)
    store.insert_many(rows)

    defects = store.defects_since(args.since)
    print(f"Shift {args.shift}: {len(defects)} defect(s) since {args.since}")
    for d in defects:
        print(
            f"  {d['ts']}  {d['component']}  {d['severity']}  {d['id']}  {d['description']}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())