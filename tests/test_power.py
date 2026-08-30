"""E4 — the sample size is decided before the evidence is spent.

The order-flow purchase this session picked a sample size from the BUDGET
and only afterwards checked what it could detect. It happened to be
adequate. That was luck, and these tests are what replaces it.
"""

from __future__ import annotations

import pytest

from occams import power


def test_smaller_effects_need_bigger_samples():
    assert power.n_for_correlation(0.05) > power.n_for_correlation(0.20)


def test_correlation_sizing_matches_the_standard_result():
    """r=0.10 at 80% power, alpha 0.05 is the textbook ~782."""
    assert 770 <= power.n_for_correlation(0.10) <= 790


def test_detectable_effect_is_the_inverse_and_the_honest_question():
    n = power.n_for_correlation(0.15)
    assert abs(power.detectable_correlation(n) - 0.15) < 0.005


def test_distinguishing_a_28pct_win_rate_from_35pct_needs_hundreds():
    n = power.n_for_proportions(0.28, 0.35)
    assert 500 < n < 900, n


def test_required_n_rejects_an_unknown_test():
    with pytest.raises(ValueError, match="unknown test"):
        power.required_n({"test": "vibes", "effect": 0.1})


# --- the precondition in the SOP ---

def test_a_declared_power_plan_demands_an_n_in_the_metrics():
    from occams import experiment
    hyp = {"id": "H-X", "power_plan": {"test": "correlation", "effect": 0.1}}
    with pytest.raises(ValueError, match="must emit an 'n'"):
        experiment._check_power(hyp, {"r": 0.02})


def test_an_underpowered_run_is_REFUSED_not_reported():
    from occams import experiment
    hyp = {"id": "H-X", "power_plan": {"test": "correlation", "effect": 0.1}}
    with pytest.raises(ValueError, match="UNDERPOWERED"):
        experiment._check_power(hyp, {"n": 100, "r": 0.02})


def test_an_adequately_powered_run_passes():
    from occams import experiment
    hyp = {"id": "H-X", "power_plan": {"test": "correlation", "effect": 0.1}}
    experiment._check_power(hyp, {"n": 900, "r": 0.02})     # must not raise


def test_no_power_plan_means_no_check():
    """Calibration work and verifications have no effect size to declare."""
    from occams import experiment
    experiment._check_power({"id": "H-X"}, {})              # must not raise


# --- E4.2: pooling correlated instruments is not free ---

def test_independent_observations_are_unchanged():
    assert power.effective_n(901) == 901
    assert power.effective_n(901, cluster_size=1, intra_r=0.9) == 901


def test_pooling_two_highly_correlated_instruments_nearly_halves_the_sample():
    """H5's actual case: 901 pooled MES+MNQ setups at ~0.9 intraday
    correlation are worth roughly 474 independent ones."""
    assert 460 <= power.effective_n(901, cluster_size=2, intra_r=0.9) <= 490


def test_perfect_correlation_collapses_a_pair_to_one():
    assert power.effective_n(900, cluster_size=2, intra_r=0.999) < 460


def test_the_gate_uses_the_DISCOUNTED_n_not_the_raw_one():
    """The defect this fixes: H5 passed a gate needing n>=783 with a raw
    n=901 that was really worth ~474."""
    from occams import experiment
    hyp = {"id": "H5", "power_plan": {"test": "correlation", "effect": 0.10,
                                      "cluster_size": 2,
                                      "intra_cluster_r": 0.9}}
    with pytest.raises(ValueError, match="UNDERPOWERED"):
        experiment._check_power(hyp, {"n": 901})


def test_the_refusal_shows_both_the_raw_and_discounted_n():
    from occams import experiment
    hyp = {"id": "H5", "power_plan": {"test": "correlation", "effect": 0.10,
                                      "cluster_size": 2,
                                      "intra_cluster_r": 0.9}}
    try:
        experiment._check_power(hyp, {"n": 901})
    except ValueError as e:
        assert "raw n=901" in str(e) and "cluster of 2" in str(e)
