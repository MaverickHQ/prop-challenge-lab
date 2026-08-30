"""Post-mortem diagnostics for the sealed 2026-07-06 verdict (NO-GO).

Re-materializes the SAME deterministic sweeps the verdict ran (same folds,
seeds, costs, sealed grid) and prints the cell-level detail the terse
verdict report omits: per instrument × fold, the null, the best cells, and
how far each gate was missed. Pure documentation of the read-once run —
the decision is already taken and cannot be changed here.
"""

from __future__ import annotations

from occams.harness import null_baseline
from occams.instruments import COSTS_BY_INSTRUMENT
from occams.search import prereg_hash_of, sweep
from occams.strategy import OrbParams, make_orb_strategy
from occams.verdict_cli import (CFG, GATES, GRID, INSTRUMENTS, RANGE_VALUES,
                                load_instrument, project_root)
from occams.verdict_run import _axes, _cell_params

from occams.calendar import load_events

HORIZON, RISK, DAILY_STOP = 60, 175.0, 500.0
SEEDS = (11, 12, 13, 14, 15)


def main() -> None:
    root = project_root()
    events = load_events(root / "occams" / "data" / "economic_calendar.csv")
    hash_ = prereg_hash_of(str(root / "docs" / "PREREG.md"))
    axes = _axes(GRID)
    print(f"protocol {hash_} · gates G1 p_pass>={GATES.p_pass_min} · "
          f"G2 edge>={GATES.edge_vs_null} · G3 breach<={GATES.p_breach_max} · "
          f"G4 plateau {GATES.plateau_cells}@{GATES.plateau_slack}")

    for inst in INSTRUMENTS:
        costs = COSTS_BY_INSTRUMENT[inst]
        days_by_rm = {rm: load_instrument(root / "data", inst, range_minutes=rm)
                      for rm in RANGE_VALUES}
        n = len(days_by_rm[RANGE_VALUES[0]])
        ls, os_ = int(n * 0.8), int(n * 0.6)
        print(f"\n## {inst} ({n} days; dev {os_} · OOS {ls - os_} · "
              f"lockbox {n - ls})")
        for fold, lo, hi in (("dev", 0, os_), ("OOS", os_, ls),
                             ("lockbox", ls, n)):
            base = days_by_rm[RANGE_VALUES[0]][lo:hi]
            null = null_baseline(base, OrbParams(1.0, 1.5, RISK,
                                                 daily_stop_usd=DAILY_STOP),
                                 CFG, costs, horizon_days=HORIZON,
                                 seeds=SEEDS, events=events)
            cells = []
            for rm in RANGE_VALUES:
                part = days_by_rm[rm][lo:hi]
                def sw(cell, _rm=rm):
                    return make_orb_strategy(
                        _cell_params(cell, RISK, DAILY_STOP), costs)
                s = sweep(part, axes, sw, CFG, costs, horizon_days=HORIZON,
                          events=events, prereg_hash=hash_)
                cells += [({**c.params, "range_minutes": rm}, c.stats)
                          for c in s.cells]
            cells.sort(key=lambda x: x[1].p_pass, reverse=True)
            g1 = sum(1 for _, s in cells if s.p_pass >= GATES.p_pass_min)
            g2 = sum(1 for _, s in cells
                     if s.p_pass - null >= GATES.edge_vs_null)
            print(f"  {fold:<8} null={null:.3f} · cells>=G1: {g1}/{len(cells)}"
                  f" · cells>=null+{GATES.edge_vs_null}: {g2}/{len(cells)}")
            for p, s in cells[:3]:
                print(f"    best p_pass={s.p_pass:.3f} breach={s.p_breach:.3f}"
                      f" med={s.median_days}d  {p}")


if __name__ == "__main__":
    main()
