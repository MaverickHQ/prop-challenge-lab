"""One-off CPI/NFP calendar backfill from saved BLS year-schedule pages.

BLS 403s every scripted fetcher, so the user saved the official per-year
schedule pages (https://www.bls.gov/schedule/<YYYY>/home.htm) by hand into
~/Downloads/<YYYY>.html. Each page carries the full year's release table
(Date · Time · Release). This script extracts every "Consumer Price Index"
and "Employment Situation" release (both 8:30 AM ET) and merges them into
occams/data/economic_calendar.csv alongside the FOMC rows.

Usage: python scripts/backfill_bls.py [downloads_dir]
Idempotent: rebuilds the CPI/NFP rows from the saved pages every run.
"""

from __future__ import annotations

import csv
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CALENDAR = ROOT / "occams" / "data" / "economic_calendar.csv"
YEARS = range(2019, 2027)
RELEASES = {"Consumer Price Index": "CPI", "Employment Situation": "NFP"}


def extract(html: str) -> list[tuple[date, str]]:
    out: list[tuple[date, str]] = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        cells = [re.sub(r"<[^>]+>", " ", c) for c in
                 re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
        cells = [re.sub(r"\s+", " ", c).strip() for c in cells]
        if len(cells) != 3:
            continue
        date_s, _time_s, release = cells
        for prefix, tag in RELEASES.items():
            # match "<name> for <Month YYYY>" only — skips annual/experimental
            # variants like "Consumer Price Index Research Series".
            if release.startswith(prefix + " for"):
                d = datetime.strptime(date_s, "%A, %B %d, %Y").date()
                out.append((d, tag))
    return out


def main() -> int:
    downloads = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads"
    rows: list[tuple[date, str]] = []
    for year in YEARS:
        f = downloads / f"{year}.html"
        if not f.exists():
            sys.exit(f"missing {f} — save https://www.bls.gov/schedule/{year}/home.htm")
        found = extract(f.read_text(errors="replace"))
        n_cpi = sum(1 for _, t in found if t == "CPI")
        n_nfp = sum(1 for _, t in found if t == "NFP")
        wrong_year = [d for d, _ in found if d.year != year]
        print(f"{year}: {n_cpi} CPI, {n_nfp} NFP"
              + (f"  WARNING off-year dates: {wrong_year}" if wrong_year else ""))
        rows.extend(found)

    with open(CALENDAR) as fh:
        kept = [(r["date"], r["event"]) for r in csv.DictReader(fh)
                if r["event"] not in RELEASES.values()]
    merged = sorted(set(kept) | {(d.isoformat(), t) for d, t in rows})
    with open(CALENDAR, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "event"])
        w.writerows(merged)
    from collections import Counter
    counts = Counter(e for _, e in merged)
    print(f"calendar written: {len(merged)} rows — {dict(counts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
