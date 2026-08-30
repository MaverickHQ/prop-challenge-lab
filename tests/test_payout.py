"""Q1 — the half this programme never modelled.

Every P(pass) ever quoted here measures getting through the door. It says
nothing about whether the money arrives. The tier we sealed has no
evaluation consistency requirement, but the qualified tier applies a **40%
largest-day rule to payout eligibility** — and `ChallengeConfig` only ever
knew about the evaluation.

So `P(pass) = 0.042` was never the objective. `P(first payout)` is.

The payout stage deliberately MIRRORS `ChallengeState` rather than inventing
new semantics: breach-before-pass ordering, a floor that trails the equity
high, sticky terminal states. Where it must differ, the difference is a
modelling choice and is named as one.
"""

from __future__ import annotations

import pytest

from occams.payout import PayoutConfig, PayoutState, PayoutStatus

CFG = PayoutConfig(account=50_000, threshold=2_000, trailing_dd=2_000,
                   min_days=5, consistency_frac=0.40)


def _run(cfg, equities, traded=True):
    st = PayoutState(cfg)
    out = [st.record_day(e, traded=traded) for e in equities]
    return st, out


# --------------------------------------------------------------------------
# the mirror: same shape as the evaluation
# --------------------------------------------------------------------------

def test_the_floor_trails_the_equity_high_and_locks_at_the_start():
    st = PayoutState(CFG)
    assert st.floor == 48_000
    st.record_day(51_000)
    assert st.floor == 49_000
    st.record_day(53_000)
    assert st.floor == 50_000          # locked at the funded balance
    st.record_day(60_000)
    assert st.floor == 50_000          # and it never rises above it


def test_a_breach_is_terminal_and_sticky():
    st, out = _run(CFG, [50_500, 47_000, 60_000])
    assert out[1] is PayoutStatus.BREACHED
    assert out[2] is PayoutStatus.BREACHED


def test_breach_is_checked_before_payout_conservatively():
    """Same ordering as the evaluation: an equity mark that is both at the
    threshold and below the floor is a breach, not a payout."""
    st = PayoutState(PayoutConfig(account=50_000, threshold=1_000,
                                  trailing_dd=500, min_days=0))
    st.record_day(56_000)              # floor -> 55,500
    assert st.record_day(55_000) is PayoutStatus.BREACHED


# --------------------------------------------------------------------------
# the payout itself
# --------------------------------------------------------------------------

def test_a_payout_needs_the_threshold_AND_the_minimum_days():
    cfg = PayoutConfig(account=50_000, threshold=2_000, trailing_dd=5_000,
                       min_days=5)
    st, out = _run(cfg, [53_000] * 4)
    assert all(s is PayoutStatus.ACTIVE for s in out)   # threshold met, days not
    assert st.record_day(53_000) is PayoutStatus.PAID   # the 5th day


def test_payout_consistency_DELAYS_rather_than_breaches():
    """A 40% largest-day rule gates the withdrawal; it never kills the
    account. Same discipline as evaluation consistency."""
    cfg = PayoutConfig(account=50_000, threshold=2_000, trailing_dd=10_000,
                       min_days=0, consistency_frac=0.40)
    st = PayoutState(cfg)
    st.record_day(52_500)                       # one 2,500 day = 100% of profit
    assert st.status is PayoutStatus.ACTIVE     # blocked, not breached
    for e in (53_000, 54_000, 55_000, 56_500):  # grind the share down
        st.record_day(e)
    assert st.status is PayoutStatus.PAID


def test_without_a_consistency_rule_the_same_path_pays_immediately():
    cfg = PayoutConfig(account=50_000, threshold=2_000, trailing_dd=10_000,
                       min_days=0, consistency_frac=None)
    st = PayoutState(cfg)
    assert st.record_day(52_500) is PayoutStatus.PAID


# --------------------------------------------------------------------------
# multiple cycles — and the withdrawal must not breach the account
# --------------------------------------------------------------------------

def test_a_withdrawal_does_not_count_against_the_drawdown():
    """The money leaving is not a loss. If the floor were left where it was,
    every successful payout would instantly breach the account — the single
    easiest way to model this wrongly.

    Note the INPUT CONVENTION, which is the other easy mistake: record_day
    takes CUMULATIVE equity, the mark a simulator produces, which never
    drops when money is withdrawn. A flat day after a payout is reported as
    the SAME cumulative number, not a lower one.
    """
    cfg = PayoutConfig(account=50_000, threshold=2_000, trailing_dd=2_000,
                       min_days=0)
    st = PayoutState(cfg)
    assert st.record_day(52_000) is PayoutStatus.PAID
    assert st.cycles_paid == 1
    assert st.total_paid == pytest.approx(2_000)
    # flat day: cumulative equity unchanged, and that is NOT a breach
    assert st.record_day(52_000) is PayoutStatus.ACTIVE


def test_cycles_accumulate_and_each_needs_the_threshold_again():
    cfg = PayoutConfig(account=50_000, threshold=2_000, trailing_dd=5_000,
                       min_days=0)
    st = PayoutState(cfg)
    st.record_day(52_000)                       # cycle 1
    st.record_day(52_000)                       # withdrawn: no new profit
    assert st.cycles_paid == 1
    st.record_day(54_000)                       # +2,000 above the withdrawal
    assert st.cycles_paid == 2
    assert st.total_paid == pytest.approx(4_000)


def test_only_part_of_the_profit_may_be_withdrawable():
    cfg = PayoutConfig(account=50_000, threshold=2_000, trailing_dd=5_000,
                       min_days=0, payout_frac=0.80)
    st = PayoutState(cfg)
    st.record_day(52_500)
    assert st.total_paid == pytest.approx(2_000)      # 0.80 x 2,500


def test_the_largest_day_resets_with_each_cycle():
    """Consistency is measured per payout cycle, not over all time."""
    cfg = PayoutConfig(account=50_000, threshold=1_000, trailing_dd=10_000,
                       min_days=0, consistency_frac=0.40)
    st = PayoutState(cfg)
    for e in (50_400, 50_800, 51_200):                # even days, pays on 3rd
        last = st.record_day(e)
    assert last is PayoutStatus.PAID
    assert st.cycles_paid == 1
    assert st.max_day_profit == 0.0                   # reset AT the payout


# --------------------------------------------------------------------------
# refusals
# --------------------------------------------------------------------------

def test_impossible_configs_are_refused():
    for bad in (dict(threshold=0), dict(trailing_dd=-1), dict(account=0),
                dict(payout_frac=0), dict(payout_frac=1.5),
                dict(consistency_frac=1.5)):
        kw = dict(account=50_000, threshold=2_000, trailing_dd=2_000)
        kw.update(bad)
        with pytest.raises(ValueError):
            PayoutConfig(**kw)


def test_state_round_trips_through_a_snapshot():
    st = PayoutState(CFG)
    st.record_day(51_500)
    st.record_day(52_200)
    back = PayoutState.restore(CFG, st.snapshot())
    assert back.snapshot() == st.snapshot()
    assert back.floor == st.floor
