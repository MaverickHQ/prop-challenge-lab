"""Family 2 — the failed-breakout fade simulator (Phase C, TDD).

Semantics mirror scripts/diagnostics.py::fade_anatomy exactly (bar-close
failure detection; extreme includes the failure bar; outcomes from the
next bar; conservative ties) so the sealed run measures the same object
the dev screening measured — plus real fills, costs, sizing, EOD exits.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from occams.fade import FadeParams, make_fade_strategy, simulate_fade_day
from occams.harness import TradingDay
from occams.sim import Costs
from occams.strategy import NoTrade

COSTS = Costs(multiplier=5.0, tick_size=0.25, commission_per_side=1.25,
              slippage_ticks=1)


def bars(rows):
    idx = pd.date_range("2024-01-02 09:30", periods=len(rows), freq="1min")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"],
                        index=idx)


def day_of(range_rows, session_rows, atr=8.0):
    return TradingDay(date=date(2024, 1, 2), session_bars=bars(session_rows),
                      atr=atr, range_bars=bars(range_rows),
                      instrument="SYN")


RANGE = [(105, 110, 100, 106)]                  # hi 110 / lo 100 / height 10


def params(**kw) -> FadeParams:
    base = dict(k_stop=0.25, width_max=None, risk_usd=200.0)
    base.update(kw)
    return FadeParams(**base)


def test_winning_fade_books_target_minus_costs() -> None:
    # Break to 112 (ext 0.2), fail (close 109), travel to the far side.
    # Entry short 110 - slip 0.25 = 109.75; target 100 + slip = 100.25;
    # stop dist = (112-110) + 0.25*10 = 4.5 -> $25.75/contract true risk
    # -> 7 contracts at $200. PnL/contract = (109.75-100.25)*5 - 2.50.
    day = day_of(RANGE, [
        (109, 112, 108, 111),      # breakout
        (111, 111.5, 108, 109),    # failure close < 110 -> entry at close
        (109, 110, 104, 105),
        (105, 106, 99, 100),       # low 99 <= 100 -> target
    ])
    r = simulate_fade_day(day, params(), COSTS)
    assert len(r.trades) == 1
    t = r.trades[0]
    assert t.contracts == 7
    assert t.pnl_usd == 7 * ((109.75 - 100.25) * 5.0 - 2.50)


def test_stop_beyond_extreme_books_true_risk_loss() -> None:
    # After entry, price runs to the stop: extreme 112 + 0.25*10 = 114.5.
    # Stop fill 114.5 + slip = 114.75. Loss/contract = (114.75-109.75)*5
    # + 2.50 commissions = $27.50 -> equals per-contract sizing estimate.
    day = day_of(RANGE, [
        (109, 112, 108, 111),
        (111, 111.5, 108, 109),
        (110, 115, 109, 114),      # high 115 >= 114.5 -> stopped
    ])
    r = simulate_fade_day(day, params(), COSTS)
    t = r.trades[0]
    assert t.pnl_usd == -t.contracts * ((114.75 - 109.75) * 5.0 + 2.50)


def test_no_breakout_or_held_breakout_is_no_trade() -> None:
    quiet = day_of(RANGE, [(105, 109, 101, 106)] * 3)
    assert simulate_fade_day(quiet, params(), COSTS).trades == []
    held = day_of(RANGE, [(109, 112, 108, 111), (111, 114, 110.5, 113)])
    assert simulate_fade_day(held, params(), COSTS).trades == []


def test_same_bar_stop_and_target_is_stop_first() -> None:
    # The bar after entry touches BOTH the stop (114.5) and the target
    # (100) -> conservative: stop first, loss booked.
    day = day_of(RANGE, [
        (109, 112, 108, 111),
        (111, 111.5, 108, 109),
        (110, 115, 99, 100),       # touches both
    ])
    r = simulate_fade_day(day, params(), COSTS)
    assert r.trades[0].pnl_usd < 0


def test_gap_open_beyond_stop_fills_at_worse_open() -> None:
    day = day_of(RANGE, [
        (109, 112, 108, 111),
        (111, 111.5, 108, 109),
        (116, 117, 115.5, 116),    # opens through the 114.5 stop
    ])
    r = simulate_fade_day(day, params(), COSTS)
    t = r.trades[0]
    # fill at open 116 + slip, not at the stop level
    assert t.pnl_usd == -t.contracts * ((116.25 - 109.75) * 5.0 + 2.50)


def test_eod_forces_flat_at_last_close() -> None:
    day = day_of(RANGE, [
        (109, 112, 108, 111),
        (111, 111.5, 108, 109),
        (109, 110, 106, 107),      # neither stop nor target by close
    ])
    r = simulate_fade_day(day, params(), COSTS)
    t = r.trades[0]
    assert t.pnl_usd == t.contracts * ((109.75 - (107 + 0.25)) * 5.0 - 2.50)


def test_width_filter_stands_aside_wide_ranges() -> None:
    # height 10, atr 8 -> width 1.25 > 0.30 -> NoTrade under the filter.
    day = day_of(RANGE, [(109, 112, 108, 111), (111, 111.5, 108, 109)])
    strat = make_fade_strategy(params(width_max=0.30), COSTS)
    assert isinstance(strat(day), NoTrade)
    # atr 40 -> width 0.25 <= 0.30 -> the plan goes through.
    day2 = day_of(RANGE, [(109, 112, 108, 111), (111, 111.5, 108, 109)],
                  atr=40.0)
    assert not isinstance(strat(day2), NoTrade)


def test_down_breakout_fades_long_mirrored() -> None:
    # Break below 100 to 98 (ext 0.2), fail back above (close 101), then
    # travel up to the far side 110.
    day = day_of(RANGE, [
        (101, 102, 98, 99),        # breakout down
        (99, 101.5, 98.5, 101),    # failure close > 100 -> long at 100.25
        (101, 111, 100.5, 110),    # high 111 >= 110 + no stop touch
    ])
    r = simulate_fade_day(day, params(), COSTS)
    t = r.trades[0]
    assert t.pnl_usd == t.contracts * ((110 - 0.25 - 100.25) * 5.0 - 2.50)


def test_follow_direction_mirrors_the_null() -> None:
    # direction="follow": at the same failure moment, trade the BREAKOUT
    # side instead (the coin-null's other face). Same geometry, same risk.
    day = day_of(RANGE, [
        (109, 112, 108, 111),
        (111, 111.5, 108, 109),
        (110, 115, 109, 114),      # fade would be stopped; follow wins ...
    ])
    r = simulate_fade_day(day, params(), COSTS, direction="follow")
    t = r.trades[0]
    assert t.pnl_usd > 0            # long from 110.25 toward 114.5 target


def test_harness_dispatches_fade_plans_through_the_ledger() -> None:
    from occams.harness import daily_ledger
    day = day_of(RANGE, [
        (109, 112, 108, 111),
        (111, 111.5, 108, 109),
        (105, 106, 99, 100),
    ])
    ledger = daily_ledger([day], make_fade_strategy(params(), COSTS), COSTS)
    assert ledger[0].traded is True
    assert ledger[0].pnl > 0
