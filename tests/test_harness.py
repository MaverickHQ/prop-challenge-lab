"""Harness — chains simulate_day results into EOD equity marks feeding the
rules engine (Phase 2.2 glue), then Monte Carlo over start days. Strategies
are injected callables: day -> DayPlan | NoTrade.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from occams.harness import TradingDay, monte_carlo, run_challenge
from occams.rules import ChallengeConfig, Status
from occams.sim import Costs, DayPlan
from occams.strategy import NoTrade

COSTS = Costs(multiplier=5.0, tick_size=0.25, commission_per_side=1.25,
              slippage_ticks=1)
# Small target so a couple of winning trades resolve the challenge in-test.
CFG = ChallengeConfig(account=50_000, target=100, trailing_dd=2_000,
                      daily_guard=1_000, min_days=1)

WIN_DAY = [
    (5004, 5012, 5003, 5011),   # long entry 5010.25
    (5011, 5026, 5010, 5025),   # 12pt target hit → 12×$5 − $2.50 = +$57.50
]
FLAT_DAY = [(5000, 5004, 4996, 5001), (5001, 5005, 4997, 5000)]


def day(rows: list, d: str = "2024-01-02") -> TradingDay:
    idx = pd.date_range(f"{d} 09:31", periods=len(rows), freq="1min")
    bars = pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx)
    # range_bars: the null (v2) sizes off the opening-range height, so the
    # fixture supplies one — same bars, height a few points.
    return TradingDay(date=date.fromisoformat(d), session_bars=bars, atr=8.0,
                      range_bars=bars)


def orb_like(_day: TradingDay) -> DayPlan:
    return DayPlan(buy_stop=5010.0, sell_stop=4990.0, stop_dist=8.0,
                   target_dist=12.0, contracts=1, max_trades=1)


def test_winning_days_chain_equity_to_a_pass() -> None:
    days = [day(WIN_DAY, "2024-01-02"), day(WIN_DAY, "2024-01-03")]
    run = run_challenge(days, orb_like, CFG, COSTS)
    assert run.status == Status.PASSED
    assert run.final_equity == 50_000 + 2 * 57.50   # exact chaining
    assert run.days_used == 2


def test_no_trade_days_advance_time_but_not_equity() -> None:
    days = [day(FLAT_DAY, "2024-01-02"), day(WIN_DAY, "2024-01-03"),
            day(WIN_DAY, "2024-01-04")]

    def skip_first(d: TradingDay):
        return NoTrade("calendar") if d.date.day == 2 else orb_like(d)

    run = run_challenge(days, skip_first, CFG, COSTS)
    assert run.status == Status.PASSED
    assert run.days_used == 3
    assert run.final_equity == 50_000 + 2 * 57.50


def test_monte_carlo_counts_outcomes_over_start_days() -> None:
    # 4 possible starts over 5 days, needing 2 win-days: all 4 starts pass.
    days = [day(WIN_DAY, f"2024-01-0{i}") for i in range(2, 7)]
    stats = monte_carlo(days, orb_like, CFG, COSTS, horizon_days=2)
    assert stats.n_runs == 4
    assert stats.p_pass == 1.0
    assert stats.p_breach == 0.0
    assert stats.median_days == 2


def test_calendar_blocked_day_advances_without_trading() -> None:
    # Codex 1.3: the SAME events map gates backtest days — no trade, no P&L,
    # but the calendar day advances and equity is still marked.
    from datetime import date as _d
    events = {_d(2024, 1, 2): "FOMC"}
    days = [day(WIN_DAY, "2024-01-02"), day(WIN_DAY, "2024-01-03")]
    run = run_challenge(days, orb_like, CFG, COSTS, events=events)
    assert run.equity_marks[0] == 50_000.0          # blocked: nothing happened
    assert run.final_equity == 50_000.0 + 57.50     # day 2 traded normally
    assert run.days_used == 2


def test_blocked_day_does_not_count_toward_min_trading_days() -> None:
    from datetime import date as _d
    from occams.rules import ChallengeConfig, Status
    cfg = ChallengeConfig(account=50_000, target=55, trailing_dd=2_000,
                          daily_guard=1_000, min_days=2)
    events = {_d(2024, 1, 2): "FOMC"}
    days = [day(WIN_DAY, "2024-01-02"), day(WIN_DAY, "2024-01-03")]
    run = run_challenge(days, orb_like, cfg, COSTS, events=events)
    # One traded day (+$57.50 >= target) but min_days=2 unmet -> still ACTIVE.
    assert run.status == Status.ACTIVE


def test_per_instrument_costs_resolved_by_day() -> None:
    # Codex 1.1: an MNQ day must use the $2 multiplier, never MES's $5.
    from occams.harness import TradingDay
    import pandas as pd
    from occams.instruments import COSTS_BY_INSTRUMENT
    idx = pd.date_range("2024-01-02 09:31", periods=2, freq="1min")
    bars = pd.DataFrame(WIN_DAY, columns=["open", "high", "low", "close"],
                        index=idx)
    from datetime import date as _d
    d_mnq = TradingDay(date=_d(2024, 1, 2), session_bars=bars, atr=8.0,
                       instrument="MNQ")
    run = run_challenge([d_mnq], orb_like, CFG, COSTS_BY_INSTRUMENT)
    # 12pt target x $2 - $2.50 commissions = +$21.50 (vs $57.50 on MES).
    assert run.final_equity == 50_000.0 + 21.50


def test_unknown_instrument_in_costs_map_is_loud() -> None:
    import pytest
    from occams.instruments import costs_for
    with pytest.raises(ValueError, match="no costs"):
        costs_for("ZC")


def test_null_baseline_threads_events_to_monte_carlo() -> None:
    from datetime import date as _d
    from occams.harness import null_baseline
    from occams.strategy import OrbParams
    days = [day(WIN_DAY, f"2024-01-0{i}") for i in range(2, 8)]
    pr = OrbParams(1.0, 1.5, 200.0)
    events = {_d(2024, 1, 3): "FOMC"}
    base = null_baseline(days, pr, CFG, COSTS, horizon_days=2)
    blocked = null_baseline(days, pr, CFG, COSTS, horizon_days=2, events=events)
    assert isinstance(base, float) and isinstance(blocked, float)
