"""Synthetic 1-min market days with a plantable follow-through edge.

`make_days(n, seed, edge_follow, drift_pts)` builds TradingDays whose
opening range is noise; after the range, one side breaks and — with
probability `edge_follow` — price *continues* in the breakout direction by
~`drift_pts`. edge_follow=0.5 with symmetric drift is the no-edge world
(costs then make any breakout strategy negative). Deterministic per seed.

Used by the positive control (Phase 5) and the null-model rehearsal
(Phase 6 machinery). Never a substitute for real data.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from occams.harness import TradingDay

RANGE_BARS = 30
POST_BARS = 120
BASE = 5000.0


def _ohlc(closes: np.ndarray, start: float, ts0: str) -> pd.DataFrame:
    opens = np.concatenate(([start], closes[:-1]))
    jitter = 0.2
    high = np.maximum(opens, closes) + jitter
    low = np.minimum(opens, closes) - jitter
    idx = pd.date_range(ts0, periods=len(closes), freq="1min")
    return pd.DataFrame({"open": opens, "high": high, "low": low,
                         "close": closes}, index=idx)


def make_day(rng: np.random.Generator, day_date: date, *, edge_follow: float,
             drift_pts: float, atr: float,
             kick_scale: float = 1.0) -> TradingDay:
    # Opening range: mean-reverting noise around BASE, ~±0.5×ATR wide.
    range_closes = BASE + rng.normal(0.0, atr / 6.0, RANGE_BARS).cumsum() * 0.3
    range_bars = _ohlc(range_closes, BASE, f"{day_date} 09:31")

    # Post-range: break one side, then follow through (edge) or wander (noise).
    direction = 1.0 if rng.random() < 0.5 else -1.0
    follows = rng.random() < edge_follow
    drift = direction * drift_pts / POST_BARS if follows else 0.0
    noise = rng.normal(0.0, atr / 10.0, POST_BARS)
    # Push price through the range boundary early so the breakout triggers.
    # kick_scale=0 → a DEAD world: pure noise, no impulse. The impulse
    # itself is harvestable by breakout timing even with edge_follow=0
    # (direction-random), so only kick_scale=0 is a true negative control
    # at realistic ATR (found during PREREG v2, 2026-07-06).
    kick = (kick_scale * direction * (atr / 2.0)
            * np.exp(-np.arange(POST_BARS) / 5.0))
    steps = drift + noise + kick / 5.0
    post_closes = float(range_closes[-1]) + steps.cumsum()
    post_bars = _ohlc(post_closes, float(range_closes[-1]),
                      f"{day_date} 10:01")

    return TradingDay(date=day_date, session_bars=post_bars, atr=atr,
                      range_bars=range_bars)


def make_days(n: int, seed: int, *, edge_follow: float, drift_pts: float,
              atr: float = 8.0, kick_scale: float = 1.0) -> list[TradingDay]:
    rng = np.random.default_rng(seed)
    d0 = date(2024, 1, 2)
    return [make_day(rng, d0 + timedelta(days=i), edge_follow=edge_follow,
                     drift_pts=drift_pts, atr=atr, kick_scale=kick_scale)
            for i in range(n)]
