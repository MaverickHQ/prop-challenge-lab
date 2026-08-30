"""Debrief → Obsidian daily note (Phase 9.2 / P4).

Writes into the dedicated `occams-razor` vault following its conventions
(see the vault's README): sorted frontmatter with `tags` and an `up:` link
so every note sits one hop from Home, and a previous-day chain link so a
challenge attempt reads like a story walked backwards. Re-runs REPLACE the
day's note (the grill decision: late /fills → recompute + resend).
"""

from __future__ import annotations

import os
from datetime import date as _date
from datetime import timedelta
from pathlib import Path


def write_debrief_note(vault_dir: str | Path, *, day: str, body: str,
                       status: str = "active", **meta) -> Path:
    d = Path(vault_dir)
    d.mkdir(parents=True, exist_ok=True)

    fm = {"date": day, "type": "occams-debrief",
          "tags": f"[occams/debrief, status/{status}]",
          "up": '"[[Debriefs]]"', "status": status, **meta}
    lines = ["---"] + [f"{k}: {fm[k]}" for k in sorted(fm)] + ["---", "", body]

    prev = _previous_note(d, day)
    footer = f"← [[{prev}]] · [[Debriefs]]" if prev else "[[Debriefs]]"
    lines += ["", footer, ""]

    path = d / f"{day}.md"
    path.write_text("\n".join(lines))        # overwrite = idempotent re-run
    return path


def _previous_note(vault_dir: Path, day: str, lookback_days: int = 10
                   ) -> str | None:
    """The most recent existing daily note before `day` (weekends/holidays
    make gaps, so walk back rather than assuming yesterday)."""
    try:
        current = _date.fromisoformat(day)
    except ValueError:
        return None
    for back in range(1, lookback_days + 1):
        candidate = (current - timedelta(days=back)).isoformat()
        if (vault_dir / f"{candidate}.md").exists():
            return candidate
    return None


def debrief_dir(env_file: str | Path = ".env") -> Path:
    """OBSIDIAN_DEBRIEF_DIR from the environment, falling back to a simple
    .env file parse (no dependency). Unset → loud error naming the P-task."""
    value = os.environ.get("OBSIDIAN_DEBRIEF_DIR")
    if not value:
        env_path = Path(env_file)
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("OBSIDIAN_DEBRIEF_DIR="):
                    value = line.split("=", 1)[1].strip()
                    break
    if not value:
        raise ValueError(
            "OBSIDIAN_DEBRIEF_DIR is not set (P4): export it or add it to "
            ".env — it should point at the vault's '10 - Debriefs' folder")
    return Path(value)
