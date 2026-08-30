"""B2.3 — the session poller's pure core.

Given the bars visible so far (already delay-clipped by `occams.feed`), work
out what the day has done: is the opening range formed, has a breakout
failed, has the entry limit traded, has the stop or target traded.

Everything here is a pure function of bars, so the whole session can be
replayed against a recorded day and checked minute by minute. The IO — the
Lambda, Telegram, S3 state — is a thin shell around this.

**This module computes levels; it never computes a fill.** `touched()`
returns the time a level traded so the human can be told to look. Booking
the price we computed would drive drift to zero by construction and the
campaign would measure nothing (docs/day-state-machine.md).

The arithmetic mirrors `occams/fade.py` exactly — same boundary, same
`extreme ± k×height`, same true-risk sizing. A divergence between them is a
defect, not a variant.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from occams import cards
from occams.feed import Bar
from occams.paper import K_STOP, MAX_CONTRACTS, RISK_USD
from occams.sim import Costs

RANGE_OPEN = (9, 30)
RANGE_CLOSE = (9, 45)
SESSION_CLOSE = (16, 0)


def _hm(b: Bar) -> tuple[int, int]:
    return (b.ts.hour, b.ts.minute)


@dataclass(frozen=True)
class OpeningRange:
    high: float
    low: float
    bars: int

    @property
    def height(self) -> float:
        return self.high - self.low

    @property
    def complete(self) -> bool:
        """All 15 one-minute bars present. An incomplete range is a
        different range: carding off 11 bars would mean the human's chart
        and the poller disagree on the levels."""
        return self.bars == 15


@dataclass(frozen=True)
class Card:
    """What the human is told to place. Protocol #4a: a LIMIT at the
    boundary — a failure close is by definition back inside the range, so
    a stop order there is on the wrong side of market and unplaceable."""
    instrument: str
    side: str                 # "long" | "short"
    entry: float              # the boundary — a LIMIT, never a stop
    stop: float
    target: float
    contracts: int
    extreme: float
    range_high: float
    range_low: float
    fired_at: datetime

    @property
    def stand_aside(self) -> bool:
        return self.contracts < 1

    def telegram(self) -> str:
        """Delegates to occams.cards — B2.4: the chart, the phone and the
        local scripts must all say the same words."""
        if self.stand_aside:
            return cards.stand_aside_card(self.instrument, RISK_USD)
        return cards.setup_card(self.instrument, self.side, self.contracts,
                                self.entry, self.stop, self.target,
                                self.extreme)


def opening_range(bars: list[Bar]) -> OpeningRange | None:
    sel = [b for b in bars if RANGE_OPEN <= _hm(b) < RANGE_CLOSE]
    if not sel:
        return None
    return OpeningRange(max(b.high for b in sel), min(b.low for b in sel),
                        len(sel))


def detect_setup(bars: list[Bar], rng: OpeningRange, costs: Costs, *,
                 instrument: str, k_stop: float = K_STOP,
                 risk_usd: float = RISK_USD) -> Card | None:
    """First breakout, then the first close back inside it. One setup per
    day, matching the engine — a second breakout is never traded."""
    post = [b for b in bars if _hm(b) >= RANGE_CLOSE]
    bi = next((i for i, b in enumerate(post)
               if b.high > rng.high or b.low < rng.low), None)
    if bi is None or rng.height <= 0:
        return None
    up = post[bi].high > rng.high
    fi = next((i for i in range(bi, len(post))
               if (post[i].close < rng.high if up else
                   post[i].close > rng.low)), None)
    if fi is None:
        return None                       # breakout still holding
    span = post[bi:fi + 1]
    extreme = (max(b.high for b in span) if up else min(b.low for b in span))

    boundary = rng.high if up else rng.low
    sgn = -1.0 if up else 1.0
    ext = (extreme - rng.high) if up else (rng.low - extreme)
    stop_dist = ext + k_stop * rng.height
    entry = boundary                      # the LIMIT price the human places
    stop = boundary - sgn * stop_dist
    target = boundary + sgn * rng.height

    # True-risk sizing, identical to fade.py: the modelled fill carries
    # adverse slippage on both the entry and the stop.
    loss_pts = abs(stop - (boundary + sgn * costs.slippage)) + costs.slippage
    per_contract = loss_pts * costs.multiplier + 2 * costs.commission_per_side
    contracts = 0 if stop_dist < costs.tick_size else min(
        int(risk_usd // per_contract), MAX_CONTRACTS)
    return Card(instrument=instrument, side="short" if up else "long",
                entry=entry, stop=stop, target=target, contracts=contracts,
                extreme=extreme, range_high=rng.high, range_low=rng.low,
                fired_at=post[fi].ts)


def touched(bars: list[Bar], level: float, *, above: bool,
            after: datetime) -> datetime | None:
    """When a level first traded after `after`. `above=True` means price
    had to rise to it. Returns a TIME, never a price — the fill is the
    human's to report."""
    for b in bars:
        if b.ts <= after:
            continue
        if (b.high >= level) if above else (b.low <= level):
            return b.ts
    return None


def entry_touched(bars: list[Bar], card: Card) -> datetime | None:
    """A LIMIT sits on the far side of the failure close, so a long fills
    when price comes DOWN to it and a short when price comes UP. This is
    the inverse of a stop entry — the bug that shipped in Pine v1.0-v1.8."""
    return touched(bars, card.entry, above=(card.side == "short"),
                   after=card.fired_at)


def exit_touched(bars: list[Bar], card: Card, *, filled_at: datetime
                 ) -> tuple[str, datetime] | None:
    """Stop is checked before target on the same bar: with 1-minute bars we
    cannot know which came first, so the engine's conservative convention
    applies here too."""
    stop = touched(bars, card.stop, above=(card.side == "short"),
                   after=filled_at)
    tgt = touched(bars, card.target, above=(card.side == "long"),
                  after=filled_at)
    if stop and (not tgt or stop <= tgt):
        return "stop", stop
    if tgt:
        return "target", tgt
    return None
