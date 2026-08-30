"""B2.4 — the chart, the phone and the local scripts must say one thing.

If they drift, the human reads one instruction on the chart and a different
one on their phone. AMENDMENT-4a is what that costs: the card said STOP
where only a LIMIT is placeable, and two of the campaign's first three
setups were never executed.

Pine cannot import Python, so the shared vocabulary is pinned here and the
`.pine` file is asserted to contain every phrase. Change the wording in one
place and this fails.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from occams import cards

PINE = Path(__file__).resolve().parent.parent / "tools" / "fade_campaign.pine"


@pytest.mark.parametrize("phrase", cards.PINE_REQUIRED)
def test_the_pine_aid_uses_the_same_wording(phrase):
    assert phrase in PINE.read_text(), (
        f"the chart no longer says {phrase!r}. Either update "
        f"tools/fade_campaign.pine or occams/cards.py — never one alone.")


def test_the_order_line_names_a_limit_never_a_stop():
    """Protocol #4a, asserted rather than trusted."""
    line = cards.order_line("long", 3, 7480.25, 7470.75, 7515.25)
    assert line == "BUY LIMIT 3x @ 7480.25 | stop 7470.75 | target 7515.25"
    assert "STOP" not in line.split("| stop")[0]


def test_the_short_side_is_also_a_limit():
    line = cards.order_line("short", 1, 7421.5, 7450.85, 7399.75)
    assert line.startswith("SELL LIMIT 1x @ 7421.5")


def test_no_pine_file_still_says_stop_at_the_entry():
    """The exact defect: 'BUY STOP'/'SELL STOP' must not reappear."""
    text = PINE.read_text()
    assert "BUY STOP" not in text and "SELL STOP" not in text


def test_whole_numbers_print_without_a_trailing_zero():
    """MNQ levels are often integral; 28415 must not read as 28415.0 on
    the phone when the chart shows 28415."""
    assert "28415 " in cards.order_line("long", 1, 28415.0, 28344.85,
                                        28725.75)


def test_a_fill_prompt_never_contains_a_price_to_copy():
    """The measurement depends on the human reading their own fill. A
    prompt that pre-filled a number would make drift measure copying."""
    p = cards.fill_prompt("MES", "stop", 7470.75, "09:49", 3)
    assert cards.FILL_PLACEHOLDER in p
    assert p.rstrip().endswith(f"{cards.FILL_PLACEHOLDER} 3")


def test_stand_aside_asks_for_a_skip_not_a_zero_size_order():
    c = cards.stand_aside_card("MNQ", 175.0)
    assert "STAND ASIDE" in c and "/skip MNQ" in c
    assert "0x" not in c, "a zero-size order must never be offered"


def test_setup_card_carries_the_ack_prompt():
    c = cards.setup_card("MES", "long", 3, 7480.25, 7470.75, 7515.25,
                         7477.75)
    assert "/ack MES placed|missed <reason>" in c
    assert "/setup MES long 7477.75" in c
