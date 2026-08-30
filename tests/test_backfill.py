"""M5 — the backfill comparator.

Small module, but it decides whether an archived result is called
reproduced, and that judgement has two ways to go wrong: a tolerance too
tight invents failures, a tolerance too loose hides them. M4 already made
the first mistake once, on its own noise floor.
"""

from __future__ import annotations

from occams import backfill as bf


def test_nested_metrics_flatten_to_dotted_keys():
    assert bf.flatten({"MES": {"n": 3, "r": -0.1}, "n": 7}) == {
        "MES.n": 3.0, "MES.r": -0.1, "n": 7.0}


def test_non_numeric_leaves_are_ignored_rather_than_coerced():
    out = bf.flatten({"note": "text", "ok": True, "r": 0.5})
    assert out == {"r": 0.5}


def test_recorded_precision_is_read_off_the_stored_value():
    assert bf.decimals(-0.1293) == 4
    assert bf.decimals(0.08) == 2
    assert bf.decimals(1631.0) == 0
    assert bf.rounding_tolerance(-0.1293) == 0.00005


def test_the_tolerance_is_half_the_last_recorded_place():
    """An archived value is already rounded, so an exact match is impossible
    in principle. The honest test is agreement to the precision at which it
    was recorded."""
    c = bf.Check("r", archived=-0.1293, recomputed=-0.12934,
                 kind=bf.DETERMINISTIC, tolerance=bf.rounding_tolerance(-0.1293))
    assert c.ok
    c2 = bf.Check("r", archived=-0.1293, recomputed=-0.1299,
                  kind=bf.DETERMINISTIC,
                  tolerance=bf.rounding_tolerance(-0.1293))
    assert not c2.ok
    assert c2.status == "MISMATCH"


def test_stochastic_metrics_get_their_own_tolerance_and_their_own_word():
    """A bootstrap CI cannot match exactly — M1's cluster bootstrap consumes
    its RNG differently from the three hand-rolled copies it replaced. Both
    are correct. Calling that a MISMATCH would train everyone to ignore the
    check."""
    checks = bf.compare({"ci_low": -0.0195, "r": -0.13},
                        {"ci_low": -0.0201, "r": -0.13},
                        stochastic=("ci_",))
    lo = next(c for c in checks if c.metric == "ci_low")
    assert lo.kind == bf.STOCHASTIC
    assert lo.ok
    assert bf.all_ok(checks)


def test_a_stochastic_metric_that_moves_too_far_is_still_reported():
    checks = bf.compare({"ci_low": -0.02}, {"ci_low": -0.50},
                        stochastic=("ci_",), stochastic_tol=0.05)
    assert not checks[0].ok
    assert checks[0].status == "DRIFT"


def test_metrics_absent_from_the_recompute_are_skipped_not_failed():
    """A partial backfill is normal. Failing on absence would make every
    incremental run look broken."""
    checks = bf.compare({"a": 1.0, "b": 2.0}, {"a": 1.0})
    assert [c.metric for c in checks] == ["a"]
    assert bf.all_ok(checks)


def test_an_explicit_decimals_override_beats_inference():
    """Inference is a LOWER bound on precision: 0.080 is stored as 0.08, so
    the inferred tolerance is conservative. When the script's own rounding
    is known, say so."""
    loose = bf.compare({"x": 0.08}, {"x": 0.0843})
    assert loose[0].ok                                  # 2dp inferred
    tight = bf.compare({"x": 0.08}, {"x": 0.0843}, decimals_override=3)
    assert not tight[0].ok


def test_render_names_how_many_reproduced():
    checks = bf.compare({"a": 1.0, "b": 2.0}, {"a": 1.0, "b": 9.0})
    text = bf.render(checks, "T")
    assert "1/2 reproduce" in text
    assert "1 NOT" in text
