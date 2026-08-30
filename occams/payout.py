"""Q1 — the half this programme never modelled: getting PAID.

`ChallengeState` scores the evaluation and stops at qualification. So every
P(pass) ever quoted here — E2's 0.042, the 0.55 gate, the whole feasibility
frontier — measures **getting through the door**, and says nothing about
whether the money arrives.

The gap is not cosmetic. Consistency rules differ BY STAGE, and we held only
the first: the tier we sealed has **no** evaluation consistency requirement,
while the qualified tier applies a **40% largest-day rule to payout
eligibility**. A strategy can therefore qualify comfortably and never be
paid, and nothing in the engine could have said so.

This module mirrors `ChallengeState` deliberately rather than inventing new
semantics: breach checked before payout, a floor that trails the equity high
and locks at the funded balance, sticky terminal states, consistency that
DELAYS rather than breaches.

Two places it must differ, and both are modelling choices rather than
mechanics:

- **A withdrawal is not a loss.** When money leaves, the equity high moves
  down with it. Leaving the floor where it was would make every successful
  payout instantly breach the account, which is the single easiest way to
  get this wrong.

  **THE INPUT CONVENTION, because it is ambiguous and cost a wrong answer
  while this was being built.** `record_day` takes CUMULATIVE equity — the
  running mark a simulator produces, which knows nothing about withdrawals
  and therefore never drops when money is taken out. Withdrawals are
  tracked here and subtracted internally. Passing broker-balance equity
  instead, which DOES drop on withdrawal, double-counts every payout and
  breaches the account on the day after its first success.
- **Consistency is measured per CYCLE.** The largest-day share resets after
  each payout, because the rule asks about the profit being withdrawn, not
  about all profit ever made.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = ["PayoutStatus", "PayoutConfig", "PayoutState"]


class PayoutStatus(Enum):
    ACTIVE = "active"
    PAID = "paid"
    BREACHED = "breached"


@dataclass(frozen=True)
class PayoutConfig:
    """Rules that apply AFTER qualification.

    `account` is the funded nominal balance, `threshold` the profit needed
    to request a withdrawal, `payout_frac` the share of that profit actually
    withdrawable. `consistency_frac` gates the withdrawal: no single day's
    profit may exceed this share of the cycle's net profit.
    """
    account: float
    threshold: float
    trailing_dd: float
    min_days: int = 0
    consistency_frac: float | None = None
    payout_frac: float = 1.0

    def __post_init__(self) -> None:
        if self.account <= 0:
            raise ValueError("account must be positive")
        if self.threshold <= 0:
            raise ValueError("threshold must be positive")
        if self.trailing_dd < 0:
            raise ValueError("trailing_dd cannot be negative")
        if self.min_days < 0:
            raise ValueError("min_days cannot be negative")
        if not 0 < self.payout_frac <= 1:
            raise ValueError("payout_frac must be in (0, 1]")
        if self.consistency_frac is not None and \
                not 0 < self.consistency_frac <= 1:
            raise ValueError("consistency_frac must be in (0, 1]")


class PayoutState:
    def __init__(self, config: PayoutConfig) -> None:
        self._cfg = config
        self._eod_high = config.account
        self._days_traded = 0
        self._status = PayoutStatus.ACTIVE
        self._prev_equity = config.account
        self._max_day_profit = 0.0
        self._withdrawn = 0.0
        self._cycles = 0
        self._cycle_start = config.account

    # ---- inspectable state ------------------------------------------------

    @property
    def status(self) -> PayoutStatus:
        return self._status

    @property
    def cycles_paid(self) -> int:
        return self._cycles

    @property
    def total_paid(self) -> float:
        return self._withdrawn

    @property
    def max_day_profit(self) -> float:
        return self._max_day_profit

    @property
    def floor(self) -> float:
        """Trails the equity high, locked at the funded balance — the same
        shape as the evaluation's floor."""
        return min(self._eod_high - self._cfg.trailing_dd, self._cfg.account)

    def snapshot(self) -> dict:
        return {"eod_high": self._eod_high, "days_traded": self._days_traded,
                "status": self._status.value, "prev_equity": self._prev_equity,
                "max_day_profit": self._max_day_profit,
                "withdrawn": self._withdrawn, "cycles": self._cycles,
                "cycle_start": self._cycle_start}

    @classmethod
    def restore(cls, config: PayoutConfig, snap: dict) -> "PayoutState":
        s = cls(config)
        s._eod_high = float(snap["eod_high"])
        s._days_traded = int(snap["days_traded"])
        s._status = PayoutStatus(snap["status"])
        s._prev_equity = float(snap["prev_equity"])
        s._max_day_profit = float(snap["max_day_profit"])
        s._withdrawn = float(snap["withdrawn"])
        s._cycles = int(snap["cycles"])
        s._cycle_start = float(snap["cycle_start"])
        return s

    # ---- the day ----------------------------------------------------------

    def record_day(self, eod_equity: float,
                   traded: bool = True) -> PayoutStatus:
        if self._status is PayoutStatus.BREACHED:
            return self._status

        # equity net of money already taken out: a withdrawal is not a loss
        equity = eod_equity - self._withdrawn

        # breach first, exactly as the evaluation orders it
        if equity <= self.floor:
            self._status = PayoutStatus.BREACHED
            return self._status

        self._days_traded += 1 if traded else 0
        self._eod_high = max(self._eod_high, equity)
        self._max_day_profit = max(self._max_day_profit,
                                   equity - self._prev_equity)
        self._prev_equity = equity

        profit = equity - self._cycle_start
        if (profit >= self._cfg.threshold
                and self._days_traded >= self._cfg.min_days
                and self._consistency_ok(profit)):
            paid = profit * self._cfg.payout_frac
            self._withdrawn += paid
            self._cycles += 1
            # the money leaving must not move the floor against us
            self._eod_high -= paid
            self._prev_equity -= paid
            self._cycle_start = equity - paid
            self._max_day_profit = 0.0        # consistency is per CYCLE
            self._status = PayoutStatus.PAID
            return self._status

        self._status = PayoutStatus.ACTIVE
        return self._status

    def _consistency_ok(self, profit: float) -> bool:
        frac = self._cfg.consistency_frac
        if frac is None:
            return True
        return self._max_day_profit <= frac * profit
