"""Family 2 — the failed-breakout fade (Phase C).

Semantics mirror `scripts/diagnostics.py::fade_anatomy` one-for-one so the
sealed run measures the same object the dev screening measured, with real
fills, costs, true-risk sizing, and EOD exits added:

  breakout  — first bar HIGH strictly above the range high (or LOW below
              the low); the earlier side wins, one setup per day.
  failure   — first bar (from the breakout bar on) whose CLOSE is back
              inside the range. The extreme includes that bar.
  entry     — a stop order AT the boundary, armed only after the breakout:
              it fills on the re-cross (fade short at hi − slip). This is
              executable live and is the mirror of the ORB entry.
  stop      — extreme ± k_stop × height (touch; gap-open fills worse).
  target    — the far side of the range (touch; no price-improvement
              credit — conservative). Same-bar stop+target = stop first.
  EOD       — force-flat at the last close.
  direction — "fade" trades against the breakout; "follow" is the exact
              mirror (same distances, breakout side) used by the coin
              null, so G2 isolates the DIRECTIONAL edge alone.

Sizing uses the TRUE per-contract loss (stop distance from the actual
entry, plus exit slippage and both commissions), floors at stand-aside,
caps at the venue position limit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from occams.harness import TradingDay
from occams.sim import Costs
from occams.strategy import NoTrade


@dataclass(frozen=True)
class FadeParams:
    """Also the per-day plan: everything else derives from the day."""
    k_stop: float                  # stop = extreme ± k_stop × height
    width_max: float | None = None  # height/ATR ceiling (absolute, sealed)
    risk_usd: float = 175.0
    max_contracts: int = 30        # venue cap (30 micros)
    direction: str = "fade"        # "fade" | "follow" (the null's face)


@dataclass
class FadeTrade:
    side: str
    entry_price: float
    exit_price: float
    contracts: int
    pnl_usd: float


@dataclass
class FadeResult:
    trades: list[FadeTrade] = field(default_factory=list)
    day_pnl_usd: float = 0.0


def _book(side: str, entry: float, exit_: float, contracts: int,
          costs: Costs) -> FadeTrade:
    direction = 1.0 if side == "long" else -1.0
    points = (exit_ - entry) * direction
    pnl = contracts * (points * costs.multiplier
                       - 2 * costs.commission_per_side)
    return FadeTrade(side=side, entry_price=entry, exit_price=exit_,
                     contracts=contracts, pnl_usd=pnl)


def simulate_fade_day(day: TradingDay, params: FadeParams, costs: Costs,
                      direction: str | None = None) -> FadeResult:
    direction = direction or params.direction
    rb, sb = day.range_bars, day.session_bars
    if rb is None or rb.empty or sb.empty:
        return FadeResult()
    hi = float(rb["high"].max())
    lo = float(rb["low"].min())
    height = hi - lo
    if height <= 0:
        return FadeResult()
    highs = sb["high"].to_numpy(float)
    lows = sb["low"].to_numpy(float)
    closes = sb["close"].to_numpy(float)
    opens = sb["open"].to_numpy(float)
    slip = costs.slippage

    up = np.argmax(highs > hi) if (highs > hi).any() else None
    dn = np.argmax(lows < lo) if (lows < lo).any() else None
    if up is None and dn is None:
        return FadeResult()
    broke_up = dn is None or (up is not None and up <= dn)
    b = int(up if broke_up else dn)

    inside = closes[b:] < hi if broke_up else closes[b:] > lo
    if not inside.any():
        return FadeResult()                      # breakout held to the close
    f = b + int(np.argmax(inside))
    extreme = float(highs[b:f + 1].max()) if broke_up \
        else float(lows[b:f + 1].min())
    ext = (extreme - hi) if broke_up else (lo - extreme)
    stop_dist = ext + params.k_stop * height     # from the boundary

    # Geometry: fade trades back across the range; follow is the mirror
    # with identical distances on the breakout side (the null's face).
    boundary = hi if broke_up else lo
    fade_short = broke_up                        # fade the up-break = short
    if direction == "follow":
        fade_short = not fade_short
    side = "short" if fade_short else "long"
    sgn = -1.0 if fade_short else 1.0
    entry = boundary + sgn * slip                # stop-entry fill
    stop_level = boundary - sgn * stop_dist      # extreme ± k×h, exact
    target = boundary + sgn * height             # far side (fade) / mirror

    # True per-contract loss: stop fill carries adverse slippage too.
    loss_pts = abs(stop_level - entry) + slip
    per_contract = loss_pts * costs.multiplier + 2 * costs.commission_per_side
    if stop_dist < costs.tick_size:
        return FadeResult()
    contracts = int(params.risk_usd // per_contract)
    if contracts < 1:
        return FadeResult()
    contracts = min(contracts, params.max_contracts)

    for i in range(f + 1, len(highs)):
        hit_stop = (highs[i] >= stop_level) if fade_short \
            else (lows[i] <= stop_level)
        hit_tgt = (lows[i] <= target) if fade_short \
            else (highs[i] >= target)
        gapped = (opens[i] >= stop_level) if fade_short \
            else (opens[i] <= stop_level)
        if hit_stop:                             # conservative: stop first
            fill = opens[i] if gapped else stop_level
            t = _book(side, entry, fill + (slip if fade_short else -slip),
                      contracts, costs)
            return FadeResult(trades=[t], day_pnl_usd=t.pnl_usd)
        if hit_tgt:                              # no improvement credit
            t = _book(side, entry, target + (slip if fade_short else -slip),
                      contracts, costs)
            return FadeResult(trades=[t], day_pnl_usd=t.pnl_usd)
    eod = closes[-1] + (slip if fade_short else -slip)
    t = _book(side, entry, eod, contracts, costs)
    return FadeResult(trades=[t], day_pnl_usd=t.pnl_usd)


def make_fade_strategy(params: FadeParams, costs):
    """TradingDay -> FadeParams | NoTrade, for the harness ledger."""
    def make_plan(day: TradingDay):
        if day.range_bars is None or day.range_bars.empty:
            return NoTrade(reason="no opening range available")
        height = (float(day.range_bars["high"].max())
                  - float(day.range_bars["low"].min()))
        if height <= 0:
            return NoTrade(reason="degenerate opening range (zero height)")
        if params.width_max is not None and day.atr > 0 \
                and height / day.atr > params.width_max:
            return NoTrade(reason="range too wide for the sealed filter")
        return params
    return make_plan


def make_fade_null_strategy(seed: int, params: FadeParams, costs):
    """The coin null: at the SAME failure moment with the SAME distances,
    a per-day deterministic coin picks fade vs follow — G2 then measures
    the directional edge and nothing else."""
    def make_plan(day: TradingDay):
        base = make_fade_strategy(params, costs)(day)
        if isinstance(base, NoTrade):
            return base
        rng = np.random.default_rng([seed, day.date.toordinal()])
        direction = "fade" if rng.random() < 0.5 else "follow"
        return FadeParams(k_stop=params.k_stop, width_max=params.width_max,
                          risk_usd=params.risk_usd,
                          max_contracts=params.max_contracts,
                          direction=direction)
    return make_plan
