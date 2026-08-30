"""B7.1 — your replies drive the day, and only your prices get recorded.

The command handler is where a bad rule would do the most damage: it is the
only path that writes a fill. So the tests here are mostly about what it
must REFUSE to do.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aws import commands  # noqa: E402

DAY = "2026-07-31"
CARD = {"side": "long", "entry": 7480.25, "stop": 7470.75,
        "target": 7515.25, "contracts": 3, "extreme": 7477.75,
        "range_high": 7515.25, "range_low": 7480.25,
        "fired_at": "2026-07-31T09:45:00-04:00"}


@pytest.fixture
def doc():
    return {DAY: {"MES": {"phase": "carded", "sent": ["range", "card"],
                          "card": dict(CARD)},
                  "MNQ": {"phase": "idle", "sent": []}}}


def test_ack_placed_moves_to_working(doc):
    reply = commands.apply_command("/ack MES placed", doc, DAY)
    assert doc[DAY]["MES"]["phase"] == "working"
    assert "PLACED" in reply


def test_ack_missed_is_recorded_as_a_defect_not_a_trade(doc):
    reply = commands.apply_command("/ack MES missed away from desk", doc, DAY)
    assert doc[DAY]["MES"]["phase"] == "awaiting_fills"
    assert doc[DAY]["MES"]["defect"] == "away from desk"
    assert "not a trade avoided" in reply


def test_entry_fill_records_YOUR_price_and_watches_the_exit(doc):
    commands.apply_command("/ack MES placed", doc, DAY)
    reply = commands.apply_command("/fills MES entry 7480.25 3", doc, DAY)
    st = doc[DAY]["MES"]
    assert st["phase"] == "filled" and st["entry_price"] == 7480.25
    assert "Watching stop and target" in reply


def test_exit_fill_produces_a_recap_with_drift(doc):
    commands.apply_command("/ack MES placed", doc, DAY)
    commands.apply_command("/fills MES entry 7480.25 3", doc, DAY)
    reply = commands.apply_command("/fills MES stop 7470.50 3", doc, DAY)
    assert "TRADE COMPLETE" in reply and "drift" in reply
    assert "7480.25 -> 7470.5" in reply
    # the model entered at boundary + slippage; you got the boundary, so
    # your fill was BETTER and drift must be positive
    assert "+$" in reply.split("drift")[1]


def test_an_offtick_price_is_refused_not_rounded(doc):
    """Live catch 2026-07-30: 7399.55 is impossible at a 0.25 tick. A
    silently corrected price would make drift measure typing."""
    commands.apply_command("/ack MES placed", doc, DAY)
    reply = commands.apply_command("/fills MES entry 7480.30 3", doc, DAY)
    assert "Unrecognised" in reply
    assert "entry_price" not in doc[DAY]["MES"]


def test_there_is_no_way_to_decline_a_card(doc):
    """B7-N1. A veto would turn a sealed mechanical strategy into a
    discretionary one and void the measurement."""
    for text in ("/ack MES declined", "/ack MES no thanks",
                 "/ack MES veto too risky"):
        reply = commands.apply_command(text, doc, DAY)
        assert "Unrecognised" in reply
        assert doc[DAY]["MES"]["phase"] == "carded", "state must not move"


def test_acking_an_instrument_with_no_card_says_so(doc):
    reply = commands.apply_command("/ack MNQ placed", doc, DAY)
    assert "nothing to acknowledge" in reply
    assert doc[DAY]["MNQ"]["phase"] == "idle"


def test_unknown_instrument_is_rejected(doc):
    assert "Unknown instrument" in commands.apply_command(
        "/skip SPY whatever", doc, DAY)


def test_status_reports_the_card_and_phase(doc):
    out = commands.apply_command("/status", doc, DAY)
    assert "MES: carded" in out and "@7480.25" in out


def test_help_is_offered_for_a_bare_hello(doc):
    assert "/ack" in commands.apply_command("hello", doc, DAY)


def test_plain_chatter_is_ignored(doc):
    assert commands.apply_command("looks choppy today", doc, DAY) is None


# ─── B7.5 period recaps ───

def _completed(day, pnl=50.0, drift=1.0):
    return {day: {"MES": {"phase": "reconciled", "sent": [],
                          "card": {"side": "long", "contracts": 3,
                                   "entry": 100.0, "stop": 95.0,
                                   "target": 110.0},
                          "entry_price": 100.0, "exit_price": 110.0,
                          "exit_event": "target", "pnl": pnl,
                          "drift": drift}}}


def test_week_recap_is_available_on_demand(doc):
    doc.update(_completed("2026-07-30"))
    out = commands.apply_command("/week", doc, DAY)
    assert "WEEK RECAP" in out and "n=" in out


def test_every_period_recap_carries_the_small_sample_caveat(doc):
    doc.update(_completed("2026-07-30"))
    for cmd in ("/week", "/month", "/all"):
        out = commands.apply_command(cmd, doc, DAY)
        assert "early samples lie, optimistically" in out, cmd
        assert "+0.1R" in out, cmd


def test_all_spans_the_whole_ledger_not_a_fixed_window(doc):
    doc.update(_completed("2026-01-05"))          # far outside 31 days
    assert "trades 1" in commands.apply_command("/all", doc, DAY)
    assert "no completed trades yet" in commands.apply_command(
        "/month", doc, DAY)


def test_recaps_report_drag_not_just_wins(doc):
    doc.update(_completed("2026-07-30"))
    doc["2026-07-29"] = {"MES": {"phase": "awaiting_fills", "sent": [],
                                 "card": {"contracts": 3},
                                 "defect": "platform rejected the order"}}
    out = commands.apply_command("/week", doc, DAY)
    assert "operational drag" in out and "defects 1" in out
