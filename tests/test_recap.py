"""B7.4-B7.6 — recaps, and the honesty guard that has to survive contact.

The guard is the point of this file. A recap that quietly reports a
flattering expectancy off six trades is worse than no recap: it is the
exact failure the campaign's own history demonstrates (+1.2R after 3
trades, +0.69R after 4, +0.35R after 5, against a measured +0.1R).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aws import recap  # noqa: E402


def _trade(day, inst="MES", pnl=50.0, drift=1.0):
    return {day: {inst: {"phase": "reconciled",
                         "card": {"side": "long", "contracts": 3,
                                  "entry": 100.0, "stop": 95.0,
                                  "target": 110.0},
                         "entry_price": 100.0, "exit_price": 110.0,
                         "exit_event": "target", "pnl": pnl,
                         "drift": drift, "sent": []}}}


def test_small_samples_carry_the_caveat_and_the_baseline():
    doc = {}
    for i in range(6):
        doc.update(_trade(f"2026-08-0{i + 1}"))
    out = recap.period(doc, sorted(doc), "week")
    assert "n=6" in out
    assert "early samples lie, optimistically" in out
    assert "+0.1R" in out, "the measured baseline must sit beside it"


def test_the_caveat_drops_only_past_the_threshold():
    doc = {}
    for i in range(25):
        doc.update(_trade(f"2026-08-{i + 1:02d}"))
    out = recap.period(doc, sorted(doc), "month")
    assert "n=25" in out and "early samples lie" not in out


def test_sample_size_is_stated_before_any_number():
    doc = _trade("2026-08-03")
    out = recap.period(doc, ["2026-08-03"], "week")
    body = out.splitlines()
    assert body[0].endswith("RECAP") and body[1].startswith("n=")


def test_defects_and_no_fills_count_in_the_denominator():
    """A defect that dodges a loser is still a defect."""
    doc = {"2026-08-03": {
        "MES": {"phase": "awaiting_fills", "sent": [],
                "card": {"contracts": 3}, "defect": "away from desk"},
        "MNQ": {"phase": "awaiting_fills", "sent": [],
                "card": {"contracts": 2},
                "skip_reason": "no fill - limit not reached"}}}
    out = recap.period(doc, ["2026-08-03"], "week")
    assert "operational drag: 2 of 2 cards did not become trades" in out


def test_kill_thresholds_are_disarmed_before_trade_ten():
    assert "arm at trade 10" in recap.kill_status({"n": 4, "mean": -99.0,
                                                   "mean_abs": 99.0})


def test_kill_fires_on_mean_drift():
    assert recap.kill_status({"n": 12, "mean": -6.0, "mean_abs": 6.0}
                             ).startswith("KILL")


def test_kill_fires_on_sign_balanced_disagreement():
    """Mean nets out but the model is still wrong."""
    s = recap.kill_status({"n": 12, "mean": 0.5, "mean_abs": 12.0})
    assert s.startswith("KILL") and "model is wrong" in s


def test_a_silent_poller_is_reported_loudly():
    """B4.1. No cards and no polls looks exactly like a quiet day."""
    out = recap.daily({}, "2026-08-03", {"polls": 0})
    assert "THE POLLER DID NOT RUN" in out
    assert "not a quiet day" in out


def test_a_low_poll_count_is_flagged_without_shouting():
    out = recap.daily({}, "2026-08-03", {"polls": 12, "last_bar_age_min": 11})
    assert "12 polls" in out and "low - expected" in out
    assert "DID NOT RUN" not in out


def test_daily_recap_names_a_defect_as_not_a_trade_avoided():
    doc = {"2026-08-03": {"MES": {"phase": "awaiting_fills", "sent": [],
                                  "defect": "platform rejected the order"}}}
    out = recap.daily(doc, "2026-08-03", {"polls": 75})
    assert "not a trade avoided" in out
