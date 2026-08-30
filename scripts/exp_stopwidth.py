# FROZEN EVIDENCE - archived under experiments/H-STOPWIDTH/.
# Do not reformat: the archived copy must stay byte-identical to the script
# that produced the registered result. Excluded from ruff in pyproject.toml.
"""H-STOPWIDTH / H-HOLD over 2019-2026, not over one week.

The user observed that the fade's DIRECTION often proves right after the
stop is hit, and asked whether we stop out too early. On 7 live setups the
adverse excursion ran 5-12x the stop distance. This asks the same question
of 3,300+ setups.

Sizing is held honest: risk is FIXED at $175, so a wider stop buys fewer
contracts. That is the constraint that makes 'just widen the stop' a
different proposition from 'hold longer'.
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
    df = load(inst)
    rows = []
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
        sg  = -1.0 if up else 1.0
        base = (ext-hi if up else lo-ext) + K*h
        tgt  = b + sg*h
        e0 = next((i for i in range(fi+1, len(s)) if (L[i] <= b if sg>0 else H[i] >= b)), None)
        if e0 is None: continue
        a = slice(e0+1, len(s))
        if e0+1 >= len(s): continue
        mae = max((b-L[i]) if sg>0 else (H[i]-b) for i in range(e0+1, len(s)))
        mfe = max((H[i]-b) if sg>0 else (b-L[i]) for i in range(e0+1, len(s)))
        row = {"d": d, "mae": mae, "mfe": mfe, "base": base, "h": h}
        for tag, m in (("x1",1.0),("x2",2.0),("x4",4.0),("x8",8.0),("nostop",None)):
            stop = None if m is None else b - sg*base*m
            n = size(base if m is None else base*m, mult, comm, tick)
            if n < 1: row[tag] = None; continue
            ex = C[-1]
            for i in range(e0+1, len(s)):
                if stop is not None and (L[i] <= stop if sg>0 else H[i] >= stop):
                    ex = stop; break
                if (H[i] >= tgt if sg>0 else L[i] <= tgt): ex = tgt; break
            row[tag] = n*((ex-b)*sg*mult - 2*comm)
        rows.append(row)
    return pd.DataFrame(rows)

for inst in ("MES","MNQ"):
    r = run(inst)
    print(f"\n=== {inst}  {len(r)} setups, {r.d.min()} .. {r.d.max()} ===")
    ratio = (r.mae/r.base).replace([np.inf,-np.inf], np.nan).dropna()
    print(f"  MAE / stop distance:  median {ratio.median():.1f}x | "
          f"75th {ratio.quantile(.75):.1f}x | 90th {ratio.quantile(.90):.1f}x")
    print(f"  share of trades whose MAE exceeds the stop: {(r.mae>r.base).mean():.1%}")
    print(f"  {'variant':<10}{'trades':>8}{'win':>7}{'R/trade':>10}{'worst $':>11}")
    for tag in ("x1","x2","x4","x8","nostop"):
        v = r[tag].dropna()
        if v.empty: print(f"  {tag:<10}{0:>8}"); continue
        print(f"  {tag:<10}{len(v):>8}{(v>0).mean():>7.1%}"
              f"{v.mean()/RISK:>+10.3f}{v.min():>11,.0f}")
