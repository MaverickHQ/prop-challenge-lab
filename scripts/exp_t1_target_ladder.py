"""T1 — does moving the TARGET outward at a fixed stop improve EV?

Registered BEFORE this file existed. The mechanism, both interpretations and
the six-value ladder are in the hypothesis record, not here.

The axis has never been searched: the sealed grid varied `k_stop` and
`width_max` and recorded "Fixed, not searched: target = far side". It is
worth searching because the archived stop ladder run BACKWARDS says
asymmetry, not cost, is what binds -- widening the stop improves net R per
trade and destroys EV, because the payoff ratio collapses and a barrier
problem punishes that far more than it rewards a better mean.

ORB is the VEHICLE, not the subject. It is closed by sealed verdicts #1 and
#2. It is used because it is implemented and has an entry auditor that Z04
cleared across 6,774 armed orders.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from occams import experiment, power, stats                      # noqa: E402
from occams.harness import daily_ledger                          # noqa: E402
from occams.instruments import costs_for                         # noqa: E402
from occams.loader import read_vendor_csv, to_trading_days       # noqa: E402
from occams.result import Result                                 # noqa: E402
from occams.strategy import OrbParams, make_orb_strategy         # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LADDER = (1.0, 1.5, 2.0, 3.0, 4.0, 6.0)      # DECLARED, fixed before running
RISK, STOP_RANGE, SEED = 175.0, 0.5, 20260830
CLUSTER_SIZE, INTRA_R = 2, 0.9
INSTRUMENTS = ("MES", "MNQ")


def load(inst: str):
    return to_trading_days(read_vendor_csv(ROOT / f"data/{inst}.csv"),
                           range_minutes=15, instrument=inst)


def main() -> int:
    days = {i: load(i) for i in INSTRUMENTS}
    for i in INSTRUMENTS:
        print(f"  {i}: {len(days[i]):,} trading days")

    metrics: dict = {"ladder": {}}
    print(f"\n{'target_r':>9s} {'trades':>8s} {'win%':>7s} {'R/trade':>9s} "
          f"{'95% CI':>22s} {'floor':>7s} {'verdict':>12s}")
    print("-" * 80)

    for t in LADDER:
        params = OrbParams(stop_range=STOP_RANGE, target_r=t, risk_usd=RISK)
        vals, clusters, wins = [], [], 0
        for inst in INSTRUMENTS:
            ledger = daily_ledger(days[inst],
                                  make_orb_strategy(params, costs_for(inst)),
                                  costs_for(inst))
            for o in ledger:
                if not o.traded:
                    continue
                r = o.pnl / RISK
                vals.append(r)
                clusters.append(str(o.date))
                wins += r > 0

        a = np.asarray(vals, dtype=float)
        n = int(a.size)
        if n < 30:
            metrics["ladder"][f"t{t}"] = {"trades": n, "note": "too few"}
            print(f"{t:>9.1f} {n:>8,}  -- too few trades to score --")
            continue
        n_eff = power.effective_n(n, cluster_size=CLUSTER_SIZE,
                                  intra_r=INTRA_R)
        lo, hi = stats.cluster_bootstrap_ci(a, clusters, seed=SEED)
        floor = power.detectable_mean_shift(n_eff) * float(a.std(ddof=1))
        res = Result(name=f"T1 target_r={t} - net R per trade",
                     estimate=float(a.mean()), ci=(lo, hi), n=n, n_eff=n_eff,
                     d=float(a.mean()), floor=floor, unit="R",
                     note=f"win rate {wins / n:.3f}; ORB vehicle, "
                          f"stop_range={STOP_RANGE}, risk=${RISK:.0f}")
        metrics["ladder"][f"t{t}"] = res.to_metrics()
        print(f"{t:>9.1f} {n:>8,} {wins / n:>6.1%} {a.mean():>+9.4f} "
              f"[{lo:>+8.4f},{hi:>+8.4f}] {floor:>7.4f} {res.verdict:>12s}")

    # The power gate requires a top-level `n`: without it the test cannot be
    # shown adequate. Pooled trades across the whole declared ladder.
    metrics["n"] = sum(v.get("n", 0) for v in metrics["ladder"].values())
    metrics["n_eff"] = power.effective_n(metrics["n"],
                                         cluster_size=CLUSTER_SIZE,
                                         intra_r=INTRA_R)

    scored = [(t, metrics["ladder"][f"t{t}"]) for t in LADDER
              if "estimate" in metrics["ladder"].get(f"t{t}", {})]
    if len(scored) >= 2:
        best = max(scored, key=lambda kv: kv[1]["estimate"])
        first, last = scored[0][1]["estimate"], scored[-1][1]["estimate"]
        metrics["monotone_increasing"] = all(
            scored[i][1]["estimate"] <= scored[i + 1][1]["estimate"]
            for i in range(len(scored) - 1))
        metrics["best_target_r"] = best[0]
        metrics["span_R"] = last - first
        print(f"\n  best rung          target_r={best[0]} at "
              f"{best[1]['estimate']:+.4f}R")
        print(f"  monotone increasing? {metrics['monotone_increasing']}")
        print(f"  span across ladder   {last - first:+.4f}R")

    experiment.emit(metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
