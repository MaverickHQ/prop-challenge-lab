"""M4 — the gate that would have caught ICT-P2 with no judgement required.

M1 put the arithmetic in one place. M2 made the estimand a required
argument. Both help only if somebody reads the code. This is the part that
does not need anybody to notice anything:

    every estimator must return ~0 on a world with no effect,
    and recover the planted effect on a world that has one.

ICT-P2 fails the first half by construction. On a zero-drift random walk a
measurement taken from a swept LEVEL returns the overshoot -- a market that
froze the instant it swept would still print a large continuation reading --
while the same measurement taken from PRICE correctly returns nothing.

The load-bearing test is `test_the_gate_REJECTS_the_reference_price_estimator`.
A calibration gate that only ever passes is decoration.
"""

from __future__ import annotations

import pytest

from occams import calibration as cal


# --------------------------------------------------------------------------
# the worlds themselves must be what they claim
# --------------------------------------------------------------------------

def test_the_dead_world_really_has_no_forward_drift():
    """Judged in STANDARD ERRORS, not absolute units. An earlier version of
    this test used a fixed 0.15 and failed on a sound estimator, because the
    sampling error of the check itself was 0.26."""
    import numpy as np
    w = cal.dead_world(2000, seed=1)
    obs = np.array([o for o in (cal.at_price(w, i) for i in range(w.n_days))
                    if o is not None])
    assert obs.size > 1500
    se = obs.std(ddof=1) / np.sqrt(obs.size)
    assert abs(obs.mean()) < 3 * se


def test_the_planted_world_really_carries_the_effect_it_claims():
    w = cal.planted_world(2000, seed=1, effect=2.0)
    obs = [cal.at_price(w, i) for i in range(w.n_days)]
    obs = [o for o in obs if o is not None]
    assert 1.5 < sum(obs) / len(obs) < 2.5


def test_both_worlds_are_deterministic_per_seed():
    a = cal.dead_world(50, seed=7)
    b = cal.dead_world(50, seed=7)
    c = cal.dead_world(50, seed=8)
    assert (a.closes == b.closes).all()
    assert not (a.closes == c.closes).all()


def test_a_sweep_is_found_on_most_days_and_price_is_beyond_the_level():
    """The trigger is a genuine sweep of the running extreme, which is what
    makes this the same SHAPE as ICT-P2 rather than an invented setup."""
    w = cal.dead_world(500, seed=3)
    found = [i for i in range(w.n_days) if w.trigger[i] >= 0]
    assert len(found) > 400
    for i in found[:50]:
        t = w.trigger[i]
        beyond = (w.closes[i, t] - w.level[i]) * w.direction[i]
        assert beyond > 0


# --------------------------------------------------------------------------
# the gate, applied to an honest estimator
# --------------------------------------------------------------------------

def test_an_honest_estimator_passes_both_halves():
    r = cal.calibrate(cal.at_price, expected=2.0, seed=11)
    assert r.dead_ok is True
    assert r.planted_ok is True
    assert r.verdict == "calibrated"
    assert "calibrated" in r.render()


def test_assert_calibrated_is_silent_when_the_estimator_is_sound():
    cal.assert_calibrated(cal.at_price, expected=2.0, seed=11)


# --------------------------------------------------------------------------
# THE test: the gate must have teeth
# --------------------------------------------------------------------------

def test_the_gate_REJECTS_the_reference_price_estimator():
    """ICT-P2, caught automatically.

    Identical data, identical arithmetic, one different reference price.
    The dead world has no forward drift at all, so any non-zero reading is
    the measurement rather than the market.
    """
    r = cal.calibrate(cal.at_level, expected=2.0, seed=11)
    assert r.dead_ok is False
    assert r.verdict == "fails the dead world"
    assert r.dead_mean > 0.5           # pure overshoot, from nothing
    assert "dead" in r.render()


def test_assert_calibrated_RAISES_on_the_reference_price_estimator():
    with pytest.raises(cal.Uncalibrated, match="dead world"):
        cal.assert_calibrated(cal.at_level, expected=2.0, seed=11)


def test_the_rejection_message_names_the_size_of_the_phantom_effect():
    with pytest.raises(cal.Uncalibrated) as e:
        cal.assert_calibrated(cal.at_level, expected=2.0, seed=11)
    assert "froze" in str(e.value)


# --------------------------------------------------------------------------
# the other failure mode: an estimator that cannot see a real effect
# --------------------------------------------------------------------------

def test_an_estimator_that_misses_a_planted_effect_is_also_rejected():
    """A dead-world pass alone is not calibration. An estimator that
    returns zero for everything passes half the gate and is useless."""
    def always_zero(world, i):
        return 0.0
    r = cal.calibrate(always_zero, expected=2.0, seed=11)
    assert r.dead_ok is True
    assert r.planted_ok is False
    assert r.verdict == "misses the planted effect"
    with pytest.raises(cal.Uncalibrated, match="planted"):
        cal.assert_calibrated(always_zero, expected=2.0, seed=11)


def test_an_estimator_that_fails_both_reports_both():
    def always_five(world, i):
        return 5.0
    r = cal.calibrate(always_five, expected=2.0, seed=11)
    assert r.dead_ok is False
    assert r.planted_ok is False
    assert r.verdict == "fails the dead world"      # the worse fault first


# --------------------------------------------------------------------------
# the engine's own estimators must pass their own gate
# --------------------------------------------------------------------------

def test_the_shipped_forward_return_estimator_is_calibrated():
    """`estimators.forward_return` with AT_PRICE, driven through the gate
    exactly as an experiment would call it."""
    cal.assert_calibrated(cal.shipped_at_price, expected=2.0, seed=11)


def test_the_shipped_decomposition_recovers_drift_and_isolates_position():
    """AT_LEVEL is not forbidden — it is forbidden UNDECOMPOSED. The drift
    term must pass the same gate the total fails."""
    cal.assert_calibrated(cal.shipped_level_drift, expected=2.0, seed=11)
    r = cal.calibrate(cal.shipped_level_total, expected=2.0, seed=11)
    assert r.dead_ok is False
