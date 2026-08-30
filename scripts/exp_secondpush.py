# FROZEN EVIDENCE - archived under experiments/H-SECONDPUSH/.
# Do not reformat: the archived copy must stay byte-identical to the script
# that produced the registered result. Excluded from ruff in pyproject.toml.
"""H-SECONDPUSH: trade WITH the breakout at the fade's stop level.

Setup is identical to the fade (first breakout, then a close back inside).
No fade is taken. Instead:

  up-break   -> BUY STOP at extreme + 0.2h, stop = range high, target = +1h
  down-break -> SELL STOP at extreme - 0.2h, stop = range low,  target = -1h

The entry is a genuinely placeable stop order, unlike the fade's, because at
signal time price is inside the range and the trigger is beyond the extreme.
"""
import pandas as pd, numpy as np
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
K, RISK, CAP = 0.2, 175.0, 30
SPEC = {"MES": (5.0, 0.25, 1.25), "MNQ": (2.0, 0.25, 1.25)}

def load(inst):
    df = pd.read_csv(f"data/{inst}.csv", usecols=["ts_event","open","high","low","close"])
    df["ts"] = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(ET)
    hm = df["ts"].dt.hour*60 + df["ts"].dt.minute
    df = df[(hm >= 570) & (hm < 960)]
    df["d"] = df["ts"].dt.date
    return df

def size(pts, mult, comm, tick):
    per = (pts + 2*tick)*mult + 2*comm
    return min(int(RISK//per), CAP)

def run(inst):
    mult, tick, comm = SPEC[inst]
    df = load(inst); out = []
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
        fi = next((i for i in range(bi, len(s)) if (C[i] < hi if up else C[i] > lo)), None)
        if fi is None: continue
        ext = H[bi:fi+1].max() if up else L[bi:fi+1].min()
        b   = hi if up else lo
        # sg is the direction of the NEW trade: WITH the breakout
        sg  = 1.0 if up else -1.0
        trig = ext + sg*K*h                 # the fade's stop = our entry
        stop = b                            # back inside the range
        tgt  = trig + sg*h                  # measured move
        n = size(abs(trig-stop), mult, comm, tick)
        rec = {"d": d, "up": up, "triggered": False, "pnl": None, "size": n}
        if n >= 1:
            e = next((i for i in range(fi+1, len(s))
                      if (H[i] >= trig if up else L[i] <= trig)), None)
            if e is not None and e+1 < len(s):
                rec["triggered"] = True
                ex = C[-1]
                for i in range(e+1, len(s)):
                    hs = L[i] <= stop if up else H[i] >= stop
                    ht = H[i] >= tgt  if up else L[i] <= tgt
                    if hs: ex = stop; break
                    if ht: ex = tgt;  break
                rec["pnl"] = n*((ex-trig)*sg*mult - 2*comm)
        out.append(rec)
    return pd.DataFrame(out)

for inst in ("MES","MNQ"):
    r = run(inst)
    t = r[r.triggered & r.pnl.notna()]
    print(f"\n=== {inst}  {len(r)} setups, {r.d.min()} .. {r.d.max()} ===")
    print(f"  triggered {len(t)} of {len(r)} setups ({len(t)/max(len(r),1):.1%})")
    if t.empty: continue
    v = t.pnl
    print(f"  win {(v>0).mean():.1%} | total ${v.sum():,.0f} | "
          f"per trade ${v.mean():.2f} ({v.mean()/RISK:+.3f}R) | worst ${v.min():,.0f}")
    print(f"  median size {int(t['size'].median())} contracts")
    print("   year  trades   R/trade")
    for y in sorted({d.year for d in t.d}):
        vv = t[[d.year==y for d in t.d]].pnl
        print(f"   {y}  {len(vv):>6}   {vv.mean()/RISK:>+8.3f}")
