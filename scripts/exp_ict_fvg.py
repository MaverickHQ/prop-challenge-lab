# FROZEN EVIDENCE - archived under experiments/ICT-P1-FVG/.
"""ICT-P1 — does a fair value gap carry forward information at all?

Tested as a PRIMITIVE, not as a strategy. All four strategies in the source
playbook (2022 Model, Silver Bullet, Judas Swing, Turtle Soup) enter with a
limit at the FVG or its consequent encroachment. The entry is their only
shared component, so one measurement speaks to all four.

The outcome is a strategy-free signed forward return -- no stop, no target,
no assumed fill. The touch is DERIVED from what the market did (E1): a limit
at CE fills only if price actually traded there. The fade's defect entered
through a P&L outcome carrying an entry assumption; a signed move from a
touched price to a later price cannot carry one.

Definitions, all mechanical, fixed before running:
  bullish FVG at bar i:  low[i]  > high[i-2]   gap = (high[i-2], low[i])
  bearish FVG at bar i:  high[i] < low[i-2]    gap = (high[i], low[i-2])
  CE = gap midpoint. Direction = the displacement that created it.
  One per instrument-day: the FIRST of the RTH session -- which is Silver
  Bullet's own rule, and keeps the unit of analysis one-per-day as every
  prior experiment here has.
Horizon: 30 one-minute bars, truncated at the session close, because our own
rules are day-flat -- there is no holding past 16:00 to measure.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd

from occams.loader import read_vendor_csv, to_trading_days

HORIZON = 30
SEED = 20260803


def first_fvg(H, L):
    """(index, direction, ce, lo, hi) of the session's first 3-bar imbalance."""
    for i in range(2, len(H)):
        if L[i] > H[i - 2]:                      # bullish: gap below price
            return i, 1.0, (H[i - 2] + L[i]) / 2.0, H[i - 2], L[i]
        if H[i] < L[i - 2]:                      # bearish: gap above price
            return i, -1.0, (H[i] + L[i - 2]) / 2.0, H[i], L[i - 2]
    return None


def rows_for(inst):
    days = to_trading_days(read_vendor_csv(f"data/{inst}.csv"),
                           range_minutes=15, instrument=f"{inst}.v.0")
    out = []
    for d in days:
        sb = pd.concat([d.range_bars, d.session_bars])   # whole RTH session
        if len(sb) < 60 or not d.atr or d.atr <= 0:
            continue
        H = sb["high"].to_numpy(float)
        L = sb["low"].to_numpy(float)
        C = sb["close"].to_numpy(float)
        f = first_fvg(H, L)
        if f is None:
            continue
        i, sign, ce, glo, ghi = f
        dist = abs(C[i] - ce)
        if dist <= 0:
            continue
        # mirror control: the same distance on the OPPOSITE side, i.e. an
        # equal extension rather than an equal retracement. Without it a
        # "fill rate" says only that price moves.
        mirror = C[i] + dist * sign

        j = None
        for k in range(i + 1, len(sb)):
            if (L[k] <= ce) if sign > 0 else (H[k] >= ce):
                j = k
                break
        m = None
        for k in range(i + 1, len(sb)):
            if (H[k] >= mirror) if sign > 0 else (L[k] <= mirror):
                m = k
                break

        touched = j is not None
        if touched:
            end = min(j + HORIZON, len(sb) - 1)
            fwd = float((C[end] - ce) / d.atr) * sign
            eod = float((C[-1] - ce) / d.atr) * sign
        else:
            fwd = eod = 0.0            # a limit that never fills is a real
            #                            outcome of the rule, not a gap
        out.append({"date": d.date, "touched": touched,
                    "mirror": m is not None, "fwd": fwd, "eod": eod,
                    "gap_atr": float((ghi - glo) / d.atr)})
    return out


def cluster_boot(vals, dates, reps=4000):
    """CI resampling DATES, not observations -- MES and MNQ on the same day
    are close to the same draw (E4.2)."""
    rng = np.random.default_rng(SEED)
    by = {}
    for v, dt in zip(vals, dates):
        by.setdefault(dt, []).append(v)
    keys = list(by)
    pool = [np.array(by[k]) for k in keys]
    means = np.empty(reps)
    for r in range(reps):
        pick = rng.integers(0, len(pool), len(pool))
        means[r] = np.concatenate([pool[p] for p in pick]).mean()
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


if __name__ == "__main__":
    out, allrows = {}, []
    for inst in ("MES", "MNQ"):
        rows = rows_for(inst)
        t = np.array([r["fwd"] for r in rows if r["touched"]])
        out[inst] = {
            "days": len(rows),
            "ce_fill_rate": round(float(np.mean([r["touched"] for r in rows])), 4),
            "mirror_fill_rate": round(float(np.mean([r["mirror"] for r in rows])), 4),
            "fwd_mean_touched": round(float(t.mean()), 5) if len(t) else None,
            "gap_atr_median": round(float(np.median(
                [r["gap_atr"] for r in rows])), 5),
        }
        print(f"  {inst}: days={len(rows):>4}  CE fill "
              f"{out[inst]['ce_fill_rate']:.3f} vs mirror "
              f"{out[inst]['mirror_fill_rate']:.3f}  "
              f"fwd(touched) {t.mean():+.5f} ATR")
        allrows += rows

    touched = [r for r in allrows if r["touched"]]
    v = np.array([r["fwd"] for r in touched])
    dts = [r["date"] for r in touched]
    lo, hi = cluster_boot(v, dts)
    sd = float(v.std(ddof=1))
    d_obs = float(v.mean() / sd) if sd else 0.0

    allv = np.array([r["fwd"] for r in allrows])
    alo, ahi = cluster_boot(allv, [r["date"] for r in allrows])

    print(f"\n  PRIMARY (conditional on CE touch): n={len(v)}")
    print(f"    mean signed 30m forward return {v.mean():+.5f} ATR"
          f"   95% CI [{lo:+.5f}, {hi:+.5f}]   Cohen d {d_obs:+.4f}")
    print(f"  SECONDARY (all days, no touch = 0): n={len(allv)}"
          f"  mean {allv.mean():+.5f} ATR  CI [{alo:+.5f}, {ahi:+.5f}]")
    e = np.array([r["eod"] for r in touched])
    print(f"  SECONDARY (touch -> session close): mean {e.mean():+.5f} ATR")

    out["pooled"] = {
        "fwd_mean": round(float(v.mean()), 5),
        "ci_low": round(lo, 5), "ci_high": round(hi, 5),
        "cohen_d": round(d_obs, 4), "sd": round(sd, 5),
        "eod_mean": round(float(e.mean()), 5),
        "unconditional_mean": round(float(allv.mean()), 5),
        "unconditional_ci": [round(alo, 5), round(ahi, 5)],
        "days_with_fvg": len(allrows),
    }
    out["n"] = len(v)
    from occams import experiment
    experiment.emit(out)
