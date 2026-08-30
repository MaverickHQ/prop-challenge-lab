"""M2 — the estimand is a required argument, not a default.

M1 put the arithmetic in one audited place. It does not help with the error
that actually cost this programme a result: ICT-P2's arithmetic was
PERFECT and its answer was still wrong, because it measured from the wrong
reference price.

That defect is not detectable by any significance test. P2 was significant
on both instruments, on both sides, and at both horizons — every robustness
check a normal process runs, all passed, all meaningless, because they were
robustness checks on an arithmetic identity rather than on a market.

So the fix is structural rather than statistical: a reference price that is
not "where price is right now" carries a positional term that is positive
by construction, and this module refuses to return it as a single number.

The load-bearing test here is `test_a_frozen_market_still_prints_a_reading`.
"""

from __future__ import annotations

import numpy as np
import pytest

from occams import estimators as est
from occams import execution as ex


def _flat(n=60, price=100.0):
    return np.full(n, price, dtype=float)


# --------------------------------------------------------------------------
# the defect, as a unit test
# --------------------------------------------------------------------------

def test_a_frozen_market_still_prints_a_reading():
    """ICT-P2 in miniature, and the reason this module exists.

    A market that trades up through a level and then FREEZES SOLID has zero
    forward drift by construction. Measured from where price actually is,
    the answer is correctly zero. Measured from the swept level, it is a
    large positive continuation reading — entirely the penetration.
    """
    closes = _flat(40, 100.0)
    closes[10:] = 105.0                      # sweeps to 105, then nothing
    level = 100.0

    honest = est.forward_return(closes, at=10, horizon=30, direction=1,
                                reference=est.AT_PRICE)
    assert honest == pytest.approx(0.0)

    d = est.forward_return(closes, at=10, horizon=30, direction=1,
                           reference=est.AT_LEVEL, level=level, decompose=True)
    assert d.drift == pytest.approx(0.0)
    assert d.positional == pytest.approx(5.0)
    assert d.total == pytest.approx(5.0)
    assert d.share_positional == pytest.approx(1.0)


def test_a_level_reference_refuses_to_return_one_number():
    closes = _flat(40)
    closes[10:] = 105.0
    with pytest.raises(est.AmbiguousReference, match="POSITIONAL"):
        est.forward_return(closes, at=10, horizon=30, direction=1,
                           reference=est.AT_LEVEL, level=100.0)


def test_a_fill_reference_also_refuses():
    """ICT-P1 measured from a touched level. Conditional on a bar reaching
    a price, that bar's close tends to sit on the far side of it — a
    smaller bias than P2's, in the same direction, and still a bias."""
    closes = _flat(40)
    closes[10:] = 101.0
    with pytest.raises(est.AmbiguousReference):
        est.forward_return(closes, at=10, horizon=30, direction=1,
                           reference=est.AT_FILL, level=100.0)


def test_the_decomposition_is_an_exact_identity():
    rng = np.random.default_rng(20260803)
    closes = 100 + np.cumsum(rng.normal(size=200))
    for at in (5, 40, 120):
        for direction in (1, -1):
            d = est.forward_return(closes, at=at, horizon=30,
                                   direction=direction,
                                   reference=est.AT_LEVEL, level=99.5,
                                   scale=2.5, decompose=True)
            assert d.positional + d.drift == pytest.approx(d.total, abs=1e-12)


def test_at_price_has_no_positional_term_by_definition():
    rng = np.random.default_rng(1)
    closes = 100 + np.cumsum(rng.normal(size=100))
    d = est.forward_return(closes, at=20, horizon=10, direction=1,
                           reference=est.AT_PRICE, decompose=True)
    assert d.positional == 0.0
    assert d.total == d.drift


# --------------------------------------------------------------------------
# direction, scale, and the day-flat truncation
# --------------------------------------------------------------------------

def test_direction_flips_the_sign_and_nothing_else():
    closes = _flat(30)
    closes[20:] = 103.0
    up = est.forward_return(closes, at=10, horizon=15, direction=1,
                            reference=est.AT_PRICE)
    dn = est.forward_return(closes, at=10, horizon=15, direction=-1,
                            reference=est.AT_PRICE)
    assert up == pytest.approx(3.0)
    assert dn == pytest.approx(-3.0)


def test_scale_normalises_and_must_be_positive():
    closes = _flat(30)
    closes[20:] = 104.0
    assert est.forward_return(closes, at=10, horizon=15, direction=1,
                              reference=est.AT_PRICE, scale=2.0) == pytest.approx(2.0)
    for bad in (0.0, -1.0):
        with pytest.raises(ValueError, match="scale"):
            est.forward_return(closes, at=10, horizon=15, direction=1,
                               reference=est.AT_PRICE, scale=bad)


def test_the_horizon_truncates_at_the_session_close_and_says_so():
    """Our rules are day-flat: there is no holding past the close, so a
    horizon that runs off the end is truncated rather than dropped. But a
    sample where 40% of observations were truncated is a different sample,
    so the flag is carried, not swallowed."""
    assert est.horizon_end(100, at=10, horizon=30) == (40, False)
    assert est.horizon_end(100, at=90, horizon=30) == (99, True)

    closes = _flat(50)
    closes[-1] = 107.0
    d = est.forward_return(closes, at=45, horizon=30, direction=1,
                           reference=est.AT_PRICE, decompose=True)
    assert d.truncated is True
    assert d.drift == pytest.approx(7.0)


def test_a_zero_length_window_is_refused_not_returned_as_zero():
    closes = _flat(50)
    with pytest.raises(ValueError, match="horizon"):
        est.forward_return(closes, at=10, horizon=0, direction=1,
                           reference=est.AT_PRICE)
    with pytest.raises(ValueError, match="last bar"):
        est.forward_return(closes, at=49, horizon=10, direction=1,
                           reference=est.AT_PRICE)


# --------------------------------------------------------------------------
# fills are DERIVED, never supplied
# --------------------------------------------------------------------------

def test_measuring_from_a_fill_derives_it_from_what_the_market_did():
    """E1 joined to M2. The caller names an ORDER
    the fill comes from the
    bars. There is no argument through which a fill price can be asserted."""
    n = 40
    highs = np.full(n, 101.0)
    lows = np.full(n, 99.0)
    opens = np.full(n, 100.0)
    closes = np.full(n, 100.0)
    lows[15] = 98.0                      # the only bar that reaches 98.5
    closes[20:] = 103.0

    order = ex.Order(ex.LIMIT, ex.BUY, 98.5)
    got = est.measure_from_fill(order, highs=highs, lows=lows, opens=opens,
                                closes=closes, placed_at=5, horizon=10,
                                direction=1)
    assert got.fill_index == 15
    assert got.fill_price == pytest.approx(98.5)
    assert got.positional == pytest.approx(1.5)      # close 100 vs fill 98.5
    assert got.positional + got.drift == pytest.approx(got.total, abs=1e-12)


def test_an_order_that_never_fills_returns_None_not_a_number():
    n = 30
    highs = np.full(n, 101.0)
    lows = np.full(n, 99.0)
    opens = np.full(n, 100.0)
    closes = np.full(n, 100.0)
    order = ex.Order(ex.LIMIT, ex.BUY, 90.0)          # never reached
    assert est.measure_from_fill(order, highs=highs, lows=lows, opens=opens,
                                 closes=closes, placed_at=0, horizon=10,
                                 direction=1) is None


def test_an_unplaceable_order_is_refused_before_it_is_measured():
    n = 30
    highs = np.full(n, 101.0)
    lows = np.full(n, 99.0)
    opens = np.full(n, 100.0)
    closes = np.full(n, 100.0)
    order = ex.Order(ex.LIMIT, ex.BUY, 105.0)     # above market: not passive
    with pytest.raises(ex.Unplaceable):
        est.measure_from_fill(order, highs=highs, lows=lows, opens=opens,
                              closes=closes, placed_at=0, horizon=10,
                              direction=1)


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------

def test_an_unknown_reference_is_refused_and_names_the_valid_ones():
    closes = _flat(30)
    with pytest.raises(ValueError, match="at_price"):
        est.forward_return(closes, at=5, horizon=10, direction=1,
                           reference="wherever")


def test_a_level_reference_without_a_level_is_refused():
    closes = _flat(30)
    with pytest.raises(ValueError, match="level"):
        est.forward_return(closes, at=5, horizon=10, direction=1,
                           reference=est.AT_LEVEL, decompose=True)


def test_direction_must_be_plus_or_minus_one():
    closes = _flat(30)
    for bad in (0, 2, -3):
        with pytest.raises(ValueError, match="direction"):
            est.forward_return(closes, at=5, horizon=10, direction=bad,
                               reference=est.AT_PRICE)


# --------------------------------------------------------------------------
# the archived result must reproduce through the estimator
# --------------------------------------------------------------------------

def test_reproduces_the_shape_of_the_archived_ICT_P2_decomposition():
    """Not the values — those need the vendor bars — but the STRUCTURE the
    control relied on: a total dominated by its positional term, with the
    drift a small remainder."""
    closes = _flat(40, 100.0)
    closes[10] = 105.3                       # sweep bar closes well through
    closes[11:] = 105.0                      # then drifts back a little
    d = est.forward_return(closes, at=10, horizon=30, direction=-1,
                           reference=est.AT_LEVEL, level=100.0,
                           decompose=True)
    assert d.share_positional > 0.9
    assert abs(d.drift) < abs(d.positional) * 0.15
    assert d.positional + d.drift == pytest.approx(d.total, abs=1e-12)
