"""P1 data acquisition — continuous MES/MNQ 1-min bars + definitions (API).

The portal cannot express continuous symbology (product selection = parent =
ALL expirations, which the loader refuses on duplicate timestamps), so the
purchase goes through the historical API instead. Provenance is this file.

Usage:
    python scripts/fetch_data.py            # QUOTE ONLY — prints cost, no spend
    python scripts/fetch_data.py --submit   # downloads after you saw the quote

Reads DATABENTO_API_KEY from .env (git-ignored) or the environment. Needs
`pip install databento` (one-off acquisition dep, not a project dep).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET = "GLBX.MDP3"
INSTRUMENTS = ("MES", "MNQ")
BARS_START = "2019-05-01"          # micros launched 2019-05-05
# End on the last completed UTC day; definitions from one recent weekday.
BARS_END = date.today().isoformat()


def api_key() -> str:
    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                line = line.strip()
                if line.startswith("DATABENTO_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip("'\"")
    if not key:
        sys.exit("no DATABENTO_API_KEY in environment or .env — create one in "
                 "the portal (Settings → API keys) and add it to .env")
    return key


def recent_weekday() -> str:
    d = date.today() - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.isoformat()


def requests_spec() -> list[dict]:
    """The four purchases, fully parameterized — this list IS the provenance."""
    defn_day = recent_weekday()
    out = []
    for inst in INSTRUMENTS:
        out.append(dict(name=f"{inst} bars", dataset=DATASET,
                        schema="ohlcv-1m", symbols=[f"{inst}.v.0"],
                        stype_in="continuous", start=BARS_START, end=BARS_END,
                        dest=ROOT / "data" / f"{inst}.csv"))
        out.append(dict(name=f"{inst} definition", dataset=DATASET,
                        schema="definition", symbols=[f"{inst}.v.0"],
                        stype_in="continuous", start=defn_day,
                        dest=ROOT / "data" / f"{inst}.definition.csv"))
    return out


def quote(client, specs: list[dict]) -> float:
    total = 0.0
    for s in specs:
        cost = client.metadata.get_cost(
            dataset=s["dataset"], symbols=s["symbols"], schema=s["schema"],
            stype_in=s["stype_in"], start=s["start"], end=s.get("end"))
        total += cost
        print(f"  {s['name']:<16} {s['schema']:<12} ${cost:,.2f}")
    print(f"  {'TOTAL':<16} {'':<12} ${total:,.2f}")
    return total


def fetch(client, s: dict) -> None:
    # Persist the raw DBN immediately — a conversion failure after the
    # billed download must never lose the data (it did once: $9.21).
    raw = s["dest"].with_suffix(".dbn")
    raw.parent.mkdir(exist_ok=True)
    if raw.exists():
        import databento as db
        store = db.DBNStore.from_file(raw)
        print(f"  reusing {raw} (already downloaded — no re-billing)")
    else:
        store = client.timeseries.get_range(
            dataset=s["dataset"], symbols=s["symbols"], schema=s["schema"],
            stype_in=s["stype_in"], start=s["start"], end=s.get("end"))
        store.to_file(raw)
    df = store.to_df(price_type="float", pretty_ts=True, map_symbols=True)
    df = df.reset_index()
    if s["schema"] == "definition":
        # loader.check_definitions expects a `multiplier` column; Databento
        # names the contract size unit_of_measure_qty. Keep outrights only.
        if "multiplier" not in df.columns and "unit_of_measure_qty" in df.columns:
            df = df.rename(columns={"unit_of_measure_qty": "multiplier"})
        if "instrument_class" in df.columns:
            outright = df["instrument_class"].astype(str).isin(("F", "FUT"))
            if outright.any():
                df = df[outright]
    s["dest"].parent.mkdir(exist_ok=True)
    df.to_csv(s["dest"], index=False)
    print(f"  wrote {s['dest']} ({len(df):,} rows)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--submit", action="store_true",
                    help="actually download (default: quote only, $0)")
    args = ap.parse_args()

    try:
        import databento as db
    except ImportError:
        sys.exit("pip install databento  (one-off; not a project dependency)")

    client = db.Historical(api_key())
    specs = requests_spec()

    print(f"Cost quote ({DATASET}, {BARS_START} → {BARS_END}):")
    total = quote(client, specs)
    if not args.submit:
        print("\nQuote only — nothing purchased. Re-run with --submit to buy.")
        return 0

    # A2: cumulative guard. This script previously had NO cost cap at
    # all -- it quoted, then bought. Refuses before any request is made.
    from occams import spend
    spend.check(total, what="P1 bars + definitions")
    print(f"  {spend.status()}")
    print("\nDownloading:")
    for s in specs:
        fetch(client, s)
    print("\nDone. Next: `occams-verdict` (fails closed if anything is off).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
