"""Phase 2 — OCO bracket simulator, tested through simulate_day() only.

Bars are synthetic 1-min OHLC; every assertion is on observable trade/P&L
behaviour in dollars. MES-like costs: $5/point multiplier, $0.25 tick,
$1.25/side commission, 1-tick slippage per fill.
"""

from __future__ import annotations

import pandas as pd

from occams.sim import Costs, DayPlan, simulate_day

COSTS = Costs(multiplier=5.0, tick_size=0.25, commission_per_side=1.25,
              slippage_ticks=1)


def bars(rows: list[tuple[float, float, float, float]]) -> pd.DataFrame:
    """Rows of (open, high, low, close) → 1-min bars from 09:31 ET."""
    idx = pd.date_range("2024-01-02 09:31", periods=len(rows), freq="1min")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx)


def plan(**kw) -> DayPlan:
    base = dict(buy_stop=5010.0, sell_stop=4990.0, stop_dist=10.0,
                target_dist=15.0, contracts=1, max_trades=1)
    base.update(kw)
    return DayPlan(**base)


def test_target_exit_pnl_exact_to_the_cent() -> None:
    # Long from 5010.25 (incl. slip), target_dist 15 → limit at 5025.25 fills
    # AT the limit when crossed. P&L = 15.00pt × $5 − $2.50 commission = $72.50.
    df = bars([
        (5004, 5012, 5003, 5011),   # entry: 5010 + slip = 5010.25
        (5011, 5026, 5010, 5025),   # high 5026 ≥ 5025.25 → target fills
    ])
    result = simulate_day(df, plan(), COSTS)
    t = result.trades[0]
    assert t.exit_price == 5025.25
    assert t.pnl_usd == 72.50
    assert result.day_pnl_usd == 72.50


def test_stop_exit_pnl_exact_negative() -> None:
    # Long from 5010.25, stop_dist 10 → stop at 5000.25; market exit slips
    # 1 tick against us → 5000.00. P&L = −10.25pt × $5 − $2.50 = −$53.75.
    df = bars([
        (5004, 5012, 5003, 5011),   # entry: 5010.25
        (5010, 5011, 4999, 5001),   # low 4999 ≤ 5000.25 → stopped
    ])
    result = simulate_day(df, plan(), COSTS)
    t = result.trades[0]
    assert t.exit_price == 5000.00
    assert t.pnl_usd == -53.75
    assert result.day_pnl_usd == -53.75


def test_bar_touching_both_stop_and_target_fills_stop_first() -> None:
    # THE conservative rule: a wide bar spans both the stop (5000.25) and the
    # target (5025.25) → we must assume the stop was hit first. Loss, not win.
    df = bars([
        (5004, 5012, 5003, 5011),   # entry: 5010.25
        (5010, 5030, 4995, 5020),   # touches BOTH → stop first
    ])
    result = simulate_day(df, plan(), COSTS)
    t = result.trades[0]
    assert t.exit_price == 5000.00          # stop fill, not target
    assert t.pnl_usd == -53.75
    assert result.day_pnl_usd < 0


def test_gap_through_stop_fills_at_worse_open() -> None:
    # Bar OPENS below the stop (5000.25): market stop fills at the open, not
    # at the stop level. Exit = 4990 − slip = 4989.75 → P&L −$105.00.
    df = bars([
        (5004, 5012, 5003, 5011),   # entry: 5010.25
        (4990, 4995, 4988, 4992),   # gap open through the stop
    ])
    result = simulate_day(df, plan(), COSTS)
    assert result.trades[0].exit_price == 4989.75
    assert result.trades[0].pnl_usd == -105.00


def test_open_position_is_force_flat_at_session_end() -> None:
    # Neither bracket hit by the last bar → market-flat at final close − slip.
    # Exit 5015 − 0.25 = 5014.75 → P&L = 4.50pt × $5 − $2.50 = $20.00.
    df = bars([
        (5004, 5012, 5003, 5011),   # entry: 5010.25
        (5011, 5018, 5008, 5015),   # quiet: no stop (5000.25), no target (5025.25)
    ])
    result = simulate_day(df, plan(), COSTS)
    t = result.trades[0]
    assert t.exit_price == 5014.75
    assert t.pnl_usd == 20.00
    assert result.day_pnl_usd == 20.00


def test_sell_stop_entry_and_short_target_exit() -> None:
    # Short from 4989.75 (4990 − slip); target 15 lower at 4974.75 → +$72.50.
    # Entry bar high stays below the stop (4999.75) so the conservative
    # same-bar rule doesn't fire and the target path is what's under test.
    df = bars([
        (4996, 4997, 4989, 4991),   # low 4989 ≤ 4990 → short entry
        (4990, 4992, 4974, 4976),   # low 4974 ≤ 4974.75 → target fills
    ])
    result = simulate_day(df, plan(), COSTS)
    t = result.trades[0]
    assert t.side == "short"
    assert t.entry_price == 4989.75
    assert t.pnl_usd == 72.50


def test_filled_entry_cancels_the_other_side() -> None:
    # OCO: once long, a later dip through the sell level must NOT open a short.
    df = bars([
        (5004, 5012, 5003, 5011),   # long entry: 5010.25 (stop 5000.25)
        (5010, 5011, 4989, 4991),   # low crosses BOTH our stop AND sell level
    ])
    result = simulate_day(df, plan(), COSTS)
    assert len(result.trades) == 1           # stopped out; no short opened
    assert result.trades[0].side == "long"


def test_max_trades_caps_reentry() -> None:
    stopout = (5010, 5011, 4999, 5001)      # stops the long (5000.25)
    retrigger = (5002, 5012, 5001, 5011)    # re-crosses the buy level
    df = bars([(5004, 5012, 5003, 5011), stopout, retrigger, stopout])
    assert len(simulate_day(df, plan(max_trades=1), COSTS).trades) == 1
    assert len(simulate_day(df, plan(max_trades=2), COSTS).trades) == 2


def test_no_trigger_means_flat_day() -> None:
    df = bars([(5000, 5005, 4995, 5002), (5002, 5006, 4996, 5000)])
    result = simulate_day(df, plan(), COSTS)
    assert result.trades == []
    assert result.day_pnl_usd == 0.0


def test_entry_bar_touching_stop_is_stopped_same_bar() -> None:
    # Review fix #1: intra-bar order is unknowable, so an entry bar whose low
    # also reaches the protective stop is assumed stopped (conservative).
    # Entry 5010.25, stop 5000.25; entry bar low 4998 → stopped SAME bar at
    # 5000.25 − slip = 5000.00 → pnl −$53.75. No gap logic (open pre-dates entry).
    df = bars([
        (5004, 5012, 4998, 5000),   # triggers entry AND touches the stop
        (5000, 5001, 4999, 5000),
    ])
    result = simulate_day(df, plan(), COSTS)
    assert len(result.trades) == 1
    assert result.trades[0].exit_price == 5000.00
    assert result.trades[0].pnl_usd == -53.75


def test_short_entry_bar_touching_stop_is_stopped_same_bar() -> None:
    # Mirror for shorts: fill 4989.75, stop 4999.75; entry bar high 5001 →
    # stopped same bar at 4999.75 + slip = 5000.00 → pnl −$53.75.
    df = bars([(4996, 5001, 4989, 4995)])
    result = simulate_day(df, plan(), COSTS)
    assert len(result.trades) == 1
    assert result.trades[0].side == "short"
    assert result.trades[0].exit_price == 5000.00
    assert result.trades[0].pnl_usd == -53.75


def test_target_never_fills_on_the_entry_bar() -> None:
    # The favourable extreme may pre-date the entry, so the target cannot fill
    # on the entry bar — position survives to force-flat at close − slip.
    df = bars([(5004, 5030, 5003, 5028)])   # high ≥ target 5025.25, stop safe
    result = simulate_day(df, plan(), COSTS)
    t = result.trades[0]
    assert t.exit_price == 5027.75          # force-flat, NOT the target
    assert t.pnl_usd == 85.00


def test_buy_stop_entry_fills_with_slippage() -> None:
    # Bar crosses the buy stop from below → long entry at stop + 1 tick.
    df = bars([
        (5000, 5005, 4999, 5004),   # no touch
        (5004, 5012, 5003, 5011),   # high crosses 5010 → triggered
    ])
    result = simulate_day(df, plan(), COSTS)
    assert len(result.trades) == 1
    t = result.trades[0]
    assert t.side == "long"
    assert t.entry_price == 5010.0 + 0.25  # stop level + slippage


def test_both_entry_stops_touched_same_bar_takes_no_entries() -> None:
    # Codex 2.4: a flat-state bar spanning BOTH armed entry levels is
    # unresolvable chaos — the old code silently went long. Conservative,
    # pre-registered rule: no further entries that day.
    df = bars([
        (5000, 5011, 4989, 5001),   # touches buy 5010 AND sell 4990 — ambiguous
        (5001, 5012, 5000, 5011),   # later clean re-trigger must NOT enter
    ])
    result = simulate_day(df, plan(max_trades=2), COSTS)
    assert result.trades == []
    assert result.day_pnl_usd == 0.0


def test_ambiguity_rule_is_symmetric() -> None:
    # Mirrored day (short-side re-trigger instead) — identical conservatism.
    df = bars([
        (5000, 5011, 4989, 4999),   # ambiguous bar
        (4999, 5000, 4988, 4990),   # clean short re-trigger must NOT enter
    ])
    result = simulate_day(df, plan(max_trades=2), COSTS)
    assert result.trades == []


def test_ambiguity_ignored_when_one_side_disarmed() -> None:
    # With the sell side disarmed (VWAP filter), a wide bar is NOT ambiguous:
    # only one entry could have happened — the long fires normally.
    from occams.sim import DayPlan
    p = DayPlan(buy_stop=5010.0, sell_stop=None, stop_dist=10.0,
                target_dist=15.0, contracts=1, max_trades=1)
    df = bars([(5000, 5011, 4989, 5001)])
    result = simulate_day(df, p, COSTS)
    assert len(result.trades) == 1
    assert result.trades[0].side == "long"
