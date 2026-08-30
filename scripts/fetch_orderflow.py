"""R2.1 — buy the `trades` tape for the setup window only.

Full-day tick data for this span quotes at ~$956; the 09:30-11:00 ET window
is ~25% of a day's messages and covers 94.3% of setups, which is what turns
an unaffordable purchase into a $54 one.

One request per instrument-day, because the API takes a start/end pair and
not a recurring daily window. Every response is cached to disk BEFORE it is
parsed: metered data is never fetched twice. That lesson has now been
learned three times in this repo -- the $9.21 lost stream, a $0.0625
re-bill, and it is not going to be learned a fourth.

    python3 scripts/fetch_orderflow.py            # QUOTE ONLY, $0
    python3 scripts/fetch_orderflow.py --submit   # buy
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aws_recon import _call, api_key  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "orderflow"
ET = ZoneInfo("America/New_York")
INSTRUMENTS = ("MES.v.0", "MNQ.v.0")
START, END = date(2024, 7, 1), date(2026, 7, 3)
# The BREAKOUT LEG only. The predictor runs from the breakout to the failure
# close; the 09:30-09:45 range period is already known from bars we own, and
# dropping it halves the cost for a 10-point coverage loss (94.3% -> 84.2%).
WINDOW = ((9, 45), (10, 15))
APPROVED_USD = 81.00                 # user approval 2026-08-01, revised
# The estimate carries ~30% noise because per-day cost varies ~8x with
# volume. The cap is what actually protects the budget, not the estimate.
CAP_USD = 90.00


def sessions() -> list[date]:
    d, out = START, []
    while d <= END:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def window_utc(d: date) -> tuple[str, str]:
    a = datetime(d.year, d.month, d.day, *WINDOW[0], tzinfo=ET)
    b = datetime(d.year, d.month, d.day, *WINDOW[1], tzinfo=ET)
    f = "%Y-%m-%dT%H:%M:%SZ"
    return (a.astimezone(ZoneInfo("UTC")).strftime(f),
            b.astimezone(ZoneInfo("UTC")).strftime(f))


def spec(sym: str, d: date) -> dict:
    a, b = window_utc(d)
    return {"dataset": "GLBX.MDP3", "symbols": sym, "schema": "trades",
            "stype_in": "continuous", "start": a, "end": b}


def cache_path(sym: str, d: date) -> Path:
    """Where a NEW fetch is written. Always gzipped: uncompressed JSON tick
    data runs ~18 MB per instrument-day and filled 6.3 GB in 356 requests."""
    return OUT / sym.replace(".", "_") / f"{d.isoformat()}.ndjson.gz"


def cached(sym: str, d: date) -> bool:
    """True if we ALREADY PAID for this instrument-day, in either form.

    This function is the one that protects the budget. An earlier batch was
    written uncompressed and later gzipped; a check that only knew about
    `.ndjson.gz` would call every one of those days uncached and re-buy the
    lot. Metered data has now been re-billed twice in this repo through
    exactly this kind of oversight -- it does not happen a third time."""
    stem = OUT / sym.replace(".", "_") / d.isoformat()
    return (stem.with_suffix(".ndjson.gz").exists()
            or stem.with_suffix(".ndjson").exists())


def _already_spent(key: str, todo_all) -> float:
    """What this purchase has cost SO FAR, priced from what is on disk.

    Read before every run, because a cap that resets per invocation is not a
    cap -- it is a per-invocation allowance, and this one let $114.82 through
    an $81 approval in two sittings."""
    have = [(s, d) for s, d in todo_all if cached(s, d)]
    if not have:
        return 0.0
    total = 0.0
    for s, d in have:
        st, body, _ = _call("metadata.get_cost",
                            {**spec(s, d), "mode": "historical-streaming"},
                            key)
        if st == 200:
            total += float(json.loads(body))
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--submit", action="store_true")
    a = ap.parse_args()
    key = api_key()
    days = sessions()
    # Interleaved by date, MOST RECENT FIRST. Three separate estimates of
    # this purchase came in 4x, 1.5x and 1.5x wrong (single quiet day; head
    # -biased sample; MES priced and doubled when MNQ trades more). So the
    # CAP decides the sample, not the estimate -- and this ordering means a
    # cap-stop yields a BALANCED, CONTIGUOUS, most-recent span rather than
    # all of one instrument and half of the other.
    #
    # Stopping on COST is legitimate; stopping on RESULTS would not be.
    # Nothing here looks at an outcome.
    todo = [(s, d) for d in reversed(days) for s in INSTRUMENTS
            if not cached(s, d)]
    print(f"{len(days)} sessions x {len(INSTRUMENTS)} instruments; "
          f"{len(todo)} not yet cached")

    if not a.submit:
        # Sample EVENLY across the span, never the head. Per-day cost
        # tracks volume and varies widely by period, so quoting the first
        # N consecutive days gives a biased estimate -- which is exactly
        # how the first attempt at this understated the total.
        step = max(len(todo) // 20, 1)
        sample = todo[::step][:20]
        tot = 0.0
        for s, d in sample:
            st, body, _ = _call("metadata.get_cost",
                                {**spec(s, d),
                                 "mode": "historical-streaming"}, key)
            if st == 200:
                tot += float(json.loads(body))
        per = tot / max(len(sample), 1)
        est = per * len(todo)
        print(f"  sampled {len(sample)} days evenly across the span")
        print(f"  mean per instrument-day  ${per:.4f}")
        print(f"  ESTIMATE for {len(todo)} requests   ${est:,.2f}")
        print(f"  approved                 ${APPROVED_USD:,.2f}")
        print(f"  hard cap                 ${CAP_USD:,.2f}")
        print("\nQuote only - nothing purchased. Re-run with --submit.")
        return 0

    # The cap MUST be cumulative across runs. It was not: `spent` reset to
    # zero on every invocation, so run 1 ($46.16) and run 2 ($68.66) each
    # passed a $90 per-run check and together reached $114.82 against an $81
    # approval. A budget guard that forgets what it already spent is not a
    # guard. Prior spend is now read from disk before anything is bought.
    spent = _already_spent(key, todo_all=[(s, d) for s in INSTRUMENTS
                                          for d in days])
    if spent >= CAP_USD:
        print(f"ALREADY AT ${spent:,.2f} of the ${CAP_USD} cap across previous "
              f"runs. Nothing further will be bought without re-approval.")
        return 0
    print(f"  already spent on this purchase: ${spent:,.2f}")
    for i, (s, d) in enumerate(todo, 1):
        p = cache_path(s, d)
        p.parent.mkdir(parents=True, exist_ok=True)
        if cached(s, d):                    # belt and braces: never re-buy
            continue
        st, body, _ = _call("metadata.get_cost",
                            {**spec(s, d), "mode": "historical-streaming"},
                            key)
        cost = float(json.loads(body)) if st == 200 else 0.0
        if spent + cost > CAP_USD:
            print(f"\nSTOPPED at ${spent:,.2f}: next request would exceed the "
                  f"${CAP_USD} cap. Re-approval required.")
            break
        st, body, _ = _call("timeseries.get_range",
                            {**spec(s, d), "encoding": "json",
                             "compression": "none"}, key, post=True)
        if st != 200:
            print(f"  !! {s} {d}: {st} {body[:120]}")
            continue
        import gzip
        with gzip.open(p, "wt") as fh:      # ~10x smaller on tick JSON
            fh.write(body)
        spent += cost
        if i % 50 == 0 or i == len(todo):
            print(f"  {i}/{len(todo)}  spent ${spent:,.2f}")
    print(f"\nDone. Spent ${spent:,.4f}. Add the row to docs/SPEND.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
