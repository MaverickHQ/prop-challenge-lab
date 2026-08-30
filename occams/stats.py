"""M1 — the statistical primitives, in one audited place.

Written because the calculations had spread. The ICT run wrote the same
cluster bootstrap THREE times, once per experiment script, and `spearman()`
in `scripts/exp_flow_predicts.py` -- the function behind H5, one of only two
live signals this programme has -- was never checked against a reference
implementation. Three copies of a formula are three chances to be wrong in
three different ways, and none of them was tested.

This is the SOP rule extended one layer down. The `METRICS:` line already
stops numbers being RETYPED into the record (CLAUDE.md 8b-SOP); this stops
them being RE-DERIVED per script.

Two design rules, both load-bearing:

- **numpy only at runtime.** `occams/` is imported by the Lambda and its
  dependency weight already broke a build once (B0.3). scipy is a
  TEST-ONLY oracle. Testing our implementation against scipy is also
  stronger than calling scipy: it pins OUR behaviour, so a future scipy
  release cannot silently move a number already in the register.
- **`seed` is required, never defaulted.** A stochastic result with no
  recorded seed is not reproducible, and a default seed is one nobody
  writes down. Making it a required keyword forces it into the call site,
  and therefore into the archived script.

What this module deliberately does NOT do is choose the estimand. ICT-P2's
arithmetic was perfect and its answer was still wrong, because it measured
from the wrong reference price. That choice lives in `estimators.py` (M2),
where it is a required argument.
"""

from __future__ import annotations

import math

import numpy as np

from occams.audit import audited

__all__ = ["ppf", "rankdata", "spearman", "pearson", "cohens_d",
           "cohens_d_from", "share_of", "mean_ci", "cluster_bootstrap_ci",
           "block_bootstrap_ci", "optimal_block_length", "proportion_ci",
           "correlation_ci"]


# --------------------------------------------------------------------------
# guards. A wrong number is worse than an error, so every one of these
# raises rather than returning nan.
# --------------------------------------------------------------------------

def _vec(v, *, name: str = "sample", minimum: int = 2) -> np.ndarray:
    a = np.asarray(v, dtype=float).ravel()
    if a.size < minimum:
        raise ValueError(f"{name} needs at least {minimum} observations, "
                         f"got {a.size}")
    if not np.isfinite(a).all():
        bad = int((~np.isfinite(a)).sum())
        raise ValueError(
            f"{name} contains {bad} non-finite value(s). Refusing rather "
            f"than dropping them silently — which observations were "
            f"discarded changes the answer, so it is the caller's decision "
            f"to make explicitly.")
    return a


def _pair(x, y) -> tuple[np.ndarray, np.ndarray]:
    a, b = _vec(x, name="x"), _vec(y, name="y")
    if a.size != b.size:
        raise ValueError(f"x and y must be the same length: "
                         f"{a.size} vs {b.size}")
    return a, b


# --------------------------------------------------------------------------
# inverse normal CDF — Wichura's AS241 (PPND16), accurate to ~1e-16.
# `power.py` carries Acklam's (~1e-9); this is the one to consolidate on.
# --------------------------------------------------------------------------

_A = (3.3871328727963666080e0, 1.3314166789178437745e2,
      1.9715909503065514427e3, 1.3731693765509461125e4,
      4.5921953931549871457e4, 6.7265770927008700853e4,
      3.3430575583588128105e4, 2.5090809287301226727e3)
_B = (1.0, 4.2313330701600911252e1, 6.8718700749205790830e2,
      5.3941960214247511077e3, 2.1213794301586595867e4,
      3.9307895800092710610e4, 2.8729085735721942674e4,
      5.2264952788528545610e3)
_C = (1.42343711074968357734e0, 4.63033784615654529590e0,
      5.76949722146069140550e0, 3.64784832476320460504e0,
      1.27045825245236838258e0, 2.41780725177450611770e-1,
      2.27238449892691845833e-2, 7.74545014278341407640e-4)
_D = (1.0, 2.05319162663775882187e0, 1.67638483018380384940e0,
      6.89767334985100004550e-1, 1.48103976427480074590e-1,
      1.51986665636164571966e-2, 5.47593808499534494600e-4,
      1.05075007164441684324e-9)
_E = (6.65790464350110377720e0, 5.46378491116411436990e0,
      1.78482653991729133580e0, 2.96560571828504891230e-1,
      2.65321895265761230930e-2, 1.24266094738807843860e-3,
      2.71155556874348757815e-5, 2.01033439929228813265e-7)
_F = (1.0, 5.99832206555887937690e-1, 1.36929880922735805310e-1,
      1.48753612908506148525e-2, 7.86869131145613259100e-4,
      1.84631831751005468180e-5, 1.42151175831644588870e-7,
      2.04426310338993978564e-15)


def _poly(c: tuple[float, ...], r: float) -> float:
    out = 0.0
    for coef in reversed(c):
        out = out * r + coef
    return out


def ppf(p: float) -> float:
    """Inverse standard-normal CDF."""
    if not 0.0 < p < 1.0:
        raise ValueError(f"p must be strictly between 0 and 1, got {p}")
    q = p - 0.5
    if abs(q) <= 0.425:
        r = 0.180625 - q * q
        return q * _poly(_A, r) / _poly(_B, r)
    r = math.sqrt(-math.log(p if q < 0 else 1.0 - p))
    if r <= 5.0:
        val = _poly(_C, r - 1.6) / _poly(_D, r - 1.6)
    else:
        val = _poly(_E, r - 5.0) / _poly(_F, r - 5.0)
    return -val if q < 0 else val


# --------------------------------------------------------------------------
# rank correlation
# --------------------------------------------------------------------------

@audited
def rankdata(v) -> np.ndarray:
    """Ranks, averaged within tie groups.

    The shortcut used in the experiment scripts, `argsort(argsort(x))`,
    hands tied values arbitrary DISTINCT ranks in whatever order they
    happen to appear — so the answer depends on row order. Bucketed
    predictors and order-flow imbalance tie constantly, so this is not a
    hypothetical difference.
    """
    a = _vec(v, name="values", minimum=1)
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(a.size, dtype=float)
    ranks[order] = np.arange(1, a.size + 1, dtype=float)
    sorted_a = a[order]
    i = 0
    while i < sorted_a.size:
        j = i
        while j + 1 < sorted_a.size and sorted_a[j + 1] == sorted_a[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + j + 2) / 2.0
        i = j + 1
    return ranks


@audited
def pearson(x, y) -> float:
    a, b = _pair(x, y)
    ac, bc = a - a.mean(), b - b.mean()
    den = math.sqrt(float((ac ** 2).sum()) * float((bc ** 2).sum()))
    if den == 0.0:
        raise ValueError("zero variance in x or y — a correlation is "
                         "undefined, not zero")
    return float((ac * bc).sum() / den)


@audited
def correlation_ci(r: float, n: int, alpha: float = 0.05
                   ) -> tuple[float, float]:
    """Fisher-z confidence interval for a correlation.

    `n` should be the INDEPENDENT-EQUIVALENT sample size, not the raw count.
    Passing the raw n when observations come in correlated clusters is
    exactly the H5 error -- 901 pooled MES/MNQ setups whose effective n was
    nearer 474 -- and it narrows the interval by roughly the square root of
    the design effect. `power.effective_n` computes the right number.
    """
    if not -1.0 < r < 1.0:
        raise ValueError(f"r must be in (-1, 1), got {r}")
    if n <= 3:
        raise ValueError(f"n must exceed 3 for a Fisher-z interval, got {n}")
    z = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    half = ppf(1.0 - alpha / 2.0) * se
    return math.tanh(z - half), math.tanh(z + half)


@audited
def spearman(x, y) -> float:
    """Rank correlation. Equals `pearson` of the tie-averaged ranks."""
    a, b = _pair(x, y)
    return pearson(rankdata(a), rankdata(b))


# --------------------------------------------------------------------------
# effect size
# --------------------------------------------------------------------------

@audited
def cohens_d(v) -> float:
    """One-sample standardised effect: mean / sd. Scale-free, which is what
    lets a result be compared against a declared detectable floor."""
    a = _vec(v)
    sd = float(a.std(ddof=1))
    if sd == 0.0:
        raise ValueError("zero variance — an effect size is undefined here, "
                         "not zero")
    return float(a.mean() / sd)


def cohens_d_from(mean: float, sd: float) -> float:
    """For reproducing a value from a record that stored only the summary."""
    if sd <= 0.0:
        raise ValueError("sd must be positive")
    return float(mean / sd)


def share_of(part: float, total: float) -> float:
    """What fraction of a total one term accounts for.

    Small, but it is the number that settled ICT-P2: the penetration term
    was 94.8% of the headline, so the headline was the reference price.
    """
    if total == 0.0:
        raise ValueError("total is zero — a share of nothing is undefined")
    return float(part / total)


# --------------------------------------------------------------------------
# bootstrap
# --------------------------------------------------------------------------

@audited
def cluster_bootstrap_ci(v, clusters, *, seed: int, reps: int = 4000,
                         alpha: float = 0.05) -> tuple[float, float]:
    """Bootstrap CI for the mean, resampling CLUSTERS rather than rows.

    E4.2, and the reason this module exists. MES and MNQ on the same date
    are close to the same draw: the second observation carries almost no
    new information. Treating them as two independent rows understates the
    uncertainty, which is how H5 came to be read as n=901 when its
    effective n was nearer 474.

    Resampling whole clusters keeps that dependence intact instead of
    correcting for it after the fact.
    """
    a = _vec(v)
    lab = np.asarray(clusters).ravel()
    if lab.size != a.size:
        raise ValueError(f"values and clusters must be the same length: "
                         f"{a.size} vs {lab.size}")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    if reps < 100:
        raise ValueError(f"reps={reps} is too few to read a percentile from")

    # first-appearance order, so the draw is a function of the data rather
    # than of dict or sort ordering
    _, first, inverse = np.unique(lab, return_index=True, return_inverse=True)
    remap = np.argsort(np.argsort(first))
    idx = remap[inverse]
    n_groups = int(idx.max()) + 1
    sums = np.bincount(idx, weights=a, minlength=n_groups)
    sizes = np.bincount(idx, minlength=n_groups).astype(float)

    rng = np.random.default_rng(seed)
    means = np.empty(reps, dtype=float)
    for r in range(reps):
        pick = rng.integers(0, n_groups, n_groups)
        means[r] = sums[pick].sum() / sizes[pick].sum()
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


@audited
def mean_ci(v, *, seed: int, reps: int = 4000, alpha: float = 0.05
            ) -> tuple[float, float]:
    """Bootstrap CI for the mean, treating every row as independent.

    Delegates to the cluster version with singleton clusters, so the two
    cannot drift apart — the independent case is a special case of the
    dependent one, not a second implementation of it.
    """
    a = _vec(v)
    return cluster_bootstrap_ci(a, np.arange(a.size), seed=seed, reps=reps,
                                alpha=alpha)


# --------------------------------------------------------------------------
# block bootstrap (M7) — for a series whose ORDER carries information
# --------------------------------------------------------------------------

@audited
def block_bootstrap_ci(v, *, block: int, seed: int, reps: int = 4000,
                       alpha: float = 0.05) -> tuple[float, float]:
    """Moving-block bootstrap CI for the mean of a TIME-ORDERED series.

    The cluster bootstrap above handles dependence between observations that
    share a LABEL — MES and MNQ on the same date. This handles dependence
    along TIME: volatility clusters, and the run of losing days that is what
    actually breaches a trailing drawdown. A per-observation resample treats
    such a run as independent draws and reports a confidence it has not
    earned.

    Overlapping blocks of length `block` are drawn with replacement and
    concatenated to the original length, so runs survive by construction.

    With `block=1` this reduces EXACTLY to `mean_ci` on the same seed — the
    independent case is a special case, not a second implementation.
    """
    a = _vec(v)
    n = a.size
    if not 1 <= block <= n:
        raise ValueError(f"block must be in [1, n={n}], got {block}")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    if reps < 100:
        raise ValueError(f"reps={reps} is too few to read a percentile from")

    starts_available = n - block + 1
    n_blocks = math.ceil(n / block)
    offsets = np.arange(block)
    rng = np.random.default_rng(seed)
    means = np.empty(reps, dtype=float)
    for r in range(reps):
        starts = rng.integers(0, starts_available, n_blocks)
        idx = (starts[:, None] + offsets[None, :]).ravel()[:n]
        means[r] = a[idx].mean()
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


@audited
def optimal_block_length(v) -> int:
    """A suggested block length from the series' own serial dependence.

    Plug-in rule of thumb, not an optimum: the AR(1) form in the
    block-bootstrap literature, b ~ (sqrt(6) * rho / (1 - rho^2))^(2/3) *
    n^(1/3). Its job is to pick the right SCALE — 1 for independent data,
    tens for strongly autocorrelated data — so nobody has to guess. It is
    deliberately not presented as an optimum, and the caller may override.

    Returns 1 when lag-1 autocorrelation is not DISTINGUISHABLE from zero,
    not merely when it is zero. On 2,000 independent observations the sample
    autocorrelation still lands around +/-0.02 by chance, and the formula
    above turns that into a block of 3 — lengthening blocks on evidence the
    series does not contain. The threshold is ~2 standard errors under the
    null, 2/sqrt(n).

    This is M4's lesson in a second place: **do not act inside your own noise
    floor.** There it was a calibration tolerance tighter than its sampling
    error; here it is a block length reacting to sampling error.

    Negative autocorrelation also returns 1 — a long block on anti-correlated
    data would destroy the alternation it ought to keep. Capped at n/4,
    because a block that is a large fraction of the series leaves too few
    distinct blocks to resample from.
    """
    a = _vec(v)
    n = a.size
    c = a - a.mean()
    denom = float((c ** 2).sum())
    if denom == 0.0:
        return 1
    rho = float((c[:-1] * c[1:]).sum() / denom)
    if rho <= 2.0 / math.sqrt(n):
        return 1
    rho = min(rho, 0.99)
    b = ((math.sqrt(6.0) * rho / (1.0 - rho ** 2)) ** (2.0 / 3.0)
         * n ** (1.0 / 3.0))
    return int(max(1, min(round(b), max(1, n // 4))))


# --------------------------------------------------------------------------
# proportions
# --------------------------------------------------------------------------

@audited
def proportion_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score interval for a proportion.

    Wilson rather than the normal approximation because it stays inside
    [0, 1] and does not collapse to zero width at k=0 or k=n — both of
    which occur in our own results (Z0.4 audited 6,940 orders and found
    zero unplaceable, and "0 out of 6,940" needs an honest upper bound).
    """
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 <= k <= n:
        raise ValueError(f"k={k} must lie in [0, n={n}]")
    z = ppf(1.0 - alpha / 2.0)
    p = k / n
    denom = 1.0 + z * z / n
    centre = p + z * z / (2.0 * n)
    spread = math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    lo = (centre - z * spread) / denom
    hi = (centre + z * spread) / denom
    return max(0.0, float(lo)), min(1.0, float(hi))
