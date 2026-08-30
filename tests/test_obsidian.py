"""Phase 9.2 (P4) — Debrief as an Obsidian daily note.

Stable frontmatter (sorted keys → clean vault queries and diffs), idempotent
re-runs (the grill decision: late /fills → recompute + RESEND replaces the
note, never duplicates), and env wiring for OBSIDIAN_DEBRIEF_DIR with a
tiny .env fallback (no new dependency).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from occams.obsidian import debrief_dir, write_debrief_note


def test_writes_daily_note_with_stable_frontmatter(tmp_path) -> None:
    p = write_debrief_note(tmp_path / "debriefs", day="2026-07-06",
                           body="🌙 Debrief 2026-07-06 — active",
                           day_pnl=57.5, equity=50_057.5, floor=48_000.0,
                           status="active")
    assert p == tmp_path / "debriefs" / "2026-07-06.md"   # dir auto-created
    text = p.read_text()
    head, _, body = text.partition("---\n\n")
    # Frontmatter keys are sorted → byte-stable across re-renders.
    keys = [line.split(":")[0] for line in head.splitlines()
            if ":" in line]
    assert keys == sorted(keys)
    assert "type: occams-debrief" in head
    assert "date: 2026-07-06" in head
    # Vault conventions: tagged and backlinked (occams-razor README).
    assert "tags: [occams/debrief, status/active]" in head
    assert 'up: "[[Debriefs]]"' in head
    assert body.startswith("🌙 Debrief")


def test_daily_notes_chain_to_the_previous_day(tmp_path) -> None:
    d = tmp_path / "debriefs"
    write_debrief_note(d, day="2026-07-06", body="day one", status="active")
    p = write_debrief_note(d, day="2026-07-07", body="day two",
                           status="active")
    text = p.read_text()
    assert "[[2026-07-06]]" in text          # chained backwards
    assert "[[Debriefs]]" in text
    # The first note of a run has no predecessor — no phantom link.
    first = (d / "2026-07-06.md").read_text()
    assert "[[2026-07-05]]" not in first


def test_rerun_replaces_the_note_never_duplicates(tmp_path) -> None:
    d = tmp_path / "debriefs"
    write_debrief_note(d, day="2026-07-06", body="provisional (no fills)",
                       status="active")
    write_debrief_note(d, day="2026-07-06", body="final (fills reconciled)",
                       status="active")
    files = list(d.glob("*.md"))
    assert len(files) == 1                       # replaced, not appended
    assert "final (fills reconciled)" in files[0].read_text()
    assert "provisional" not in files[0].read_text()


def test_debrief_dir_reads_env_then_dotenv_then_fails_loud(
        tmp_path, monkeypatch) -> None:
    # 1) OS environment wins.
    monkeypatch.setenv("OBSIDIAN_DEBRIEF_DIR", str(tmp_path / "a"))
    assert debrief_dir(env_file=tmp_path / "nope.env") == tmp_path / "a"

    # 2) Falls back to a .env file when the variable is unset.
    monkeypatch.delenv("OBSIDIAN_DEBRIEF_DIR")
    env = tmp_path / ".env"
    env.write_text("# comment\nTELEGRAM_BOT_TOKEN=\n"
                   f"OBSIDIAN_DEBRIEF_DIR={tmp_path / 'b'}\n")
    assert debrief_dir(env_file=env) == tmp_path / "b"

    # 3) Neither set → loud error naming the P-task.
    with pytest.raises(ValueError, match="P4"):
        debrief_dir(env_file=tmp_path / "nope.env")


def test_note_round_trips_through_the_real_report_builder(tmp_path) -> None:
    from occams.report import debrief
    body = debrief(day="2026-07-06", day_pnl=57.50, equity=50_057.50,
                   floor=48_000.0, target_equity=53_000.0, status="active",
                   fills_logged=True)
    p = write_debrief_note(tmp_path, day="2026-07-06", body=body,
                           status="active")
    text = Path(p).read_text()
    assert "⛽" in text and "+$57.50" in text     # fuel gauge + P&L intact
    assert "/fills" not in text                   # fills logged → no nudge
