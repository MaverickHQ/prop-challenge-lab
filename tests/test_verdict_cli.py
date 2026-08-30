"""occams/verdict_cli.py — the P1 command. Fails CLOSED unless every sealed
input is present: CSVs, vendor definitions (asserted), calendar, PREREG hash.
Uses a project root resolved from the module, not cwd (Codex #3/#4)."""

from __future__ import annotations

import pandas as pd
import pytest

from occams.instruments import costs_for
from occams.verdict_cli import load_instrument, project_root


def _write(dir_, inst, days, with_def=True):
    dir_.mkdir(parents=True, exist_ok=True)
    rows = []
    for d in days:
        idx = pd.date_range(f"{d} 14:30", periods=400, freq="1min", tz="UTC")
        for i, ts in enumerate(idx):
            o = 5000 + i * 0.1
            rows.append({"ts_event": ts.isoformat(), "open": o, "high": o + 1,
                         "low": o - 1, "close": o + 0.5, "volume": 10,
                         "symbol": inst, "instrument_id": 1})
    pd.DataFrame(rows).to_csv(dir_ / f"{inst}.csv", index=False)
    if with_def:
        c = costs_for(inst)
        pd.DataFrame([{"symbol": inst,
                       "min_price_increment": c.tick_size,
                       "multiplier": c.multiplier}]).to_csv(
            dir_ / f"{inst}.definition.csv", index=False)


def test_project_root_is_cwd_independent() -> None:
    root = project_root()
    assert (root / "docs" / "PREREG.md").exists()   # resolves regardless of cwd


def test_missing_definition_fails_closed(tmp_path) -> None:
    days = [f"2024-01-0{i}" for i in (2, 3, 4)]
    _write(tmp_path, "MES", days, with_def=False)
    with pytest.raises(FileNotFoundError, match="definition"):
        load_instrument(tmp_path, "MES", range_minutes=30)


def test_wrong_multiplier_in_definition_is_loud(tmp_path) -> None:
    days = [f"2024-01-0{i}" for i in (2, 3, 4)]
    _write(tmp_path, "MES", days)
    (tmp_path / "MES.definition.csv").write_text(
        "symbol,min_price_increment,multiplier\nMES,0.25,50.0\n")
    with pytest.raises(ValueError, match="definition"):
        load_instrument(tmp_path, "MES", range_minutes=30)


def test_good_inputs_load_and_assert(tmp_path) -> None:
    days = [f"2024-01-{i:02d}" for i in range(2, 12)]
    _write(tmp_path, "MES", days)
    out = load_instrument(tmp_path, "MES", range_minutes=30, atr_period=2,
                          min_bars=8)
    assert out and all(td.instrument == "MES" for td in out)
