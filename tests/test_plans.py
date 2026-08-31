"""R1 — the plan menu as a decision variable, and EV in dollars.

The previous programme modelled ONE plan and optimised P(pass). Both were
too narrow, and the second was wrong: P(pass) is the probability of clearing
one gate, and says nothing about what the attempt cost or what the prize was
worth. `Q1-PAYOUT` found half of this the hard way -- "P(pass) was never the
objective, and it flatters weak strategies" -- but it arrived late, because
the business objective was never written down as a requirement.

What a provider actually sells is a MENU of contracts. They differ in price,
in how many barriers stand between you and money, in the profit target, in
the drawdown geometry, in the consistency rule, and in the size of the prize
-- by an order of magnitude on that last one. A frontier computed for one of
them is a property of THAT geometry, not a law of nature.

So this module answers, per plan: how much edge does a strategy need before
the contract is worth buying? The arithmetic is over published constraints
rather than noisy observations, which is why it costs nothing and spends no
alpha -- it is optimisation, not inference.
"""

from __future__ import annotations

import pytest

from occams.plans import Plan, PlanEconomics, ev, required_edge
from occams.payout import PayoutConfig
from occams.rules import ChallengeConfig


def _funded(threshold=3000.0, consistency=None, payout_frac=0.5):
    return PayoutConfig(account=50_000.0, threshold=threshold,
                        trailing_dd=2000.0, min_days=5,
                        consistency_frac=consistency,
                        payout_frac=payout_frac)


def _eval_stage():
    return ChallengeConfig(account=50_000.0, target=3000.0, trailing_dd=2000.0,
                           daily_guard=1000.0, min_days=1)


def _econ(fee=139.0, kind="monthly", ceiling=1500.0):
    return PlanEconomics(fee=fee, fee_kind=kind, max_payout=ceiling,
                         payouts_per_month=4)


# ─── the shape of a plan ───

def test_a_plan_without_an_evaluation_has_one_barrier():
    """The structural fact the previous project never used: some contracts
    are sold already qualified. A year was spent optimising the probability
    of clearing a gate that can be bought past."""
    direct = Plan(name="direct", account=50_000.0, evaluation=None,
                  funded=_funded(), economics=_econ(fee=519.0, kind="once",
                                                    ceiling=2000.0))
    staged = Plan(name="staged", account=50_000.0, evaluation=_eval_stage(),
                  funded=_funded(), economics=_econ())
    assert direct.barriers == 1
    assert staged.barriers == 2


def test_fee_kind_must_be_recognised():
    with pytest.raises(ValueError, match="fee_kind"):
        PlanEconomics(fee=1.0, fee_kind="annually", max_payout=1.0,
                      payouts_per_month=1)


# ─── the economics the previous model was missing ───

def test_a_one_time_fee_does_not_accumulate_with_time():
    """A monthly plan that takes six months costs six fees. A one-time plan
    that takes six months costs one. The previous model had no fee at all,
    so a slow strategy looked identical to a fast one."""
    once = _econ(fee=519.0, kind="once")
    monthly = _econ(fee=139.0, kind="monthly")
    assert once.fees_for(months=6) == pytest.approx(519.0)
    assert monthly.fees_for(months=6) == pytest.approx(834.0)
    assert monthly.fees_for(months=1) == pytest.approx(139.0)


def test_the_payout_ceiling_caps_the_prize():
    """Max payout is the number that differs by 10x across plans on the same
    account size, and it was modelled nowhere."""
    econ = _econ(ceiling=1500.0)
    assert econ.prize(gross_profit=10_000.0, payout_frac=0.5) == 1500.0
    assert econ.prize(gross_profit=2000.0, payout_frac=0.5) == 1000.0


def test_the_withdrawal_share_applies_before_the_ceiling():
    """Withdraw up to 50% of profit per request, then capped. Applying the
    ceiling first would overstate every plan's prize."""
    econ = _econ(ceiling=5000.0)
    assert econ.prize(gross_profit=4000.0, payout_frac=0.5) == 2000.0


# ─── EV, which is the actual objective ───

def test_ev_is_the_prize_times_its_probability_minus_the_fees_paid():
    plan = Plan(name="p", account=50_000.0, evaluation=None,
                funded=_funded(), economics=_econ(fee=100.0, kind="once",
                                                  ceiling=2000.0))
    got = ev(plan, p_payout=0.10, gross_profit=3000.0, months=2.0)
    # 0.10 * min(3000*0.5, 2000) = 150, less a single 100 fee
    assert got == pytest.approx(50.0)


def test_a_weak_signal_is_negative_ev_on_every_plan():
    """The honest caveat, asserted rather than hoped: plan selection cannot
    rescue a losing strategy. It can only decide whether a MARGINAL one is
    viable. If this test ever fails, the model has a sign error."""
    weak = 0.0115          # the measured P(first payout) from Q1-PAYOUT
    plans = [
        Plan("zero", 50_000.0, _eval_stage(), _funded(),
             _econ(139.0, "monthly", 1500.0)),
        Plan("direct", 50_000.0, None, _funded(),
             _econ(519.0, "once", 2000.0)),
        Plan("advanced", 50_000.0, _eval_stage(), _funded(),
             _econ(209.0, "monthly", 15_000.0)),
    ]
    for p in plans:
        assert ev(p, p_payout=weak, gross_profit=3000.0, months=3.0) < 0


def test_a_bigger_ceiling_is_worthless_below_the_profit_that_reaches_it():
    """FOUND BY THE MODEL ON ITS FIRST RUN, and it corrects an assumption in
    this project's own brief.

    A tenfold larger `max_payout` looks decisive. It is not, because the
    withdrawal SHARE binds first: at $4,000 gross and a 50% share you take
    out $2,000 whichever plan you hold, so a $15,000 ceiling and a $1,500
    ceiling differ by $500 -- and the bigger-ceiling plan costs $70/month
    more for it.

    The ceiling only separates plans once gross profit is large enough for
    the share to exceed the smaller ceiling. Reaching a $15,000 ceiling at a
    50% share needs $30,000 of profit on a 50K account whose drawdown is
    $1,750, which is a different proposition entirely.
    """
    small = Plan("small", 50_000.0, _eval_stage(), _funded(),
                 _econ(139.0, "monthly", 1500.0))
    big = Plan("big", 50_000.0, _eval_stage(), _funded(),
               _econ(209.0, "monthly", 15_000.0))

    modest = dict(p_payout=0.05, gross_profit=4000.0, months=3.0)
    assert ev(big, **modest) < ev(small, **modest), (
        "at modest profit the dearer plan must lose -- its ceiling is idle")

    large = dict(p_payout=0.05, gross_profit=40_000.0, months=3.0)
    assert ev(big, **large) > ev(small, **large), (
        "once the share exceeds the small ceiling, the prize gap dominates")


# ─── the deliverable: sixteen frontiers, not one ───

def test_required_edge_differs_by_plan():
    """FEASIBILITY computed ONE frontier -- +0.25R at 0.5 trades/day -- and
    every family failed it tenfold. That number is a property of one plan's
    geometry. Sixteen contracts means sixteen frontiers."""
    def p_of_edge(e: float) -> float:
        """A stand-in monotone map from edge to P(payout)."""
        return max(0.0, min(1.0, e * 2.0))

    staged = Plan("staged", 50_000.0, _eval_stage(), _funded(),
                  _econ(139.0, "monthly", 2000.0))
    # Same hurdle and same prize; the only difference is that the fee stops
    # accruing. Over three months that is $417 of hurdle the staged plan
    # must clear and the one-time plan does not.
    one_off = Plan("one-off", 50_000.0, None, _funded(),
                   _econ(139.0, "once", 2000.0))

    need_staged = required_edge(staged, p_of_edge, gross_profit=4000.0,
                                months=3.0)
    need_one_off = required_edge(one_off, p_of_edge, gross_profit=4000.0,
                                 months=3.0)
    assert need_one_off < need_staged, (
        "a contract whose fee stops accruing must break even at a smaller "
        "edge -- if not, the fee model is not being applied")


def test_required_edge_reports_unreachable_rather_than_guessing():
    """A plan whose prize cannot cover its fees at ANY attainable edge must
    say so, not return the top of the search range as though it were a
    finding."""
    hopeless = Plan("hopeless", 50_000.0, _eval_stage(), _funded(),
                    _econ(fee=5000.0, kind="monthly", ceiling=10.0))
    assert required_edge(hopeless, lambda e: e, gross_profit=100.0,
                         months=1.0) is None
