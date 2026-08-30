# FROZEN EVIDENCE - archived under experiments/Z-ARMED/.
"""Is the sealed +0.1R reachable by an order a human can actually place?

fade.py ASSUMES a fill at the boundary at the failure close. This asks
whether arming a stop at the boundary during the breakout -- an order that
is valid at the moment it is placed, because price is then outside the
range -- reproduces that number.

It also measures the case protocol #4b has to pre-register: the armed stop
filling on a dip that never produces a failure close.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
from occams.loader import read_vendor_csv, to_trading_days
from occams.fade import FadeParams, simulate_fade_day
from occams.instruments import COSTS_BY_INSTRUMENT
RISK = 175.0
P = FadeParams(k_stop=0.2, width_max=None, risk_usd=RISK)

def armed(day, costs, require_close=False):
    rb, sb = day.range_bars, day.session_bars
    if rb is None or rb.empty or sb.empty: return None
    hi, lo = float(rb["high"].max()), float(rb["low"].min()); h = hi - lo
    if h <= 0: return None
    H,L,C = (sb["high"].to_numpy(float), sb["low"].to_numpy(float),
             sb["close"].to_numpy(float))
    bi = next((i for i in range(len(sb)) if H[i] > hi or L[i] < lo), None)
    if bi is None: return None
    up = H[bi] > hi
    b = hi if up else lo; sg = -1.0 if up else 1.0
    slip = costs.slippage
    # The order is ARMED on the breakout bar and rests at the boundary.
    # It fills the first time price trades back to it.
    fill = next((i for i in range(bi, len(sb))
                 if (L[i] <= b if up else H[i] >= b)), None)
    if fill is None: return None
    # the engine's own failure close, for comparison
    fc = next((i for i in range(bi, len(sb))
               if (C[i] < hi if up else C[i] > lo)), None)
    if require_close and (fc is None or fill < fc):
        return ("SKIPPED", fill, fc)
    ext = H[bi:fill+1].max() if up else L[bi:fill+1].min()
    stop = b - sg*((ext-hi if up else lo-ext) + 0.2*h); tgt = b + sg*h
    lp = abs(stop-(b+sg*slip)) + slip
    n = min(int(RISK//(lp*costs.multiplier + 2*costs.commission_per_side)), 30)
    if n < 1: return None
    entry = b + sg*slip
    ex = C[-1]
    for i in range(fill+1, len(sb)):
        if (L[i] <= stop if sg > 0 else H[i] >= stop): ex = stop; break
        if (H[i] >= tgt  if sg > 0 else L[i] <= tgt):  ex = tgt;  break
    pnl = n*((ex-entry)*sg*costs.multiplier - 2*costs.commission_per_side)
    no_close = (fc is None) or (fill < fc)
    return ("TRADE", pnl, no_close)

for inst in ("MES","MNQ"):
    costs = COSTS_BY_INSTRUMENT[inst]
    days = to_trading_days(read_vendor_csv(f"data/{inst}.csv"),
                           range_minutes=15, instrument=f"{inst}.v.0")
    sealed = [t.pnl_usd for d in days for t in simulate_fade_day(d,P,costs).trades]
    rows = [armed(d, costs) for d in days]
    rows = [r for r in rows if r and r[0]=="TRADE"]
    allp = np.array([r[1] for r in rows])
    noclose = np.array([r[1] for r in rows if r[2]])
    withclose = np.array([r[1] for r in rows if not r[2]])
    print(f"\n=== {inst} ===")
    print(f"  sealed engine (assumed fill)      n={len(sealed):>5}  "
          f"{np.mean(sealed)/RISK:+.3f}R")
    print(f"  ARMED STOP, all fills             n={len(allp):>5}  "
          f"{allp.mean()/RISK:+.3f}R")
    print(f"    of which: filled BEFORE a close n={len(noclose):>5}  "
          f"{(noclose.mean()/RISK if len(noclose) else 0):+.3f}R"
          f"   ({len(noclose)/len(allp):.1%} of trades)")
    print(f"    of which: close came first      n={len(withclose):>5}  "
          f"{(withclose.mean()/RISK if len(withclose) else 0):+.3f}R")
