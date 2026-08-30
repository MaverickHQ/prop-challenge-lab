"""B7.1 — the command handler: your replies drive the day forward.

Telegram commands are PULLED, not pushed, so a `/ack` typed at 09:57 would
otherwise sit unread until the next poll. This runs on its own 10-minute
weekday schedule and covers the hours the session poller does not.

Every command goes through `occams.paper.parse_command` — the SAME parser
the local path uses, so the two can never drift. Unparseable input is
rejected out loud and never guessed at: a mistyped fill would corrupt the
one number this campaign exists to measure.

**Fills come only from you.** The system tells you a level traded; the
price is always read off your Trading Panel. Nothing here ever invents one.
"""

from __future__ import annotations

from datetime import datetime, timezone

from occams.paper import (AckLog, FillLog, RangeLog, SetupLog, SkipLog,
                          model_trade, parse_command, trade_drift,
                          trading_day_of)

from aws.jobs import COSTS, INSTRUMENTS, _advance, _send

OFFSET_KEY = "logs/offset.txt"

HELP = (
    "Cards arrive automatically. You reply:\n"
    "/ack <SYM> placed | missed <reason> | partial <n> <reason>\n"
    "/fills <SYM> entry|stop|target|eod <price> <contracts>\n"
    "/skip <SYM> <reason>\n"
    "/status - today so far\n"
    "/week /month /all - recaps\n"
    "\nAck records what HAPPENED, never what you preferred - there is no\n"
    "way to decline a card on judgement, by design."
)


def _fmt_money(x: float) -> str:
    return f"{'+' if x >= 0 else '-'}${abs(x):,.2f}"


def _trade_recap(inst: str, st: dict, fill: FillLog) -> str:
    """Actual vs the sealed engine, for the trade just completed.

    The model is re-derived from the SAME logged levels the card came from,
    so drift isolates execution — the difference between what you got and
    what the engine assumed you would get."""
    card = st.get("card") or {}
    entry_actual = st.get("entry_price")
    if entry_actual is None or not card:
        return (f"{inst} exit logged, but no entry fill is on record - "
                f"drift cannot be computed for this trade.")
    costs = COSTS[inst]
    model = model_trade(range_high=card["range_high"],
                        range_low=card["range_low"],
                        extreme=card["extreme"], side=card["side"],
                        costs=costs)
    drift = trade_drift(model, entry_actual=entry_actual,
                        exit_event=fill.event, exit_actual=fill.price,
                        contracts=fill.contracts, costs=costs)
    direction = 1.0 if card["side"] == "long" else -1.0
    pts = (fill.price - entry_actual) * direction
    pnl = fill.contracts * (pts * costs.multiplier
                            - 2 * costs.commission_per_side)
    # Persisted so every later recap reads the SAME number the human was
    # shown at the time — a recap that recomputes can silently disagree
    # with what was sent.
    st["drift"] = round(drift, 2)
    st["pnl"] = round(pnl, 2)
    return (f"{inst} TRADE COMPLETE ({fill.event})\n"
            f"  you    {entry_actual} -> {fill.price}  x{fill.contracts}"
            f"   {_fmt_money(pnl)}\n"
            f"  model  {model.entry} -> "
            f"{model.exit_price(fill.event) or fill.price}\n"
            f"  drift  {_fmt_money(drift)}   (actual minus model)\n"
            f"Sample is still small - early expectancy lies, optimistically.")


def apply_command(text: str, doc: dict, day_str: str) -> str | None:
    """One message -> at most one state change and one reply."""
    rec = parse_command(text)
    if rec is None:
        low = text.strip().lower()
        if low.startswith("/help") or low in ("hello", "hi", "/start"):
            return HELP
        if low.startswith("/status"):
            return _status(doc, day_str)
        for cmd, days, label in (("/week", 7, "week"),
                                 ("/month", 31, "month"),
                                 ("/all", None, "since inception")):
            if low.startswith(cmd):
                return _period(doc, day_str, days, label)
        if low.startswith("/"):
            return f"Unrecognised: {text.strip()!r}\n\n{HELP}"
        return None

    inst = rec.instrument
    if inst not in INSTRUMENTS:
        return f"Unknown instrument {inst!r} - expected one of {INSTRUMENTS}."
    from aws import state
    st = state.day(doc, day_str, inst)

    if isinstance(rec, AckLog):
        if rec.state == "placed":
            before = st["phase"]
            _advance(st, "ack_placed")
            if st["phase"] == before:
                return (f"{inst} is {before} - nothing to acknowledge yet.")
            return f"{inst} acknowledged as PLACED. Watching the entry level."
        _advance(st, "ack_missed")
        st["defect"] = rec.reason
        return (f"{inst} recorded as MISSED: {rec.reason}\n"
                f"This stays in the denominator as a process defect - it is "
                f"not a trade avoided.")

    if isinstance(rec, FillLog):
        if rec.event == "entry":
            st["entry_price"] = rec.price
            st["contracts"] = rec.contracts
            st["filled_at"] = datetime.now(timezone.utc).isoformat()
            _advance(st, "fills_entry")
            return (f"{inst} entry {rec.price} x{rec.contracts} recorded. "
                    f"Watching stop and target.")
        _advance(st, "fills_exit")
        st["exit_price"] = rec.price
        st["exit_event"] = rec.event
        return _trade_recap(inst, st, rec)

    if isinstance(rec, SkipLog):
        _advance(st, "skip")
        st["skip_reason"] = rec.reason
        return f"{inst} skipped: {rec.reason}"

    if isinstance(rec, (RangeLog, SetupLog)):
        # The poller already computed these; your copy is kept as the
        # human-side record so the two can be compared later.
        st.setdefault("human", {})[type(rec).__name__] = text.strip()
        return None                     # silent: no need to buzz twice

    return None


def _period(doc: dict, day_str: str, days: int | None, label: str) -> str:
    """`/all` spans whatever the ledger holds; the others look back a fixed
    window. Either way the recap states its own sample size first."""
    from datetime import date as _date

    from aws import recap
    if days is None:
        window = sorted(doc)
    else:
        window = recap.days_back(_date.fromisoformat(day_str), days)
    return recap.period(doc, window, label)


def _status(doc: dict, day_str: str) -> str:
    lines = [f"Status {day_str}"]
    for inst in INSTRUMENTS:
        st = (doc.get(day_str) or {}).get(inst) or {}
        phase = st.get("phase", "idle")
        card = st.get("card")
        line = f"  {inst}: {phase}"
        if card:
            line += (f" | {card['side']} {card['contracts']}x @{card['entry']}"
                     f" stop {card['stop']} target {card['target']}")
        if st.get("entry_price"):
            line += f" | filled {st['entry_price']}"
        lines.append(line)
    if len(lines) == 1:
        lines.append("  nothing yet today")
    return "\n".join(lines)


def run_commands(now_et: datetime | None = None) -> dict:
    from zoneinfo import ZoneInfo

    from aws import notify, state
    now_et = now_et or datetime.now(ZoneInfo("America/New_York"))
    day_str = trading_day_of(now_et).isoformat()

    import os
    if not os.environ.get("STATE_BUCKET"):
        return {"job": "command", "skipped": "STATE_BUCKET is not configured"}

    offset = _load_offset()
    updates = notify.fetch_updates(offset)
    if not updates:
        return {"job": "command", "processed": 0, "offset": offset}

    replies: list[str] = []
    for attempt in range(3):
        doc, etag = state.load()
        replies = []
        for _uid, _ts, text in updates:
            reply = apply_command(text, doc, day_str)
            if reply:
                replies.append(reply)
        if state.save(doc, etag):
            break

    for r in replies:
        _send(r)
    # Advance the offset only AFTER the state write and the replies land.
    # Doing it first would drop a command permanently on any failure; doing
    # it last means the worst case is a duplicate reply, which is recoverable.
    _save_offset(max(u[0] for u in updates) + 1)
    return {"job": "command", "processed": len(updates),
            "replies": len(replies)}


def _load_offset() -> int:
    import os

    import boto3
    try:
        body = boto3.client("s3").get_object(
            Bucket=os.environ["STATE_BUCKET"], Key=OFFSET_KEY)["Body"].read()
        return int(body.decode().strip() or 0)
    except Exception:
        return 0


def _save_offset(offset: int) -> None:
    import os

    import boto3
    boto3.client("s3").put_object(Bucket=os.environ["STATE_BUCKET"],
                                  Key=OFFSET_KEY, Body=str(offset).encode())
