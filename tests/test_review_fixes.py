"""Review fixes #3, #4, #5, #10 — pinning tests (2026-07-03 code review).

#3  search.py G4 plateau must implement PREREG's rule exactly: Chebyshev-1
    neighbourhood (incl. the cell), size ≥ plateau_cells, MEDIAN P(pass)
    within plateau_slack of the winner.
#4  the random-entry null must be a deterministic function of (seed, date) —
    same day, same side, regardless of call order or MC window overlap.
#5  session/timezone contract: vendor bars must be tz-aware; conversion to
    US/Eastern is explicit; naive input is a loud error (not a silent shift).
#10 build_plan on an empty opening range is NoTrade, never NaN levels.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from occams.harness import MCStats, TradingDay
from occams.search import Gates, GridAxis, Sweep, SweepCell, find_winner
from occams.sim import Costs
from occams.strategy import NoTrade, OrbParams, build_plan, make_null_strategy

COSTS = Costs(multiplier=5.0, tick_size=0.25, commission_per_side=1.25,
              slippage_ticks=1)
PARAMS = OrbParams(stop_range=1.0, target_r=1.5, risk_usd=200.0, max_trades=1)


def _cell(i: int, p_pass: float) -> SweepCell:
    return SweepCell(indices=(i,), params={"x": i},
                     stats=MCStats(n_runs=50, p_pass=p_pass, p_breach=0.0,
                                   median_days=10))


def _sweep(p_passes: list[float]) -> Sweep:
    return Sweep(cells=tuple(_cell(i, p) for i, p in enumerate(p_passes)),
                 axes=(GridAxis("x", tuple(range(len(p_passes)))),))


NULL_P = 0.10   # float baseline (mean over null seeds)
GATES = Gates(p_pass_min=0.55, edge_vs_null=0.15, p_breach_max=0.30,
              plateau_cells=2, plateau_slack=0.05)


def test_g4_lone_spike_is_rejected_by_the_median_rule() -> None:
    # Spike 0.90 surrounded by 0.20: its neighbourhood median is far below
    # 0.90 − 0.05 → rejected. No other cell clears G1 → no winner at all.
    assert find_winner(_sweep([0.90, 0.20, 0.20, 0.20]), NULL_P, GATES) is None


def test_g4_plateau_qualifies_by_neighbourhood_median() -> None:
    # DISCRIMINATING case (median rule vs each-cell rule): winner 0.80 in the
    # middle; neighbourhood {0.79, 0.80, 0.20} has median 0.79 (within slack)
    # but contains one far-off cell. PREREG's median rule → qualifies with a
    # 3-cell plateau; the old each-cell rule would shrink it to 2 and reject.
    gates3 = Gates(p_pass_min=0.55, edge_vs_null=0.15, p_breach_max=0.30,
                   plateau_cells=3, plateau_slack=0.05)
    w = find_winner(_sweep([0.79, 0.80, 0.20]), NULL_P, gates3)
    assert w is not None
    assert w.p_pass == 0.80
    assert len(w.plateau) == 3


def test_null_strategy_is_deterministic_per_day() -> None:
    # The null must be a pure function of (seed, date): the SAME day gets the
    # SAME side regardless of call order, instance, or MC-window overlap.
    bars = pd.DataFrame(
        {"open": [5000.0], "high": [5001.0], "low": [4999.0],
         "close": [5000.5]},
        index=pd.date_range("2024-03-05 10:01", periods=1, freq="1min"))
    days = [TradingDay(date=date(2024, 3, d), session_bars=bars, atr=8.0,
                       range_bars=bars)
            for d in range(1, 20)]

    def sides(strategy, day_seq):
        return {d.date: strategy(d).buy_stop is None for d in day_seq}

    forward = sides(make_null_strategy(11, PARAMS, COSTS), days)
    backward = sides(make_null_strategy(11, PARAMS, COSTS), list(reversed(days)))
    assert forward == backward          # order-independent
    # And the sides genuinely vary across days (it's still a coin, not a rut).
    assert len(set(forward.values())) == 2


def test_sessions_reject_naive_timestamps_and_convert_utc_to_eastern() -> None:
    from occams.sessions import to_eastern

    naive = pd.DataFrame({"open": [1.0]}, index=pd.date_range(
        "2024-01-02 14:30", periods=1, freq="1min"))
    with pytest.raises(ValueError, match="tz-aware"):
        to_eastern(naive)

    # Winter (EST): 14:30 UTC == 09:30 ET. Summer (EDT): 13:30 UTC == 09:30 ET.
    winter = naive.tz_localize("UTC")
    assert to_eastern(winter).index[0].strftime("%H:%M") == "09:30"
    summer = pd.DataFrame({"open": [1.0]}, index=pd.date_range(
        "2024-07-02 13:30", periods=1, freq="1min", tz="UTC"))
    assert to_eastern(summer).index[0].strftime("%H:%M") == "09:30"


def test_build_plan_on_empty_range_is_no_trade_not_nan() -> None:
    empty = pd.DataFrame(columns=["open", "high", "low", "close"])
    plan = build_plan(empty, params=PARAMS, costs=COSTS)
    assert isinstance(plan, NoTrade)
    assert "empty" in plan.reason
