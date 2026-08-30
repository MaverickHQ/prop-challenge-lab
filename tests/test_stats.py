"""M1 — the maths engine, tested two ways.

Why this module exists: the ICT run wrote the same cluster bootstrap THREE
times, once per experiment script, and `spearman()` in
`scripts/exp_flow_predicts.py` -- the function behind H5, one of only two
live signals -- was never checked against a reference implementation.

Two kinds of test here, and both are needed:

**Known-answer.** Compared against scipy, which is a TEST-ONLY dependency.
`occams/` is imported by the Lambda and its dependency weight already broke
a build once (B0.3), so the runtime stays numpy-only. Testing our own
implementation against scipy is also stronger than simply calling scipy:
it pins OUR behaviour, so a future scipy release cannot silently move a
recorded number.

**Property.** Invariants that must hold for any input. These catch the
errors a fixture cannot -- an estimator that happens to match on one sample
and is wrong in general.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats as sps

from occams import stats

SEED = 20260803


def _rng():
    return np.random.default_rng(SEED)


# --------------------------------------------------------------------------
# known-answer: rank correlation
# --------------------------------------------------------------------------

def test_spearman_matches_scipy_on_continuous_data():
    r = _rng()
    x = r.normal(size=500)
    y = 0.3 * x + r.normal(size=500)
    assert stats.spearman(x, y) == pytest.approx(sps.spearmanr(x, y).statistic,
                                                 abs=1e-12)


def test_spearman_matches_scipy_WITH_TIES():
    """The one that matters.

    The hand-rolled version in the experiment scripts ranks with
    `argsort(argsort(x))`, which hands tied values arbitrary DISTINCT ranks
    in whatever order they happen to appear. The correct treatment averages
    ranks across a tie group. Order-flow imbalance and bucketed predictors
    tie constantly, so this is not a hypothetical.
    """
    r = _rng()
    x = r.integers(0, 5, size=400).astype(float)     # heavily tied
    y = r.integers(0, 3, size=400).astype(float)     # heavily tied
    assert stats.spearman(x, y) == pytest.approx(sps.spearmanr(x, y).statistic,
                                                 abs=1e-12)


def test_the_naive_rank_really_does_disagree_under_ties():
    """Pins the BUG SHAPE, so nobody reintroduces the shortcut believing it
    is equivalent."""
    x = np.array([1.0, 1.0, 1.0, 2.0, 2.0, 3.0])
    y = np.array([5.0, 1.0, 3.0, 2.0, 4.0, 6.0])
    naive_rank = np.argsort(np.argsort(x)).astype(float)
    assert not np.allclose(naive_rank, stats.rankdata(x))
    assert stats.spearman(x, y) == pytest.approx(sps.spearmanr(x, y).statistic)


def test_pearson_matches_scipy():
    r = _rng()
    x = r.normal(size=300)
    y = -0.6 * x + r.normal(size=300)
    assert stats.pearson(x, y) == pytest.approx(sps.pearsonr(x, y).statistic,
                                                abs=1e-12)


def test_fisher_z_interval_matches_the_textbook_worked_example():
    """r = 0.50 on n = 100 gives (0.337, 0.634) in every reference that
    prints one."""
    lo, hi = stats.correlation_ci(0.5, 100)
    assert lo == pytest.approx(0.337, abs=5e-4)
    assert hi == pytest.approx(0.634, abs=5e-4)


def test_a_correlation_interval_narrows_with_n_and_brackets_the_estimate():
    wide = stats.correlation_ci(0.2, 100)
    narrow = stats.correlation_ci(0.2, 2000)
    assert (narrow[1] - narrow[0]) < (wide[1] - wide[0])
    for ci in (wide, narrow):
        assert ci[0] < 0.2 < ci[1]


def test_a_correlation_interval_refuses_impossible_inputs():
    for bad in (-1.0, 1.0, 1.5):
        with pytest.raises(ValueError, match="r must be"):
            stats.correlation_ci(bad, 100)
    with pytest.raises(ValueError, match="must exceed 3"):
        stats.correlation_ci(0.2, 3)


def test_wilson_interval_matches_scipy():
    for k, n in ((9, 10), (42, 100), (0, 30), (30, 30), (1, 3)):
        lo, hi = stats.proportion_ci(k, n)
        ref = sps.binomtest(k, n).proportion_ci(method="wilson")
        assert lo == pytest.approx(ref.low, abs=1e-12)
        assert hi == pytest.approx(ref.high, abs=1e-12)


# --------------------------------------------------------------------------
# property: things that must hold for any input
# --------------------------------------------------------------------------

def test_a_ci_always_contains_its_own_point_estimate():
    r = _rng()
    for _ in range(20):
        v = r.normal(loc=r.uniform(-2, 2), scale=r.uniform(0.1, 3), size=200)
        lo, hi = stats.mean_ci(v, seed=SEED)
        assert lo <= v.mean() <= hi


def test_cohens_d_is_scale_invariant_and_the_mean_is_not():
    r = _rng()
    v = r.normal(loc=0.4, scale=2.0, size=500)
    assert stats.cohens_d(v * 7.0) == pytest.approx(stats.cohens_d(v))
    assert (v * 7.0).mean() == pytest.approx(v.mean() * 7.0)


def test_a_sample_symmetric_about_zero_has_no_effect():
    r = _rng()
    v = r.normal(size=4000)
    v = np.concatenate([v, -v])            # exactly symmetric
    assert stats.cohens_d(v) == pytest.approx(0.0, abs=1e-12)


def test_spearman_survives_any_monotone_transform():
    r = _rng()
    x = r.normal(size=300)
    y = 0.5 * x + r.normal(size=300)
    base = stats.spearman(x, y)
    assert stats.spearman(np.exp(x), y) == pytest.approx(base)
    assert stats.spearman(x, y ** 3) == pytest.approx(base)


def test_spearman_of_a_series_with_itself_is_one():
    r = _rng()
    x = r.normal(size=100)
    assert stats.spearman(x, x) == pytest.approx(1.0)
    assert stats.spearman(x, -x) == pytest.approx(-1.0)


# --------------------------------------------------------------------------
# the cluster bootstrap: the reason this module exists
# --------------------------------------------------------------------------

def test_singleton_clusters_reduce_to_the_plain_bootstrap():
    r = _rng()
    v = r.normal(size=200)
    labels = np.arange(200)                # every observation its own cluster
    assert stats.cluster_bootstrap_ci(v, labels, seed=SEED) == pytest.approx(
        stats.mean_ci(v, seed=SEED))


def test_a_cluster_bootstrap_is_WIDER_when_clusters_are_correlated():
    """The whole reason the function exists (E4.2).

    MES and MNQ on the same date are close to the same draw. Treating them
    as two independent observations understates the uncertainty, which is
    exactly how H5 was read as n=901 when its effective n was nearer 474.
    """
    r = _rng()
    day_effect = r.normal(scale=1.0, size=400)
    v = np.repeat(day_effect, 2) + r.normal(scale=0.05, size=800)
    labels = np.repeat(np.arange(400), 2)

    clo, chi = stats.cluster_bootstrap_ci(v, labels, seed=SEED)
    nlo, nhi = stats.mean_ci(v, seed=SEED)
    assert (chi - clo) > (nhi - nlo) * 1.25


def test_stochastic_results_are_reproducible_and_the_seed_is_required():
    r = _rng()
    v = r.normal(size=150)
    assert stats.mean_ci(v, seed=7) == stats.mean_ci(v, seed=7)
    assert stats.mean_ci(v, seed=7) != stats.mean_ci(v, seed=8)
    with pytest.raises(TypeError):
        stats.mean_ci(v)          # seed is keyword-only AND required


# --------------------------------------------------------------------------
# refusals: a wrong number is worse than an error
# --------------------------------------------------------------------------

def test_degenerate_input_raises_rather_than_returning_nan():
    with pytest.raises(ValueError, match="at least 2"):
        stats.mean_ci(np.array([1.0]), seed=SEED)
    with pytest.raises(ValueError, match="zero variance"):
        stats.cohens_d(np.array([3.0, 3.0, 3.0]))
    with pytest.raises(ValueError, match="zero variance"):
        stats.spearman(np.array([1.0, 1.0, 1.0]), np.array([1.0, 2.0, 3.0]))


def test_mismatched_lengths_raise():
    with pytest.raises(ValueError, match="same length"):
        stats.spearman(np.array([1.0, 2.0]), np.array([1.0, 2.0, 3.0]))
    with pytest.raises(ValueError, match="same length"):
        stats.cluster_bootstrap_ci(np.array([1.0, 2.0]), np.array([0]),
                                   seed=SEED)


def test_nan_is_refused_rather_than_silently_propagated():
    v = np.array([1.0, 2.0, np.nan, 4.0])
    with pytest.raises(ValueError, match="non-finite"):
        stats.mean_ci(v, seed=SEED)
    with pytest.raises(ValueError, match="non-finite"):
        stats.cohens_d(v)


# --------------------------------------------------------------------------
# the archived results must still reproduce through the engine
# --------------------------------------------------------------------------

def test_reproduces_the_archived_ICT_P1_effect_size():
    """M5's first backfill target, pinned as a test.

    ICT-P1 recorded Cohen d = -0.0015 from mean -0.00036 and sd 0.24361.
    The engine must agree with what is in the register.
    """
    assert stats.cohens_d_from(-0.00036, 0.24361) == pytest.approx(-0.0015,
                                                                  abs=5e-5)


def test_reproduces_the_archived_ICT_P2_control_decomposition():
    """total = penetration + drift is an exact identity, and it is what
    proved 94.8% of P2's headline was the reference price.

    Tolerance is 2e-5, not zero: the identity holds EXACTLY in the run, but
    the register stores each term rounded to five decimals, so re-adding
    two stored values can drift by up to 1e-5 each. Worth stating rather
    than loosening silently — the slack is rounding in the record, not
    slack in the arithmetic.
    """
    total, penetration, drift = -0.15853, -0.15023, -0.00829
    assert penetration + drift == pytest.approx(total, abs=2e-5)
    assert stats.share_of(penetration, total) == pytest.approx(0.9477,
                                                              abs=5e-4)


# --------------------------------------------------------------------------
# the inverse normal CDF, and the duplicate that already exists
# --------------------------------------------------------------------------

def test_ppf_matches_scipy_to_machine_precision():
    for p in (1e-9, 1e-4, 0.005, 0.025, 0.1, 0.4, 0.5, 0.6, 0.9,
              0.975, 0.995, 1 - 1e-9):
        assert stats.ppf(p) == pytest.approx(float(sps.norm.ppf(p)),
                                             rel=1e-13, abs=1e-13)


def test_ppf_is_symmetric_and_rejects_the_endpoints():
    assert stats.ppf(0.5) == pytest.approx(0.0, abs=1e-15)
    assert stats.ppf(0.975) == pytest.approx(-stats.ppf(0.025), abs=1e-14)
    for bad in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(ValueError, match="strictly between"):
            stats.ppf(bad)


def test_the_power_module_still_agrees_within_its_own_accuracy():
    """`power._z` is Acklam's (~1e-9); this is AS241 (~1e-16). They must
    agree to Acklam's stated accuracy, which pins the duplication until
    `power` is consolidated onto this one. If this ever fails, a sample-size
    gate has silently moved."""
    from occams import power
    for p in (0.8, 0.9, 0.95, 0.975, 0.99):
        assert power._z(p) == pytest.approx(stats.ppf(p), abs=1e-8)
