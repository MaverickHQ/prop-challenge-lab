# FROZEN EVIDENCE - archived under experiments/ICT-P2-SWEEP/.
"""ICT-P2 — does a sweep of the prior session's extreme reverse?

Tested as a PRIMITIVE. The 2022 Model, Judas Swing and Turtle Soup differ
only in WHICH level is swept; prior-day RTH high/low is the cleanest and
most objective of them, so it is the one measured. One number speaks to
three named strategies.

This family is our failed-breakout fade under another name, and the
counter-evidence was written into the register before this ran: R1 measured
the gross signal at +0.02 to +0.04R against +0.25R needed; H-STOPWIDTH found
expectancy flat across a four-rung stop ladder; Z0 priced four placeable
orders on it, all negative. What is new here is the LEVEL and the
strategy-free outcome.

Definitions, fixed before running:
  prior extreme = prior INCLUDED RTH session's high and low (no lookahead --
  it is complete before this session opens).
  sweep = the first RTH bar whose high > prior high, or low < prior low.
  Signed REVERSAL: a high sweep is signed short, a low sweep signed long,
  so a positive mean means the sweep reversed.
Horizon: 30 one-minute bars, truncated at the session close (day-flat).
Reference price is the swept LEVEL, not the bar close -- the level is the
only price on that bar we know actually traded.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd

from occams.loader import read_vendor_csv, to_trading_days

HORIZON = 30
SEED = 20260803


def rows_for(inst):
    days = to_trading_days(read_vendor_csv(f"data/{inst}.csv"),
                           range_minutes=15, instrument=f"{inst}.v.0")
    out = []
    prev = None
    for d in days:
        sb = pd.concat([d.range_bars, d.session_bars])
        if len(sb) < 60 or not d.atr or d.atr <= 0:
            prev = sb
            continue
        if prev is None:
            prev = sb
            continue
        phi = float(prev["high"].max())
        plo = float(prev["low"].min())
        prev = sb

        H = sb["high"].to_numpy(float)
        L = sb["low"].to_numpy(float)
        C = sb["close"].to_numpy(float)
        i = next((k for k in range(len(sb)) if H[k] > phi or L[k] < plo), None)
        if i is None:
            out.append({"date": d.date, "swept": False, "fwd": 0.0,
                        "eod": 0.0, "side": 0})
            continue
        # if a bar breaks BOTH in one minute, the level reached first is
        # unknowable from a bar; drop it rather than guess (delay-parity
        # discipline: never infer intrabar order).
        up = H[i] > phi
        dn = L[i] < plo
        if up and dn:
            continue
        level = phi if up else plo
        sign = -1.0 if up else 1.0                    # REVERSAL-signed
        end = min(i + HORIZON, len(sb) - 1)
        out.append({"date": d.date, "swept": True, "side": 1 if up else -1,
                    "fwd": float((C[end] - level) / d.atr) * sign,
                    "eod": float((C[-1] - level) / d.atr) * sign})
    return out


def cluster_boot(vals, dates, reps=4000):
    rng = np.random.default_rng(SEED)
    by = {}
    for v, dt in zip(vals, dates):
        by.setdefault(dt, []).append(v)
    pool = [np.array(by[k]) for k in by]
    means = np.empty(reps)
    for r in range(reps):
        pick = rng.integers(0, len(pool), len(pool))
        means[r] = np.concatenate([pool[p] for p in pick]).mean()
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


if __name__ == "__main__":
    out, allrows = {}, []
    for inst in ("MES", "MNQ"):
        rows = rows_for(inst)
        s = [r for r in rows if r["swept"]]
        v = np.array([r["fwd"] for r in s])
        out[inst] = {
            "days": len(rows),
            "sweep_rate": round(float(np.mean([r["swept"] for r in rows])), 4),
            "fwd_mean": round(float(v.mean()), 5) if len(v) else None,
        }
        print(f"  {inst}: days={len(rows):>4}  sweep rate "
              f"{out[inst]['sweep_rate']:.3f}  reversal fwd "
              f"{v.mean():+.5f} ATR")
        allrows += rows

    s = [r for r in allrows if r["swept"]]
    v = np.array([r["fwd"] for r in s])
    lo, hi = cluster_boot(v, [r["date"] for r in s])
    sd = float(v.std(ddof=1))
    d_obs = float(v.mean() / sd) if sd else 0.0
    e = np.array([r["eod"] for r in s])

    print(f"\n  PRIMARY (reversal-signed, 30m): n={len(v)}")
    print(f"    mean {v.mean():+.5f} ATR   95% CI [{lo:+.5f}, {hi:+.5f}]"
          f"   Cohen d {d_obs:+.4f}")
    print(f"  same number CONTINUATION-signed: {-v.mean():+.5f} ATR")
    print(f"  SECONDARY (sweep -> session close): {e.mean():+.5f} ATR")
    for lbl, side in (("high sweeps", 1), ("low  sweeps", -1)):
        w = np.array([r["fwd"] for r in s if r["side"] == side])
        print(f"    {lbl}: n={len(w):>4}  reversal fwd {w.mean():+.5f} ATR")

    out["pooled"] = {
        "fwd_mean_reversal": round(float(v.mean()), 5),
        "ci_low": round(lo, 5), "ci_high": round(hi, 5),
        "cohen_d": round(d_obs, 4), "sd": round(sd, 5),
        "eod_mean_reversal": round(float(e.mean()), 5),
    }
    out["n"] = len(v)
    from occams import experiment
    experiment.emit(out)
