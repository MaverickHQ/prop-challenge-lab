"""M7 — the block bootstrap, kept from an external feature specification.

We already resample historical START dates (`harness.monte_carlo`, over every
viable start day). That preserves the market path exactly but only ever
replays the one history we own. A per-observation resample gives variety and
destroys the thing that matters: volatility clusters, and the run of losing
days that is what actually breaches a trailing drawdown.

Block resampling sits between them — it keeps runs intact by construction.
The spec's reasoning for preferring it over a per-trade shuffle was right,
and it is the one part of that document worth taking on statistical grounds
rather than product grounds.

Two properties carry the whole module:

- with `block=1` it must reduce EXACTLY to the plain bootstrap, so the
  independent case is a special case rather than a second implementation
- on a serially correlated series it must be WIDER than the plain
  bootstrap, which is the entire reason it exists
"""

from __future__ import annotations

import numpy as np
import pytest

from occams import stats

SEED = 20260803


def _ar1(n: int, rho: float, seed: int = 5) -> np.ndarray:
    rng = np.random.default_rng(seed)
    e = rng.normal(size=n)
    v = np.empty(n)
    v[0] = e[0]
    for i in range(1, n):
        v[i] = rho * v[i - 1] + e[i]
    return v


# --------------------------------------------------------------------------
# the two load-bearing properties
# --------------------------------------------------------------------------

def test_a_block_of_one_reduces_EXACTLY_to_the_plain_bootstrap():
    """Not 'close to'. Identical, on the same seed — the independent case is
    a special case of the dependent one, not a second implementation of it.
    Same rule as `mean_ci` delegating to the cluster bootstrap in M1."""
    v = np.random.default_rng(1).normal(size=300)
    assert stats.block_bootstrap_ci(v, block=1, seed=7) == \
        stats.mean_ci(v, seed=7)


def test_a_block_bootstrap_is_WIDER_on_a_serially_correlated_series():
    """The whole reason it exists. A per-observation resample treats a run
    of losing days as independent draws and reports a confidence it has not
    earned."""
    v = _ar1(1200, rho=0.7)
    blo, bhi = stats.block_bootstrap_ci(v, block=20, seed=SEED)
    plo, phi = stats.mean_ci(v, seed=SEED)
    assert (bhi - blo) > (phi - plo) * 1.4


def test_on_independent_data_the_two_agree():
    """If blocking widened an iid series too, it would just be a penalty
    rather than a correction."""
    v = np.random.default_rng(3).normal(size=1200)
    blo, bhi = stats.block_bootstrap_ci(v, block=20, seed=SEED)
    plo, phi = stats.mean_ci(v, seed=SEED)
    assert 0.8 < (bhi - blo) / (phi - plo) < 1.25


def test_the_interval_widens_monotonically_with_block_length_under_dependence():
    v = _ar1(1500, rho=0.6)
    widths = [stats.block_bootstrap_ci(v, block=b, seed=SEED)[1]
              - stats.block_bootstrap_ci(v, block=b, seed=SEED)[0]
              for b in (1, 5, 20)]
    assert widths[0] < widths[1] < widths[2]


def test_the_ci_contains_its_own_point_estimate():
    for rho in (0.0, 0.5, 0.85):
        v = _ar1(800, rho=rho)
        lo, hi = stats.block_bootstrap_ci(v, block=10, seed=SEED)
        assert lo <= v.mean() <= hi


# --------------------------------------------------------------------------
# choosing the block length
# --------------------------------------------------------------------------

def test_the_suggested_block_length_grows_with_serial_dependence():
    lengths = [stats.optimal_block_length(_ar1(2000, rho=r))
               for r in (0.0, 0.3, 0.6, 0.85)]
    assert lengths[0] == 1
    assert lengths[1] < lengths[2] < lengths[3]


def test_the_suggested_block_length_stays_within_sane_bounds():
    for rho in (0.0, 0.5, 0.95, 0.99):
        for n in (100, 2000):
            b = stats.optimal_block_length(_ar1(n, rho=rho))
            assert 1 <= b <= max(1, n // 4)


def test_negative_autocorrelation_does_not_ask_for_a_long_block():
    v = np.array([1.0, -1.0] * 500)          # strongly anti-correlated
    assert stats.optimal_block_length(v) == 1


# --------------------------------------------------------------------------
# refusals and reproducibility
# --------------------------------------------------------------------------

def test_the_seed_is_required_and_the_result_is_reproducible():
    v = np.random.default_rng(2).normal(size=200)
    assert stats.block_bootstrap_ci(v, block=5, seed=3) == \
        stats.block_bootstrap_ci(v, block=5, seed=3)
    assert stats.block_bootstrap_ci(v, block=5, seed=3) != \
        stats.block_bootstrap_ci(v, block=5, seed=4)
    with pytest.raises(TypeError):
        stats.block_bootstrap_ci(v, block=5)


def test_an_impossible_block_length_is_refused():
    v = np.random.default_rng(2).normal(size=50)
    with pytest.raises(ValueError, match="block"):
        stats.block_bootstrap_ci(v, block=0, seed=1)
    with pytest.raises(ValueError, match="block"):
        stats.block_bootstrap_ci(v, block=51, seed=1)


def test_non_finite_input_is_refused_here_too():
    v = np.array([1.0, 2.0, np.nan, 4.0])
    with pytest.raises(ValueError, match="non-finite"):
        stats.block_bootstrap_ci(v, block=2, seed=1)
