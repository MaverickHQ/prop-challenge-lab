"""Paper-campaign evening debrief (cron ~17:00 ET) — PAPER-PREREG §4/§5.

Pulls the day's Telegram logs, re-derives the model side from the logged
levels, computes per-trade drift, updates the append-only state, checks
the sealed kill thresholds, and sends + vaults the Debrief. Idempotent:
re-running a day REPLACES its records (late /fills → recompute + resend).
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from occams.instruments import COSTS_BY_INSTRUMENT  # noqa: E402
from occams.obsidian import debrief_dir, write_debrief_note  # noqa: E402
from occams.paper import (FillLog, RangeLog, SetupLog, SkipLog,  # noqa: E402
                          model_trade, parse_command, trade_drift,
                          trading_day_of)
from occams.state import StateStore  # noqa: E402
from occams.telegram import fetch_updates, send  # noqa: E402

STATE = ROOT / "data" / "paper_state.json"
OFFSET = ROOT / "data" / "paper_offset.txt"
LOGS = ROOT / "data" / "paper_logs.jsonl"     # raw append-only audit trail
CAMPAIGN_START = "2026-07-29"                  # cron live 2026-07-28
ET = ZoneInfo("America/New_York")


def _et_date(unix_ts: int) -> str:
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc) \
        .astimezone(ET).date().isoformat()


def pull_new_logs() -> None:
    """Fetch new Telegram updates into the raw audit trail (append-only)."""
    import json
    offset = int(OFFSET.read_text()) if OFFSET.exists() else 0
    updates = fetch_updates(offset)
    if not updates:
        return
    with open(LOGS, "a") as fh:
        for uid, ts, text in updates:
            fh.write(json.dumps({"update_id": uid, "date": _et_date(ts),
                                 "text": text}) + "\n")
    OFFSET.parent.mkdir(exist_ok=True)
    OFFSET.write_text(str(max(u[0] for u in updates) + 1))


def day_records(day: str) -> list:
    import json
    if not LOGS.exists():
        return []
    out = []
    for line in LOGS.read_text().splitlines():
        rec = json.loads(line)
        if rec["date"] == day:
            parsed = parse_command(rec["text"])
            if parsed is not None:
                out.append(parsed)
    return out


def main() -> int:
    today = trading_day_of(datetime.now(ET)).isoformat()
    pull_new_logs()
    records = day_records(today)

    ranges = {r.instrument: r for r in records if isinstance(r, RangeLog)}
    setups = {r.instrument: r for r in records if isinstance(r, SetupLog)}
    skips = {r.instrument: r for r in records if isinstance(r, SkipLog)}
    fills: dict[str, dict[str, FillLog]] = {}
    for r in records:
        if isinstance(r, FillLog):
            fills.setdefault(r.instrument, {})[r.event] = r

    drifts: list[float] = []
    lines: list[str] = []
    for inst in ("MES", "MNQ"):
        if inst in skips:
            lines.append(f"{inst}: no setup — {skips[inst].reason}")
            continue
        if inst not in ranges:
            lines.append(f"{inst}: NO LOG (process defect if it traded)")
            continue
        f = fills.get(inst, {})
        entry = f.get("entry")
        exit_ = next((f[e] for e in ("stop", "target", "eod") if e in f),
                     None)
        if inst not in setups or entry is None or exit_ is None:
            lines.append(f"{inst}: incomplete log "
                         f"(range={inst in ranges} setup={inst in setups} "
                         f"entry={entry is not None} exit={exit_ is not None})"
                         f" — resend /fills and re-run")
            continue
        costs = COSTS_BY_INSTRUMENT[inst]
        m = model_trade(range_high=ranges[inst].high,
                        range_low=ranges[inst].low,
                        extreme=setups[inst].extreme,
                        side=setups[inst].side, costs=costs)
        d = trade_drift(m, entry_actual=entry.price,
                        exit_event=exit_.event, exit_actual=exit_.price,
                        contracts=entry.contracts, costs=costs)
        drifts.append(d)
        size_note = "" if entry.contracts == m.contracts else \
            f" (SIZE MISMATCH: logged {entry.contracts} vs model "\
            f"{m.contracts})"
        lines.append(f"{inst}: {setups[inst].side} {entry.contracts}x — "
                     f"exit {exit_.event} — drift ${d:+.2f}{size_note}")

    store = StateStore(STATE)
    state = store.load()
    state.set_day_drifts(today, drifts)
    state.record_processed(today, trades=len(drifts))
    store.save(state)

    log = state.parity_log(kill_threshold_usd=5.0,
                           min_trades_before_kill=10,
                           abs_kill_threshold_usd=10.0)
    n_days = len(state.processed_days)
    status = (f"n={log.n} trades · mean drift ${log.mean_drift:+.2f} · "
              f"mean |drift| ${log.mean_abs_drift:.2f} · day {n_days} "
              f"since {CAMPAIGN_START}")
    if log.kill:
        status += f"\n*** KILL THRESHOLD FIRED: {log.reason} *** " \
                  f"Campaign over per PAPER-PREREG §5 — stop trading, " \
                  f"write-up begins."
    body = f"DEBRIEF {today} (protocol #4)\n" + "\n".join(lines) \
        + f"\n{status}"
    send(body)
    print(body)
    try:
        write_debrief_note(debrief_dir(ROOT / ".env"), day=today, body=body)
    except Exception as exc:                       # vault is best-effort
        print(f"[vault note skipped: {exc}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
