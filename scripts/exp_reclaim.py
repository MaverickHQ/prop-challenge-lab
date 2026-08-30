# FROZEN EVIDENCE - archived as experiments/H-RECLAIM/exp_reclaim.py.
# Do not reformat: the archived copy must remain byte-identical to the
# script that produced the registered result. Excluded from ruff in
# pyproject.toml for this reason.
"""Hypothesis test: the RECLAIM filter, stated in advance by the user.

Same setup, same stop, same target. The only change is WHEN you enter:
  1. price must trade THROUGH the original stop level
  2. then back through it
  3. then back through the ORIGINAL ENTRY
  -> enter there

The point is not a better entry price. It is a FILTER: days that never
reclaim are never traded, and those are the days that just keep going.
"""
import pandas as pd, numpy as np
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
K, RISK, CAP = 0.2, 175.0, 30
SPEC = {"MES": (5.0, 0.25, 1.25), "MNQ": (2.0, 0.25, 1.25)}

def load(inst):
    df = pd.read_csv(f"data/{inst}.csv", usecols=["ts_event","open","high","low","close"])
    df["ts"] = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(ET)
    df = df.drop(columns=["ts_event"])
    hm = df["ts"].dt.hour*60 + df["ts"].dt.minute
    df = df[(hm >= 570) & (hm < 960)]              # 09:30-16:00 ET
    df["d"] = df["ts"].dt.date
    return df

def size(pts, mult, comm, tick):
    per = (pts + 2*tick)*mult + 2*comm
    return min(int(RISK//per), CAP)

def run(inst):
    mult, tick, comm = SPEC[inst]
    df = load(inst)
    out = []
    for d, g in df.groupby("d", sort=True):
        hm = g["ts"].dt.hour*60 + g["ts"].dt.minute
        rb = g[(hm >= 570) & (hm < 585)]
        if len(rb) < 15: continue
        hi, lo = rb["high"].max(), rb["low"].min()
        h = hi - lo
        if h <= 0: continue
        s = g[hm >= 585]
        if s.empty: continue
        H,L,C = s["high"].to_numpy(), s["low"].to_numpy(), s["close"].to_numpy()
        bi = next((i for i in range(len(s)) if H[i] > hi or L[i] < lo), None)
        if bi is None: continue
        up = H[bi] > hi
        fi = next((i for i in range(bi, len(s))
                   if (C[i] < hi if up else C[i] > lo)), None)
        if fi is None: continue
        ext = H[bi:fi+1].max() if up else L[bi:fi+1].min()
        b = hi if up else lo
        sg = -1.0 if up else 1.0
        stop = b - sg*((ext-hi if up else lo-ext) + K*h)
        tgt  = b + sg*h
        n = size(abs(stop - b), mult, comm, tick)
        if n < 1: continue

        def settle(i0, entry, stop_, n_):
            for i in range(i0, len(s)):
                hs = L[i] <= stop_ if sg > 0 else H[i] >= stop_
                ht = H[i] >= tgt   if sg > 0 else L[i] <= tgt
                if hs: return n_*((stop_-entry)*sg*mult - 2*comm)
                if ht: return n_*((tgt-entry)*sg*mult - 2*comm)
            return n_*((C[-1]-entry)*sg*mult - 2*comm)

        # V0 sealed: enter at the boundary the moment the limit trades
        e0 = next((i for i in range(fi+1, len(s))
                   if (L[i] <= b if sg > 0 else H[i] >= b)), None)
        v0 = settle(e0+1, b, stop, n) if e0 is not None else None

        # V5 reclaim: through the stop -> back through it -> back through entry
        v5 = None
        p = next((i for i in range(fi+1, len(s))
                  if (L[i] <= stop if sg > 0 else H[i] >= stop)), None)
        if p is not None:
            q = next((i for i in range(p, len(s))
                      if (H[i] > stop if sg > 0 else L[i] < stop)), None)
            if q is not None:
                r = next((i for i in range(q, len(s))
                          if (H[i] > b if sg > 0 else L[i] < b)), None)
                if r is not None:
                    v5 = settle(r+1, b, stop, n)
        out.append((d, v0, v5))
    return out

for inst in ("MES","MNQ"):
    res = run(inst)
    v0 = [x[1] for x in res if x[1] is not None]
    v5 = [x[2] for x in res if x[2] is not None]
    yrs = sorted({d.year for d,_,_ in res})
    print(f"\n=== {inst}  ({len(res)} setups, {yrs[0]}-{yrs[-1]}) ===")
    for nm, v in (("V0 sealed", v0), ("V5 reclaim", v5)):
        if not v: print(f"  {nm}: no trades"); continue
        a = np.array(v)
        print(f"  {nm:<11} trades {len(a):>5} | win {np.mean(a>0):>5.1%} | "
              f"total ${a.sum():>10,.0f} | per trade ${a.mean():>7.2f} "
              f"({a.mean()/RISK:+.3f}R)")
    # per-year, to see if it is one regime or persistent
    print("   year   V0 trades   V0 R/trade   V5 trades   V5 R/trade")
    for y in yrs:
        a = np.array([x[1] for x in res if x[0].year==y and x[1] is not None])
        c = np.array([x[2] for x in res if x[0].year==y and x[2] is not None])
        print(f"   {y}   {len(a):>9}   {a.mean()/RISK if len(a) else 0:>+10.3f}"
              f"   {len(c):>9}   {c.mean()/RISK if len(c) else 0:>+10.3f}")
