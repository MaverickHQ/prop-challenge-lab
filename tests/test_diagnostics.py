"""Phase B tooling sanity — fade_anatomy on a hand-built day where every
outcome is known by inspection (garbage-in guard for the diagnostics)."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from occams.harness import TradingDay

from diagnostics import fade_anatomy


def bars(rows):
    idx = pd.date_range("2024-01-02 09:30", periods=len(rows), freq="1min")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"],
                        index=idx)


def test_up_breakout_failure_fade_wins_to_far_side() -> None:
    # Range 100-110 (height 10). Breaks up to 112 (extreme ext 0.2), closes
    # back below 110 (failure), then travels down through 100 (far side)
    # without touching the k-stop above the extreme -> win at every k.
    rb = bars([(105, 110, 100, 106)])
    sb = bars([
        (109, 112, 108, 111),    # breakout: high 112 > 110
        (111, 111.5, 108, 109),  # failure: close 109 < 110; extreme 112
        (109, 110, 104, 105),    # travelling down (stops untouched)
        (105, 106, 99, 100),     # target: low 99 <= 100 -> WIN
    ])
    day = TradingDay(date=date(2024, 1, 2), session_bars=sb, atr=8.0,
                     range_bars=rb)
    r = fade_anatomy(day)
    assert r["setup"] == "failed" and r["side"] == "up"
    assert abs(r["extreme_ext"] - 0.2) < 1e-9
    assert r["k0.25"] == "win" and r["k0.5"] == "win"


def test_stop_touch_before_target_is_a_loss() -> None:
    # Same failure, but price first pops to 115: >= 112 + 0.25*10 = 114.5
    # (k=0.25 stop hit -> loss) but < 112 + 0.5*10 = 117 (k=0.5 survives,
    # then reaches the target -> win). Distinguishes the stops.
    rb = bars([(105, 110, 100, 106)])
    sb = bars([
        (109, 112, 108, 111),
        (111, 111.5, 108, 109),
        (110, 115, 109, 111),    # k=0.25 stop (114.5) hit; k=0.5 (117) not
        (111, 112, 99, 100),     # far side reached
    ])
    day = TradingDay(date=date(2024, 1, 2), session_bars=sb, atr=8.0,
                     range_bars=rb)
    r = fade_anatomy(day)
    assert r["k0.25"] == "loss"
    assert r["k0.5"] == "win"


def test_no_breakout_and_held_breakout_are_classified() -> None:
    rb = bars([(105, 110, 100, 106)])
    inside = bars([(105, 109, 101, 106)] * 3)
    day = TradingDay(date=date(2024, 1, 2), session_bars=inside, atr=8.0,
                     range_bars=rb)
    assert fade_anatomy(day)["setup"] == "none"
    held = bars([(109, 112, 108, 111), (111, 113, 110.5, 112.5)])
    day2 = TradingDay(date=date(2024, 1, 3), session_bars=held, atr=8.0,
                      range_bars=rb)
    assert fade_anatomy(day2)["setup"] == "held"
