"""B3.2 — the poll job replayed minute by minute over a real session.

The schedule fires ~75 times between 09:45 and 16:05, so the property that
matters most is that 75 passes produce exactly the messages one pass would.
This drives the job over 2026-07-31 at one-minute resolution with a fake
clock and a fake sender, and checks both what is said and how often.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aws import jobs  # noqa: E402

from occams.feed import ET, ReplaySource, bars_from_fixture  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "bars-2026-07-31.json"
DAY = date(2026, 7, 31)


@pytest.fixture
def sent(monkeypatch) -> list[str]:
    out: list[str] = []
    monkeypatch.setattr(jobs, "_send", out.append)
    return out


def _source(now_et: datetime) -> ReplaySource:
    return ReplaySource(bars_from_fixture(json.loads(FIXTURE.read_text())),
                        now=lambda: now_et.astimezone(timezone.utc))


# The delayed tape sets the real timeline, and it is not the obvious one:
#   09:44 bar closes 09:45 -> range complete and VISIBLE at 09:55
#   09:45 setup bar closes 09:46 -> card sent at 09:56
#   human acks ~09:57
#   09:46 entry bar closes 09:47 -> entry notice at 09:57
#   09:49 stop bar  closes 09:50 -> stop notice  at 10:00
# In real time the trade was over at 09:49, before the card could exist.
# PAPER-PREREG §3 is what makes that sound: the venue fills on the same
# delayed tape, so the sequence is shifted, not distorted.
ACK_AT = (9, 57)
FILL_AT = (9, 58)


def _drive(st: dict, sent: list[str], *, until=(10, 5), acks=None):
    """Poll every minute from 09:30 to `until`, applying human replies at
    the minute they are keyed in `acks`."""
    acks = acks or {}
    t = datetime(2026, 7, 31, 9, 30, tzinfo=ET)
    end = datetime(2026, 7, 31, until[0], until[1], tzinfo=ET)
    while t <= end:
        jobs.poll_instrument("MES", st, DAY, _source(t))
        if (t.hour, t.minute) in acks:
            event, extra = acks[(t.hour, t.minute)]
            jobs._advance(st, event)
            st.update(extra)
        t += timedelta(minutes=1)
    return st


def _fresh() -> dict:
    return {"phase": "idle", "sent": []}


def test_range_and_card_are_each_sent_exactly_once(sent):
    """~30 polls, two messages."""
    _drive(_fresh(), sent)
    assert sum("opening range" in m for m in sent) == 1
    assert sum("BUY LIMIT" in m for m in sent) == 1


def test_the_range_message_carries_the_verified_levels(sent):
    _drive(_fresh(), sent)
    assert "/range MES 7515.25 7480.25" in sent[0]


def test_the_card_names_a_limit_and_asks_for_an_ack(sent):
    _drive(_fresh(), sent)
    card = next(m for m in sent if "LIMIT" in m)
    assert "BUY LIMIT 3x @ 7480.25" in card
    assert "stop 7470.75" in card and "target 7515.25" in card
    assert "/ack MES placed|missed" in card


def test_no_entry_notice_until_the_card_is_acked(sent):
    """The poller must not chase a level for an order that was never
    placed — B7-N1 makes /ack the record of execution reality."""
    _drive(_fresh(), sent)
    assert not any("entry level" in m for m in sent)


def test_entry_notice_fires_once_after_ack_and_asks_for_YOUR_fill(sent):
    st = _drive(_fresh(), sent, acks={ACK_AT: ("ack_placed", {})})
    notes = [m for m in sent if "entry level" in m]
    assert len(notes) == 1
    assert "traded at 09:46 ET" in notes[0]
    assert "<YOUR FILL>" in notes[0], "must never state a computed price"
    assert st["phase"] == "working"


def test_exit_notice_fires_once_and_names_the_stop(sent):
    st = _drive(_fresh(), sent, acks={
        ACK_AT: ("ack_placed", {}),
        FILL_AT: ("fills_entry",
                  {"filled_at": datetime(2026, 7, 31, 9, 46,
                                         tzinfo=ET).isoformat()})})
    notes = [m for m in sent if "STOP level" in m]
    assert len(notes) == 1
    assert "7470.75 traded at 09:49 ET" in notes[0]
    assert "<YOUR FILL>" in notes[0]
    assert st["phase"] == "filled"


def test_a_full_session_of_polls_says_nothing_extra(sent):
    """The idempotency claim, end to end: every send is tagged and the tag
    is checked, so re-running the whole day changes nothing."""
    st = _drive(_fresh(), sent, acks={
        ACK_AT: ("ack_placed", {}),
        FILL_AT: ("fills_entry",
                  {"filled_at": datetime(2026, 7, 31, 9, 46,
                                         tzinfo=ET).isoformat()})})
    first = list(sent)
    sent.clear()
    _drive(st, sent)                      # replay every poll again
    assert sent == [], "a repeat pass must be silent"
    assert len(first) == 4                # range, card, entry, stop


def test_nothing_is_sent_before_the_range_completes(sent):
    st = _fresh()
    jobs.poll_instrument("MES", st, DAY,
                         _source(datetime(2026, 7, 31, 9, 40, tzinfo=ET)))
    assert sent == [] and st["phase"] == "idle"


def test_poll_health_counter_increments_on_every_pass(sent):
    """B4.1 depends on this number, and a counter that silently stays at
    zero would make the dead-man's switch cry wolf every evening."""
    st = _fresh()
    for minute in (35, 40, 45, 50):
        jobs.poll_instrument("MES", st, DAY,
                             _source(datetime(2026, 7, 31, 9, minute,
                                              tzinfo=ET)))
    assert st["polls"] == 4


def test_last_bar_age_is_recorded_for_the_health_line(sent):
    st = _fresh()
    jobs.poll_instrument("MES", st, DAY,
                         _source(datetime(2026, 7, 31, 10, 0, tzinfo=ET)))
    assert st["last_bar"].startswith("2026-07-31T09:")


def test_the_morning_job_refuses_to_fire_at_a_weekend(monkeypatch):
    """trading_day_of maps a Saturday morning back to Friday, so the
    mapped date alone would send a Friday card on Saturday."""
    from datetime import datetime as dt

    from occams.feed import ET as _ET
    out = jobs.run_morning(dt(2026, 8, 1, 8, 46, tzinfo=_ET))   # Saturday
    assert out["skipped"] == "weekend"
