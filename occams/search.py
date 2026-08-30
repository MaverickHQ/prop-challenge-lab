"""Grid sweep, gated winner selection, verdict — the machinery Phase 8
consumes once real data lands (P1). Deterministic; the gates match
docs/PREREG.md §6 exactly and are passed in, never hard-coded.

The plateau rule (G4) is the single non-obvious piece: a lone maximum in
the sweep is treated as noise. A winning cell's Chebyshev-1 neighbourhood
(including the cell) must have at least `plateau_cells` members AND a
MEDIAN P(pass) within `plateau_slack` of the winner — exactly the PREREG §6
wording (review fix #3). The null comparison (G2) takes a float baseline:
the MEAN null P(pass) over several coin-seeds (`harness.null_baseline`),
so one seed's luck can never move a GO/NO-GO verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from statistics import median as _median
from typing import Any, Callable, Iterable

from occams.harness import (MakePlan, MCStats, TradingDay, ValidityError,
                            monte_carlo)
from occams.rules import ChallengeConfig


@dataclass(frozen=True)
class GridAxis:
    name: str
    values: tuple[Any, ...]


@dataclass(frozen=True)
class SweepCell:
    indices: tuple[int, ...]
    params: dict[str, Any]
    stats: MCStats


@dataclass(frozen=True)
class Sweep:
    cells: tuple[SweepCell, ...]
    axes: tuple[GridAxis, ...]
    prereg_hash: str = ""       # protocol provenance (Codex 3.3)

    @property
    def n_cells(self) -> int:
        return len(self.cells)


def sweep(days: list[TradingDay], axes: tuple[GridAxis, ...],
          make_strategy: Callable[[dict], MakePlan],
          cfg: ChallengeConfig, costs, *, horizon_days: int,
          events: dict | None = None, prereg_hash: str = "") -> Sweep:
    """Enumerate the full cartesian product; MC each cell on the same days."""
    cells: list[SweepCell] = []
    ranges = [range(len(a.values)) for a in axes]
    for idx in product(*ranges):
        params = {a.name: a.values[i] for a, i in zip(axes, idx)}
        stats = monte_carlo(days, make_strategy(params), cfg, costs,
                            horizon_days=horizon_days, events=events)
        cells.append(SweepCell(indices=tuple(idx), params=params, stats=stats))
    if cells and all(c.stats.traded_days == 0 for c in cells):
        raise ValidityError(
            "sweep traded zero days in every cell — instrument failure "
            "(PREREG v2 validity gate): fix the harness/params; this is "
            "never a NO-GO")
    return Sweep(cells=tuple(cells), axes=axes, prereg_hash=prereg_hash)


@dataclass(frozen=True)
class Gates:
    p_pass_min: float
    edge_vs_null: float
    p_breach_max: float
    plateau_cells: int          # min neighbourhood size incl. the cell itself
    plateau_slack: float        # max P(pass) drop within the plateau


@dataclass(frozen=True)
class Winner:
    params: dict[str, Any]
    p_pass: float
    p_breach: float
    median_days: int
    plateau: tuple[SweepCell, ...] = field(default_factory=tuple)


def _neighbourhood(cell: SweepCell, sweep_: Sweep) -> list[SweepCell]:
    """ALL cells within Chebyshev distance 1 (including the cell itself)."""
    return [other for other in sweep_.cells
            if all(abs(a - b) <= 1
                   for a, b in zip(other.indices, cell.indices))]


def find_winner(sweep_: Sweep, null_p_pass: float, gates: Gates) -> Winner | None:
    """Pick the highest-P(pass) cell that clears every gate incl. the plateau."""
    candidates = sorted(sweep_.cells, key=lambda c: c.stats.p_pass, reverse=True)
    for c in candidates:
        s = c.stats
        if s.p_pass < gates.p_pass_min:
            return None                                 # ordered → no hope below
        if s.p_pass - null_p_pass < gates.edge_vs_null:
            continue
        if s.p_breach > gates.p_breach_max:
            continue
        # G4 exactly as sealed in PREREG §6 (review fix #3): the Chebyshev-1
        # neighbourhood (incl. the cell) must have ≥ plateau_cells members
        # AND a MEDIAN P(pass) within plateau_slack of the winner.
        plateau = _neighbourhood(c, sweep_)
        med = _median(x.stats.p_pass for x in plateau)
        if len(plateau) < gates.plateau_cells or s.p_pass - med > gates.plateau_slack:
            continue                                    # lone spike — reject
        return Winner(params=dict(c.params), p_pass=s.p_pass,
                      p_breach=s.p_breach, median_days=s.median_days,
                      plateau=tuple(plateau))
    return None


@dataclass(frozen=True)
class Verdict:
    decision: str                   # "GO" | "NO-GO"
    oos_winner: Winner | None
    lockbox_winner: Winner | None
    reason: str


def verdict(oos: Sweep, oos_null: float, lockbox: Sweep,
            lockbox_null: float, gates: Gates) -> Verdict:
    """Both OOS and lockbox must clear the gates — CONTEXT §7. Sweeps sealed
    under different protocols are not comparable (Codex 3.3): that is an
    operator error, raised loudly, never a market verdict."""
    if oos.prereg_hash != lockbox.prereg_hash:
        raise ValueError(
            f"protocol mismatch: OOS sweep sealed under "
            f"{oos.prereg_hash or '<none>'} but lockbox under "
            f"{lockbox.prereg_hash or '<none>'} — refusing to compare")
    w_oos = find_winner(oos, oos_null, gates)
    w_lb = find_winner(lockbox, lockbox_null, gates)
    if w_oos is None:
        return Verdict("NO-GO", w_oos, w_lb, "OOS did not clear gates")
    if w_lb is None:
        return Verdict("NO-GO", w_oos, w_lb, "lockbox did not clear gates")
    return Verdict("GO", w_oos, w_lb,
                   f"OOS P(pass)={w_oos.p_pass:.2f}, "
                   f"lockbox P(pass)={w_lb.p_pass:.2f}")


def combined_verdict(per_instrument: dict[str, Verdict]) -> Verdict:
    """PREREG §5 (Codex 3.2): every instrument split must clear the gates
    independently — combined performance cannot mask one failing split."""
    failing = {k: v for k, v in per_instrument.items()
               if v.decision != "GO"}
    if failing:
        detail = "; ".join(f"{k}: {v.reason}" for k, v in failing.items())
        return Verdict("NO-GO", None, None,
                       f"instrument splits failed independently — {detail}")
    detail = ", ".join(sorted(per_instrument))
    return Verdict("GO", None, None,
                   f"all instrument splits cleared ({detail})")


def prereg_hash_of(path: str = "docs/PREREG.md") -> str:
    """The protocol fingerprint stamped into every sweep (seal procedure)."""
    import hashlib
    from pathlib import Path as _P
    return hashlib.sha256(_P(path).read_bytes()).hexdigest()[:16]


# Helper (imported lazily by tests to keep import surface small).
__all__ = ["GridAxis", "SweepCell", "Sweep", "sweep", "Gates", "Winner",
           "find_winner", "Verdict", "verdict", "combined_verdict",
           "prereg_hash_of"]


def _keep_type_alias() -> Iterable[Any]:      # pragma: no cover
    return ()
