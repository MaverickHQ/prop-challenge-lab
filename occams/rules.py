"""The challenge rules engine — the literal rule set as executable code.

The objective is the rule set, never a proxy (the series' hardest-won
lesson). `ChallengeState.record_day(eod_equity)` consumes end-of-day equity
marks and returns the account status; `floor` is public state (the fuel
gauge reads it).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Status(Enum):
    ACTIVE = "active"
    PASSED = "passed"
    BREACHED = "breached"


@dataclass(frozen=True)
class ChallengeConfig:
    account: float
    target: float
    trailing_dd: float
    # The venue's daily loss guard is an INTRADAY LOCKOUT (liquidate + lock
    # until 6PM ET), NOT an account failure — confirmed 2026-07-04
    # (venue.local.md). Kept for reporting; it never breaches. Our own daily
    # stop (~$500) + max-2-trades binds far below it.
    daily_guard: float
    min_days: int
    # Evaluation consistency rule (sibling plans only — the verified Zero
    # tier has none): no single day's profit may exceed this fraction of
    # net profit AT PASS TIME. Gates the pass; delays, never breaches.
    consistency_frac: float | None = None


class ChallengeState:
    def __init__(self, config: ChallengeConfig) -> None:
        self._cfg = config
        self._eod_high = config.account
        self._days_traded = 0
        self._status = Status.ACTIVE
        self._prev_equity = config.account
        self._max_day_profit = 0.0

    def snapshot(self) -> dict:
        """Persistable state (review fix #2) — everything record_day mutates."""
        return {"eod_high": self._eod_high,
                "days_traded": self._days_traded, "status": self._status.value,
                "prev_equity": self._prev_equity,
                "max_day_profit": self._max_day_profit}

    @classmethod
    def restore(cls, config: ChallengeConfig, snap: dict) -> "ChallengeState":
        s = cls(config)
        s._eod_high = float(snap["eod_high"])
        s._days_traded = int(snap["days_traded"])
        s._status = Status(snap["status"])
        # Defaults keep pre-consistency snapshots (Zero tier) restorable.
        s._prev_equity = float(snap.get("prev_equity", config.account))
        s._max_day_profit = float(snap.get("max_day_profit", 0.0))
        return s

    @property
    def floor(self) -> float:
        # Trails the EOD equity high, but locks at the start balance once
        # cleared (min): the floor never rises above the account's start.
        return min(self._eod_high - self._cfg.trailing_dd, self._cfg.account)

    def record_day(self, eod_equity: float, traded: bool = True) -> Status:
        if self._status is not Status.ACTIVE:
            return self._status  # terminal states are sticky

        # Breach first (conservative ordering), then the pass. The ONLY
        # account-killer is the trailing-DD floor: the venue's daily guard is
        # an intraday lockout, never a failure (confirmed 2026-07-04).
        if eod_equity <= self.floor:
            self._status = Status.BREACHED
            return self._status

        self._days_traded += 1 if traded else 0
        self._eod_high = max(self._eod_high, eod_equity)
        self._max_day_profit = max(self._max_day_profit,
                                   eod_equity - self._prev_equity)
        self._prev_equity = eod_equity

        if (eod_equity >= self._cfg.account + self._cfg.target
                and self._days_traded >= self._cfg.min_days
                and self._consistency_ok(eod_equity)):
            self._status = Status.PASSED
        return self._status

    def _consistency_ok(self, eod_equity: float) -> bool:
        frac = self._cfg.consistency_frac
        if frac is None:
            return True
        net = eod_equity - self._cfg.account
        return self._max_day_profit <= frac * net
