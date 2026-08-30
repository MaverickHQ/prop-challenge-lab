"""B1 — the queryable copy: CSV to Parquet, partitioned by instrument/year.

The vendor CSVs are 400 MB and reparse from text on every run. Parquet is
columnar and roughly 10x smaller, so `derived/` becomes the thing you
actually query and `raw/` stays untouched as the purchased original.

NO DuckDB. I recommended it earlier on the grounds that it needs no
infrastructure, which is true, and then checked: the whole dataset is ~80 MB
as Parquet and fits in memory, so pandas -- already a dependency -- reads it
directly through pyarrow. A dependency bought for a convenience we do not
need is the thing the razor is for. Revisit only if a query genuinely
exceeds RAM.

`derived/` is deliberately mutable: it is regenerable from `raw/` by
definition, so nothing here is evidence.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "derived"
ET = "America/New_York"


def convert(inst: str) -> list[Path]:
    src = ROOT / "data" / f"{inst}.csv"
    if not src.exists():
        print(f"  {inst}: no source CSV")
        return []
    df = pd.read_csv(src, usecols=["ts_event", "open", "high", "low",
                                   "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(ET)
    df = df.drop(columns=["ts_event"])
    df["year"] = df["ts"].dt.year
    written = []
    for year, g in df.groupby("year"):
        d = OUT / f"instrument={inst}" / f"year={year}"
        d.mkdir(parents=True, exist_ok=True)
        p = d / "bars.parquet"
        g.drop(columns=["year"]).to_parquet(p, index=False,
                                            compression="zstd")
        written.append(p)
    csv_mb = src.stat().st_size / 1e6
    pq_mb = sum(p.stat().st_size for p in written) / 1e6
    print(f"  {inst}: {len(df):,} rows  {csv_mb:,.0f} MB CSV -> "
          f"{pq_mb:,.0f} MB Parquet  ({csv_mb/max(pq_mb,0.001):.1f}x smaller)")
    return written


def load(inst: str, years=None) -> pd.DataFrame:
    """Read the derived bars back. This is the query layer -- no engine, no
    catalog, no service."""
    base = OUT / f"instrument={inst}"
    parts = sorted(base.glob("year=*/bars.parquet"))
    if years:
        parts = [p for p in parts
                 if int(p.parent.name.split("=")[1]) in set(years)]
    if not parts:
        raise FileNotFoundError(f"no derived parquet for {inst}")
    return pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for inst in ("MES", "MNQ"):
        convert(inst)
    # prove the round trip rather than assert it (D7.3)
    df = load("MES", years=[2026])
    print(f"\n  round trip: MES 2026 -> {len(df):,} rows, "
          f"{df['ts'].min():%Y-%m-%d} .. {df['ts'].max():%Y-%m-%d}")
