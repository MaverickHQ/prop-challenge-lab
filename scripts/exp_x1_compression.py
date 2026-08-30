# FROZEN EVIDENCE - archived under experiments/X1-COMPRESSION/.
"""X1 — does volatility compression predict subsequent expansion?

The best-scoring family on the map, and the only one whose mechanism is a
DOCUMENTED STATISTICAL PROPERTY (volatility clusters and mean-reverts)
rather than a story about what participants are thinking.

First experiment to run on the completed maths engine: every statistic here
comes from `occams.stats`, which is calibration-gated (M4), and the run
writes a `calcs.json` naming which estimator produced each number (M3).

PRIMARY -- prior days only, and that choice was made on design grounds
before any number existed. The obvious predictor, today's opening range, is
contaminated: the opening range and the rest of the same session are both
measurements of that day's volatility, and intraday volatility PERSISTS, so
a quiet open genuinely predicts a quiet day. That confound would swamp any
across-day mean reversion. The consecutive-contraction count is computed
entirely from COMPLETED PRIOR SESSIONS and cannot contain any part of the
outcome.

    predictor  consecutive contracting RTH sessions ending at N-1
    outcome    day N realised RTH range / trailing ATR (prior days only)

SECONDARY, reported as a CONFOUND CHECK rather than as evidence: today's
opening-range height over its trailing 20-day median, against the
post-range expansion of the same day. A POSITIVE reading here is expected
even if the mechanism is false.

The outcome is strategy-free -- a realised range, no entry, no stop, no
target -- because a P&L outcome is how the fade's unobtainable fill entered
the record.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd

from occams import power, stats
from occams.loader import read_vendor_csv, to_trading_days
from occams.result import Result

MEDIAN_WINDOW = 20
FLOOR = 0.07                      # the declared detectable effect


def rows_for(inst):
    """One observation per trading day. Everything predictive uses only
    sessions that had already closed."""
    days = to_trading_days(read_vendor_csv(f"data/{inst}.csv"),
                           range_minutes=15, instrument=f"{inst}.v.0")
    rth, orh, out = [], [], []
    for d in days:
        sb = pd.concat([d.range_bars, d.session_bars])
        if len(sb) < 60 or not d.atr or d.atr <= 0:
            continue
        rng_full = float(sb["high"].max() - sb["low"].min())
        rb = d.range_bars
        post = d.session_bars
        if rb.empty or post.empty or rng_full <= 0:
            continue
        rth.append(rng_full)
        orh.append(float(rb["high"].max() - rb["low"].min()))
        out.append({"date": d.date, "atr": float(d.atr), "range": rng_full,
                    "or_height": orh[-1],
                    "post_expansion": float(post["high"].max()
                                            - post["low"].min())})

    # consecutive contracting sessions ending at N-1 -- prior days only
    run = 0
    for i, r in enumerate(out):
        r["contraction_run"] = run
        if i > 0:
            run = run + 1 if rth[i] < rth[i - 1] else 0
        # trailing median of the opening-range height, prior days only
        if i >= MEDIAN_WINDOW:
            med = float(np.median(orh[i - MEDIAN_WINDOW:i]))
            r["or_ratio"] = r["or_height"] / med if med > 0 else np.nan
        else:
            r["or_ratio"] = np.nan
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
        ok = [r for r in rows if np.isfinite(r["or_ratio"])]
        x = np.array([r["contraction_run"] for r in ok], dtype=float)
        y = np.array([r["range"] / r["atr"] for r in ok])
        per[inst] = {"n": len(ok),
                     "primary_r": round(stats.spearman(x, y), 4),
                     "max_run": int(x.max()),
                     "mean_run": round(float(x.mean()), 3)}
        print(f"  {inst}: n={len(ok):>5}  primary r = "
              f"{per[inst]['primary_r']:+.4f}   longest contraction run "
              f"{per[inst]['max_run']}")
        pooled += ok

    print()
    x = np.array([r["contraction_run"] for r in pooled], dtype=float)
    y = np.array([r["range"] / r["atr"] for r in pooled])
    primary = report("X1 PRIMARY — contraction run (prior days) -> next-day "
                     "range / ATR", stats.spearman(x, y), len(pooled),
                     note="positive = the mechanism holds; negative = "
                          "volatility persists across days instead")

    xs = np.array([r["or_ratio"] for r in pooled])
    ys = np.array([r["post_expansion"] / r["atr"] for r in pooled])
    secondary = report("X1 SECONDARY (CONFOUND CHECK) — opening-range ratio "
                       "-> same-day post-range expansion",
                       stats.spearman(xs, ys), len(pooled),
                       note="a POSITIVE reading is expected even if the "
                            "mechanism is false: intraday volatility "
                            "persists, so a quiet open means a quiet day")

    # pre-specified: mean outcome by contraction-run bucket
    print("  outcome by contraction run (pre-specified secondary):")
    for lbl, m in (("run = 0", x == 0), ("run = 1", x == 1),
                   ("run = 2", x == 2), ("run >= 3", x >= 3)):
        if m.sum():
            print(f"    {lbl:<10} n={int(m.sum()):>5}   mean next-day range "
                  f"{y[m].mean():.4f} ATR")

    from occams import experiment
    experiment.emit({
        "MES": per["MES"], "MNQ": per["MNQ"],
        "primary": primary.to_metrics(),
        "secondary_confound": secondary.to_metrics(),
        "buckets": {lbl: round(float(y[m].mean()), 4)
                    for lbl, m in (("run_0", x == 0), ("run_1", x == 1),
                                   ("run_2", x == 2), ("run_3plus", x >= 3))
                    if m.sum()},
        "n": len(pooled),
    })
