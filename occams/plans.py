"""R1 — a provider's plan menu as a decision variable, and EV in dollars.

**What this is for.** A funded-account provider does not sell "a challenge".
It sells a MENU of contracts, and they differ in every dimension that
decides whether buying one is rational:

- a **price**, which may be monthly or one-time
- a **number of barriers** — some plans are sold already qualified, so the
  evaluation stage does not exist for them at all
- a **target** and a **drawdown geometry**
- a **consistency rule**, which can run opposite to intuition: a *lower*
  percentage is *stricter*, because it caps how much of the total profit any
  single day may contribute
- a **prize**, which on one real menu differs by a factor of ten across
  plans of identical account size

**Why it was missed.** The previous programme modelled one plan and
optimised `P(pass)` — the probability of clearing one gate. That number says
nothing about what the attempt cost or what the prize was worth.
`docs/Q1-PAYOUT.md` found half of this the hard way, and late, because the
business objective was never written down as a requirement.

**Why it is cheap.** This module is arithmetic over published constraints,
not inference from noisy observations. It spends no alpha and needs no
market data, because nothing here is being estimated — only optimised. That
is why it runs before anything is bought.

**What it does NOT do.** It cannot rescue a losing strategy. With negative
expectancy every contract is negative EV, and `tests/test_plans.py` asserts
exactly that so a sign error cannot masquerade as a discovery. What the menu
decides is whether a *marginal* strategy is viable, and on which contract.
"""

from __future__ import annotations

from dataclasses import dataclass

from occams.payout import PayoutConfig
from occams.rules import ChallengeConfig

__all__ = ["PlanEconomics", "Plan", "ev", "required_edge"]

MONTHLY, ONCE = "monthly", "once"
FEE_KINDS = (MONTHLY, ONCE)


@dataclass(frozen=True)
class PlanEconomics:
    """The money, which no previous model carried.

    `max_payout` is the ceiling on a single withdrawal request. It is the
    number that differs tenfold across plans of the same account size, and
    it was modelled nowhere -- so two contracts whose hurdles look similar
    could not be told apart.
    """
    fee: float
    fee_kind: str
    max_payout: float
    payouts_per_month: int = 4

    def __post_init__(self) -> None:
        if self.fee < 0:
            raise ValueError("fee cannot be negative")
        if self.fee_kind not in FEE_KINDS:
            raise ValueError(f"fee_kind must be one of {FEE_KINDS}, "
                             f"got {self.fee_kind!r}")
        if self.max_payout <= 0:
            raise ValueError("max_payout must be positive")
        if self.payouts_per_month <= 0:
            raise ValueError("payouts_per_month must be positive")

    def fees_for(self, months: float) -> float:
        """Total paid to hold the contract for `months`.

        A monthly plan taking six months costs six fees; a one-time plan
        taking six months costs one. With no fee model at all, a slow
        strategy looked identical to a fast one -- which is how a programme
        can optimise for a gate while the meter runs.
        """
        if months < 0:
            raise ValueError("months cannot be negative")
        return self.fee * months if self.fee_kind == MONTHLY else self.fee

    def prize(self, gross_profit: float, payout_frac: float) -> float:
        """Cash actually received for `gross_profit` of trading profit.

        Order matters: the withdrawable SHARE applies first, then the
        ceiling. Capping first would overstate every plan's prize.
        """
        return min(gross_profit * payout_frac, self.max_payout)


@dataclass(frozen=True)
class Plan:
    """One contract on the menu.

    `evaluation` is None for a plan sold already qualified. That is not a
    detail -- it removes an entire barrier, and it is the structural fact
    the previous project never used.
    """
    name: str
    account: float
    evaluation: ChallengeConfig | None
    funded: PayoutConfig
    economics: PlanEconomics

    @property
    def barriers(self) -> int:
        return 2 if self.evaluation is not None else 1


def ev(plan: Plan, *, p_payout: float, gross_profit: float,
       months: float) -> float:
    """Expected value in DOLLARS -- the objective, replacing P(pass).

        EV = P(reach a payout) x prize  -  fees paid getting there
    """
    if not 0.0 <= p_payout <= 1.0:
        raise ValueError("p_payout must be a probability")
    prize = plan.economics.prize(gross_profit, plan.funded.payout_frac)
    return p_payout * prize - plan.economics.fees_for(months)


def required_edge(plan: Plan, p_of_edge, *, gross_profit: float,
                  months: float, hi: float = 1.0, tol: float = 1e-6):
    """The smallest edge at which this contract breaks even. **The
    deliverable.**

    `FEASIBILITY.md` computed ONE frontier -- roughly +0.25R per trade at
    0.5 trades/day -- and every strategy family failed it by a factor of
    ten. That number is a property of one plan's geometry, not a law of
    nature: a sixteen-contract menu has sixteen frontiers, and one was
    computed.

    `p_of_edge` maps an edge to P(reach a payout) and must be monotone
    non-decreasing; supply it from the harness rather than assuming a shape.

    Returns None when no attainable edge covers the fees. That case must be
    reported rather than returned as `hi`, because a search range's ceiling
    presented as a result is a fabricated finding -- the failure mode this
    repository exists to catch.
    """
    if ev(plan, p_payout=p_of_edge(hi), gross_profit=gross_profit,
          months=months) < 0:
        return None

    lo = 0.0
    if ev(plan, p_payout=p_of_edge(lo), gross_profit=gross_profit,
          months=months) >= 0:
        return lo
    while hi - lo > tol:
        mid = (lo + hi) / 2.0
        if ev(plan, p_payout=p_of_edge(mid), gross_profit=gross_profit,
              months=months) >= 0:
            hi = mid
        else:
            lo = mid
    return hi
