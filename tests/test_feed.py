"""B2.1/B2.2 — the DataSource port, and delay parity as an executable rule.

B-C1 is the constraint that voids the campaign if broken, so the tests that
matter here are the ones asserting a fresher bar can NEVER reach the engine.
No network: every case runs off the recorded 2026-07-31 fixture.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from occams.feed import ET, Bar, ReplaySource, bars_from_fixture

FIXTURE = Path(__file__).parent / "fixtures" / "bars-2026-07-31.json"
DAY = date(2026, 7, 31)


@pytest.fixture
def bars() -> dict[str, list[Bar]]:
    return bars_from_fixture(json.loads(FIXTURE.read_text()))


def _at(h: int, m: int) -> datetime:
    """Wall-clock UTC corresponding to an ET time on the fixture's day."""
    return datetime(2026, 7, 31, h, m, tzinfo=ET).astimezone(timezone.utc)


def test_fixture_reproduces_the_known_opening_range(bars):
    """The range that CME, Yahoo and the chart all agreed on."""
    src = ReplaySource(bars, now=lambda: _at(16, 0))
    rng = [b for b in src.bars("MES", DAY)
           if (9, 30) <= (b.ts.hour, b.ts.minute) < (9, 45)]
    assert len(rng) == 15
    assert max(b.high for b in rng) == 7515.25
    assert min(b.low for b in rng) == 7480.25


def test_no_bar_fresher_than_the_venue_delay_can_ever_be_returned(bars):
    """B-C1. Deciding on newer information than the venue fills at would
    flatter every fill and void the parity measurement."""
    for hh, mm in ((9, 50), (10, 0), (11, 30), (16, 0)):
        src = ReplaySource(bars, now=lambda h=hh, m=mm: _at(h, m))
        cutoff = _at(hh, mm) - timedelta(minutes=10)
        for b in src.bars("MES", DAY):
            assert b.closed_at <= cutoff, f"leaked {b.ts:%H:%M} at {hh}:{mm}"


def test_a_bar_becomes_visible_only_after_it_has_CLOSED(bars):
    """Gating on the OPEN time would leak the last 10 minutes of a bar that
    is still forming — the subtle half of the parity rule."""
    # the 09:45 bar opens 09:45, closes 09:46 -> visible from 09:56 ET
    just_before = ReplaySource(bars, now=lambda: _at(9, 55)).bars("MES", DAY)
    just_after = ReplaySource(bars, now=lambda: _at(9, 56)).bars("MES", DAY)
    stamps_before = {(b.ts.hour, b.ts.minute) for b in just_before}
    stamps_after = {(b.ts.hour, b.ts.minute) for b in just_after}
    assert (9, 45) not in stamps_before
    assert (9, 45) in stamps_after


def test_the_setup_bar_is_invisible_until_its_delayed_arrival(bars):
    """Concretely: 2026-07-31's failure close printed at 09:45 ET and the
    trade was stopped by 09:49 in real time. On the delayed tape the human
    could not have seen the setup before 09:56 — which is exactly why the
    uniform-delay argument (PAPER-PREREG §3) requires the venue to fill on
    the same delayed tape, and why the poller must not run ahead of it."""
    src = ReplaySource(bars, now=lambda: _at(9, 50))
    assert max(b.ts for b in src.bars("MES", DAY)).strftime("%H:%M") == "09:39"


def test_a_shorter_delay_is_honoured_when_configured(bars):
    """At live, feed and execution are both real-time and the constraint
    dissolves — so the delay is a parameter, not a constant."""
    src = ReplaySource(bars, venue_delay_minutes=0, now=lambda: _at(9, 50))
    assert max(b.ts for b in src.bars("MES", DAY)).strftime("%H:%M") == "09:49"


def test_unknown_day_and_instrument_return_nothing_rather_than_guessing(bars):
    src = ReplaySource(bars, now=lambda: _at(16, 0))
    assert src.bars("MES", date(2026, 7, 30)) == []
    assert src.bars("SPY", DAY) == []


def test_both_instruments_are_present(bars):
    src = ReplaySource(bars, now=lambda: _at(16, 0))
    assert len(src.bars("MES", DAY)) == len(src.bars("MNQ", DAY)) == 31
