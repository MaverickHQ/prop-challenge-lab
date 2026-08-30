# FROZEN EVIDENCE - archived under experiments/C2-MAE-PREDICTABLE/.
"""C2 — is adverse excursion foreseeable BEFORE entry?

H-STOPWIDTH showed MAE is large (77% of trades exceed the stop, median 3x).
This asks whether it is predictable, which is a different question with a
much stronger mechanism: MAE is a realised-volatility quantity and
volatility clusters.

Not a directional edge and cannot become one. At most a sizing or
stand-aside filter.

Four predictors, fixed at registration. All computable BEFORE entry.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
from occams.loader import read_vendor_csv, to_trading_days

RANGE_OPEN, RANGE_CLOSE = (9, 30), (9, 45)
K = 0.2


def spearman(x, y):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean()
    ry -= ry.mean()
    d = np.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / d) if d else 0.0


def rows_for(inst):
    days = to_trading_days(read_vendor_csv(f"data/{inst}.csv"),
                           range_minutes=15, instrument=f"{inst}.v.0")
    prior_ranges, out = [], []
    prev_close = None
    for d in days:
        rb, sb = d.range_bars, d.session_bars
        if rb is None or rb.empty or sb.empty:
            continue
        hi, lo = float(rb["high"].max()), float(rb["low"].min())
        h = hi - lo
        atr = float(d.atr or 0.0)
        day_hi = max(hi, float(sb["high"].max()))
        day_lo = min(lo, float(sb["low"].min()))
        if h <= 0 or atr <= 0:
            prior_ranges.append(day_hi - day_lo)
            prev_close = float(sb["close"].iloc[-1])
            continue
        H = sb["high"].to_numpy(float)
        L = sb["low"].to_numpy(float)
        C = sb["close"].to_numpy(float)
        bi = next((i for i in range(len(sb)) if H[i] > hi or L[i] < lo), None)
        fi = None
        if bi is not None:
            up = H[bi] > hi
            fi = next((i for i in range(bi, len(sb))
                       if (C[i] < hi if up else C[i] > lo)), None)
        if bi is not None and fi is not None:
            up = H[bi] > hi
            ext = H[bi:fi+1].max() if up else L[bi:fi+1].min()
            b = hi if up else lo
            sg = 1.0 if not up else -1.0        # fade direction
            stop_d = (ext - hi if up else lo - ext) + K * h
            if stop_d > 0 and fi + 1 < len(sb):
                mae = max((b - L[i]) if sg > 0 else (H[i] - b)
                          for i in range(fi + 1, len(sb)))
                # --- the four PRE-ENTRY predictors, fixed at registration
                p1 = h / atr
                p2 = (abs(float(sb["open"].iloc[0]) - prev_close) / atr
                      if prev_close else np.nan)
                p3 = (float(np.mean(prior_ranges[-5:])) / atr
                      if len(prior_ranges) >= 5 else np.nan)
                p4 = float(bi)                   # minutes 09:45 -> breakout
                out.append((p1, p2, p3, p4, max(mae, 1e-9) / stop_d))
        prior_ranges.append(day_hi - day_lo)
        prev_close = float(sb["close"].iloc[-1])
    return out


NAMES = ("range/ATR", "overnight gap/ATR", "5d mean range/ATR",
         "mins to breakout")

if __name__ == "__main__":
    res, pooled = {}, []
    for inst in ("MES", "MNQ"):
        r = rows_for(inst)
        pooled += r
        a = np.array([x for x in r if not any(np.isnan(v) for v in x)])
        print(f"\n=== {inst}  n={len(a)} ===")
        res[inst] = {"n": len(a)}
        y = np.log(a[:, 4])
        for j, nm in enumerate(NAMES):
            rho = spearman(a[:, j], y)
            print(f"  {nm:<22} spearman r = {rho:+.4f}")
            res[inst][nm] = round(rho, 4)
    a = np.array([x for x in pooled if not any(np.isnan(v) for v in x)])
    y = np.log(a[:, 4])
    print(f"\n=== POOLED n={len(a)} ===")
    res["pooled"] = {}
    for j, nm in enumerate(NAMES):
        rho = spearman(a[:, j], y)
        print(f"  {nm:<22} spearman r = {rho:+.4f}")
        res["pooled"][nm] = round(rho, 4)
    res["n"] = len(a)
    print(f"\n  MAE/stop ratio: median {np.median(a[:,4]):.2f}x  "
          f"p90 {np.percentile(a[:,4],90):.2f}x")
    from occams import experiment
    experiment.emit(res)
