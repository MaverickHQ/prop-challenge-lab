# FROZEN EVIDENCE - archived under experiments/Q1-PAYOUT-PATH/.
"""Q1 — what happens after qualification, which was never modelled.

E2 reported P(pass). That measures GETTING THROUGH THE DOOR. It says nothing
about whether the money arrives, and the two differ because consistency
rules differ BY STAGE: the tier we sealed has no evaluation consistency
requirement, while the qualified tier applies a largest-day rule to payout
eligibility. A strategy can qualify comfortably and never be paid.

This is a CAPABILITY DEMONSTRATION, not a hypothesis test, and it is
registered at zero alpha for that reason. The fade is already dead on
obtainability (#3a) — no number here can revive it, so nothing rides on the
result and no alpha is spent. What is being shown is that the engine can now
express the question at all.

THE PAYOUT PARAMETERS BELOW ARE ILLUSTRATIVE AND ARE NOT VERIFIED RULES.
We verified the evaluation geometry; we never verified the funded-stage
terms. They are stated here so the shape can be read, and every number this
produces is conditional on them. Verifying them is a user task, and until it
is done these figures demonstrate a capability rather than describe a
venue.

Both variants are scored so the comparison is visible: the SEALED fade (the
optimistic artifact, entry unobtainable) and the OBTAINABLE limit variant.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import importlib.util

from occams.calendar import blocked_reason
from occams.fade import FadeParams, simulate_fade_day
from occams.harness import DayOutcome, PayoutStats, Status, run_from_ledger
from occams.instruments import COSTS_BY_INSTRUMENT
from occams.loader import read_vendor_csv, to_trading_days
from occams.payout import PayoutConfig, PayoutState, PayoutStatus
from occams.profiles import PROFILE_DIR, load

# reuse E2's own obtainable-entry model rather than re-deriving it
_spec = importlib.util.spec_from_file_location(
    "_e2", Path(__file__).resolve().parent / "exp_objective.py")
_e2 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _e2
_spec.loader.exec_module(_e2)

EVAL_HORIZON, FUNDED_HORIZON = 90, 180

# ILLUSTRATIVE — see the module docstring. Not verified terms.
PAYOUT = PayoutConfig(account=50_000, threshold=2_000, trailing_dd=2_000,
                      min_days=5, consistency_frac=0.40, payout_frac=1.0)


def chain(ledger, cfg):
    n = passed = paid = two = breach = 0
    for start in range(0, len(ledger) - EVAL_HORIZON + 1):
        n += 1
        run = run_from_ledger(ledger[start:start + EVAL_HORIZON], cfg)
        if run.status is not Status.PASSED:
            continue
        passed += 1
        st = PayoutState(PAYOUT)
        equity = float(PAYOUT.account)
        resume = start + run.days_used
        for o in ledger[resume:resume + FUNDED_HORIZON]:
            equity += o.pnl
            if st.record_day(equity, traded=o.traded) is PayoutStatus.BREACHED:
                breach += 1
                break
        paid += 1 if st.cycles_paid >= 1 else 0
        two += 1 if st.cycles_paid >= 2 else 0
    return PayoutStats(
        n_runs=n, p_pass=passed / n, p_first_payout=paid / n,
        p_two_cycles=two / n, mean_cycles_given_pass=0.0,
        p_breach_while_funded=(breach / passed if passed else 0.0),
        median_days_to_payout=0)


if __name__ == "__main__":
    cfg = load(PROFILE_DIR / "example-50k.json").config
    days = to_trading_days(read_vendor_csv("data/MES.csv"),
                           range_minutes=15, instrument="MES.v.0")
    costs = COSTS_BY_INSTRUMENT["MES"]
    blocked = {d.date for d in days if blocked_reason(d.date, _e2.EVENTS)}

    def ledger_from(fn):
        return [DayOutcome(d.date, 0.0, False) if d.date in blocked
                else DayOutcome(d.date, fn(d), fn(d) != 0.0) for d in days]

    variants = {
        "sealed_unobtainable": ledger_from(
            lambda d: simulate_fade_day(
                d, FadeParams(k_stop=0.2, width_max=None, risk_usd=175.0),
                costs).day_pnl_usd),
        "obtainable_limit": ledger_from(
            lambda d: _e2.obtainable_pnl(d, costs, 175.0)),
    }

    out = {}
    for name, led in variants.items():
        st = chain(led, cfg)
        print(f"\n{name}")
        print(st.render())
        gap = st.p_pass - st.p_first_payout
        print(f"  ---> qualifying but never paid: {gap:.4f} "
              f"({gap / st.p_pass:.0%} of those that passed)"
              if st.p_pass else "  ---> nothing qualified")
        out[name] = {"n": st.n_runs, "p_pass": round(st.p_pass, 4),
                     "p_first_payout": round(st.p_first_payout, 4),
                     "p_two_cycles": round(st.p_two_cycles, 4),
                     "p_breach_while_funded":
                         round(st.p_breach_while_funded, 4)}

    print("\nPayout parameters are ILLUSTRATIVE and unverified — these "
          "figures demonstrate a capability, they do not describe a venue.")
    from occams import experiment
    experiment.emit({**out, "n": out["obtainable_limit"]["n"],
                     "payout_params_verified": False,
                     "eval_horizon": EVAL_HORIZON,
                     "funded_horizon": FUNDED_HORIZON})
