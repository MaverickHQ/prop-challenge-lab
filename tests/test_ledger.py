"""Codex 3.1/3.2/3.3 — sweep scalability and verdict integrity.

3.1: days are independent (fixed-dollar risk, per-day plans), so each day is
simulated ONCE into a ledger; Monte Carlo replays the rules over slices.
Equivalence with the direct path is proven, not assumed.
3.2: instrument splits must pass independently (PREREG §5).
3.3: verdicts refuse to compare sweeps sealed under different protocols.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from occams.harness import (TradingDay, daily_ledger, monte_carlo,
                            run_challenge)
from occams.rules import ChallengeConfig, Status
from occams.sim import Costs, DayPlan

COSTS = Costs(multiplier=5.0, tick_size=0.25, commission_per_side=1.25,
              slippage_ticks=1)
CFG = ChallengeConfig(account=50_000, target=100, trailing_dd=2_000,
                      daily_guard=1_000, min_days=1)
WIN = [(5004, 5012, 5003, 5011), (5011, 5026, 5010, 5025)]
LOSS = [(5004, 5012, 5003, 5011), (5010, 5011, 4999, 5001)]


def day(rows, d) -> TradingDay:
    idx = pd.date_range(f"{d} 09:31", periods=len(rows), freq="1min")
    return TradingDay(date=date.fromisoformat(d), atr=8.0,
                      session_bars=pd.DataFrame(
                          rows, columns=["open", "high", "low", "close"],
                          index=idx))


def orb_like(_day):
    return DayPlan(buy_stop=5010.0, sell_stop=4990.0, stop_dist=8.0,
                   target_dist=12.0, contracts=1, max_trades=1)


DAYS = [day(WIN, "2024-01-02"), day(LOSS, "2024-01-03"),
        day(WIN, "2024-01-04"), day(WIN, "2024-01-05"),
        day(LOSS, "2024-01-08"), day(WIN, "2024-01-09")]


def test_cached_monte_carlo_matches_direct_path_exactly() -> None:
    # The uncached reference: run_challenge from every start (the old MC).
    horizon = 3
    direct = []
    for s in range(len(DAYS) - horizon + 1):
        direct.append(run_challenge(DAYS[s:s + horizon], orb_like, CFG, COSTS))
    cached = monte_carlo(DAYS, orb_like, CFG, COSTS, horizon_days=horizon)
    assert cached.n_runs == len(direct)
    assert cached.p_pass == sum(
        1 for r in direct if r.status is Status.PASSED) / len(direct)
    assert cached.p_breach == 0.0


def test_each_day_simulated_exactly_once_in_monte_carlo() -> None:
    calls: list[date] = []

    def counting(d):
        calls.append(d.date)
        return orb_like(d)

    monte_carlo(DAYS, counting, CFG, COSTS, horizon_days=3)
    # 4 windows × 3 days would be 12 under the old path; ledger = 6.
    assert len(calls) == len(DAYS)
    assert len(set(calls)) == len(DAYS)


def test_ledger_respects_calendar_blocks() -> None:
    events = {date(2024, 1, 2): "FOMC"}
    led = daily_ledger(DAYS[:2], orb_like, COSTS, events=events)
    assert led[0].pnl == 0.0 and led[0].traded is False
    assert led[1].traded is True


def test_empty_horizon_returns_zero_runs() -> None:
    stats = monte_carlo(DAYS[:2], orb_like, CFG, COSTS, horizon_days=5)
    assert stats.n_runs == 0 and stats.p_pass == 0.0


def test_instrument_split_failure_blocks_go() -> None:
    from occams.search import Verdict, combined_verdict
    go = Verdict("GO", None, None, "ok")
    nogo = Verdict("NO-GO", None, None, "lockbox failed")
    both = combined_verdict({"MES": go, "MNQ": go})
    assert both.decision == "GO"
    blocked = combined_verdict({"MES": go, "MNQ": nogo})
    assert blocked.decision == "NO-GO"
    assert "MNQ" in blocked.reason


def test_verdict_refuses_mismatched_prereg_hashes() -> None:
    from occams.search import Gates, GridAxis, Sweep, verdict
    gates = Gates(p_pass_min=0.55, edge_vs_null=0.10, p_breach_max=0.30,
                  plateau_cells=2, plateau_slack=0.10)
    a = Sweep(cells=(), axes=(GridAxis("x", (1,)),), prereg_hash="aaaa")
    b = Sweep(cells=(), axes=(GridAxis("x", (1,)),), prereg_hash="bbbb")
    with pytest.raises(ValueError, match="protocol"):
        verdict(a, 0.1, b, 0.1, gates)


def test_sweep_carries_prereg_hash() -> None:
    from occams.search import GridAxis, sweep
    result = sweep(DAYS, (GridAxis("stop_range", (1.0,)),),
                   lambda cell: orb_like, CFG, COSTS, horizon_days=3,
                   prereg_hash="cafe1234")
    assert result.prereg_hash == "cafe1234"
