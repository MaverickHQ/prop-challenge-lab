"""M6 — the guard that keeps M5 true.

M5 established that the archive reproduces through the audited engine. That
is a statement about one afternoon. This is what stops it decaying.

**Two tiers, because a single-tier design fails either way.**

Tier 1 pins the ENGINE on deterministic synthetic inputs. It needs no
licensed data and no network, so it runs in `make check` every time, and any
change to `spearman`, the bootstrap, `cohens_d` or `forward_return` breaks it
in milliseconds. This is the tier that actually protects the archive: an
archived number can only move if an estimator moves, and this is what an
estimator moving looks like.

Tier 2 re-scores the REAL archived results end to end. It needs 2 GB of
vendor bars and S3, so it skips when they are absent -- and a test that
usually skips is a test that rots. It is therefore marked `reproduction`,
excluded from the default run, and wired to `make reproduce`, which is the
gate before any archived number is cited or published.

The archived values are pinned as constants BELOW even though tier 2 may
skip, so the expected numbers are visible in the repo rather than only in a
bucket. If a value here ever disagrees with the register, one of them is
wrong and that is worth finding out.

Golden values were generated once, by the engine, at 716c6ac. They are not
hand-computed and are not claimed to be independently correct -- M1's
known-answer tests against scipy are what establish correctness. These pin
BEHAVIOUR: that today's engine still does what the archive was scored with.
"""

from __future__ import annotations

import numpy as np
import pytest

from occams import calibration as cal
from occams import estimators as est
from occams import stats

TOL = 1e-11


def _inputs():
    """Deterministic, synthetic, and free of any vendor data."""
    rng = np.random.default_rng(20260806)
    x = rng.normal(size=1200)
    y = 0.25 * x + rng.normal(size=1200)
    tied = np.floor(x * 2) / 2.0                 # heavily tied on purpose
    v = rng.normal(loc=0.03, scale=0.9, size=1500)
    lab = np.repeat(np.arange(750), 2)
    closes = 100 + np.cumsum(rng.normal(size=400))
    return x, y, tied, v, lab, closes


# --------------------------------------------------------------------------
# TIER 1 — the engine's own numbers, pinned. Always runs.
# --------------------------------------------------------------------------

def test_rank_correlation_is_unchanged():
    x, y, tied, *_ = _inputs()
    assert stats.spearman(x, y) == pytest.approx(0.235404913476, abs=TOL)
    assert stats.pearson(x, y) == pytest.approx(0.238668559359, abs=TOL)


def test_rank_correlation_UNDER_TIES_is_unchanged():
    """The one that matters. C2's `mins to breakout` was 97.1% tied and moved
    28% on MNQ when the tie-averaged rank replaced `argsort(argsort(x))`.
    If this value ever shifts, every tied-predictor result in the archive
    has moved with it."""
    _, y, tied, *_ = _inputs()
    assert stats.spearman(tied, y) == pytest.approx(0.228207244261, abs=TOL)


def test_effect_size_and_bootstrap_intervals_are_unchanged():
    *_, v, lab, _ = _inputs()
    assert stats.cohens_d(v) == pytest.approx(0.014313332488, abs=TOL)
    lo, hi = stats.mean_ci(v, seed=7)
    assert (lo, hi) == pytest.approx((-0.030531317869, 0.058830519246),
                                     abs=TOL)


def test_the_cluster_bootstrap_is_unchanged_and_still_differs_from_the_plain_one():
    """Seeded, so it is reproducible; and WIDER than the independent version,
    which is the whole reason it exists (E4.2)."""
    *_, v, lab, _ = _inputs()
    clo, chi = stats.cluster_bootstrap_ci(v, lab, seed=7)
    assert (clo, chi) == pytest.approx((-0.03130857255, 0.056327042277),
                                       abs=TOL)


def test_the_block_bootstrap_is_unchanged_and_still_declines_iid_data():
    """M7. The block length must stay 1 on this independent series — the
    rule ignores autocorrelation inside its own noise floor, and if that
    threshold ever moves, every block length it has suggested moves too."""
    *_, v, lab, _ = _inputs()
    assert stats.block_bootstrap_ci(v, block=20, seed=7) == pytest.approx(
        (-0.031413020611, 0.058998137304), abs=TOL)
    assert stats.optimal_block_length(v) == 1


def test_the_wilson_interval_on_zero_of_6940_is_unchanged():
    """Z0.4 audited 6,940 orders and found zero unplaceable. The honest
    upper bound on that is the number this pins."""
    lo, hi = stats.proportion_ci(0, 6940)
    assert lo == 0.0
    assert hi == pytest.approx(0.000553218106, abs=TOL)


def test_the_inverse_normal_is_unchanged():
    assert stats.ppf(0.975) == pytest.approx(1.95996398454, abs=TOL)


def test_the_forward_return_decomposition_is_unchanged():
    *_, closes = _inputs()
    d = est.forward_return(closes, at=100, horizon=30, direction=1,
                           reference=est.AT_LEVEL, level=99.0, scale=2.0,
                           decompose=True)
    assert d.total == pytest.approx(9.047639432113, abs=TOL)
    assert d.positional == pytest.approx(6.230491090826, abs=TOL)
    assert d.drift == pytest.approx(2.817148341287, abs=TOL)
    assert d.positional + d.drift == pytest.approx(d.total, abs=1e-12)


def test_the_calibration_gate_still_separates_the_two_estimators():
    """If these converge, the gate has stopped discriminating and every
    'calibrated' verdict downstream is worthless."""
    honest = cal.calibrate(cal.at_price, expected=2.0, seed=11)
    artifact = cal.calibrate(cal.at_level, expected=2.0, seed=11)
    assert honest.dead_sigmas == pytest.approx(0.527834, abs=1e-5)
    assert artifact.dead_sigmas == pytest.approx(5.029294, abs=1e-5)
    assert honest.verdict == "calibrated"
    assert artifact.verdict == "fails the dead world"


# --------------------------------------------------------------------------
# TIER 2 — the real archive, end to end. Needs vendor bars + S3.
# --------------------------------------------------------------------------

ARCHIVED = {
    "H5.pooled.spearman": -0.0723,
    "C2.pooled.range/ATR": -0.1312,        # unchanged by the tie fix
    "C2.pooled.mins to breakout": -0.0440,  # CORRECTED 2026-08-03 from -0.0459
    "Z0.sealed engine (ASSUMED fill).MES": 0.08015468041603568,
    "Z0.a_limit_after_close.MES": -0.0559013939564053,
    "Z0.b_market_at_close.MES": -0.07555058592002953,
    "Z0.c_stop_armed_at_breakout.MES": -0.11879829031727884,
}


def _backfill():
    import importlib.util
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    if not (root / "data" / "MES.csv").exists():
        pytest.skip("vendor bars absent — this is the cache, not the archive")
    spec = importlib.util.spec_from_file_location(
        "_bf", root / "scripts" / "backfill_m5.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.reproduction
@pytest.mark.parametrize("target", ["H5", "C2", "Z0"])
def test_the_archived_result_still_reproduces(target):
    from occams import backfill
    bf = _backfill()
    kind, key, fn, places, sup = bf.TARGETS[target]
    try:
        arch = bf.archived(key)
    except Exception as e:                      # no credentials, no network
        pytest.skip(f"archive unreachable: {type(e).__name__}")
    checks = backfill.compare(arch, fn(), decimals_override=places,
                              superseded=sup)
    assert checks, f"{target} produced no comparable metrics"
    bad = [c for c in checks if not c.ok]
    assert not bad, backfill.render(checks, f"{target} [{kind}]")


@pytest.mark.reproduction
def test_the_pinned_archive_values_match_the_register():
    """The constants above exist so the expected numbers are visible in the
    repo. If they drift from the register, one of the two is wrong."""
    from occams import backfill
    bf = _backfill()
    try:
        flat = {}
        for name, (_, key, _, _, _) in bf.TARGETS.items():
            for k, v in backfill.flatten(bf.archived(key)).items():
                flat[f"{name}.{k}"] = v
    except Exception as e:
        pytest.skip(f"archive unreachable: {type(e).__name__}")
    for key, expected in ARCHIVED.items():
        if key.startswith("C2.pooled.mins"):
            continue          # superseded by the M5 correction record
        assert flat[key] == pytest.approx(expected, abs=5e-5), key
