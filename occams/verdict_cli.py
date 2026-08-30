"""The P1 verdict command — fails CLOSED unless every sealed input is present
(Codex #3/#4): CSVs, vendor definitions (asserted vs Costs), the economic
calendar, and the PREREG hash. Paths resolve from the project root, never the
cwd, so cron/Lambda/any-directory execution is safe.

    occams-verdict            # (installed console script)
    python -m occams.verdict_cli
"""

from __future__ import annotations

import sys
from pathlib import Path

from occams.calendar import load_events
from occams.harness import TradingDay
from occams.instruments import COSTS_BY_INSTRUMENT, costs_for
from occams.loader import (check_definitions, quality_report, read_vendor_csv,
                           to_trading_days)
from occams.harness import ValidityError
from occams.rules import ChallengeConfig
from occams.search import Gates, prereg_hash_of
from occams.verdict_run import Protocol, run_verdict

import pandas as pd

INSTRUMENTS = ("MES", "MNQ")
RANGE_VALUES = (15,)                 # v3: 30-min ranges strictly worse (B)
CFG = ChallengeConfig(50_000, 3_000, 2_000, 1_000, 1)
# PREREG v3 §6 gates (unchanged since v1) + §2 Family-2 grid (9 cells).
GATES = Gates(p_pass_min=0.55, edge_vs_null=0.15, p_breach_max=0.30,
              plateau_cells=5, plateau_slack=0.05)
# Family 2 (PREREG v3): the failed-breakout fade. k_stop = stop distance
# beyond the extreme in range-heights; width_max = ABSOLUTE height/ATR
# ceiling (sealed values, never in-sample quantiles); None = unfiltered.
GRID = {"range_minutes": (15,), "k_stop": (0.2, 0.25, 0.33),
        "width_max": (None, 0.30, 0.25)}


def project_root() -> Path:
    """Repo root, from THIS file's location — independent of cwd (Codex #3)."""
    return Path(__file__).resolve().parent.parent


def load_instrument(data_dir: Path, inst: str, *, range_minutes: int,
                    atr_period: int = 14, min_bars: int = 300
                    ) -> list[TradingDay]:
    """Load one instrument's bars, ASSERT its vendor definition against Costs,
    and split at range_minutes. Missing CSV or definition → loud failure."""
    data_dir = Path(data_dir)
    csv = data_dir / f"{inst}.csv"
    if not csv.exists():
        raise FileNotFoundError(f"missing market data {csv} (buy it — P1)")
    defn = data_dir / f"{inst}.definition.csv"
    if not defn.exists():
        raise FileNotFoundError(
            f"missing definition {defn} — request the `definition` schema "
            f"alongside ohlcv-1m so identity is asserted, not assumed")
    check_definitions(pd.read_csv(defn), inst, costs_for(inst))
    df = read_vendor_csv(csv)
    return to_trading_days(df, range_minutes=range_minutes, instrument=inst,
                           atr_period=atr_period, min_bars=min_bars)


def main() -> int:
    root = project_root()
    data_dir = root / "data"

    events = load_events(root / "occams" / "data" / "economic_calendar.csv")
    if not events:
        print("FAIL CLOSED: economic calendar is empty — complete the CPI/NFP "
              "backfill before sealing (backtest and live must share a day "
              "universe)")
        return 2

    days_by_range_minutes: dict[int, dict[str, list[TradingDay]]] = {}
    for rm in RANGE_VALUES:
        days_by_range_minutes[rm] = {}
        for inst in INSTRUMENTS:
            try:
                days = load_instrument(data_dir, inst, range_minutes=rm)
            except (FileNotFoundError, ValueError) as exc:
                print(f"FAIL CLOSED: {exc}")
                return 2
            days_by_range_minutes[rm][inst] = days
            if rm == RANGE_VALUES[0]:
                print(f"{inst}: {quality_report(read_vendor_csv(data_dir / f'{inst}.csv')).render()}")

    # funded_value (v3): cadence-matched, sealed as a deterministic dict —
    # derivations in PREREG v3 §7. Open (unfiltered, ~1.8 setups/day both
    # instruments): ~2 payout cycles/mo x ~$235 x 3mo x 0.8 = $1,100.
    # Filtered (~0.6/day): ~3.3 cycles over 3mo x ~$200 x 0.8 = $500.
    proto = Protocol(grid=GRID, gates=GATES, cfg=CFG, horizon_days=90,
                     risk_usd=175.0, daily_stop_usd=None, family="fade",
                     funded_value_by_filter={"open": 1_100.0,
                                             "filtered": 500.0},
                     prereg_hash=prereg_hash_of(str(root / "docs" / "PREREG.md")))
    try:
        report = run_verdict(days_by_range_minutes[RANGE_VALUES[0]], proto,
                             COSTS_BY_INSTRUMENT, events=events,
                             days_by_range_minutes=days_by_range_minutes)
    except ValidityError as exc:
        print(f"INSTRUMENT FAILURE (not a NO-GO): {exc}")
        return 2
    (data_dir / "verdict.md").write_text(report.render())
    print("\n" + report.render())
    return 0


if __name__ == "__main__":
    sys.exit(main())
