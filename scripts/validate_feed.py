"""B0.5 — is Yahoo's delayed tape good enough to compute the card from?

The B0.1 gate killed the poller on our Databento entitlement (8-hour
wall). Yahoo's `MES=F`/`MNQ=F` measured exactly 10.0 minutes delayed —
the TradingView free-tier delay — which would satisfy delay parity
(B-C1) by construction, at $0. This decides whether its BARS are good
enough to compute a plan card from.

One number must match: the **09:30-09:45 ET range high and low, to the
tick**. Everything downstream — entry at the boundary, stop at
extreme ± 0.2 x height, target at the far side, and the true-risk size —
is derived from those two prices. A one-tick disagreement moves all four
and corrupts the drift measurement the whole campaign exists to make.

Databento is ground truth here because the sealed verdicts were computed
from it.

Usage:
    python3 scripts/validate_feed.py            # QUOTE ONLY, $0
    python3 scripts/validate_feed.py --submit   # buy the top-up, compare
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aws_recon import _call, _ctx, _parse_ts, api_key  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ET = ZoneInfo("America/New_York")
TICK = 0.25
DAYS_BACK = 8                     # Yahoo's 1-minute window is ~7 sessions
PAIRS = (("MES.v.0", "MES=F"), ("MNQ.v.0", "MNQ=F"))
RANGE_OPEN, RANGE_CLOSE = (9, 30), (9, 45)

# per-symbol actual billing: 0.0 when served from cache
BILLED: list[float | None] = []


def _window() -> tuple[datetime, datetime]:
    """Ends at the 8-hour wall — asking past it is refused (B0.1)."""
    now = datetime.now(timezone.utc)
    return (now - timedelta(days=DAYS_BACK)).replace(
        hour=0, minute=0, second=0, microsecond=0), now - timedelta(hours=8)


def _iso(d: datetime) -> str:
    return d.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _spec(sym: str) -> dict:
    a, b = _window()
    return {"dataset": "GLBX.MDP3", "symbols": sym, "schema": "ohlcv-1m",
            "stype_in": "continuous", "start": _iso(a), "end": _iso(b)}


def quote(key: str) -> float:
    total = 0.0
    for db_sym, _ in PAIRS:
        st, body, _ = _call("metadata.get_cost",
                            {**_spec(db_sym), "mode": "historical-streaming"},
                            key)
        if st != 200:
            sys.exit(f"quote failed for {db_sym}: {st} {body[:200]}")
        c = float(json.loads(body))
        total += c
        print(f"  {db_sym:<10} ${c:.4f}")
    print(f"  {'TOTAL':<10} ${total:.4f}")
    return total


def databento_bars(key: str, sym: str) -> dict[str, list[tuple]]:
    """{et_date: [(et_dt, high, low)]} — prices are int64 scaled by 1e9.

    Cached on disk keyed by symbol+window: metered data is never fetched
    twice. (Learned twice now — the $9.21 lost stream, then a $0.0625
    re-bill on this very script.) `data/` is git-ignored: the bars are
    licensed and must not be committed."""
    spec = _spec(sym)
    cache = (ROOT / "data" /
             f"b05-{sym}-{spec['start'][:10]}-{spec['end'][:10]}.ndjson")
    if cache.exists():
        body = cache.read_text()
        print(f"  reusing {cache.name} (no re-billing)")
        BILLED.append(0.0)
    else:
        BILLED.append(None)       # filled by the caller's quote
        st, body, _ = _call("timeseries.get_range",
                            {**spec, "encoding": "json",
                             "compression": "none"}, key, post=True)
        if st != 200:
            sys.exit(f"fetch failed for {sym}: {st} {body[:300]}")
        cache.parent.mkdir(exist_ok=True)
        cache.write_text(body)
    out: dict[str, list[tuple]] = defaultdict(list)
    for line in body.splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        ts = _parse_ts((r.get("hd") or {}).get("ts_event") or r.get("ts_event"))
        if ts is None:
            continue
        et = ts.astimezone(ET)
        out[et.date().isoformat()].append(
            (et, int(r["high"]) / 1e9, int(r["low"]) / 1e9))
    return out


def yahoo_bars(sym: str) -> dict[str, list[tuple]]:
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/"
           f"{urllib.parse.quote(sym)}?interval=1m&range={DAYS_BACK}d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30, context=_ctx()) as r:
        res = json.loads(r.read())["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    out: dict[str, list[tuple]] = defaultdict(list)
    for i, epoch in enumerate(res["timestamp"]):
        hi, lo = q["high"][i], q["low"][i]
        if hi is None or lo is None:
            continue
        et = datetime.fromtimestamp(epoch, tz=timezone.utc).astimezone(ET)
        out[et.date().isoformat()].append((et, float(hi), float(lo)))
    return out


def opening_range(bars: list[tuple]) -> tuple[float, float, int] | None:
    """High/low over bars whose OPEN time is in [09:30, 09:45) ET — the
    same 15 bars the Pine aid and the sealed engine use."""
    sel = [(h, lo) for t, h, lo in bars
           if RANGE_OPEN <= (t.hour, t.minute) < RANGE_CLOSE]
    if not sel:
        return None
    return max(h for h, _ in sel), min(lo for _, lo in sel), len(sel)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--submit", action="store_true")
    a = ap.parse_args()
    key = api_key()

    start, end = _window()
    print(f"B0.5 — {start:%Y-%m-%d} → {end:%Y-%m-%d %H:%M}Z (8h wall)\n")
    print("Databento quote:")
    total = quote(key)
    if not a.submit:
        print("\nQuote only — nothing purchased. Re-run with --submit.")
        return 0

    # A2: cumulative guard. This script previously had NO cost cap at
    # all -- it quoted, then bought. Refuses before any request is made.
    from occams import spend
    spend.check(total, what="B0.5 feed validation top-up")
    print(f"  {spend.status()}")
    rows, verdicts = [], []
    for db_sym, y_sym in PAIRS:
        db, yh = databento_bars(key, db_sym), yahoo_bars(y_sym)
        for day in sorted(set(db) & set(yh)):
            d, y = opening_range(db[day]), opening_range(yh[day])
            if d is None and y is None:
                continue          # weekend/holiday or pre-open: not a session
            if d is None or y is None:
                # one side has an opening range and the other does not —
                # a real disagreement, not a non-session
                rows.append((db_sym, day, d, y, "ONE-SIDED — investigate"))
                verdicts.append(False)
                continue
            dh, dl, dn = d
            yh_, yl, yn = y
            ok = abs(dh - yh_) < TICK / 2 and abs(dl - yl) < TICK / 2
            verdicts.append(ok)
            rows.append((db_sym, day, d, y,
                         "MATCH" if ok else
                         f"DIFF hi {yh_ - dh:+.2f} lo {yl - dl:+.2f}"))

    print(f"\n{'sym':<9}{'date':<12}{'CME hi/lo':<20}{'Yahoo hi/lo':<20}"
          f"{'bars':<8}verdict")
    for sym, day, d, y, note in rows:
        ds = f"{d[0]:.2f}/{d[1]:.2f}" if d else "—"
        ys = f"{y[0]:.2f}/{y[1]:.2f}" if y else "—"
        bars = f"{d[2] if d else 0}/{y[2] if y else 0}"
        print(f"{sym:<9}{day:<12}{ds:<20}{ys:<20}{bars:<8}{note}")

    n = len(verdicts)
    good = sum(verdicts)
    # actual billing, not the quote — cached symbols cost nothing
    billed = sum(total / len(PAIRS) if b is None else b for b in BILLED)
    print(f"\nSessions compared: {n} · exact tick match: {good}"
          f" · billed this run ${billed:.4f}")
    print("GATE: PASS — Yahoo is fit for the poller" if n and good == n
          else "GATE: FAIL — Yahoo cannot compute the card; poller abandoned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
