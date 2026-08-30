# FROZEN EVIDENCE - archived under experiments/Q2-ATTRIBUTION/.
"""Q2 — why each of E2's attempts actually died.

E2 reported P(pass) 0.042 and P(breach) 0.440. Those do not sum to one, so
about half of all attempts ended in some unnamed way. This names them.

A capability demonstration on an already-recorded result, registered at ZERO
ALPHA: the decomposition asks nothing new of the market, it re-reads runs
that E2 already produced. No number here can revive the fade.

The remedies differ, which is the whole point of decomposing:
  breach   -> less size; more days would only have breached sooner
  timeout  -> more days; size was not the problem
  min_days -> neither; the geometry cleared and the clock did not
"""
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from occams.attribution import tally
from occams.calendar import blocked_reason
from occams.fade import FadeParams, simulate_fade_day
from occams.harness import DayOutcome, run_from_ledger
from occams.instruments import COSTS_BY_INSTRUMENT
from occams.loader import read_vendor_csv, to_trading_days
from occams.profiles import PROFILE_DIR, load

_spec = importlib.util.spec_from_file_location(
    "_e2", Path(__file__).resolve().parent / "exp_objective.py")
_e2 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _e2
_spec.loader.exec_module(_e2)

HORIZON = 90


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
        runs = [run_from_ledger(led[s:s + HORIZON], cfg)
                for s in range(0, len(led) - HORIZON + 1)]
        t = tally(runs, cfg, horizon=HORIZON)
        print(f"\n{name}   n={t['n']:,}")
        print(f"  {'passed':<20}{t['p_pass']:>8.4f}")
        for reason, share in t["shares"].items():
            print(f"  {reason:<20}{share:>8.4f}   "
                  f"({t['reasons'][reason]:,} attempts)")
        total = t["p_pass"] + sum(t["shares"].values())
        print(f"  {'-' * 30}\n  {'sums to':<20}{total:>8.4f}")
        for reason, detail in t["example"].items():
            print(f"    e.g. {reason}: {detail}")
        out[name] = {"n": t["n"], "p_pass": round(t["p_pass"], 4),
                     "reasons": t["reasons"],
                     "shares": {k: round(v, 4)
                                for k, v in t["shares"].items()}}

    from occams import experiment
    experiment.emit({**out, "n": out["obtainable_limit"]["n"],
                     "horizon": HORIZON})
