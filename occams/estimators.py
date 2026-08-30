"""M2 — the domain quantities, with the estimand as a required argument.

M1 (`stats.py`) put the arithmetic in one audited place. This module exists
because that is not the error that cost us a result.

ICT-P2's arithmetic was PERFECT. It read -0.159 ATR at Cohen d = -0.43, six
times its own declared detectable floor, significant on both instruments, on
both sides, and at both horizons. Every robustness check a normal process
runs, passed. All of it was meaningless, because 94.8% of the number was the
reference price: the run measured the forward move from the swept LEVEL, and
on an up-sweep price is already ABOVE that level when the bar closes.

    C[end] - level  =  (C[at] - level)  +  (C[end] - C[at])
                        POSITIONAL          drift
                        positive by         the thing the
                        construction        claim is about

**A market that froze solid the instant it triggered would still print a
large continuation reading.** No significance test asks that question,
because none of them asks what price the number is measured from.

So the fix here is structural, not statistical:

- `reference` is a REQUIRED argument. There is no default, because the
  default is exactly what nobody thinks about.
- Any reference other than `AT_PRICE` carries a positional term, and this
  module **refuses to return it as a single number**. You get a
  `Decomposition` or you get an exception.
- The identity is checked on every call. It cannot fail unless this code is
  wrong, which is the point of asserting it.

What this module does NOT do is decide whether the estimand is right. It
makes the choice explicit and reviewable. Nothing makes it impossible.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from occams import execution as ex
from occams.audit import audited

AT_PRICE = "at_price"    # from where price actually is: the only clean one
AT_LEVEL = "at_level"    # from a named level — ICT-P2's mode
AT_FILL = "at_fill"      # from a DERIVED fill — ICT-P1's mode

REFERENCES = (AT_PRICE, AT_LEVEL, AT_FILL)

__all__ = ["AT_PRICE", "AT_LEVEL", "AT_FILL", "REFERENCES", "Decomposition",
           "FillMeasurement", "AmbiguousReference", "forward_return",
           "horizon_end", "measure_from_fill"]


class AmbiguousReference(ValueError):
    """A reference price that is not where price is, reported as if it were."""


@dataclass(frozen=True)
class Decomposition:
    """total = positional + drift, exactly.

    `positional` is where price already was relative to the reference at the
    moment of measurement. `drift` is what happened afterwards — the only
    term any forward-looking claim is about.
    """
    total: float
    positional: float
    drift: float
    truncated: bool
    bars: int

    @property
    def share_positional(self) -> float:
        """How much of the headline is the reference price. ICT-P2: 0.948."""
        return 0.0 if self.total == 0.0 else self.positional / self.total


@dataclass(frozen=True)
class FillMeasurement(Decomposition):
    """A decomposition whose reference price was DERIVED from the bars."""
    fill_index: int = -1
    fill_price: float = float("nan")


def horizon_end(n: int, at: int, horizon: int) -> tuple[int, bool]:
    """(end index, was it truncated).

    Truncation is at the session close because our rules are day-flat —
    there is no holding past 16:00 to measure. But a sample where 40% of
    observations ran off the end is a different sample from one where none
    did, so the flag is carried rather than swallowed.
    """
    end = at + horizon
    return (n - 1, True) if end > n - 1 else (end, False)


def _check(closes, at: int, horizon: int, direction: int, scale: float,
           reference: str) -> np.ndarray:
    a = np.asarray(closes, dtype=float).ravel()
    if reference not in REFERENCES:
        raise ValueError(f"reference={reference!r} is not one of "
                         f"{REFERENCES}. It has no default: the estimand is "
                         f"the decision this module exists to make explicit.")
    if direction not in (1, -1):
        raise ValueError(f"direction must be +1 or -1, got {direction!r}")
    if scale <= 0:
        raise ValueError(f"scale must be positive, got {scale}")
    if horizon < 1:
        raise ValueError(f"horizon must be at least 1 bar, got {horizon}")
    if not 0 <= at < a.size:
        raise ValueError(f"at={at} is outside the series (n={a.size})")
    if at >= a.size - 1:
        raise ValueError(
            f"at={at} is the last bar (n={a.size}) — there is no forward "
            f"window to measure. Returning 0 here would put a fabricated "
            f"observation into the sample.")
    if not np.isfinite(a[at]):
        raise ValueError(f"non-finite price at bar {at}")
    return a


@audited
def forward_return(closes, *, at: int, horizon: int, direction: int,
                   reference: str, level: float | None = None,
                   scale: float = 1.0, decompose: bool = False
                   ) -> float | Decomposition:
    """Signed forward return over `horizon` bars from `at`.

    `reference` says WHERE THE MEASUREMENT STARTS, and is required:

    - `AT_PRICE` — from `closes[at]`. The only reference with no positional
      term, and the only one that may be returned as a single number.
    - `AT_LEVEL` — from a named price (a swept extreme, a band, a gap
      midpoint). Requires `decompose=True`.
    - `AT_FILL`  — from a derived fill. Requires `decompose=True`; prefer
      `measure_from_fill`, which derives the fill for you.
    """
    a = _check(closes, at, horizon, direction, scale, reference)
    end, truncated = horizon_end(a.size, at, horizon)
    if not np.isfinite(a[end]):
        raise ValueError(f"non-finite price at bar {end}")

    if reference == AT_PRICE:
        ref = float(a[at])
    else:
        if level is None:
            raise ValueError(
                f"reference={reference!r} needs an explicit `level` — the "
                f"price the measurement starts from.")
        ref = float(level)
        if not decompose:
            raise AmbiguousReference(
                f"reference={reference!r} cannot be returned as a single "
                f"number. At bar {at} price is already away from the "
                f"reference, so the result carries a POSITIONAL term that is "
                f"positive by construction — a market that froze the instant "
                f"it triggered would still print a large reading. This is "
                f"exactly ICT-P2, where 94.8% of a d=-0.43 headline was the "
                f"reference price and the real drift crossed zero. Pass "
                f"decompose=True and read the `drift` term.")

    d = float(direction)
    positional = (float(a[at]) - ref) * d / scale
    drift = (float(a[end]) - float(a[at])) * d / scale
    total = (float(a[end]) - ref) * d / scale

    # cannot fail unless this code is wrong — which is why it is asserted
    if abs(total - positional - drift) > 1e-9 * max(1.0, abs(total)):
        raise AssertionError(
            f"decomposition identity broken: {total} != {positional} + "
            f"{drift}. This is an engine defect, not a market result.")

    if not decompose:
        return total
    return Decomposition(total=total, positional=positional, drift=drift,
                         truncated=truncated, bars=end - at)


@audited
def measure_from_fill(order: ex.Order, *, highs, lows, opens, closes,
                      placed_at: int, horizon: int, direction: int,
                      scale: float = 1.0, slippage: float = 0.0
                      ) -> FillMeasurement | None:
    """Measure forward from a fill that is DERIVED, never supplied.

    E1 joined to M2. The caller names an ORDER — kind, side, level — and the
    fill comes from what the market then did. There is deliberately no
    argument through which a fill price can be asserted, because that
    assertion is what made the fade's +0.1R an artifact.

    Returns None when the order never filled: a rule that produces no trade
    is a real outcome of the rule, not a missing observation. Raises
    `Unplaceable` when the order could not have been entered at all.
    """
    market = float(np.asarray(closes, dtype=float).ravel()[placed_at])
    ex.validate(order, market)                       # refuses before measuring
    got = ex.fill(order, highs, lows, opens, placed_at, slippage)
    if got is None:
        return None
    idx, price = got
    c = np.asarray(closes, dtype=float).ravel()
    if idx >= c.size - 1:
        return None                                  # filled on the last bar
    d = forward_return(c, at=idx, horizon=horizon, direction=direction,
                       reference=AT_FILL, level=price, scale=scale,
                       decompose=True)
    return FillMeasurement(total=d.total, positional=d.positional,
                           drift=d.drift, truncated=d.truncated, bars=d.bars,
                           fill_index=int(idx), fill_price=float(price))
