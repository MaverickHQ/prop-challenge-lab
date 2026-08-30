"""E7 — read edge existence off the P(pass) curve, not off expectancy.

Expectancy has misled this lab twice: once via an unobtainable entry price,
once via a cost model that made a gross-positive strategy net-negative. The
shape of P(pass) against size depends on neither.
"""

from __future__ import annotations

from occams.harness import edge_shape


def test_the_real_e2_curve_is_diagnosed_as_no_edge():
    """The measured obtainable fade: 0.000, 0.009, 0.042, 0.088, 0.174."""
    out = edge_shape({75: 0.000, 125: 0.009, 175: 0.042,
                      250: 0.088, 350: 0.174})
    assert out["shape"] == "monotonic increasing"
    assert out["edge"] is False
    assert "variance" in out["reason"]


def test_an_interior_peak_is_diagnosed_as_a_real_edge():
    out = edge_shape({75: 0.31, 125: 0.58, 175: 0.66, 250: 0.49, 350: 0.22})
    assert out["shape"] == "interior peak"
    assert out["edge"] is True
    assert out["peak_risk"] == 175


def test_a_strategy_that_never_passes_is_dead_not_merely_flat():
    out = edge_shape({75: 0.0, 125: 0.0, 175: 0.0})
    assert out["shape"] == "dead"


def test_two_points_cannot_show_a_shape():
    assert edge_shape({100: 0.1, 200: 0.2})["shape"] == "indeterminate"


def test_a_boundary_peak_warns_that_the_ladder_is_the_constraint():
    """If the maximum sits at the edge of the sizes tested, the ladder is
    measuring risk appetite, not skill."""
    out = edge_shape({75: 0.9, 125: 0.5, 175: 0.2})
    assert out["edge"] is False and "Widen it" in out["reason"]
