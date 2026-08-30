# FROZEN EVIDENCE - archived under experiments/E2-OBJECTIVE/.
"""E2 — score against the REAL objective, not expectancy.

Everything to date has been R per trade. The challenge is a path-dependent
SURVIVAL problem: a trailing drawdown floor, a profit target, a minimum
number of days. A lower-expectancy, lower-variance configuration can pass
more often than a higher-expectancy one, so expectancy is not the thing to
maximise and never was.

This scores, through the sealed rules engine, on every start day:

  1. the SEALED fade -- the one whose entry cannot be obtained
  2. the OBTAINABLE fade -- limit at the boundary, the best real order
  3. the obtainable fade at a LADDER of risk sizes

(3) tests the prediction registered in advance: that P(pass) is
non-monotonic in size and peaks BELOW the expectancy-maximising size.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
from occams.loader import read_vendor_csv, to_trading_days
from occams.fade import FadeParams, simulate_fade_day
from occams.harness import DayOutcome, run_from_ledger
from occams.rules import ChallengeConfig, Status
from occams.instruments import COSTS_BY_INSTRUMENT
from occams.calendar import blocked_reason, load_events

CFG = ChallengeConfig(50_000, 3_000, 2_000, 1_000, 1)   # verified Zero tier
EVENTS = load_events(Path("occams/data/economic_calendar.csv"))
HORIZONS = (60, 90)


def obtainable_pnl(day, costs, risk):
    """The fade entered by a LIMIT resting at the boundary -- the best order
    that can actually be placed. Returns 0.0 when it never fills."""
    rb, sb = day.range_bars, day.session_bars
    if rb is None or rb.empty or sb.empty: return 0.0
    hi, lo = float(rb["high"].max()), float(rb["low"].min()); h = hi - lo
    if h <= 0: return 0.0
    H, L, C = (sb["high"].to_numpy(float), sb["low"].to_numpy(float),
               sb["close"].to_numpy(float))
    bi = next((i for i in range(len(sb)) if H[i] > hi or L[i] < lo), None)
    if bi is None: return 0.0
    up = H[bi] > hi
    fc = next((i for i in range(bi, len(sb))
               if (C[i] < hi if up else C[i] > lo)), None)
    if fc is None: return 0.0
    ext = H[bi:fc+1].max() if up else L[bi:fc+1].min()
    b = hi if up else lo; sg = -1.0 if up else 1.0
    stop = b - sg*((ext-hi if up else lo-ext) + 0.2*h); tgt = b + sg*h
    lp = abs(stop - (b + sg*costs.slippage)) + costs.slippage
    n = min(int(risk // (lp*costs.multiplier + 2*costs.commission_per_side)), 30)
    if n < 1: return 0.0
    e = next((i for i in range(fc+1, len(sb))
              if (H[i] >= b if up else L[i] <= b)), None)
    if e is None: return 0.0                      # limit never filled
    ex = C[-1]
    for i in range(e+1, len(sb)):
        if (L[i] <= stop if sg > 0 else H[i] >= stop): ex = stop; break
        if (H[i] >= tgt  if sg > 0 else L[i] <= tgt):  ex = tgt;  break
    return n*((ex-b)*sg*costs.multiplier - 2*costs.commission_per_side)


def mc(ledger, horizon):
    runs = [run_from_ledger(ledger[s:s+horizon], CFG)
            for s in range(0, len(ledger) - horizon + 1)]
    if not runs: return None
    p = sum(1 for r in runs if r.status is Status.PASSED) / len(runs)
    br = sum(1 for r in runs if r.status is Status.BREACHED) / len(runs)
    dd = [r.days_used for r in runs if r.status is Status.PASSED]
    return dict(n=len(runs), p_pass=round(p, 4), p_breach=round(br, 4),
                median_days=(int(np.median(dd)) if dd else None))


if __name__ == "__main__":
    days = to_trading_days(read_vendor_csv("data/MES.csv"),
                           range_minutes=15, instrument="MES.v.0")
    costs = COSTS_BY_INSTRUMENT["MES"]
    blocked = {d.date for d in days if blocked_reason(d.date, EVENTS)}

    def ledger_from(fn):
        return [DayOutcome(d.date, 0.0, False) if d.date in blocked
                else DayOutcome(d.date, fn(d), fn(d) != 0.0) for d in days]

    sealed = ledger_from(
        lambda d: simulate_fade_day(
            d, FadeParams(k_stop=0.2, width_max=None, risk_usd=175.0),
            costs).day_pnl_usd)
    out = {"sealed_unobtainable": {}, "obtainable_limit": {}, "risk_ladder": {}}
    print(f"{'variant':<32}{'horizon':>8}{'P(pass)':>10}{'P(breach)':>11}"
          f"{'median d':>10}")
    for hz in HORIZONS:
        r = mc(sealed, hz); out["sealed_unobtainable"][hz] = r
        print(f"{'SEALED (entry unobtainable)':<32}{hz:>8}{r['p_pass']:>10.3f}"
              f"{r['p_breach']:>11.3f}{str(r['median_days']):>10}")
    obt = ledger_from(lambda d: obtainable_pnl(d, costs, 175.0))
    for hz in HORIZONS:
        r = mc(obt, hz); out["obtainable_limit"][hz] = r
        print(f"{'OBTAINABLE (limit @ boundary)':<32}{hz:>8}{r['p_pass']:>10.3f}"
              f"{r['p_breach']:>11.3f}{str(r['median_days']):>10}")
    print()
    print(f"{'risk ladder, obtainable, 90d':<32}{'risk $':>8}{'P(pass)':>10}"
          f"{'P(breach)':>11}")
    for risk in (75, 125, 175, 250, 350):
        led = ledger_from(lambda d, r=risk: obtainable_pnl(d, costs, float(r)))
        r_ = mc(led, 90); out["risk_ladder"][risk] = r_
        print(f"{'':<32}{risk:>8}{r_['p_pass']:>10.3f}{r_['p_breach']:>11.3f}")
    print("\nfrontier requires P(pass) >= 0.55 (G1) and ideally ~0.65 for "
          "economics (FEASIBILITY.md)")
    from occams import experiment
    experiment.emit(out)
