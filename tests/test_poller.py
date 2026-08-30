"""B2.3 — the poller replayed against a day whose answer is known.

2026-07-31 is the reference case because every number in it was verified
three independent ways on the day: the opening range agreed to the tick
across CME, Yahoo and the chart, and the outcome was read off the tape
(setup 09:45, entry level 09:46, stop 09:49).

If the poller reproduces that minute by minute it is doing the same thing
the human's chart does — which is the only claim it needs to support.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from occams.feed import ET, ReplaySource, bars_from_fixture
from occams.poller import (Card, detect_setup, entry_touched, exit_touched,
                           opening_range)
from occams.sim import Costs

FIXTURE = Path(__file__).parent / "fixtures" / "bars-2026-07-31.json"
DAY = date(2026, 7, 31)
MES = Costs(multiplier=5.0, tick_size=0.25, commission_per_side=1.25,
            slippage_ticks=1)


def _at(h: int, m: int) -> datetime:
    return datetime(2026, 7, 31, h, m, tzinfo=ET).astimezone(timezone.utc)


@pytest.fixture
def bars():
    src = ReplaySource(bars_from_fixture(json.loads(FIXTURE.read_text())),
                       now=lambda: _at(16, 0))
    return src.bars("MES", DAY)


@pytest.fixture
def card(bars) -> Card:
    return detect_setup(bars, opening_range(bars), MES, instrument="MES")


def test_opening_range_matches_all_three_sources(bars):
    rng = opening_range(bars)
    assert (rng.high, rng.low) == (7515.25, 7480.25)
    assert rng.height == 35.0 and rng.complete


def test_card_matches_the_levels_the_chart_showed(card):
    assert card.side == "long"
    assert (card.entry, card.stop, card.target) == (7480.25, 7470.75, 7515.25)
    assert card.contracts == 3
    assert card.extreme == 7477.75
    assert card.fired_at.strftime("%H:%M") == "09:45"


def test_the_card_names_a_limit_not_a_stop(card):
    """Protocol #4a. The word that cost two of the first three setups."""
    text = card.telegram()
    assert "BUY LIMIT" in text and "STOP" not in text.split("| stop")[0]
    assert "/ack MES placed|missed" in text


def test_entry_and_exit_times_match_the_tape(card, bars):
    assert entry_touched(bars, card).strftime("%H:%M") == "09:46"
    kind, when = exit_touched(bars, card, filled_at=entry_touched(bars, card))
    assert kind == "stop"
    assert when.strftime("%H:%M") == "09:49"


def test_a_long_entry_fills_on_a_move_DOWN_to_the_limit(card, bars):
    """The inverted-fill bug from Pine v1.0-v1.8: testing `high >= entry`
    for a long is already true the instant the setup fires, so it would
    report an immediate fill every day. The 09:45 bar closed at 7481.25,
    ABOVE the 7480.25 limit — a fill there would be the bug."""
    assert entry_touched(bars, card) > card.fired_at
    fill_bar = next(b for b in bars if b.ts == entry_touched(bars, card))
    assert fill_bar.low <= card.entry, "must trade DOWN to the limit"


def test_no_setup_before_the_range_completes(bars):
    early = [b for b in bars if (b.ts.hour, b.ts.minute) < (9, 45)]
    rng = opening_range(early)
    assert rng.bars < 15 or rng.complete
    assert detect_setup(early, rng, MES, instrument="MES") is None


def test_an_incomplete_range_is_visible_as_incomplete(bars):
    partial = [b for b in bars if (b.ts.hour, b.ts.minute) < (9, 40)]
    rng = opening_range(partial)
    assert rng.bars == 10 and not rng.complete


def test_stand_aside_when_the_stop_is_too_far(bars):
    """A stop wide enough that one contract exceeds the risk budget must
    produce a stand-aside, never a rounded-down zero-size order."""
    rng = opening_range(bars)
    card = detect_setup(bars, rng, MES, instrument="MES", k_stop=40.0)
    assert card.stand_aside and card.contracts == 0
    assert "STAND ASIDE" in card.telegram() and "/skip" in card.telegram()


def test_poller_sizing_equals_the_sealed_engine(card):
    """fade.py's true-risk formula, recomputed here. A divergence between
    the poller and the engine is a defect, not a variant (B1.4)."""
    loss_pts = abs(card.stop - (card.entry + MES.slippage)) + MES.slippage
    per = loss_pts * MES.multiplier + 2 * MES.commission_per_side
    assert card.contracts == min(int(175.0 // per), 30) == 3
