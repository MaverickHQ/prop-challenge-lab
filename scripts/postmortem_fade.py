"""Post-mortem for the sealed Family-2 verdict (deterministic re-run of
the same computation — documentation, the decision is already taken).

Answers the question the terse report can't: did the fade's dev-fold
expectancy (+0.23R/trade unconditioned) VANISH out-of-sample (a mining
artifact) or PERSIST but fall short of the challenge bar (real but
insufficient)? Reports per instrument x fold: per-trade expectancy in R,
win rate, trade counts — plus the sweep's cell stats vs the gates.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from occams.calendar import load_events  # noqa: E402
from occams.fade import FadeParams, make_fade_strategy  # noqa: E402
from occams.harness import daily_ledger, monte_carlo  # noqa: E402
from occams.instruments import COSTS_BY_INSTRUMENT  # noqa: E402
from occams.verdict_cli import (CFG, GATES, GRID, load_instrument,  # noqa: E402
                                project_root)

RISK = 175.0
HORIZON = 90


def main() -> None:
    root = project_root()
    events = load_events(root / "occams" / "data" / "economic_calendar.csv")
    print(f"gates: G1>={GATES.p_pass_min} G2>=null+{GATES.edge_vs_null} "
          f"G3<={GATES.p_breach_max} G4 {GATES.plateau_cells}@"
          f"{GATES.plateau_slack} · horizon {HORIZON}d · risk ${RISK:.0f}")
    for inst in ("MES", "MNQ"):
        costs = COSTS_BY_INSTRUMENT[inst]
        days = load_instrument(root / "data", inst, range_minutes=15)
        n = len(days)
        os_, ls = int(n * 0.6), int(n * 0.8)
        folds = (("dev", days[:os_]), ("OOS", days[os_:ls]),
                 ("lockbox", days[ls:]))
        print(f"\n## {inst} ({n} days)")
        for k in GRID["k_stop"]:
            for wm in GRID["width_max"]:
                p = FadeParams(k_stop=k, width_max=wm, risk_usd=RISK)
                strat = make_fade_strategy(p, costs)
                row = [f"k={k} w={wm}"]
                for fold_name, fold_days in folds:
                    ledger = daily_ledger(fold_days, strat, costs,
                                          events=events)
                    pnls = [o.pnl for o in ledger if o.traded]
                    if not pnls:
                        row.append(f"{fold_name}: no trades")
                        continue
                    er = float(np.mean(pnls)) / RISK
                    wr = float(np.mean([x > 0 for x in pnls]))
                    stats = monte_carlo(fold_days, strat, CFG, costs,
                                        horizon_days=min(HORIZON,
                                                         len(fold_days) - 1),
                                        events=events)
                    row.append(f"{fold_name}: n={len(pnls)} "
                               f"E[R]={er:+.3f} WR={wr:.0%} "
                               f"p={stats.p_pass:.2f}/b={stats.p_breach:.2f}")
                print(" | ".join(row))


if __name__ == "__main__":
    main()
