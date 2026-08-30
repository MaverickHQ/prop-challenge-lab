# FROZEN EVIDENCE - archived under experiments/ICT-P2-CONTROL/.
"""ICT-P2-CONTROL — is P2's -0.159 ATR a market fact or my reference price?

P2 measured the forward move from the swept LEVEL. That choice was made for
obtainability reasons and it is WRONG for a directional test, for a reason
that is visible without any data: on an up-sweep bar, price is already ABOVE
the level when the bar closes. So

    C[end] - level  =  (C[i] - level)  +  (C[end] - C[i])
                       \_____________/    \_____________/
                        PENETRATION        forward drift
                        positive by        the thing the
                        construction       hypothesis is about

A market that froze solid the instant it swept would still print a positive
continuation reading, purely from the first term. P2's headline is therefore
uninterpretable until the two terms are separated.

This is the Z0 check applied to my own measurement rather than to a
strategy. It adds no free parameters and cannot produce a better number --
the two terms must sum to P2's r1 result, which is what makes it a control
and not a second look.

Also reported: the sweep-bar-close reading is what a MARKET order after the
sweep would actually see, so it doubles as the obtainability figure.
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
    out, prev = [], None
    for d in days:
        sb = pd.concat([d.range_bars, d.session_bars])
        if len(sb) < 60 or not d.atr or d.atr <= 0 or prev is None:
            prev = sb
            continue
        phi, plo = float(prev["high"].max()), float(prev["low"].min())
        prev = sb
        H = sb["high"].to_numpy(float)
        L = sb["low"].to_numpy(float)
        C = sb["close"].to_numpy(float)
        i = next((k for k in range(len(sb)) if H[k] > phi or L[k] < plo), None)
        if i is None:
            continue
        up, dn = H[i] > phi, L[i] < plo
        if up and dn:
            continue
        level = phi if up else plo
        sign = -1.0 if up else 1.0                       # reversal-signed
        end = min(i + HORIZON, len(sb) - 1)
        out.append({
            "date": d.date,
            "total": float((C[end] - level) / d.atr) * sign,   # == P2 r1
            "penetration": float((C[i] - level) / d.atr) * sign,
            "drift": float((C[end] - C[i]) / d.atr) * sign,
            "excursion": float((H[i] - phi if up else plo - L[i]) / d.atr),
        })
    return out


def cluster_boot(vals, dates, reps=4000):
    rng = np.random.default_rng(SEED)
    by = {}
    for v, dt in zip(vals, dates):
        by.setdefault(dt, []).append(v)
    pool = [np.array(by[k]) for k in by]
    m = np.empty(reps)
    for r in range(reps):
        pick = rng.integers(0, len(pool), len(pool))
        m[r] = np.concatenate([pool[p] for p in pick]).mean()
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


if __name__ == "__main__":
    allrows = []
    for inst in ("MES", "MNQ"):
        rows = rows_for(inst)
        t = np.array([r["total"] for r in rows])
        p = np.array([r["penetration"] for r in rows])
        g = np.array([r["drift"] for r in rows])
        print(f"  {inst}: n={len(rows):>4}  total {t.mean():+.5f}"
              f"  = penetration {p.mean():+.5f} + drift {g.mean():+.5f}")
        allrows += rows

    t = np.array([r["total"] for r in allrows])
    p = np.array([r["penetration"] for r in allrows])
    g = np.array([r["drift"] for r in allrows])
    dts = [r["date"] for r in allrows]
    glo, ghi = cluster_boot(g, dts)
    plo_, phi_ = cluster_boot(p, dts)
    sd = float(g.std(ddof=1))

    print(f"\n  POOLED n={len(t)}   (reversal-signed, ATR units)")
    print(f"    total       {t.mean():+.5f}   <- P2 r1 reproduced")
    print(f"    penetration {p.mean():+.5f}   CI [{plo_:+.5f}, {phi_:+.5f}]"
          f"   share of total {p.mean()/t.mean()*100:5.1f}%")
    print(f"    drift       {g.mean():+.5f}   CI [{glo:+.5f}, {ghi:+.5f}]"
          f"   Cohen d {g.mean()/sd:+.4f}")
    print(f"    median sweep excursion {np.median([r['excursion'] for r in allrows]):.5f} ATR")

    from occams import experiment
    experiment.emit({
        "n": len(t),
        "total_mean": round(float(t.mean()), 5),
        "penetration_mean": round(float(p.mean()), 5),
        "penetration_share": round(float(p.mean() / t.mean()), 4),
        "drift_mean": round(float(g.mean()), 5),
        "drift_ci": [round(glo, 5), round(ghi, 5)],
        "drift_cohen_d": round(float(g.mean() / sd), 4),
        "identity_holds": bool(abs(t.mean() - p.mean() - g.mean()) < 1e-9),
    })
