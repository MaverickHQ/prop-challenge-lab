"""E4 — how much evidence would it take, decided before any is spent.

An ambiguous null costs alpha exactly as surely as a real test does, and it
is worse than a refusal because it tempts a second look at a larger sample
— which is optional stopping, and inflates the false-positive rate the
multiplicity ledger exists to track.

This session nearly bought the wrong amount of order-flow data for exactly
that reason: the sample size was chosen from the budget and only afterwards
checked against what it could detect. It happened to be adequate. That was
luck, and luck is not a method.

So: state the smallest effect worth acting on, get the sample size it
demands, and if the data cannot supply it, do not run the test.

Stdlib only — no scipy for four formulas.
"""

from __future__ import annotations

import math

ALPHA, POWER = 0.05, 0.80


def _z(p: float) -> float:
    """Inverse normal CDF (Acklam's rational approximation, ~1e-9)."""
    a = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00)
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > ph:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def _zs(alpha: float, power: float) -> tuple[float, float]:
    return _z(1 - alpha / 2), _z(power)


def n_for_correlation(r: float, alpha: float = ALPHA,
                      power: float = POWER) -> int:
    """Sample size to detect a correlation of |r| (Fisher z)."""
    if not 0 < abs(r) < 1:
        raise ValueError("r must be in (0, 1)")
    za, zb = _zs(alpha, power)
    zr = 0.5 * math.log((1 + abs(r)) / (1 - abs(r)))
    return math.ceil(((za + zb) / zr) ** 2 + 3)


def detectable_correlation(n: int, alpha: float = ALPHA,
                           power: float = POWER) -> float:
    """The inverse, and usually the more honest question: with the sample we
    actually have, what is the smallest effect we could see?"""
    if n <= 4:
        return 1.0
    za, zb = _zs(alpha, power)
    zr = (za + zb) / math.sqrt(n - 3)
    return math.tanh(zr)


def n_for_proportions(p1: float, p2: float, alpha: float = ALPHA,
                      power: float = POWER) -> int:
    """Per-group size to distinguish two rates — e.g. a win rate of 28% from
    one of 35%."""
    if p1 == p2:
        raise ValueError("no effect to detect")
    za, zb = _zs(alpha, power)
    pbar = (p1 + p2) / 2
    num = (za * math.sqrt(2 * pbar * (1 - pbar))
           + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return math.ceil(num / (p1 - p2) ** 2)


# The design effect's correlation, MEASURED rather than asserted.
#
# E4.2 introduced `intra_r` and every power calculation in this programme
# used 0.9 -- a stated assumption that was never checked. Measured on 1,637
# paired trading days, the same-date correlation between MES and MNQ net R
# per trade is 0.3818, CI [0.3396, 0.4224]: less than half, with the interval
# excluding 0.9 by a wide margin.
#
# It is NOT the default. Changing a default silently re-scores every future
# result against a different standard than the archived ones, and 0.9 is the
# conservative direction. Callers opt in, and say which they used.
#
# `scripts/backfill_rho.py` re-scored all 20 archived scored blocks under the
# measured value: floors fell ~15% and NOTHING changed verdict. The
# correction is real and its consequences for the register are nil -- which
# could not have been assumed, and is why the backfill ran over everything
# rather than only where it flattered.
MEASURED_INTRA_R_MES_MNQ = 0.3818
ASSUMED_INTRA_R = 0.90


def detectable_mean_shift(n: int, alpha: float = ALPHA,
                          power: float = POWER) -> float:
    """Smallest mean shift, in standard deviations, this sample could see.

    The counterpart to `detectable_correlation`, and the one an expectancy
    result needs: a per-trade edge is a mean shift, not a correlation, so
    without this there was no floor to measure one against -- which is how
    the H- family came to be recorded as bare means with no uncertainty at
    all. Multiply by the sample's own SD to put the floor in R.
    """
    if n <= 1:
        return float("inf")
    za, zb = _zs(alpha, power)
    return (za + zb) / math.sqrt(n)


def n_for_mean_shift(d: float, alpha: float = ALPHA,
                     power: float = POWER) -> int:
    """One-sample size to detect a shift of `d` standard deviations. For
    per-trade expectancy: d = effect_in_R / sd_of_R_per_trade."""
    if d <= 0:
        raise ValueError("d must be positive")
    za, zb = _zs(alpha, power)
    return math.ceil(((za + zb) / d) ** 2)


REQUIRED = {"correlation": lambda e, a, p: n_for_correlation(e, a, p),
            "proportions": lambda e, a, p: n_for_proportions(*e, a, p),
            "mean_shift": lambda e, a, p: n_for_mean_shift(e, a, p)}


def required_n(plan: dict) -> int:
    """`plan` is the `power_plan` recorded on a hypothesis:
    {"test": "correlation", "effect": 0.10, "alpha": 0.05, "power": 0.8}"""
    test = plan.get("test")
    if test not in REQUIRED:
        raise ValueError(f"unknown test {test!r}; expected one of "
                         f"{sorted(REQUIRED)}")
    return REQUIRED[test](plan["effect"], plan.get("alpha", ALPHA),
                          plan.get("power", POWER))


def effective_n(n: int, *, cluster_size: int = 1, intra_r: float = 0.0
                ) -> int:
    """Independent-equivalent sample size when observations come in
    correlated clusters (the design-effect correction).

    E4.2, added the same day the original gate passed a run it should have
    questioned. H5 pooled 453 MES setups with 448 MNQ setups and called it
    n=901, when the second observation on a given date carries much less new
    information than the first.

    THE 0.9 THAT WAS ORIGINALLY ASSUMED HERE IS WRONG. Measured on 1,637
    paired days the same-date correlation of net R per trade is 0.3818, CI
    [0.3396, 0.4224] -- see `MEASURED_INTRA_R_MES_MNQ`. H5's effective n was
    nearer 650 than the 474 quoted under the assumption. The conclusion it
    supported does not change (`scripts/backfill_rho.py`: 20 blocks
    re-scored, none moved verdict), but the number was asserted for months
    and the docstring asserted it too.

        n_eff = n / (1 + (m - 1) * rho)

    A power gate that treats pooling as free will keep waving through runs
    that cannot see what they claim to look for."""
    if cluster_size <= 1 or intra_r <= 0:
        return n
    deff = 1 + (cluster_size - 1) * min(intra_r, 0.999)
    return max(int(n / deff), 1)
