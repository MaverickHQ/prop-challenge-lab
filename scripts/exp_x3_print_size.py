# FROZEN EVIDENCE - archived under experiments/X3-PRINT-SIZE/.
"""X3 — does the SIZE DISTRIBUTION of aggressive prints predict direction?

The only non-public axis this programme holds. Every family that has died --
ORB, the fade, second push, ICT, X1, X2 -- traded price structure visible to
anyone with a chart. That is why X3 stayed queued after two price families
died in one afternoon.

    predictor  share of 09:45-10:00 volume in prints at or above that
               window's own 90th-percentile print size
    direction  sign of the 09:45 -> 10:00 price move
    outcome    direction-signed forward return over the following hour,
               measured from the 10:00 bar close

SEPARATION. The predictor uses prints strictly before 10:00; the outcome
starts at the 10:00 close. They share no bar and no print. Momentum, if it
exists in this window, shifts the MEAN signed return but cannot create a
correlation with print-size share -- so the primary is clean of it by
construction, and the unconditional mean is reported separately as context.

POWER, AND IT IS THE BINDING CONSTRAINT. 525 sessions per instrument means
at most 552 independent-equivalent observations. The 0.07 floor used in X1
and X2 is impossible here. The declared floor is 0.13, and the consequence
is carried with it: **a null here means 'no effect big enough for 552
effective observations to see', which is materially weaker than X1's or
X2's nulls.**

CONFOUND, registered as a control for the third time: a chunky tape is a
busy tape, so large-print share should predict subsequent VOLATILITY. X1's
analogous control returned 5.00x the floor and X2's 2.33x while both
hypotheses were refuted. A large positive here is expected and is not
evidence.
"""
import gzip
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd

from occams import estimators as est
from occams import power, stats
from occams.loader import read_vendor_csv, to_trading_days
from occams.result import Result

FLOW = Path("data/orderflow")
HORIZON = 60
FLOOR = 0.13
SPLIT_ET = "10:00"
WINDOW_START_ET = "09:45"


def window_prints(inst_dir: Path, d: date, end_ns: int):
    """(sizes,) for prints strictly before `end_ns`, or None."""
    f = inst_dir / f"{d.isoformat()}.ndjson.gz"
    if not f.exists():
        return None
    sizes = []
    with gzip.open(f, "rt") as fh:
        for ln in fh:
            if not ln.strip():
                continue
            r = json.loads(ln)
            if r.get("action") != "T" or r.get("side") not in ("A", "B"):
                continue
            if int((r.get("hd") or {}).get("ts_event", 0)) >= end_ns:
                continue
            sizes.append(int(r["size"]))
    return np.array(sizes) if len(sizes) >= 200 else None


def rows_for(inst):
    flow_dir = FLOW / f"{inst}_v_0"
    if not flow_dir.is_dir():
        return []
    days = to_trading_days(read_vendor_csv(f"data/{inst}.csv"),
                           range_minutes=15, instrument=f"{inst}.v.0")
    out = []
    for d in days:
        sb = pd.concat([d.range_bars, d.session_bars])
        if len(sb) < 120 or not d.atr or d.atr <= 0:
            continue
        idx = sb.index
        try:
            i_start = int(np.flatnonzero(
                idx.strftime("%H:%M") == WINDOW_START_ET)[0])
            i_split = int(np.flatnonzero(
                idx.strftime("%H:%M") == SPLIT_ET)[0])
        except IndexError:
            continue
        end_ns = int(idx[i_split].to_pydatetime().timestamp() * 1e9)
        sizes = window_prints(flow_dir, d.date, end_ns)
        if sizes is None:
            continue

        p90 = float(np.percentile(sizes, 90))
        big = sizes[sizes >= p90]
        share = float(big.sum() / sizes.sum())

        closes = sb["close"].to_numpy(float)
        move = float(closes[i_split] - closes[i_start])
        if move == 0.0:
            continue                       # no direction to sign by
        direction = 1 if move > 0 else -1
        fwd = est.forward_return(closes, at=i_split, horizon=HORIZON,
                                 direction=direction,
                                 reference=est.AT_PRICE, scale=d.atr)
        out.append({"date": d.date, "share": share, "fwd": fwd,
                    "abs_fwd": abs(fwd), "prints": len(sizes),
                    "p90": p90, "window_move_atr": abs(move) / d.atr})
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
        if not rows:
            print(f"  {inst}: no overlapping sessions")
            continue
        x = np.array([r["share"] for r in rows])
        y = np.array([r["fwd"] for r in rows])
        per[inst] = {"n": len(rows),
                     "primary_r": round(stats.spearman(x, y), 4),
                     "share_median": round(float(np.median(x)), 4),
                     "p90_median": round(float(np.median(
                         [r["p90"] for r in rows])), 1)}
        print(f"  {inst}: n={len(rows):>4}  primary r = "
              f"{per[inst]['primary_r']:+.4f}   median large-print share "
              f"{per[inst]['share_median']:.3f}   median p90 size "
              f"{per[inst]['p90_median']:.0f}")
        pooled += rows

    print()
    x = np.array([r["share"] for r in pooled])
    y = np.array([r["fwd"] for r in pooled])
    primary = report("X3 PRIMARY — large-print share -> signed forward "
                     "return, next hour", stats.spearman(x, y), len(pooled),
                     note="positive = large prints mark flow that extends; "
                          "negative = they mark exhaustion/absorption")

    af = np.array([r["abs_fwd"] for r in pooled])
    confound = report("X3 CONTROL (CONFOUND) — large-print share -> "
                      "|forward move|", stats.spearman(x, af), len(pooled),
                      note="a large POSITIVE is expected even if the primary "
                           "is zero: a chunky tape is a busy tape. Third "
                           "experiment running, third such control")

    print(f"  unconditional mean signed forward return "
          f"{y.mean():+.5f} ATR   (does momentum exist in this window at "
          f"all? it shifts this mean but cannot correlate with share)")
    print("\n  signed forward move by large-print-share tercile:")
    q = np.quantile(x, [1 / 3, 2 / 3])
    for lbl, m in (("low  share", x <= q[0]),
                   ("mid  share", (x > q[0]) & (x < q[1])),
                   ("high share", x >= q[1])):
        print(f"    {lbl}: n={int(m.sum()):>4}   mean fwd {y[m].mean():+.5f} "
              f"ATR   mean |fwd| {af[m].mean():.5f}")

    from occams import experiment
    experiment.emit({
        **{k: v for k, v in per.items()},
        "primary": primary.to_metrics(),
        "control_confound": confound.to_metrics(),
        "unconditional_mean_fwd": round(float(y.mean()), 5),
        "n": len(pooled),
    })
