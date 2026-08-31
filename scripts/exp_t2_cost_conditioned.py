"""T2 — is cost burden a selectable property?

Registered before this file existed, INCLUDING the statement that it cannot
resolve whether the strategy becomes +EV: the gap to break-even is 0.024R
and the smallest floor on this data is 0.0526R. The claim is about the
mechanism, and the record says so.

Cost in R = fixed per-contract cost / per-contract risk. Contracts cancel,
so it is invariant to risk per trade -- but it varies 15x with stop
distance, which is set by the opening-range height and therefore known
BEFORE the trade. Filtering on it removes the most cost-burdened trades
without touching the target, the stop multiple or the signal, which is the
one way found so far to raise the mean that does not buy it with variance.
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
from occams.strategy import (OrbParams, build_plan,              # noqa: E402
                             make_orb_strategy, per_contract_risk)

ROOT = Path(__file__).resolve().parent.parent
LADDER = (None, 0.10, 0.07, 0.05)      # DECLARED, fixed before running
TARGET_R, RISK, STOP_RANGE, SEED = 2.0, 175.0, 0.5, 20260830
CLUSTER_SIZE, INTRA_R = 2, 0.9
INSTRUMENTS = ("MES", "MNQ")


def cost_in_r(day, params, costs) -> float | None:
    """Ex-ante cost burden: fixed per-contract cost over per-contract risk.

    Both terms are known from the opening range, before any trade is taken
    -- which is what makes this a filter rather than hindsight.
    """
    plan = build_plan(day.range_bars, params=params, costs=costs)
    if not hasattr(plan, "stop_dist"):
        return None
    slip = costs.slippage_ticks * costs.tick_size
    fixed = slip * costs.multiplier + 2 * costs.commission_per_side
    return fixed / per_contract_risk(plan.stop_dist, costs)


def main() -> int:
    params = OrbParams(stop_range=STOP_RANGE, target_r=TARGET_R,
                       risk_usd=RISK)
    rows = []                       # (net_R, cost_R, date)
    for inst in INSTRUMENTS:
        days = to_trading_days(read_vendor_csv(ROOT / f"data/{inst}.csv"),
                               range_minutes=15, instrument=inst)
        print(f"  {inst}: {len(days):,} trading days")
        costs = costs_for(inst)
        by_date = {d.date: d for d in days}
        for o in daily_ledger(days, make_orb_strategy(params, costs), costs):
            if not o.traded:
                continue
            d = by_date.get(o.date)
            if d is None or d.range_bars is None or d.range_bars.empty:
                continue
            c = cost_in_r(d, params, costs)
            if c is not None:
                rows.append((o.pnl / RISK, c, str(o.date)))

    all_r = np.array([r for r, _, _ in rows])
    all_c = np.array([c for _, c, _ in rows])
    print(f"\n  trades {len(rows):,}   cost-in-R: median {np.median(all_c):.4f}"
          f"  p10 {np.percentile(all_c, 10):.4f}"
          f"  p90 {np.percentile(all_c, 90):.4f}")

    metrics: dict = {"ladder": {}, "n": len(rows)}
    print(f"\n{'max cost_R':>11s} {'kept':>7s} {'keep%':>7s} {'net R':>9s} "
          f"{'95% CI':>22s} {'floor':>7s} {'verdict':>12s}")
    print("-" * 82)
    for thr in LADDER:
        mask = np.ones(len(rows), bool) if thr is None else all_c <= thr
        vals = all_r[mask]
        clus = [rows[i][2] for i in range(len(rows)) if mask[i]]
        key = "nofilter" if thr is None else f"c{thr}"
        if vals.size < 30:
            metrics["ladder"][key] = {"trades": int(vals.size),
                                      "note": "too few"}
            print(f"{str(thr):>11s} {vals.size:>7,}  -- too few to score --")
            continue
        n_eff = power.effective_n(int(vals.size), cluster_size=CLUSTER_SIZE,
                                  intra_r=INTRA_R)
        lo, hi = stats.cluster_bootstrap_ci(vals, clus, seed=SEED)
        floor = power.detectable_mean_shift(n_eff) * float(vals.std(ddof=1))
        res = Result(name=f"T2 cost_R<={thr} - net R per trade",
                     estimate=float(vals.mean()), ci=(lo, hi),
                     n=int(vals.size), n_eff=n_eff, d=float(vals.mean()),
                     floor=floor, unit="R",
                     note=f"kept {vals.size / len(rows):.1%} of trades")
        metrics["ladder"][key] = res.to_metrics()
        print(f"{str(thr):>11s} {vals.size:>7,} {vals.size / len(rows):>6.1%} "
              f"{vals.mean():>+9.4f} [{lo:>+8.4f},{hi:>+8.4f}] "
              f"{floor:>7.4f} {res.verdict:>12s}")

    scored = [(k, v) for k, v in metrics["ladder"].items() if "estimate" in v]
    if len(scored) >= 2:
        base = metrics["ladder"]["nofilter"]["estimate"]
        best = max(scored, key=lambda kv: kv[1]["estimate"])
        metrics["improvement_over_nofilter"] = best[1]["estimate"] - base
        metrics["best_threshold"] = best[0]
        metrics["exceeds_floor"] = (best[1]["estimate"] - base) > best[1]["floor"]
        print(f"\n  unfiltered         {base:+.4f}R")
        print(f"  best               {best[0]} at {best[1]['estimate']:+.4f}R")
        print(f"  improvement        {best[1]['estimate'] - base:+.4f}R "
              f"(floor {best[1]['floor']:.4f})")
        print(f"  exceeds its floor? {metrics['exceeds_floor']}")
    metrics["n_eff"] = power.effective_n(metrics["n"],
                                         cluster_size=CLUSTER_SIZE,
                                         intra_r=INTRA_R)
    experiment.emit(metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
