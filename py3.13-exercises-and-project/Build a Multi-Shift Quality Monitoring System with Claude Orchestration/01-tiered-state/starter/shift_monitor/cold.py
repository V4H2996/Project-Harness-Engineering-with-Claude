"""Cold tier: monthly Markdown summaries derived deterministically from the warm tier."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .warm import WarmStore


@dataclass
class ColdStore:
    store: WarmStore
    cold_dir: Path

    def write_monthly_summary(self, year: int, month: int) -> Path:
        self.cold_dir.mkdir(parents=True, exist_ok=True)
        target = self.cold_dir / f"{year:04d}-{month:02d}.md"

        total = self.store.count_for_month(year, month)
        top = self.store.top_components_for_month(year, month, n=3)

        lines: list[str] = []
        lines.append(f"# {year:04d}-{month:02d}")
        lines.append("")
        lines.append(f"Total defects: {total}")
        lines.append("")
        lines.append("## Top components")
        for component, count in top:
            lines.append(f"- {component}: {count} defect{'s' if count != 1 else ''}")
        lines.append("")

        target.write_text("\n".join(lines), encoding="utf-8")
        return target