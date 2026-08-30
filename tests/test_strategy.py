"""Phase 4 — ORB plan builder + risk manager, tested through build_plan() only.

build_plan(range_bars, params) → DayPlan | NoTrade(reason). Pure: the caller
supplies the opening-range bars and the daily ATR; sizing comes from the ruin
math (fixed risk in dollars ÷ dollar stop distance).
"""

from __future__ import annotations

import pandas as pd

from occams.sim import Costs
from occams.strategy import NoTrade, OrbParams, build_plan

COSTS = Costs(multiplier=5.0, tick_size=0.25, commission_per_side=1.25,
              slippage_ticks=1)


def range_bars(rows: list[tuple[float, float, float, float]]) -> pd.DataFrame:
    idx = pd.date_range("2024-01-02 09:30", periods=len(rows), freq="1min")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx)


def params(**kw) -> OrbParams:
    base = dict(stop_range=0.4, target_r=1.5, risk_usd=200.0, max_trades=1,
                vwap_filter=False)
    base.update(kw)
    return OrbParams(**base)


def test_risk_too_small_for_one_contract_is_no_trade() -> None:
    # height 20 × 2.5 = 50pt stop → $253.75/contract > $200 risk → stand aside.
    bars = range_bars([(5000, 5010, 4990, 5005)])
    plan = build_plan(bars, params=params(stop_range=2.5), costs=COSTS)
    assert isinstance(plan, NoTrade)
    assert "risk" in plan.reason


def test_vwap_filter_arms_only_the_vwap_side() -> None:
    # Range closes well below its VWAP → only the short side stays armed.
    # (Constant volume: volume-weighted == time-weighted, expectation unchanged.)
    bars = range_bars([
        (5010, 5012, 5008, 5011),   # early strength lifts VWAP
        (5008, 5009, 4990, 4991),   # closes weak, far below VWAP
    ])
    bars["volume"] = 100
    plan = build_plan(bars, params=params(vwap_filter=True), costs=COSTS)
    assert plan.buy_stop is None             # long disarmed
    assert plan.sell_stop == 4989.75


def test_sim_never_triggers_a_disarmed_side() -> None:
    from occams.sim import DayPlan, simulate_day
    df = range_bars([(5000, 5020, 4999, 5015)])  # would cross a buy stop
    plan = DayPlan(buy_stop=None, sell_stop=4980.0, stop_dist=8.0,
                   target_dist=12.0, contracts=1)
    assert simulate_day(df, plan, COSTS).trades == []


def test_own_daily_stop_suppresses_further_entries() -> None:
    # Trade 1 loses ≥ the daily stop → trade 2 is never taken even though
    # max_trades=2 and the level re-triggers.
    from occams.sim import DayPlan, simulate_day
    df = range_bars([
        (5004, 5012, 5003, 5011),   # long entry 5010.25 (stop 8 → 5002.25)
        (5010, 5011, 5001, 5003),   # stopped out ≈ −$45/contract
        (5003, 5013, 5002, 5012),   # re-trigger — must be suppressed
        (5012, 5013, 5001, 5002),
    ])
    plan = DayPlan(buy_stop=5010.0, sell_stop=4990.0, stop_dist=8.0,
                   target_dist=12.0, contracts=1, max_trades=2,
                   daily_stop_usd=40.0)
    result = simulate_day(df, plan, COSTS)
    assert len(result.trades) == 1          # second entry suppressed


def test_calendar_blocks_tier1_release_days() -> None:
    from datetime import date

    from occams.calendar import blocked_reason
    events = {date(2026, 1, 28): "FOMC", date(2026, 3, 6): "NFP"}
    assert blocked_reason(date(2026, 1, 28), events) == "FOMC"
    assert blocked_reason(date(2026, 1, 29), events) is None


def test_shipped_calendar_covers_the_data_era() -> None:
    # The seed CSV must span the buyable history (2019→2026, micros era) so
    # backtests and live block the SAME days. FOMC verified from the Fed's
    # own calendar pages 2026-07-04, incl. the 2020 emergency meetings.
    from datetime import date
    from pathlib import Path

    from occams.calendar import load_events
    events = load_events(Path("occams/data/economic_calendar.csv"))
    fomc = [d for d, e in events.items() if e == "FOMC"]
    assert min(fomc) == date(2019, 1, 30)
    assert max(fomc) == date(2026, 12, 9)
    assert len(fomc) >= 69                       # 8/yr + 2020 emergencies
    assert date(2020, 3, 15) in events           # emergency cut — a SUNDAY
    # Scheduled meetings are weekdays; emergencies aren't (2020-03-15 was a
    # Sunday). Weekend entries are harmless to the filter (no RTH session).
    weekday = sum(1 for d in events if d.weekday() < 5)
    assert weekday >= len(events) - 2


def test_opening_range_yields_sized_bracket_plan() -> None:
    # Range high 5010 / low 4990 (height 20) × stop_range 0.4 → stop 8pt.
    # Entries 1 tick beyond the range; sizing from the ruin math.
    bars = range_bars([
        (5000, 5008, 4992, 5005),
        (5005, 5010, 4990, 4998),
    ])
    plan = build_plan(bars, params=params(), costs=COSTS)
    assert plan.buy_stop == 5010.25          # range high + 1 tick
    assert plan.sell_stop == 4989.75         # range low − 1 tick
    assert plan.stop_dist == 8.0             # 0.4 × range height 20
    assert plan.target_dist == 12.0          # 1.5R
    # TRUE dollars-at-risk sizing (Codex 2.3): a stopped contract loses
    # stop 8pt×$5 + exit slip 0.25pt×$5 + $2.50 commissions = $43.75
    # → floor($200 / $43.75) = 4, not the naive 5.
    assert plan.contracts == 4
    assert plan.max_trades == 1


def test_sizing_matches_simulated_stop_loss(tmp_path=None) -> None:
    # Codex 2.3: the sizing estimate equals a plain stopped trade's loss.
    from occams.sim import DayPlan, simulate_day
    df = range_bars([
        (5004, 5012, 5003, 5011),   # entry 5010.25 (stop 5002.25)
        (5010, 5011, 4999, 5001),   # clean stop-out, no gap
    ])
    plan = DayPlan(buy_stop=5010.0, sell_stop=None, stop_dist=8.0,
                   target_dist=12.0, contracts=1, max_trades=1)
    result = simulate_day(df, plan, COSTS)
    per_contract_risk = (8.0 + 0.25) * 5.0 + 2 * 1.25    # the sizing formula
    assert result.trades[0].pnl_usd == -per_contract_risk


def test_build_plan_carries_daily_stop(tmp_path=None) -> None:
    # Codex 2.1: the sealed risk control must be ACTIVE in generated plans.
    bars = range_bars([(5000, 5010, 4990, 5005)])
    plan = build_plan(bars, params=params(daily_stop_usd=500.0),
                      costs=COSTS)
    assert plan.daily_stop_usd == 500.0


def test_mnq_sizing_uses_its_own_multiplier(tmp_path=None) -> None:
    from occams.instruments import costs_for
    bars = range_bars([(5000, 5010, 4990, 5005)])
    mnq = build_plan(bars, params=params(), costs=costs_for("MNQ"))
    # MNQ: (8 + 0.25)×$2 + $2.50 = $19 per contract → floor(200/19) = 10.
    assert mnq.contracts == 10


def test_vwap_filter_is_volume_weighted() -> None:
    # Codex 4.1: with a volume column, VWAP must weight by volume — massive
    # volume at the LOW prices drags VWAP to ~4990 while the time-weighted
    # mean sits ~5017; close 4990 is below neither/both accordingly. The
    # weighted rule arms ONLY the side the naive mean would get wrong.
    idx = pd.date_range("2024-01-02 09:30", periods=3, freq="1min")
    bars = pd.DataFrame({
        "open":  [5030.0, 5030.0, 4990.0],
        "high":  [5032.0, 5032.0, 4992.0],
        "low":   [5028.0, 5028.0, 4988.0],
        "close": [5030.0, 5030.0, 4991.0],
        "volume": [1, 1, 998],              # volume lives at the LOW prices
    }, index=idx)
    # volume-weighted VWAP ≈ 4990.4 < close 4991 → LONG side armed;
    # the old time-mean (≈ 5017) would have called this weak and gone short.
    plan = build_plan(bars, params=params(vwap_filter=True),
                      costs=COSTS)
    assert plan.sell_stop is None           # short disarmed
    assert plan.buy_stop is not None


def test_vwap_filter_requires_volume_column() -> None:
    # No silent fallback for real use: filter on + no volume = loud error.
    import pytest
    bars = range_bars([(5000, 5010, 4990, 5005), (5005, 5008, 4995, 5000)])
    with pytest.raises(ValueError, match="volume"):
        build_plan(bars, params=params(vwap_filter=True), costs=COSTS)


def test_vwap_filter_off_needs_no_volume() -> None:
    bars = range_bars([(5000, 5010, 4990, 5005)])
    plan = build_plan(bars, params=params(vwap_filter=False),
                      costs=COSTS)
    assert plan.buy_stop is not None and plan.sell_stop is not None


def test_stop_scales_with_opening_range_height() -> None:
    # PREREG v2: the stop is ORB-native — a multiple of the range height, so
    # sizing stays dimensionally consistent with the $-risk budget at any
    # volatility (the verdict-#1 defect: daily-ATR stops → 0 contracts).
    narrow = range_bars([(5000, 5005, 4995, 5002)])        # height 10
    wide = range_bars([(5000, 5025, 4975, 5010)])          # height 50
    p_narrow = build_plan(narrow, params=params(), costs=COSTS)
    p_wide = build_plan(wide, params=params(), costs=COSTS)
    assert p_narrow.stop_dist == 4.0                       # 0.4 × 10
    assert p_wide.stop_dist == 20.0                        # 0.4 × 50
    assert p_narrow.contracts > p_wide.contracts           # fixed $ risk


def test_degenerate_range_is_no_trade() -> None:
    bars = range_bars([(5000, 5000, 5000, 5000)])          # height 0
    plan = build_plan(bars, params=params(), costs=COSTS)
    assert isinstance(plan, NoTrade)
    assert "degenerate" in plan.reason


def test_sub_tick_stop_is_no_trade() -> None:
    bars = range_bars([(5000.0, 5000.25, 5000.0, 5000.25)])  # height 1 tick
    plan = build_plan(bars, params=params(stop_range=0.5), costs=COSTS)
    assert isinstance(plan, NoTrade)                       # stop 0.125 < tick
    assert "tick" in plan.reason


def test_contracts_capped_at_venue_position_limit() -> None:
    # Narrow range on MNQ: 0.5 × height 2 = 1pt stop → $5/contract →
    # naive 40 contracts; the venue cap (30 micros) must bind.
    from occams.instruments import costs_for
    bars = range_bars([(5000, 5001, 4999, 5000.5)])
    plan = build_plan(bars, params=params(stop_range=0.5),
                      costs=costs_for("MNQ"))
    assert plan.contracts == 30


def test_null_strategy_sizes_off_range_height() -> None:
    # The null must share the SAME risk manager (PREREG §3) — stop from the
    # opening-range height, venue cap included, no ATR anywhere.
    from datetime import date as _date

    from occams.harness import TradingDay
    from occams.strategy import make_null_strategy
    rb = range_bars([(5000, 5010, 4990, 5005)])            # height 20
    sb = range_bars([(5005, 5015, 5000, 5010)] * 5)
    day = TradingDay(date=_date(2024, 1, 2), session_bars=sb, atr=999.0,
                     range_bars=rb, instrument="SYN")
    plan = make_null_strategy(7, params(), COSTS)(day)
    assert plan.stop_dist == 8.0                           # 0.4 × 20, not ATR
