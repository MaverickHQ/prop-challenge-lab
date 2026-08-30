"""ParityLog — measured backtest-vs-live drift + a kill signal.

CONTEXT §12 calls this the exceptional-project metric. The Debrief pushes
`mean_drift` alongside the fuel gauge; `kill` firing during the 30-day paper
gate ends the live path before it starts — the sim we trained on and the
platform executing us must agree, or we don't know what we're doing.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParityLog:
    kill_threshold_usd: float
    min_trades_before_kill: int = 10
    # Review fix #6: dispersion threshold — sign-balanced disagreement (mean
    # ~0 but big per-trade misses) is also a broken model. None → same value
    # as the signed threshold.
    abs_kill_threshold_usd: float | None = None
    _drifts: list[float] = field(default_factory=list)

    def record(self, sim_pnl: float, live_pnl: float) -> None:
        self._drifts.append(live_pnl - sim_pnl)

    def record_drift(self, drift: float) -> None:
        """Low-level feed (used when rebuilding from persisted state)."""
        self._drifts.append(drift)

    @property
    def n(self) -> int:
        return len(self._drifts)

    @property
    def mean_drift(self) -> float:
        return sum(self._drifts) / self.n if self._drifts else 0.0

    @property
    def mean_abs_drift(self) -> float:
        return (sum(abs(d) for d in self._drifts) / self.n
                if self._drifts else 0.0)

    @property
    def _abs_threshold(self) -> float:
        return (self.abs_kill_threshold_usd
                if self.abs_kill_threshold_usd is not None
                else self.kill_threshold_usd)

    @property
    def kill(self) -> bool:
        if self.n < self.min_trades_before_kill:
            return False
        return (abs(self.mean_drift) > self.kill_threshold_usd
                or self.mean_abs_drift > self._abs_threshold)

    @property
    def reason(self) -> str:
        if not self.kill:
            return "parity within tolerance"
        if abs(self.mean_drift) > self.kill_threshold_usd:
            direction = "worse" if self.mean_drift < 0 else "better"
            return (f"live consistently {direction} than sim by "
                    f"${abs(self.mean_drift):,.2f}/trade over {self.n} trades "
                    f"— parity drift exceeds ${self.kill_threshold_usd:,.2f}")
        return (f"per-trade dispersion ${self.mean_abs_drift:,.2f} over "
                f"{self.n} trades exceeds ${self._abs_threshold:,.2f} — sim "
                f"and live disagree trade-by-trade even though the mean nets "
                f"out")
