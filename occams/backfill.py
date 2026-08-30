"""M5 — does an archived result still reproduce through the audited engine?

Two different questions travel under one name, and keeping them apart is the
whole design:

- **Reproduction.** Same estimator, same data, run again. Anything but a
  match is a defect — in the engine, the data, or the record.
- **Estimator swap.** The number was produced by a hand-rolled function that
  M1 replaced. H5 and C2 both rest on a `spearman()` that ranked ties by
  row order. Here a difference is a FINDING, not a failure, and it has to
  be reported as one rather than quietly accepted.

**Two tolerances, for two different reasons.**

*Rounding.* The register stores values already rounded — C2's correlations
to four decimals, Z0's R-per-trade to three. An exact match is therefore
impossible in principle, and the honest test is "agrees to the precision at
which it was recorded". Inferring the decimals from the stored value is a
LOWER bound on the true precision (0.080 is stored as 0.08), so the inferred
tolerance is conservative: it can miss a drift smaller than the recorded
precision, but it can never invent one. Pass `decimals` explicitly when the
script's own rounding is known.

*Monte Carlo.* A bootstrap CI cannot match exactly, because M1's cluster
bootstrap consumes its RNG differently from the three hand-rolled copies it
replaced. Both are correct; the draws differ. Declaring which metrics are
stochastic BEFORE running is what stops a legitimate RNG difference reading
as a reproduction failure — or, worse, an exact-match rule being quietly
relaxed the first time it fails.
"""

from __future__ import annotations

from dataclasses import dataclass

DETERMINISTIC = "deterministic"
STOCHASTIC = "stochastic"
SUPERSEDED = "superseded"

__all__ = ["DETERMINISTIC", "STOCHASTIC", "SUPERSEDED", "Check", "flatten",
           "decimals", "rounding_tolerance", "compare", "render", "all_ok"]


def flatten(d: dict, prefix: str = "") -> dict[str, float]:
    """Nested metrics to dotted keys, numeric leaves only."""
    out: dict[str, float] = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, f"{key}."))
        elif isinstance(v, bool):
            continue
        elif isinstance(v, (int, float)):
            out[key] = float(v)
    return out


def decimals(x: float) -> int:
    """Decimal places actually present in the stored value."""
    s = repr(float(x))
    if "e" in s or "E" in s:
        return 12
    return len(s.split(".")[1].rstrip("0")) if "." in s else 0


def rounding_tolerance(x: float, places: int | None = None) -> float:
    """Half of the last recorded place — the most a correct value can differ
    from its own rounded record."""
    p = decimals(x) if places is None else places
    return 0.5 * (10.0 ** -p) if p > 0 else 0.5


@dataclass(frozen=True)
class Check:
    metric: str
    archived: float
    recomputed: float
    kind: str
    tolerance: float

    @property
    def delta(self) -> float:
        return self.recomputed - self.archived

    @property
    def ok(self) -> bool:
        if self.kind == SUPERSEDED:
            return True
        return abs(self.delta) <= self.tolerance

    @property
    def status(self) -> str:
        if self.kind == SUPERSEDED:
            return "superseded"
        if self.ok:
            return "match"
        return "DRIFT" if self.kind == STOCHASTIC else "MISMATCH"


def compare(archived: dict, recomputed: dict, *, stochastic=(),
            superseded=(), decimals_override: int | None = None,
            stochastic_tol: float = 0.05,
            only: tuple[str, ...] = ()) -> list[Check]:
    """Diff a recomputed metrics dict against the archived one.

    `stochastic` names metrics whose value depends on an RNG draw; those get
    `stochastic_tol` instead of a rounding tolerance. Metrics present in the
    archive but absent from the recompute are skipped rather than failed —
    a backfill that recomputes a subset is normal, and pretending otherwise
    would make every partial run look broken.

    `superseded` names metrics a later record has CORRECTED. The register is
    append-only, so the original value stays in place forever; without this
    a corrected metric reports a mismatch on every future run, and the
    obvious "fix" is to loosen a tolerance until it passes. They are shown,
    not hidden — the difference is the correction, and it should be legible.
    """
    a, r = flatten(archived), flatten(recomputed)
    checks: list[Check] = []
    for key in sorted(a):
        if key not in r:
            continue
        if only and not any(o in key for o in only):
            continue
        if any(x in key for x in superseded):
            checks.append(Check(metric=key, archived=a[key],
                                recomputed=r[key], kind=SUPERSEDED,
                                tolerance=0.0))
            continue
        is_stoch = any(s in key for s in stochastic)
        tol = (stochastic_tol if is_stoch
               else rounding_tolerance(a[key], decimals_override))
        checks.append(Check(metric=key, archived=a[key], recomputed=r[key],
                            kind=STOCHASTIC if is_stoch else DETERMINISTIC,
                            tolerance=tol))
    return checks


def all_ok(checks: list[Check]) -> bool:
    return all(c.ok for c in checks)


def render(checks: list[Check], title: str = "") -> str:
    lines = []
    if title:
        lines.append(title)
    lines.append(f"  {'metric':<32}{'archived':>12}{'recomputed':>13}"
                 f"{'delta':>12}   status")
    for c in checks:
        lines.append(f"  {c.metric:<32}{c.archived:>+12.5f}"
                     f"{c.recomputed:>+13.5f}{c.delta:>+12.2e}   {c.status}")
    bad = [c for c in checks if not c.ok]
    sup = [c for c in checks if c.kind == SUPERSEDED]
    lines.append(f"  {len(checks) - len(bad) - len(sup)}/"
                 f"{len(checks) - len(sup)} reproduce"
                 + (f"   {len(sup)} superseded" if sup else "")
                 + (f"   {len(bad)} NOT" if bad else ""))
    return "\n".join(lines)
