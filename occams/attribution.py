"""Q2 — why each failed attempt died, not just how many did.

E2 reported P(pass) 0.042 and P(breach) 0.440. Those do not sum to one, so
roughly half of all attempts ended in some unnamed way — and "unnamed" turns
out to contain at least three genuinely different outcomes with genuinely
different remedies:

- an attempt that **ran out of horizon** while still alive wants more days,
  not less size
- an attempt that **breached** wants less size, and more days would only
  have let it breach sooner
- an attempt **blocked by a consistency rule** wants neither: it had the
  money and could not claim it

A single probability is a scoreboard. This is a diagnosis.

**Exactly one reason per path.** A path can have several things wrong with
it; only one ended it. Which one is decided by a declared precedence
(`REASONS`) rather than by whichever check happens to run first — the
latter reads as an ordering detail and behaves as a definition.

The shares are computed over **all attempts, including passes**, so P(pass)
and the failure shares sum to one. Reporting shares of failures only invites
the reader to double-count.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from occams.rules import ChallengeConfig, Status

__all__ = ["Failure", "REASONS", "Attribution", "attribute", "tally"]


class Failure(Enum):
    BREACH_DRAWDOWN = "breach_drawdown"
    NEVER_TRADED = "never_traded"
    CONSISTENCY = "consistency"
    MIN_DAYS = "min_days"
    TIMEOUT_IN_PROFIT = "timeout_in_profit"
    TIMEOUT_UNDERWATER = "timeout_underwater"


#: Precedence, highest first. Declared rather than emergent: an attempt that
#: breached below target had several things wrong, and only one ended it.
REASONS: tuple[Failure, ...] = (
    Failure.BREACH_DRAWDOWN,   # terminal — nothing else could still happen
    Failure.NEVER_TRADED,      # instrument failure, never a market result
    Failure.CONSISTENCY,       # had the money, could not claim it
    Failure.MIN_DAYS,          # had the money, had not been there long enough
    Failure.TIMEOUT_IN_PROFIT,   # short of target, but ahead — wants days
    Failure.TIMEOUT_UNDERWATER,  # short of target and BEHIND — wants a strategy
)


@dataclass(frozen=True)
class Attribution:
    reason: Failure
    detail: str


def attribute(run, cfg: ChallengeConfig, *, horizon: int) -> Attribution:
    """The single reason this attempt ended. Raises on a pass."""
    if run.status is Status.PASSED:
        raise ValueError("run PASSED — a success has no failure reason, and "
                         "silently assigning one would corrupt the tally")

    if run.status is Status.BREACHED:
        return Attribution(
            Failure.BREACH_DRAWDOWN,
            f"equity {run.final_equity:,.0f} hit the trailing floor after "
            f"{run.days_used} days")

    marks = list(run.equity_marks or [])
    if marks and max(marks) == min(marks) == cfg.account:
        return Attribution(
            Failure.NEVER_TRADED,
            f"{run.days_used} days, equity never moved — an instrument "
            f"failure, not a market result (verdict #1's lesson: silence "
            f"must never be read as a NO-GO)")

    profit = run.final_equity - cfg.account
    reached = profit >= cfg.target

    if reached and cfg.consistency_frac is not None:
        gains = [b - a for a, b in zip(marks, marks[1:])] if len(marks) > 1 \
            else [profit]
        largest = max(gains) if gains else profit
        if profit > 0 and largest > cfg.consistency_frac * profit:
            return Attribution(
                Failure.CONSISTENCY,
                f"target reached, but the largest day was "
                f"{largest / profit:.0%} of net profit against a "
                f"{cfg.consistency_frac:.0%} limit — the money was there and "
                f"could not be claimed")

    if reached and run.days_used < cfg.min_days:
        return Attribution(
            Failure.MIN_DAYS,
            f"target reached on day {run.days_used}, but {cfg.min_days} "
            f"trading days are required")

    # Splitting the timeout bucket is not cosmetic. "Ran out of days" reads
    # as "nearly made it" and implies the remedy is a longer horizon. For a
    # losing strategy it is the opposite: those attempts were bleeding
    # slowly enough not to breach, and more days would have produced more
    # BREACHES, not more passes. The first run of Q2 put both in one bucket
    # and the label would have misled anyone reading it.
    short = cfg.target - profit
    if profit > 0:
        return Attribution(
            Failure.TIMEOUT_IN_PROFIT,
            f"still alive and AHEAD at day {run.days_used} of {horizon}, "
            f"{short:,.0f} short of the {cfg.target:,.0f} target — a longer "
            f"horizon is the remedy that fits")
    return Attribution(
        Failure.TIMEOUT_UNDERWATER,
        f"still alive but DOWN {-profit:,.0f} at day {run.days_used} of "
        f"{horizon} — not 'nearly there'. More days would have produced "
        f"more breaches, not more passes")


def tally(runs, cfg: ChallengeConfig, *, horizon: int) -> dict:
    """Decompose a set of attempts. `p_pass` plus every share sums to 1."""
    runs = list(runs)
    if not runs:
        raise ValueError("no attempts to attribute — an empty decomposition "
                         "reported as zeros is a wrong answer, not a null")

    passed = sum(1 for r in runs if r.status is Status.PASSED)
    counts: Counter[str] = Counter()
    details: dict[str, str] = {}
    for r in runs:
        if r.status is Status.PASSED:
            continue
        a = attribute(r, cfg, horizon=horizon)
        counts[a.reason.value] += 1
        details.setdefault(a.reason.value, a.detail)

    n = len(runs)
    ordered = {f.value: counts.get(f.value, 0) for f in REASONS
               if counts.get(f.value, 0)}
    return {
        "n": n,
        "passed": passed,
        "p_pass": passed / n,
        "reasons": ordered,
        "shares": {k: v / n for k, v in ordered.items()},
        "example": details,
    }
