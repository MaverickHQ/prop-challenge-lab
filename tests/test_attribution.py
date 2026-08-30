"""Q2 — every failed path gets a principal reason.

E2 returned P(pass) 0.042 and P(breach) 0.440 and never said WHY each path
died. Those two do not sum to one, so a third of all attempts ended in some
unnamed way — and "unnamed" turned out to include at least three genuinely
different outcomes with different remedies.

A single probability is a scoreboard. A decomposition is a diagnosis: an
attempt that ran out of time wants more horizon, one that breached wants
less size, and one blocked by a consistency rule wants neither.

The rule that matters: **exactly one reason per path, and they must sum to
the total.** A path with two problems gets the one that ended it, decided by
a fixed precedence rather than by whichever check happened to run first.
"""

from __future__ import annotations

import pytest

from occams.attribution import REASONS, Failure, attribute, tally
from occams.harness import ChallengeRun
from occams.rules import ChallengeConfig, Status

CFG = ChallengeConfig(account=50_000, target=3_000, trailing_dd=2_000,
                      daily_guard=1_000, min_days=5)


def _run(status, equity, days, marks=None):
    return ChallengeRun(status=status, final_equity=equity, days_used=days,
                        equity_marks=marks or [equity])


# --------------------------------------------------------------------------
# the reasons themselves
# --------------------------------------------------------------------------

def test_a_breach_by_realised_loss_is_named_as_one():
    r = _run(Status.BREACHED, 47_500, 30)
    assert attribute(r, CFG, horizon=90).reason is Failure.BREACH_DRAWDOWN


def test_running_out_of_horizon_is_NOT_the_same_as_breaching():
    """The commonest silent outcome, and the one with a different remedy:
    an attempt that was still alive and simply ran out of days wants more
    horizon, not less size."""
    r = _run(Status.ACTIVE, 51_200, 90)
    f = attribute(r, CFG, horizon=90)
    assert f.reason is Failure.TIMEOUT_IN_PROFIT
    assert "still alive" in f.detail


def test_an_attempt_still_short_of_target_at_timeout_says_how_short():
    r = _run(Status.ACTIVE, 51_200, 90)
    f = attribute(r, CFG, horizon=90)
    assert "1,800" in f.detail                 # 3,000 target less 1,200 made


def test_reaching_the_target_but_not_the_minimum_days_is_its_own_reason():
    r = _run(Status.ACTIVE, 53_500, 3)
    assert attribute(r, CFG, horizon=90).reason is Failure.MIN_DAYS


def test_reaching_the_target_but_failing_consistency_is_its_own_reason():
    cfg = ChallengeConfig(account=50_000, target=3_000, trailing_dd=2_000,
                          daily_guard=1_000, min_days=1,
                          consistency_frac=0.40)
    r = _run(Status.ACTIVE, 53_500, 40, marks=[50_000, 53_400, 53_500])
    assert attribute(r, cfg, horizon=90).reason is Failure.CONSISTENCY


def test_a_pass_is_not_a_failure_and_is_refused():
    with pytest.raises(ValueError, match="PASSED"):
        attribute(_run(Status.PASSED, 53_000, 40), CFG, horizon=90)


def test_an_attempt_that_never_traded_is_flagged_as_an_instrument_problem():
    """Verdict #1's lesson: silence is not a NO-GO. A run that never took a
    trade is an instrument failure and must never be counted as a market
    result."""
    r = _run(Status.ACTIVE, 50_000, 90, marks=[50_000] * 90)
    f = attribute(r, CFG, horizon=90)
    assert f.reason is Failure.NEVER_TRADED
    assert "instrument" in f.detail


# --------------------------------------------------------------------------
# precedence — a path with two problems gets the one that ENDED it
# --------------------------------------------------------------------------

def test_a_breach_outranks_everything_else():
    """An account that breached at a mark below target had several things
    wrong; only one of them ended it."""
    r = _run(Status.BREACHED, 47_000, 12, marks=[50_000, 47_000])
    assert attribute(r, CFG, horizon=90).reason is Failure.BREACH_DRAWDOWN


def test_min_days_outranks_timeout_when_the_target_was_reached():
    r = _run(Status.ACTIVE, 53_500, 2)
    assert attribute(r, CFG, horizon=90).reason is Failure.MIN_DAYS


def test_a_timeout_that_was_UNDERWATER_is_not_the_same_as_nearly_made_it():
    """The refinement that changed the reading of Q2's first run. "Ran out
    of days" implies the remedy is a longer horizon. For a losing strategy
    it is the opposite: those attempts were bleeding slowly enough not to
    breach, and more days would have produced more BREACHES."""
    ahead = attribute(_run(Status.ACTIVE, 51_200, 90), CFG, horizon=90)
    behind = attribute(_run(Status.ACTIVE, 48_968, 90), CFG, horizon=90)
    assert ahead.reason is Failure.TIMEOUT_IN_PROFIT
    assert behind.reason is Failure.TIMEOUT_UNDERWATER
    assert "more breaches" in behind.detail
    assert "AHEAD" in ahead.detail


def test_the_precedence_order_is_explicit_and_total():
    """No path can fall through: every reason is reachable and the order is
    declared, not emergent from check ordering."""
    assert REASONS[0] is Failure.BREACH_DRAWDOWN
    assert Failure.TIMEOUT_UNDERWATER in REASONS
    assert len(REASONS) == len(set(REASONS)) == len(Failure)


# --------------------------------------------------------------------------
# the tally must sum
# --------------------------------------------------------------------------

def test_the_decomposition_sums_to_the_number_of_failures():
    runs = [_run(Status.BREACHED, 47_000, 10),
            _run(Status.ACTIVE, 51_000, 90),
            _run(Status.ACTIVE, 53_500, 2),
            _run(Status.PASSED, 53_500, 40)]
    t = tally(runs, CFG, horizon=90)
    assert t["passed"] == 1
    assert sum(t["reasons"].values()) == 3
    assert t["reasons"]["breach_drawdown"] == 1
    assert t["reasons"]["timeout_in_profit"] == 1
    assert t["reasons"]["min_days"] == 1


def test_shares_are_of_ALL_attempts_not_just_failures():
    """P(pass) and the failure shares must add to 1, or the decomposition
    invites the reader to double-count."""
    runs = [_run(Status.BREACHED, 47_000, 10),
            _run(Status.PASSED, 53_500, 40)]
    t = tally(runs, CFG, horizon=90)
    assert t["p_pass"] == pytest.approx(0.5)
    assert t["shares"]["breach_drawdown"] == pytest.approx(0.5)
    assert t["p_pass"] + sum(t["shares"].values()) == pytest.approx(1.0)


def test_an_empty_input_is_refused_rather_than_reported_as_zero():
    with pytest.raises(ValueError, match="no attempts"):
        tally([], CFG, horizon=90)
