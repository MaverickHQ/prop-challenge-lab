"""M4 — the calibration gate: does this estimator measure the market, or
itself?

M1 put the arithmetic in one audited place. M2 made the estimand a required
argument. Both of those help only if somebody reads the code. This is the
part that needs nobody to notice anything:

    an estimator must return ~0 on a world with NO effect,
    and recover the planted effect on a world that HAS one.

ICT-P2 fails the first half by construction, and that is the whole point.
On a zero-drift random walk, a measurement taken from a swept LEVEL returns
the overshoot -- **a market that froze solid the instant it swept would
still print a large continuation reading** -- while the identical
measurement taken from PRICE correctly returns nothing. Same data, same
arithmetic, one different reference price. No significance test asks that
question. This does, mechanically, before any real data is touched.

**Both halves are required.** An estimator that returns zero for everything
passes the dead world and is useless; one that reports an effect from noise
passes the planted world and is dangerous. A gate that only ever passes is
decoration.

**Why not `synth.py`.** That module plants a follow-through edge in
`TradingDay`s and is the validated control for STRATEGIES (Phase 5) -- it
deliberately does not expose the trigger bar or the direction, because a
strategy is supposed to find those for itself. Calibrating a MEASUREMENT is
the opposite problem: the trigger and the direction must be known, so that
the only thing under test is the measurement. Hence a much smaller world
here, and `synth.py` left alone.

The trigger is a genuine sweep of the running extreme, so the geometry is
the same SHAPE as ICT-P2 rather than an invented setup that happens to fail.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from occams import estimators as est

BARS = 140
TRIGGER_FROM = 20
HORIZON = 40
SIGMA = 1.0

__all__ = ["World", "CalibrationReport", "Uncalibrated", "dead_world",
           "planted_world", "at_price", "at_level", "shipped_at_price",
           "shipped_level_drift", "shipped_level_total", "calibrate",
           "assert_calibrated"]


class Uncalibrated(ValueError):
    """The estimator does not measure what it claims to measure."""


@dataclass(frozen=True)
class World:
    closes: np.ndarray          # (n_days, BARS)
    trigger: np.ndarray         # bar index of the sweep, or -1
    direction: np.ndarray       # +1 for a high sweep, -1 for a low sweep
    level: np.ndarray           # the extreme that was swept
    planted: float              # true signed drift over the horizon

    @property
    def n_days(self) -> int:
        return int(self.closes.shape[0])


def _build(n_days: int, *, seed: int, effect: float) -> World:
    """Vectorised, because the gate is only decisive when n is large enough
    that its own sampling error is well below the effect it must reject.
    The first attempt looped and had to run small, which made the noise
    floor larger than the tolerance — a gate that rejects sound estimators
    at random is worse than none."""
    rng = np.random.default_rng(seed)
    closes = 100.0 + np.cumsum(rng.normal(0.0, SIGMA, (n_days, BARS)), axis=1)

    # a sweep is the first bar to exceed the running extreme of everything
    # before it — the same SHAPE as ICT-P2, not an invented setup
    run_max = np.maximum.accumulate(closes, axis=1)
    run_min = np.minimum.accumulate(closes, axis=1)
    lo_i, hi_i = TRIGGER_FROM, BARS - 1          # leave a forward window
    up = closes[:, lo_i:hi_i] > run_max[:, lo_i - 1:hi_i - 1]
    dn = closes[:, lo_i:hi_i] < run_min[:, lo_i - 1:hi_i - 1]
    brk = up | dn
    has = brk.any(axis=1)
    first = np.argmax(brk, axis=1)

    trig = np.where(has, first + lo_i, -1)
    rows = np.arange(n_days)
    is_up = np.where(has, up[rows, first], False)
    direction = np.where(has, np.where(is_up, 1, -1), 0).astype(int)
    prev = np.clip(trig - 1, 0, BARS - 1)
    level = np.where(has, np.where(is_up, run_max[rows, prev],
                                   run_min[rows, prev]), 0.0)

    if effect:
        # planted AFTER the trigger, so it cannot move the trigger
        step = np.arange(BARS)[None, :] - trig[:, None]
        ramp = np.clip(step, 0, None) * (direction * effect / HORIZON)[:, None]
        closes = closes + np.where(has[:, None], ramp, 0.0)

    return World(closes=closes, trigger=trig, direction=direction,
                 level=level, planted=float(effect))


def dead_world(n_days: int = 2000, *, seed: int) -> World:
    """No forward drift at all. Any non-zero reading is the measurement."""
    return _build(n_days, seed=seed, effect=0.0)


def planted_world(n_days: int = 2000, *, seed: int,
                  effect: float) -> World:
    """A known signed drift over the horizon, in price units."""
    if effect <= 0:
        raise ValueError("effect must be positive; direction is applied "
                         "per day by the world, not by the caller")
    return _build(n_days, seed=seed, effect=effect)


# --------------------------------------------------------------------------
# reference estimators — the honest one and the artifact, side by side
# --------------------------------------------------------------------------

def _window(world: World, i: int):
    t = int(world.trigger[i])
    if t < 0:
        return None
    end = min(t + HORIZON, BARS - 1)
    return t, end, int(world.direction[i])


def at_price(world: World, i: int) -> float | None:
    """From where price actually is. The only reference with no positional
    term."""
    w = _window(world, i)
    if w is None:
        return None
    t, end, d = w
    return float(world.closes[i, end] - world.closes[i, t]) * d


def at_level(world: World, i: int) -> float | None:
    """From the swept level. ICT-P2's estimator, kept here as the thing the
    gate must reject."""
    w = _window(world, i)
    if w is None:
        return None
    t, end, d = w
    return float(world.closes[i, end] - world.level[i]) * d


def shipped_at_price(world: World, i: int) -> float | None:
    """The engine's own `forward_return`, driven as an experiment calls it."""
    w = _window(world, i)
    if w is None:
        return None
    t, _, d = w
    return float(est.forward_return(world.closes[i], at=t, horizon=HORIZON,
                                    direction=d, reference=est.AT_PRICE))


def shipped_level_drift(world: World, i: int) -> float | None:
    """AT_LEVEL is not forbidden — it is forbidden UNDECOMPOSED. The drift
    term must pass the same gate the total fails."""
    w = _window(world, i)
    if w is None:
        return None
    t, _, d = w
    return float(est.forward_return(world.closes[i], at=t, horizon=HORIZON,
                                    direction=d, reference=est.AT_LEVEL,
                                    level=float(world.level[i]),
                                    decompose=True).drift)


def shipped_level_total(world: World, i: int) -> float | None:
    w = _window(world, i)
    if w is None:
        return None
    t, _, d = w
    return float(est.forward_return(world.closes[i], at=t, horizon=HORIZON,
                                    direction=d, reference=est.AT_LEVEL,
                                    level=float(world.level[i]),
                                    decompose=True).total)


# --------------------------------------------------------------------------
# the gate
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class CalibrationReport:
    """Tolerances are expressed in STANDARD ERRORS, not absolute units.

    The first version used a fixed tolerance and it was tighter than the
    gate's own sampling error, so a sound estimator failed on noise. A gate
    whose threshold sits inside its own noise floor rejects at random, which
    is worse than no gate: it teaches you to ignore it.
    """
    dead_mean: float
    dead_se: float
    dead_n: int
    planted_mean: float
    planted_se: float
    planted_n: int
    expected: float
    sigmas: float = 3.0
    slack: float = 0.10          # allowance for small systematic bias

    @property
    def dead_tol(self) -> float:
        return self.sigmas * self.dead_se

    @property
    def planted_tol(self) -> float:
        return self.sigmas * self.planted_se + self.slack * abs(self.expected)

    @property
    def dead_sigmas(self) -> float:
        return abs(self.dead_mean) / self.dead_se if self.dead_se else 0.0

    @property
    def dead_ok(self) -> bool:
        return abs(self.dead_mean) <= self.dead_tol

    @property
    def planted_ok(self) -> bool:
        return abs(self.planted_mean - self.expected) <= self.planted_tol

    @property
    def verdict(self) -> str:
        if not self.dead_ok:
            return "fails the dead world"
        if not self.planted_ok:
            return "misses the planted effect"
        return "calibrated"

    def render(self) -> str:
        return "\n".join([
            f"  dead world     {self.dead_mean:+.4f}  "
            f"= {self.dead_sigmas:.1f} sigma  "
            f"(n={self.dead_n:,}, tolerance +/-{self.dead_tol:.3f})",
            f"  planted world  {self.planted_mean:+.4f}  "
            f"(n={self.planted_n:,}, expected {self.expected:+.4f} "
            f"+/-{self.planted_tol:.3f})",
            f"  VERDICT        {self.verdict}",
        ])


Measure = Callable[[World, int], float | None]


def calibrate(measure: Measure, *, expected: float, seed: int,
              n_days: int = 2000, sigmas: float = 3.0,
              slack: float = 0.10) -> CalibrationReport:
    """Run `measure` over both worlds and report whether it measures the
    market or itself.

    `measure(world, i)` returns one signed observation per day, or None
    where the day had no trigger — a day with no setup is a real outcome,
    not a missing observation.
    """
    if expected <= 0:
        raise ValueError("expected must be positive")

    def run(world: World) -> tuple[float, float, int]:
        vals = [measure(world, i) for i in range(world.n_days)]
        vals = np.array([v for v in vals if v is not None], dtype=float)
        if vals.size < 2:
            raise Uncalibrated("the estimator produced no observations at "
                               "all — it cannot be calibrated")
        se = float(vals.std(ddof=1) / np.sqrt(vals.size))
        return float(vals.mean()), se, int(vals.size)

    dm, dse, dn = run(dead_world(n_days, seed=seed))
    pm, pse, pn = run(planted_world(n_days, seed=seed + 1, effect=expected))
    return CalibrationReport(dead_mean=dm, dead_se=dse, dead_n=dn,
                             planted_mean=pm, planted_se=pse, planted_n=pn,
                             expected=expected, sigmas=sigmas, slack=slack)


def assert_calibrated(measure: Measure, *, expected: float, seed: int,
                      **kw) -> CalibrationReport:
    """Refuse an uncalibrated estimator. Raises rather than warns, and there
    is no override — a gate with a bypass is a suggestion."""
    r = calibrate(measure, expected=expected, seed=seed, **kw)
    if not r.dead_ok:
        raise Uncalibrated(
            f"FAILS THE DEAD WORLD: mean {r.dead_mean:+.4f} = "
            f"{r.dead_sigmas:.1f} SIGMA from zero, where the true effect is "
            f"exactly zero (tolerance +/-{r.dead_tol:.3f}, n={r.dead_n:,}). The world has no forward drift, so this "
            f"reading is the measurement rather than the market — a market "
            f"that froze solid at the trigger would still print it. This is "
            f"the ICT-P2 defect: 94.8% of a d=-0.43 headline was the "
            f"reference price.\n\n{r.render()}")
    if not r.planted_ok:
        raise Uncalibrated(
            f"MISSES THE PLANTED EFFECT: recovered {r.planted_mean:+.4f} "
            f"against a true {r.expected:+.4f} "
            f"(tolerance +/-{r.planted_tol:.3f}, n={r.planted_n:,}). Passing "
            f"the dead world alone is not calibration — an estimator that "
            f"returns zero for everything passes it and is "
            f"useless.\n\n{r.render()}")
    return r
