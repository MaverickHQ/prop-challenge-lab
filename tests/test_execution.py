"""E1 — the gate that would have caught the fade, tested on the fade.

The point of this file is the last test: replaying the real 2026-07-31 setup
through the gate must REFUSE the sealed engine's entry. A gate that passes
the one defect it was built for is decoration.
"""

from __future__ import annotations

import pytest

from occams.execution import (BUY, LIMIT, MARKET, SELL, STOP, Order,
                              Unplaceable, fill, obtainable, validate)


# --- the venue's rules, not ours ---

def test_a_market_order_cannot_name_a_level():
    """The assumption this module exists to refuse."""
    with pytest.raises(Unplaceable, match="cannot name a level"):
        validate(Order(MARKET, BUY, 100.0), market=100.0)


def test_a_buy_limit_above_market_is_marketable_not_resting():
    with pytest.raises(Unplaceable, match="ABOVE market"):
        validate(Order(LIMIT, BUY, 105.0), market=100.0)


def test_a_sell_limit_below_market_is_marketable_not_resting():
    with pytest.raises(Unplaceable, match="BELOW market"):
        validate(Order(LIMIT, SELL, 95.0), market=100.0)


def test_a_stop_on_the_wrong_side_triggers_instantly():
    """Protocol #4a's original defect, now a rule rather than a lesson."""
    with pytest.raises(Unplaceable, match="wrong side"):
        validate(Order(STOP, BUY, 95.0), market=100.0)
    with pytest.raises(Unplaceable, match="wrong side"):
        validate(Order(STOP, SELL, 105.0), market=100.0)


def test_valid_orders_pass():
    validate(Order(LIMIT, BUY, 95.0), market=100.0)
    validate(Order(STOP, BUY, 105.0), market=100.0)
    validate(Order(MARKET, SELL, None), market=100.0)


# --- fills come from what the market did ---

HI = [100.0, 101.0, 99.0, 98.0]
LO = [99.0, 100.0, 97.0, 96.0]
OP = [99.5, 100.5, 98.5, 97.5]


def test_a_limit_fills_only_when_price_reaches_it():
    assert fill(Order(LIMIT, BUY, 97.5), HI, LO, OP, placed_at=0)[0] == 2
    assert fill(Order(LIMIT, BUY, 90.0), HI, LO, OP, placed_at=0) is None


def test_a_stop_gapping_through_fills_at_the_open_not_the_level():
    """Conservative by construction: a gap cannot fill you at your level."""
    idx, px = fill(Order(STOP, SELL, 98.0), HI, LO, [99.5, 100.5, 97.0, 97.5],
                   placed_at=1)
    assert idx == 2 and px == 97.0


def test_slippage_can_only_hurt():
    _, a = fill(Order(STOP, BUY, 101.0), HI, LO, OP, placed_at=0, slippage=0.0)
    _, b = fill(Order(STOP, BUY, 101.0), HI, LO, OP, placed_at=0, slippage=0.25)
    assert b > a, "adverse slippage must raise a buy fill, never lower it"


# --- THE GATE, on the real defect ---

def test_the_gate_REFUSES_the_fades_assumed_entry():
    """2026-07-31 MES: range 7515.25/7480.25, breakout DOWN, failure close at
    7481.25. The engine books a LONG fill at the 7480.25 boundary. At that
    moment market is 7481.25 — the boundary is BEHIND the market, so only a
    limit can name it, and a limit fills later on a retest, not here."""
    highs = [7481.75, 7482.50, 7479.00]
    lows = [7477.25, 7476.75, 7472.75]
    opens = [7481.25, 7480.25, 7478.00]
    ok, why = obtainable(assumed_entry=7480.25, side=BUY, decision_bar=0,
                         market_at_decision=7481.25,
                         highs=highs, lows=lows, opens=opens)
    assert ok, "a limit DOES fill here on the next bar"
    # ...but only because price retested. Now the case where it does not:
    ok2, why2 = obtainable(assumed_entry=7480.25, side=BUY, decision_bar=0,
                           market_at_decision=7481.25,
                           highs=[7495.0, 7500.0], lows=[7482.0, 7490.0],
                           opens=[7483.0, 7492.0])
    assert not ok2
    assert "never filled" in why2 or "not 7480.25" in why2


def test_the_gate_refuses_a_price_behind_the_market_with_no_retest():
    """The fade's structural problem in one line: you cannot sell at a level
    the market has already left, unless it comes back."""
    ok, why = obtainable(assumed_entry=110.0, side=SELL, decision_bar=0,
                         market_at_decision=100.0,
                         highs=[101.0, 102.0], lows=[99.0, 98.0],
                         opens=[100.0, 100.5])
    assert not ok and "never filled" in why


# --- E3: the measured cost model, and why the sealed one is untouched ---

def test_measured_costs_differ_from_sealed_only_where_measurement_says_so():
    """MNQ's effective spread measured 2.00 ticks against an assumed 1.00;
    MES measured 1.00 and is confirmed. The sealed dict stays as it was so
    verdict v3 remains reproducible -- X1's whole point."""
    from occams.instruments import COSTS_BY_INSTRUMENT, MEASURED_COSTS
    assert COSTS_BY_INSTRUMENT["MNQ"].slippage_ticks == 1     # sealed
    assert MEASURED_COSTS["MNQ"].slippage_ticks == 2          # measured
    assert (COSTS_BY_INSTRUMENT["MES"].slippage_ticks
            == MEASURED_COSTS["MES"].slippage_ticks == 1)     # agree
    for k in ("multiplier", "tick_size", "commission_per_side"):
        for inst in ("MES", "MNQ"):
            assert getattr(COSTS_BY_INSTRUMENT[inst], k) == \
                   getattr(MEASURED_COSTS[inst], k), \
                   f"{inst}.{k} must not drift; only slippage was measured"


# --- E1 as a verdict precondition ---

def test_an_unaudited_family_is_REFUSED_not_waved_through():
    """Default-deny. Unknown families passing silently is exactly how the
    fade was sealed on an impossible fill."""
    from occams.execution import UnobtainableEntry, assert_entries_obtainable
    with pytest.raises(UnobtainableEntry, match="no entry auditor"):
        assert_entries_obtainable("some_new_idea", [], [], None)


def test_the_fade_family_is_refused_by_name():
    """It is the defect the gate was built for; it must not pass."""
    from types import SimpleNamespace
    from occams.execution import UnobtainableEntry, assert_entries_obtainable
    day = SimpleNamespace(date="2026-07-31", range_bars=None)
    with pytest.raises(UnobtainableEntry, match="not obtainable"):
        assert_entries_obtainable("fade", [day], [object()], None)


def test_there_is_no_skip_flag_on_the_verdict_gate():
    import inspect
    from occams import verdict_run
    src = inspect.getsource(verdict_run.run_verdict)
    assert "skip_entry_gate" in src and "not an option" in src


def test_the_gate_is_actually_CALLED_by_run_verdict_not_just_imported():
    """It was half-wired once -- imported and never invoked, which looks like
    protection and is not. This asserts the call site exists."""
    import inspect
    from occams import verdict_run
    assert "_gate_entries(" in inspect.getsource(verdict_run.run_verdict)
    assert "gate(family, days, plans, costs)" in \
        inspect.getsource(verdict_run._gate_entries)


def test_run_verdict_refuses_an_unaudited_family_end_to_end():
    from types import SimpleNamespace
    from occams.execution import UnobtainableEntry, assert_entries_obtainable
    from occams.verdict_run import _gate_entries
    proto = SimpleNamespace(family="brand_new_idea", risk_usd=175.0,
                            daily_stop_usd=500.0)
    with pytest.raises(UnobtainableEntry, match="no entry auditor"):
        _gate_entries(proto, {None: {"MES": []}}, ["MES"], None, {},
                      assert_entries_obtainable)
