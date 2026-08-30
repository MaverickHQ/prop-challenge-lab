"""Phase A — the feasibility map: the edge REQUIRED before any is hunted.

Monte-Carlo synthetic Bernoulli trade streams through the REAL rules engine
(`ChallengeState`), sweeping win rate x net payoff ratio x trades/day x
risk x horizon x plan geometry. No market data touched; the output is the
iso-P(pass) frontier every Family-2 hypothesis is screened against.

Conventions (stated in FEASIBILITY.md):
- R_net is the NET payoff ratio: a win pays +R_net x risk, a loss costs
  exactly -risk (our sizing already folds costs into the risked dollar).
- trades/day f < 1 means trading a Bernoulli(f) subset of days — the
  selective-regime shape; f = 2 caps at two independent trades/day.
- Plan geometries: Zero 50k fully VERIFIED; Advanced 50k partially
  verified (target 4,000 / MLL 1,750 / no guard / min 2 days / 50% eval
  consistency); Premium EXCLUDED until its rules are verified.

Usage: python scripts/feasibility.py [--runs 400] > report; writes
docs/FEASIBILITY.md.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from occams.rules import ChallengeConfig, ChallengeState, Status  # noqa: E402
from occams.verdict_run import expected_cost  # noqa: E402

PLANS = {
    "zero-50k": ChallengeConfig(50_000, 3_000, 2_000, 1_000, 1),
    "advanced-50k": ChallengeConfig(50_000, 4_000, 1_750, 0, 2,
                                    consistency_frac=0.5),
}
WIN_RATES = (0.40, 0.45, 0.475, 0.50, 0.525, 0.55, 0.575, 0.60, 0.65)
R_NETS = (1.0, 1.5, 2.0, 3.0)
FREQS = (0.33, 0.5, 1.0, 2.0)          # trades per day (f<1 = selective)
RISKS = (125.0, 175.0, 250.0)
HORIZONS = (60, 90, 120)
G1, G3 = 0.55, 0.30
MONTHLY, RESET = 119.0, 109.0


@dataclass(frozen=True)
class Cell:
    p_pass: float
    p_breach: float
    median_days: int


def simulate(cfg: ChallengeConfig, wr: float, r_net: float, freq: float,
             risk: float, horizon: int, runs: int, seed: int) -> Cell:
    rng = np.random.default_rng(seed)
    passes = breaches = 0
    days_used: list[int] = []
    per_day = max(1, int(round(freq))) if freq >= 1 else 1
    p_trade_day = min(freq, 1.0)
    for _ in range(runs):
        st = ChallengeState(cfg)
        eq = float(cfg.account)
        outcome_day = horizon
        for d in range(horizon):
            traded = bool(rng.random() < p_trade_day)
            pnl = 0.0
            if traded:
                wins = rng.random(per_day) < wr
                pnl = float(np.where(wins, r_net * risk, -risk).sum())
            eq += pnl
            status = st.record_day(eq, traded=traded)
            if status is not Status.ACTIVE:
                outcome_day = d + 1
                break
        days_used.append(outcome_day)
        if status is Status.PASSED:
            passes += 1
        elif status is Status.BREACHED:
            breaches += 1
    return Cell(p_pass=passes / runs, p_breach=breaches / runs,
                median_days=int(np.median(days_used)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=400)
    args = ap.parse_args()

    rows = []
    seed = 0
    for plan, cfg in PLANS.items():
        for h in HORIZONS:
            for risk in RISKS:
                for f in FREQS:
                    for r in R_NETS:
                        for wr in WIN_RATES:
                            seed += 1
                            c = simulate(cfg, wr, r, f, risk, h,
                                         args.runs, seed)
                            rows.append((plan, h, risk, f, r, wr, c))

    # The frontier: per (plan, horizon, risk, freq, R) the MINIMUM win rate
    # whose cell clears G1 AND G3; '-' if none in the sweep does.
    lines = [
        "# FEASIBILITY — the required-edge frontier (Phase A)",
        "",
        f"MC {args.runs} runs/cell through the real rules engine "
        f"(`ChallengeState`), seeded, no market data. R_net is NET of "
        f"costs; a loss is exactly -risk. f<1 = selective (Bernoulli "
        f"subset of days). Gates: G1 P(pass)>={G1} AND G3 P(breach)<={G3}."
        f" E[cost] = time-based (${MONTHLY:.0f}/mo + ${RESET:.0f}/reset) "
        f"at the frontier cell's median days.",
        "",
        "Plan geometries: zero-50k VERIFIED; advanced-50k partially "
        "verified (4,000/1,750/no guard/min 2 days/50% eval consistency) "
        "— VERIFY before any decision leans on it. Premium excluded "
        "(rules unverified).",
        "",
        "## Minimum win rate clearing BOTH gates",
        "",
        "| plan | horizon | risk | trades/day | R_net | min WR | P(pass) "
        "| P(breach) | med days | E[cost] |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    frontier = {}
    for plan, h, risk, f, r, wr, c in rows:
        key = (plan, h, risk, f, r)
        if c.p_pass >= G1 and c.p_breach <= G3 and key not in frontier:
            frontier[key] = (wr, c)
    for plan in PLANS:
        for h in HORIZONS:
            for risk in RISKS:
                for f in FREQS:
                    for r in R_NETS:
                        key = (plan, h, risk, f, r)
                        if key in frontier:
                            wr, c = frontier[key]
                            ec = expected_cost(c.p_pass, c.median_days,
                                               MONTHLY, RESET)
                            lines.append(
                                f"| {plan} | {h} | {risk:.0f} | {f} | {r} "
                                f"| **{wr:.3f}** | {c.p_pass:.2f} "
                                f"| {c.p_breach:.2f} | {c.median_days} "
                                f"| ${ec:.0f} |")
                        else:
                            lines.append(
                                f"| {plan} | {h} | {risk:.0f} | {f} | {r} "
                                f"| — | | | | |")
    out = "\n".join(lines) + "\n"
    (ROOT / "docs" / "FEASIBILITY.md").write_text(out)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
