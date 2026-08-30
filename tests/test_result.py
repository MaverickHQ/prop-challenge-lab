"""M3 — one object that carries the whole picture, and a ledger of how it
was computed.

Two problems, one module each.

**Scripts formatting their own numbers.** Every experiment script prints its
own table and builds its own METRICS dict, so the human line and the
recorded line are two independent renderings of the same result. They can
disagree, and nobody would notice.

**`engine_sha` pins the commit, not the calculation.** A record says which
repo state produced a number. It does not say which FUNCTION did, nor with
what arguments. Three years on, "the commit that produced it" is not the
same as "the estimator that produced it" — especially now that M1 replaced
three divergent copies of a bootstrap with one.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from occams import audit
from occams.result import Result


# --------------------------------------------------------------------------
# Result: significance and materiality are DIFFERENT questions
# --------------------------------------------------------------------------

def _r(**kw):
    base = dict(name="test", estimate=0.0, ci=(-1.0, 1.0), n=100, d=0.0,
                floor=0.07)
    base.update(kw)
    return Result(**base)


def test_a_ci_that_spans_zero_is_reported_as_spanning_zero():
    assert _r(ci=(-0.01, 0.02)).crosses_zero is True
    assert _r(ci=(0.01, 0.02)).crosses_zero is False
    assert _r(ci=(-0.02, -0.01)).crosses_zero is False


def test_effect_is_expressed_in_multiples_of_its_own_declared_floor():
    """The one transformation that makes a correlation, a Cohen's d and an
    ATR-scaled return comparable on the same axis."""
    assert _r(d=-0.0015, floor=0.07).floor_multiples == pytest.approx(-0.0214,
                                                                     abs=1e-3)
    assert _r(d=-0.4318, floor=0.07).floor_multiples == pytest.approx(-6.17,
                                                                     abs=1e-2)


def test_the_four_verdicts_separate_significance_from_materiality():
    """A result can be statistically clean and materially irrelevant, and
    the frontier work cares about the second. Collapsing them into
    'significant / not significant' is how a 1.7%-of-variance signal gets
    reported as a finding."""
    assert _r(ci=(-0.01, 0.01), d=0.001).verdict == "null"
    assert _r(ci=(0.10, 0.30), d=0.20).verdict == "detectable"
    assert _r(ci=(0.001, 0.004), d=0.002).verdict == "precise but immaterial"
    assert _r(ci=(-0.05, 0.40), d=0.20).verdict == "inconclusive"


def test_ICT_P1_reproduces_as_a_null_through_the_Result_object():
    r = Result(name="ICT-P1 FVG -> CE continuation", estimate=-0.00036,
               ci=(-0.0104, 0.0090), n=3159, n_eff=1662, d=-0.0015,
               floor=0.07, unit="ATR")
    assert r.verdict == "null"
    assert r.crosses_zero
    assert abs(r.floor_multiples) < 0.05


def test_ICT_P2_raw_reproduces_as_detectable_which_is_the_whole_problem():
    """It WAS detectable. That is exactly why a significance test could not
    save us and the control had to."""
    r = Result(name="ICT-P2 raw", estimate=-0.15853, ci=(-0.175, -0.14229),
               n=3156, d=-0.4318, floor=0.07, unit="ATR")
    assert r.verdict == "detectable"
    assert not r.crosses_zero


# --------------------------------------------------------------------------
# one source for the human line and the machine line
# --------------------------------------------------------------------------

def test_the_rendered_line_and_the_recorded_metrics_come_from_one_place():
    r = Result(name="drift", estimate=-0.00829, ci=(-0.01953, 0.00256),
               n=3156, n_eff=1662, d=-0.0341, floor=0.07, unit="ATR")
    text = r.render()
    m = r.to_metrics()
    assert "-0.00829" in text
    assert "ATR" in text
    assert "null" in text
    assert m["estimate"] == -0.00829
    assert m["ci"] == [-0.01953, 0.00256]
    assert m["n"] == 3156
    assert m["verdict"] == "null"
    assert json.loads(json.dumps(m)) == m          # must survive the record


def test_n_eff_is_carried_separately_because_pooling_is_not_free():
    r = Result(name="x", estimate=0.0, ci=(-1.0, 1.0), n=3159, n_eff=1662,
               d=0.0, floor=0.07)
    assert r.to_metrics()["n"] == 3159
    assert r.to_metrics()["n_eff"] == 1662
    assert "1,662" in r.render()


def test_a_result_refuses_impossible_inputs():
    with pytest.raises(ValueError, match="n must be positive"):
        _r(n=0)
    with pytest.raises(ValueError, match="floor"):
        _r(floor=-0.1)
    with pytest.raises(ValueError, match="ci"):
        _r(ci=(0.5, 0.1))
    with pytest.raises(ValueError, match="n_eff"):
        _r(n=100, n_eff=200)


# --------------------------------------------------------------------------
# the calculation ledger
# --------------------------------------------------------------------------

def test_an_audited_call_records_the_function_and_its_source_hash():
    audit.reset()
    from occams import stats
    stats.spearman([1.0, 2.0, 3.0, 4.0], [2.0, 1.0, 4.0, 3.0])
    entries = audit.ledger()
    names = {e["function"] for e in entries}
    assert "occams.stats.spearman" in names
    row = next(e for e in entries if e["function"] == "occams.stats.spearman")
    assert len(row["source_sha256"]) == 64
    assert row["calls"] == 1


def test_nested_calls_are_recorded_so_the_delegation_is_visible():
    """`spearman` is pearson-of-ranks and `mean_ci` is the cluster bootstrap
    with singleton clusters. Both are deliberate, and the ledger should show
    it rather than hide it behind the public name."""
    audit.reset()
    from occams import stats
    stats.mean_ci(np.arange(50, dtype=float), seed=1)
    names = {e["function"] for e in audit.ledger()}
    assert "occams.stats.mean_ci" in names
    assert "occams.stats.cluster_bootstrap_ci" in names


def test_array_arguments_are_recorded_by_shape_and_hash_not_by_value():
    """A ledger that inlined the inputs would be larger than the data. What
    matters for reproduction is that the SAME input was used, which a hash
    settles."""
    audit.reset()
    from occams import stats
    stats.cohens_d(np.random.default_rng(0).normal(size=5000))
    row = next(e for e in audit.ledger()
               if e["function"] == "occams.stats.cohens_d")
    arg = row["args"][0]
    assert arg["shape"] == [5000]
    assert len(arg["sha256"]) == 16
    assert len(json.dumps(row)) < 800


def test_the_same_data_hashes_the_same_and_different_data_does_not():
    audit.reset()
    from occams import stats
    v = np.arange(100, dtype=float)
    stats.cohens_d(v)
    stats.cohens_d(v.copy())
    stats.cohens_d(v + 1.0)
    row = next(e for e in audit.ledger()
               if e["function"] == "occams.stats.cohens_d")
    assert row["calls"] == 3
    hashes = {a["sha256"] for call in row["arg_samples"] for a in call}
    assert len(hashes) == 2                       # v and v+1, copy matches v


def test_the_ledger_is_bounded_so_a_loop_cannot_blow_it_up():
    audit.reset()
    from occams import stats
    for i in range(500):
        stats.cohens_d(np.array([1.0, 2.0, 3.0 + i]))
    row = next(e for e in audit.ledger()
               if e["function"] == "occams.stats.cohens_d")
    assert row["calls"] == 500
    assert len(row["arg_samples"]) <= audit.MAX_SAMPLES


def test_the_ledger_writes_json_that_the_archive_can_take():
    audit.reset()
    from occams import stats
    stats.pearson([1.0, 2.0, 3.0], [3.0, 2.0, 1.5])
    blob = json.loads(audit.dumps())
    assert blob["engine_sha"]
    assert isinstance(blob["calculations"], list)
    assert blob["calculations"][0]["function"].startswith("occams.")


def test_reset_clears_and_is_what_keeps_runs_independent():
    audit.reset()
    from occams import stats
    stats.pearson([1.0, 2.0, 3.0], [3.0, 2.0, 1.5])
    assert audit.ledger()
    audit.reset()
    assert audit.ledger() == []
