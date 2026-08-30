"""B0.1 + B0.2 spike — how fresh is the newest retrievable 1-minute bar?

The AWS poller (B2.3) can only decide on bars it can actually fetch. This
measures that, repeatedly, across a session, and writes the latency table
the B0.1 gate is decided from.

Two lags are recorded because they are not the same number:

  claimed_lag  now - metadata.get_dataset_range().end    (free call)
  true_lag     now - newest bar an actual fetch returns  (metered)

`claimed` is what the API advertises; `true` is what a poller would really
see. Only `true` can be trusted for delay-parity (B-C1), so the metered
probe is the measurement and the free one is context.

Deliberately stdlib-only (urllib + json) — that IS the B0.2 spike. If this
works, the Lambda needs no `databento` client and therefore no numpy,
pandas or zstandard in the artifact.

Never records prices. Timestamps and counts only, so the samples file
carries no licensed market data and is safe to commit.

Usage:
    python scripts/aws_recon.py --probe               # free only, $0
    python scripts/aws_recon.py --probe --fetch       # + metered, quoted first
    python scripts/aws_recon.py --report              # render AWS-RECON.md
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "docs" / "aws-recon-samples.jsonl"
# The regenerable data table. The DECISION lives in AWS-RECON.md, which is
# hand-written and cites this — so re-probing can never silently rewrite a
# conclusion that a human reached.
REPORT = ROOT / "docs" / "aws-recon-latency.md"

BASE = "https://hist.databento.com/v0"
DATASET = "GLBX.MDP3"
SCHEMA = "ohlcv-1m"
SYMBOL = "MES.v.0"
STYPE = "continuous"

# Cost guard (B-C6). A tail probe is a handful of bars; anything above this
# means the request is not what we think it is, so refuse rather than spend.
MAX_COST_PER_FETCH = 0.05
FETCH_WINDOW_MIN = 30       # look back far enough to see the tail even if stale


def api_key() -> str:
    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.strip().startswith("DATABENTO_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip("'\"")
    if not key:
        sys.exit("no DATABENTO_API_KEY in environment or .env")
    return key


def _ctx() -> ssl.SSLContext:
    """python.org builds ship no CA bundle; certifi is already a dep of the
    Telegram path for exactly this reason."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _call(path: str, params: dict, key: str, *, post: bool = False):
    """One authenticated REST call. Returns (status, body_text, elapsed_s)."""
    auth = base64.b64encode(f"{key}:".encode()).decode()
    headers = {"Authorization": f"Basic {auth}",
               "Accept": "application/json"}
    body = urllib.parse.urlencode(params, doseq=True).encode()
    if post:
        req = urllib.request.Request(f"{BASE}/{path}", data=body,
                                     headers=headers, method="POST")
    else:
        req = urllib.request.Request(f"{BASE}/{path}?{body.decode()}",
                                     headers=headers)
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=60, context=_ctx()) as r:
            return r.status, r.read().decode(), time.monotonic() - t0
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400], time.monotonic() - t0
    except Exception as e:                      # network/DNS/TLS
        return 0, f"{type(e).__name__}: {e}", time.monotonic() - t0


def _parse_ts(raw) -> datetime | None:
    """Databento hands timestamps back as ISO8601 or as ns-since-epoch,
    depending on the endpoint. Accept both rather than guess."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)) or (isinstance(raw, str) and raw.isdigit()):
        return datetime.fromtimestamp(int(raw) / 1e9, tz=timezone.utc)
    s = str(raw).replace("Z", "+00:00")
    # fromisoformat rejects nanosecond precision; trim to microseconds
    if "." in s:
        head, _, tail = s.partition(".")
        digits = "".join(c for c in tail if c.isdigit())[:6]
        offset = tail[len(digits):].lstrip("0123456789")
        s = f"{head}.{digits:<06}{offset}"
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _newest_bar_ts(body: str) -> tuple[datetime | None, int]:
    """Newest ts_event across an NDJSON response, and the record count."""
    newest, n = None, 0
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        n += 1
        hd = rec.get("hd") or rec
        ts = _parse_ts(hd.get("ts_event") or rec.get("ts_event"))
        if ts and (newest is None or ts > newest):
            newest = ts
    return newest, n


def probe(key: str, *, fetch: bool) -> dict:
    now = datetime.now(timezone.utc)
    s: dict = {"probed_at": now.isoformat(timespec="seconds"),
               "et": now.astimezone().isoformat(timespec="seconds")}

    # ---- free: what does the API claim is available? ----
    status, body, elapsed = _call("metadata.get_dataset_range",
                                  {"dataset": DATASET}, key)
    s["range_status"], s["range_ms"] = status, round(elapsed * 1000)
    if status == 200:
        try:
            rng = json.loads(body)
            end = _parse_ts(rng.get("end") or (rng.get("range") or {}).get("end"))
            s["available_end"] = end.isoformat() if end else None
            if end:
                s["claimed_lag_min"] = round((now - end).total_seconds() / 60, 1)
        except json.JSONDecodeError:
            s["range_error"] = body[:200]
    else:
        s["range_error"] = body[:200]

    if not fetch:
        return s

    # ---- metered: what can a poller actually retrieve? ----
    # Anchor the window on the advertised tail, not on `now`. With a delayed
    # entitlement a now-anchored window returns zero bars and measures
    # nothing; probing across the boundary shows where data really stops.
    anchor = _parse_ts(s.get("available_end")) or now
    end_at = min(anchor, now)
    start = (end_at - timedelta(minutes=FETCH_WINDOW_MIN)).replace(microsecond=0)
    window = {"dataset": DATASET, "symbols": SYMBOL, "schema": SCHEMA,
              "stype_in": STYPE,
              "start": start.isoformat().replace("+00:00", "Z"),
              "end": end_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")}

    # quote before spend — the standing rule, enforced not remembered
    status, body, _ = _call("metadata.get_cost",
                            {**window, "mode": "historical-streaming"}, key)
    if status != 200:
        s["quote_error"] = f"{status}: {body[:200]}"
        return s
    try:
        cost = float(json.loads(body))
    except (json.JSONDecodeError, TypeError, ValueError):
        cost = float(body.strip() or 0)
    s["quoted_usd"] = round(cost, 6)
    # A2: the per-request cap below never accumulated across probes. The
    # cumulative guard is the one that actually protects the budget.
    sys.path.insert(0, str(ROOT))
    from occams import spend
    spend.check(cost, what="B0.1 latency probe")
    if cost > MAX_COST_PER_FETCH:
        s["fetch_skipped"] = f"quote ${cost:.4f} > cap ${MAX_COST_PER_FETCH}"
        return s

    status, body, elapsed = _call("timeseries.get_range",
                                  {**window, "encoding": "json",
                                   "compression": "none"}, key, post=True)
    s["fetch_status"], s["fetch_ms"] = status, round(elapsed * 1000)
    s["spent_usd"] = round(cost, 6)
    if status != 200:
        s["fetch_error"] = body[:300]
        return s
    newest, n = _newest_bar_ts(body)
    s["bars"] = n
    s["bytes"] = len(body)
    if newest:
        s["newest_bar"] = newest.isoformat()
        s["true_lag_min"] = round((now - newest).total_seconds() / 60, 1)
    return s


def _rows() -> list[dict]:
    if not SAMPLES.exists():
        return []
    return [json.loads(ln) for ln in SAMPLES.read_text().splitlines() if ln.strip()]


def report() -> None:
    rows = _rows()
    if not rows:
        sys.exit("no samples yet — run `--probe --fetch` a few times first")
    true_lags = [r["true_lag_min"] for r in rows if "true_lag_min" in r]
    spend = sum(r.get("spent_usd", 0) for r in rows)

    def et(r: dict) -> str:
        return _parse_ts(r["probed_at"]).astimezone(
            timezone(timedelta(hours=-4))).strftime("%H:%M")

    lines = [
        "# Latency samples — regenerated by `scripts/aws_recon.py --report`",
        "",
        "Raw measurement only. The decision it feeds is in `AWS-RECON.md`.",
        "",
        f"Dataset `{DATASET}` · schema `{SCHEMA}` · symbol `{SYMBOL}` "
        f"(`stype_in={STYPE}`) · historical REST API.",
        "",
        "## B0.1 — intraday availability",
        "",
        "`claimed` is `metadata.get_dataset_range().end` (free). `true` is the",
        "newest bar an actual fetch returned — the only number a poller can",
        "rely on, and the one the delay-parity rule (B-C1) is set against.",
        "",
        "| probe (ET) | claimed lag | true lag | bars | fetch ms | $ |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {et(r)} | "
            f"{r.get('claimed_lag_min', '—')} min | "
            f"{r.get('true_lag_min', r.get('fetch_error', '—') if 'fetch_status' in r else '—')}"
            f"{' min' if 'true_lag_min' in r else ''} | "
            f"{r.get('bars', '—')} | {r.get('fetch_ms', '—')} | "
            f"{r.get('spent_usd', 0):.4f} |")
    lines += ["", f"Samples: {len(rows)} · metered spend: **${spend:.4f}**", ""]
    if true_lags:
        lines += [
            f"True lag — min **{min(true_lags)}** · median "
            f"**{sorted(true_lags)[len(true_lags) // 2]}** · max "
            f"**{max(true_lags)}** minutes.", ""]
    REPORT.write_text("\n".join(lines) + "\n")
    print(f"wrote {REPORT} ({len(rows)} samples, ${spend:.4f} spent)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--fetch", action="store_true",
                    help="also run the metered probe (quoted first)")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()

    if a.report:
        report()
        return 0
    if not a.probe:
        ap.error("nothing to do — pass --probe or --report")

    s = probe(api_key(), fetch=a.fetch)
    SAMPLES.parent.mkdir(exist_ok=True)
    with SAMPLES.open("a") as f:
        f.write(json.dumps(s) + "\n")
    print(json.dumps(s, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
