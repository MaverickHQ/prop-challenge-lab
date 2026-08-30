"""T1.3/T1.4 — the paper-campaign core (pure logic, TDD).

Telegram command parsing, model-implied prices/sizing from logged levels
(must match the fade engine's math exactly), and per-trade drift.
"""

from __future__ import annotations

from occams.instruments import costs_for
from occams.paper import (AckLog, FillLog, RangeLog, SetupLog, SkipLog,
                          model_trade, parse_command, trade_drift)

MES = costs_for("MES")


def test_parse_range_setup_fills_skip() -> None:
    assert parse_command("/range MES 6355.25 6349.50") == \
        RangeLog(instrument="MES", high=6355.25, low=6349.50)
    assert parse_command("/setup MNQ short 6360.00") == \
        SetupLog(instrument="MNQ", side="short", extreme=6360.00)
    assert parse_command("/fills MES entry 6349.00 4") == \
        FillLog(instrument="MES", event="entry", price=6349.00, contracts=4)
    assert parse_command("/skip MES no failure") == \
        SkipLog(instrument="MES", reason="no failure")


def test_parse_rejects_garbage_loudly() -> None:
    for bad in ("/range MES abc 1", "/fills MES teleport 1 1",
                "/setup MES sideways 5", "hello", "/range MES 5"):
        assert parse_command(bad) is None


def test_model_trade_matches_the_fade_engine_math() -> None:
    # Range 100-110 (height 10), up-break extreme 112, k=0.2 sealed.
    # Short entry = boundary - slip = 109.75; stop = 112 + 0.2*10 = 114;
    # target = far side 100; loss_pts = |114 - 109.75| + 0.25 = 4.5 ->
    # per-contract 4.5*5 + 2.5 = $25 -> 175 // 25 = 7 contracts.
    m = model_trade(range_high=110.0, range_low=100.0, extreme=112.0,
                    side="short", costs=MES)
    assert m.entry == 109.75
    assert m.stop_level == 114.0
    assert m.target == 100.0
    assert m.contracts == 7
    # Model exit prices by event type (slip on the exit side too):
    assert m.exit_price("stop") == 114.25
    assert m.exit_price("target") == 100.25


def test_model_trade_long_mirrors() -> None:
    m = model_trade(range_high=110.0, range_low=100.0, extreme=98.0,
                    side="long", costs=MES)
    assert m.entry == 100.25          # boundary + slip
    assert m.stop_level == 96.0       # 98 - 0.2*10
    assert m.target == 110.0
    assert m.exit_price("target") == 109.75


def test_trade_drift_is_actual_minus_model_pnl() -> None:
    # Actual: entry 6349.00 (25c better than model 6349.25... short:
    # model entry 109.75 vs actual 109.50 = worse by 0.25), exit target
    # actual 100.50 vs model 100.25 = worse by 0.25 -> drift negative.
    m = model_trade(range_high=110.0, range_low=100.0, extreme=112.0,
                    side="short", costs=MES)
    d = trade_drift(m, entry_actual=109.50, exit_event="target",
                    exit_actual=100.50, contracts=7, costs=MES)
    # model pnl = (109.75-100.25)*5*7 - 2*1.25*7; actual = (109.50-100.50)*...
    model = (109.75 - 100.25) * 5 * 7 - 2.50 * 7
    actual = (109.50 - 100.50) * 5 * 7 - 2.50 * 7
    assert d == actual - model
    assert d < 0


def test_eod_exit_contributes_entry_side_drift_only() -> None:
    # EOD exits have no model price (we don't carry TV's close) — the
    # model books the SAME exit price, so drift isolates the entry side.
    m = model_trade(range_high=110.0, range_low=100.0, extreme=112.0,
                    side="short", costs=MES)
    d = trade_drift(m, entry_actual=109.75, exit_event="eod",
                    exit_actual=105.0, contracts=7, costs=MES)
    assert d == 0.0                   # perfect entry -> zero drift


def test_debrief_targets_the_right_trading_day_across_midnight() -> None:
    # A debrief firing on next-morning wake (after ET midnight) must
    # process YESTERDAY's session, not the runtime calendar date.
    from datetime import datetime

    from occams.paper import trading_day_of
    assert str(trading_day_of(datetime(2026, 7, 29, 17, 30))) == "2026-07-29"
    assert str(trading_day_of(datetime(2026, 7, 30, 3, 0))) == "2026-07-29"
    assert str(trading_day_of(datetime(2026, 7, 30, 8, 59))) == "2026-07-29"
    assert str(trading_day_of(datetime(2026, 7, 30, 9, 1))) == "2026-07-30"


def test_parser_rejects_prices_off_the_tick_grid() -> None:
    # Live catch 2026-07-30: '/range MES 7421.5 7399.55' parsed happily,
    # but .55 is impossible at a 0.25 tick. A typo'd level silently
    # corrupts the model's range/stop/size, so drift would measure the
    # typing, not the execution. Reject loudly instead.
    assert parse_command("/range MES 7421.5 7399.55") is None
    assert parse_command("/range MES 7421.5 7399.75") is not None
    assert parse_command("/setup MES long 7399.13") is None
    assert parse_command("/fills MES entry 7399.10 2") is None
    assert parse_command("/fills MES entry 7399.25 2") is not None


# ─── /ack grammar (B7.2) — records reality, never preference ───

def test_ack_placed():
    a = parse_command("/ack MES placed")
    assert a == AckLog("MES", "placed")


def test_ack_missed_requires_a_reason():
    """A bare 'missed' is rejected: the reason IS the process-defect
    record, and without it the drag number cannot be explained later."""
    assert parse_command("/ack MES missed") is None
    a = parse_command("/ack MES missed away from desk")
    assert a.state == "missed" and a.reason == "away from desk"


def test_ack_partial_needs_both_size_and_reason():
    assert parse_command("/ack MES partial 2") is None
    a = parse_command("/ack MES partial 2 only 2 of 3 filled")
    assert a.contracts == 2 and a.reason == "only 2 of 3 filled"


def test_ack_has_no_veto_verb():
    """B7-N1: there is deliberately no way to decline a card on judgement.
    Anything that is not placed/missed/partial is rejected outright."""
    for text in ("/ack MES declined", "/ack MES skip bad setup",
                 "/ack MES no", "/ack MES vetoed too risky"):
        assert parse_command(text) is None, text
