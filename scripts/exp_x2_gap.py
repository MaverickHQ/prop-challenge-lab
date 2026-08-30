# FROZEN EVIDENCE - archived under experiments/X2-OVERNIGHT-GAP/.
"""X2 — does the overnight gap carry directional information?

Structurally different from every family that has already died, all of
which traded intraday price structure. Runs on the audited engine: every
statistic from `occams.stats`, calibration-gated (M4), with `calcs.json`
naming which estimator produced each number (M3).

    predictor  signed gap = (RTH open - prior RTH close) / trailing ATR
    outcome    signed forward return over the first session hour,
               measured from the CLOSE of the 09:30-09:31 bar

REFERENCE PRICE, by design and not by default (M2). The gap is known at
09:30 from the OPEN. The measurement starts from the CLOSE of the first
minute, by which time the gap is observable and an order could have been
placed. Predictor and outcome therefore share no bar. Measuring from the
open would fold the first minute's reaction into both -- the ICT-P2 defect
in a new place -- and `estimators.forward_return` is called with
`reference=AT_PRICE` so it cannot carry a positional term at all.

CONFOUND, registered as a control: gap SIZE against subsequent ABSOLUTE
movement. A big gap almost certainly means a busy day, and that is
volatility persistence rather than directional information. In X1 the
analogous control came back at five times the detectable floor while the
hypothesis itself was refuted. A large positive here is expected and is
NOT evidence.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd

from occams import estimators as est
from occams import power, stats
from occams.loader import read_vendor_csv, to_trading_days
from occams.result import Result

HORIZON = 60                      # the first session hour
FLOOR = 0.07


def rows_for(inst):
    days = to_trading_days(read_vendor_csv(f"data/{inst}.csv"),
                           range_minutes=15, instrument=f"{inst}.v.0")
    out, prev_close = [], None
    for d in days:
        sb = pd.concat([d.range_bars, d.session_bars])
        if len(sb) < 90 or not d.atr or d.atr <= 0:
            prev_close = None if len(sb) == 0 else float(sb["close"].iloc[-1])
            continue
        closes = sb["close"].to_numpy(float)
        this_open = float(sb["open"].iloc[0])
        if prev_close is not None:
            gap = (this_open - prev_close) / d.atr
            direction = 1 if gap >= 0 else -1
            # measured from the CLOSE of bar 0, so predictor and outcome
            # share no bar; AT_PRICE has no positional term by construction
            fwd = est.forward_return(closes, at=0, horizon=HORIZON,
                                     direction=1, reference=est.AT_PRICE,
                                     scale=d.atr)
            eod = est.forward_return(closes, at=0, horizon=len(closes) - 1,
                                     direction=1, reference=est.AT_PRICE,
                                     scale=d.atr)
            out.append({"date": d.date, "gap": gap, "abs_gap": abs(gap),
                        "fwd": fwd, "eod": eod, "abs_fwd": abs(fwd),
                        "signed_fwd": fwd * direction})
        prev_close = float(sb["close"].iloc[-1])
    return out


def report(name, r, n_raw, note=""):
    n_eff = power.effective_n(n_raw, cluster_size=2, intra_r=0.9)
    res = Result(name=name, estimate=r, ci=stats.correlation_ci(r, n_eff),
                 n=n_raw, n_eff=n_eff, d=r, floor=FLOOR, unit="Spearman r",
                 note=note)
    print(res.render())
    print()
    return res


if __name__ == "__main__":
    per, pooled = {}, []
    for inst in ("MES", "MNQ"):
        rows = rows_for(inst)
        g = np.array([r["gap"] for r in rows])
        f = np.array([r["fwd"] for r in rows])
        per[inst] = {"n": len(rows),
                     "primary_r": round(stats.spearman(g, f), 4),
                     "median_abs_gap_atr": round(float(np.median(
                         [r["abs_gap"] for r in rows])), 4)}
        print(f"  {inst}: n={len(rows):>5}  primary r = "
              f"{per[inst]['primary_r']:+.4f}   median |gap| "
              f"{per[inst]['median_abs_gap_atr']:.4f} ATR")
        pooled += rows

    print()
    g = np.array([r["gap"] for r in pooled])
    f = np.array([r["fwd"] for r in pooled])
    primary = report("X2 PRIMARY — signed gap -> signed forward return, "
                     "first session hour", stats.spearman(g, f), len(pooled),
                     note="positive = incomplete absorption (continuation); "
                          "negative = overreaction (gaps fade)")

    e = np.array([r["eod"] for r in pooled])
    to_close = report("X2 SECONDARY — same predictor, held to the session "
                      "close", stats.spearman(g, e), len(pooled),
                      note="pre-specified secondary horizon")

    ag = np.array([r["abs_gap"] for r in pooled])
    af = np.array([r["abs_fwd"] for r in pooled])
    confound = report("X2 CONTROL (CONFOUND) — |gap| -> |forward move|",
                      stats.spearman(ag, af), len(pooled),
                      note="a large POSITIVE is expected even if the primary "
                           "is zero: a big gap means a busy day. Volatility "
                           "persistence, NOT directional information")

    print("  signed forward move by gap decile (pre-specified secondary):")
    q = np.quantile(g, np.linspace(0, 1, 11))
    for i in range(10):
        m = (g >= q[i]) & (g <= q[i + 1] if i == 9 else g < q[i + 1])
        if m.sum():
            print(f"    decile {i + 1:>2}  gap {q[i]:+.4f}..{q[i+1]:+.4f}  "
                  f"n={int(m.sum()):>4}   mean fwd {f[m].mean():+.5f} ATR")

    from occams import experiment
    experiment.emit({
        "MES": per["MES"], "MNQ": per["MNQ"],
        "primary": primary.to_metrics(),
        "secondary_to_close": to_close.to_metrics(),
        "control_confound": confound.to_metrics(),
        "n": len(pooled),
    })
