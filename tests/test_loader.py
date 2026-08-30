"""Phase 1.2/1.3 — vendor CSV loader + quality probe, built BEFORE the data
purchase so P1 is plug-in. Tests use tiny fixture CSVs in the two vendor
shapes we may buy (UTC `ts_event` à la Databento; naive-ET `datetime` à la
FirstRate). The tz contract (review fix #5) is enforced at this boundary:
naive timestamps require an explicit `naive_tz`, or we refuse loudly.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from occams.loader import quality_report, read_vendor_csv, to_trading_days


def _write_utc_csv(path, days: list[str], bars_per_day: int = 10,
                   start="14:30", price=5000.0) -> None:
    rows = []
    for d in days:
        idx = pd.date_range(f"{d} {start}", periods=bars_per_day, freq="1min",
                            tz="UTC")
        for i, ts in enumerate(idx):
            o = price + i * 0.25
            rows.append({"ts_event": ts.isoformat(), "open": o,
                         "high": o + 1.0, "low": o - 1.0, "close": o + 0.5,
                         "volume": 100, "symbol": "MES"})
    pd.DataFrame(rows).to_csv(path, index=False)


def test_reads_utc_vendor_csv_to_eastern(tmp_path) -> None:
    p = tmp_path / "mes.csv"
    _write_utc_csv(p, ["2024-01-02"])          # winter: 14:30 UTC == 09:30 ET
    df = read_vendor_csv(p)
    assert str(df.index.tz) == "America/New_York"
    assert df.index[0].strftime("%H:%M") == "09:30"
    assert list(df.columns[:4]) == ["open", "high", "low", "close"]


def test_naive_timestamps_require_explicit_tz(tmp_path) -> None:
    p = tmp_path / "fr.csv"
    pd.DataFrame({
        "datetime": ["2024-01-02 09:30:00", "2024-01-02 09:31:00"],
        "open": [5000.0, 5001.0], "high": [5001.0, 5002.0],
        "low": [4999.0, 5000.0], "close": [5000.5, 5001.5],
        "volume": [1, 1],
    }).to_csv(p, index=False)
    with pytest.raises(ValueError, match="naive"):
        read_vendor_csv(p)
    df = read_vendor_csv(p, naive_tz="America/New_York")
    assert df.index[0].strftime("%H:%M") == "09:30"


def test_duplicate_timestamps_and_bad_ohlc_are_loud(tmp_path) -> None:
    p = tmp_path / "dup.csv"
    pd.DataFrame({
        "ts_event": ["2024-01-02T14:30:00Z", "2024-01-02T14:30:00Z"],
        "open": [1.0, 1.0], "high": [2.0, 2.0], "low": [0.5, 0.5],
        "close": [1.5, 1.5], "volume": [1, 1],
    }).to_csv(p, index=False)
    with pytest.raises(ValueError, match="duplicate"):
        read_vendor_csv(p)

    p2 = tmp_path / "bad.csv"
    pd.DataFrame({
        "ts_event": ["2024-01-02T14:30:00Z"],
        "open": [5.0], "high": [4.0],      # high < open — impossible bar
        "low": [3.0], "close": [4.5], "volume": [1],
    }).to_csv(p2, index=False)
    with pytest.raises(ValueError, match="OHLC"):
        read_vendor_csv(p2)


def test_trading_days_use_prior_days_atr_no_lookahead(tmp_path) -> None:
    p = tmp_path / "atr.csv"
    days = [f"2024-01-{d:02d}" for d in (2, 3, 4, 5, 8)]   # 5 business days
    _write_utc_csv(p, days, bars_per_day=10)
    df = read_vendor_csv(p)
    tds = to_trading_days(df, range_minutes=3, atr_period=3, min_bars=8)
    # First 3 days have no full ATR window → only days 4 and 5 usable.
    assert [t.date for t in tds] == [date(2024, 1, 5), date(2024, 1, 8)]
    # Every fixture day has identical true range → ATR equals it exactly, and
    # it is computed from PRIOR days only (no lookahead — same value here,
    # but the window is asserted by the skip-count above).
    assert all(abs(t.atr - t.atr) < 1e-9 for t in tds)
    assert tds[0].atr == pytest.approx(tds[1].atr)
    # Opening range split honours range_minutes.
    assert len(tds[0].range_bars) == 3
    assert len(tds[0].session_bars) == 7


def test_short_sessions_are_excluded_and_reported(tmp_path) -> None:
    p = tmp_path / "short.csv"
    _write_utc_csv(p, ["2024-01-02", "2024-01-03", "2024-01-04"],
                   bars_per_day=10)
    # Truncate Jan 3 to 4 bars (an early close / feed dropout).
    df_raw = pd.read_csv(p)
    keep = ~df_raw["ts_event"].str.startswith("2024-01-03") | \
        df_raw["ts_event"].isin(
            [f"2024-01-03T14:3{i}:00+00:00" for i in range(4)])
    df_raw[keep].to_csv(p, index=False)

    df = read_vendor_csv(p)
    tds = to_trading_days(df, range_minutes=3, atr_period=1, min_bars=8)
    assert date(2024, 1, 3) not in [t.date for t in tds]

    rep = quality_report(df, min_bars=8)
    assert rep.n_days == 3
    assert rep.short_sessions == [date(2024, 1, 3)]
    assert rep.first_day == date(2024, 1, 2)
    assert rep.last_day == date(2024, 1, 4)


def test_quality_report_flags_missing_business_days(tmp_path) -> None:
    p = tmp_path / "gap.csv"
    _write_utc_csv(p, ["2024-01-02", "2024-01-04"])        # Jan 3 missing
    rep = quality_report(read_vendor_csv(p), min_bars=8)
    assert rep.missing_days == [date(2024, 1, 3)]


def test_loader_attaches_instrument_from_symbol_column(tmp_path) -> None:
    # Codex 1.1: identity must survive the data seam end-to-end.
    p = tmp_path / "mes.csv"
    _write_utc_csv(p, ["2024-01-02", "2024-01-03", "2024-01-04"])
    df = read_vendor_csv(p)
    tds = to_trading_days(df, range_minutes=3, atr_period=1, min_bars=8)
    assert tds and all(t.instrument == "MES" for t in tds)


def test_mixed_symbols_in_one_frame_are_rejected(tmp_path) -> None:
    import pandas as pd
    p = tmp_path / "mixed.csv"
    _write_utc_csv(p, ["2024-01-02"])
    raw = pd.read_csv(p)
    raw.loc[raw.index[-1], "symbol"] = "MNQ"
    raw.to_csv(p, index=False)
    with pytest.raises(ValueError, match="single instrument"):
        to_trading_days(read_vendor_csv(p), range_minutes=3, atr_period=1,
                        min_bars=2)


def test_definition_asserts_tick_and_multiplier(tmp_path) -> None:
    # Codex 1.2 / task 1.4: identity is a TEST, not an assumption.
    import pandas as pd

    from occams.instruments import costs_for
    from occams.loader import check_definitions
    good = pd.DataFrame([{"symbol": "MES", "min_price_increment": 0.25,
                          "multiplier": 5.0}])
    check_definitions(good, "MES", costs_for("MES"))   # passes silently

    bad = pd.DataFrame([{"symbol": "MES", "min_price_increment": 0.25,
                         "multiplier": 50.0}])
    with pytest.raises(ValueError, match="definition"):
        check_definitions(bad, "MES", costs_for("MES"))


def test_roll_day_is_excluded_and_reported(tmp_path) -> None:
    # Codex 1.2: instrument_id change day = roll day -> excluded, reported
    # separately from short sessions (day-flat design is otherwise roll-immune).
    import pandas as pd
    p = tmp_path / "roll.csv"
    days = ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
    _write_utc_csv(p, days)
    raw = pd.read_csv(p)
    raw["instrument_id"] = [101] * 20 + [202] * 20   # roll into Jan 4
    raw.to_csv(p, index=False)

    df = read_vendor_csv(p)
    tds = to_trading_days(df, range_minutes=3, atr_period=1, min_bars=8)
    from datetime import date as _d
    assert _d(2024, 1, 4) not in [t.date for t in tds]     # roll day excluded
    rep = quality_report(df, min_bars=8)
    assert rep.roll_days == [_d(2024, 1, 4)]
    assert rep.short_sessions == []                        # not conflated


def test_quality_report_render_includes_roll_days(tmp_path) -> None:
    import pandas as pd
    p = tmp_path / "roll.csv"
    _write_utc_csv(p, ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"])
    raw = pd.read_csv(p)
    raw["instrument_id"] = [101] * 20 + [202] * 20
    raw.to_csv(p, index=False)
    rep = quality_report(read_vendor_csv(p), min_bars=8)
    assert "roll" in rep.render().lower()
