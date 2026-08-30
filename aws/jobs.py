"""B3.2 — the poll job: bars in, cards and nudges out.

One pass per invocation, per instrument. Everything decided here is a pure
function of the visible bars (`occams.poller`) driven through the day state
machine (`occams.dayflow`); this module is the shell that fetches, persists
and sends.

**Idempotency is the whole design.** The schedule fires every 5 minutes and
a level stays touched for hours, so every send is recorded in `sent` and
never repeated. Re-running any invocation must change nothing.

**It never books a fill.** A `*_touched` event only ever asks the human to
read their Trading Panel. See docs/day-state-machine.md.
"""

from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from occams import cards
from occams.dayflow import (DayPhase, Transition,
                             transition)
from occams.feed import YahooDelayed
from occams.paper import RISK_USD, trading_day_of
from occams.poller import (detect_setup, entry_touched, exit_touched,
                           opening_range)
from occams.sim import Costs

INSTRUMENTS = ("MES", "MNQ")
COSTS = {
    "MES": Costs(multiplier=5.0, tick_size=0.25, commission_per_side=1.25,
                 slippage_ticks=1),
    "MNQ": Costs(multiplier=2.0, tick_size=0.25, commission_per_side=1.25,
                 slippage_ticks=1),
}


def _send(text: str) -> None:
    from aws import notify
    notify.send(text)


def _once(st: dict, tag: str, text: str) -> None:
    """Send `text` unless this tag already went out today. The poller runs
    ~75 times a session; without this the phone would buzz on every pass."""
    if tag in st["sent"]:
        return
    _send(text)
    st["sent"].append(tag)


def _advance(st: dict, event: str) -> tuple[DayPhase, tuple[str, ...]]:
    out = transition(DayPhase(st["phase"]), event)
    if isinstance(out, Transition):
        st["phase"] = out.phase.value
        return out.phase, out.actions
    return DayPhase(st["phase"]), ()          # Reject: state untouched


def poll_instrument(instrument: str, st: dict, day, source) -> None:
    bars = source.bars(instrument, day)
    # Counted even on an empty pass: the dead-man's switch (B4.1) needs to
    # distinguish "the poller ran and saw nothing" from "the poller never
    # ran", which otherwise look identical from the outside.
    st["polls"] = st.get("polls", 0) + 1
    if not bars:
        return
    st["last_bar"] = max(b.ts for b in bars).isoformat()
    _advance(st, "poll")

    rng = opening_range(bars)
    if rng is None or not rng.complete:
        return                                 # range still forming

    if st["phase"] == DayPhase.IDLE.value:
        _advance(st, "range")
        _once(st, "range", cards.range_card(instrument, rng.high, rng.low))

    card = detect_setup(bars, rng, COSTS[instrument], instrument=instrument)
    if card is None:
        return
    # range_high/low are stored because the drift calculation re-derives
    # the model from the SAME levels the card came from.
    st["card"] = {"side": card.side, "entry": card.entry, "stop": card.stop,
                  "target": card.target, "contracts": card.contracts,
                  "extreme": card.extreme,
                  "range_high": card.range_high,
                  "range_low": card.range_low,
                  "fired_at": card.fired_at.isoformat()}

    if st["phase"] == DayPhase.PLANNED.value:
        _advance(st, "setup")
        _once(st, "card", card.telegram())
        if card.stand_aside:                   # nothing to watch
            _advance(st, "skip")
        return

    # --- WORKING: the entry limit is live; has it traded? ---
    if st["phase"] == DayPhase.WORKING.value:
        when = entry_touched(bars, card)
        if when:
            _advance(st, "entry_touched")
            _once(st, "entry",
                  cards.fill_prompt(instrument, "entry", card.entry,
                                    f"{when:%H:%M}", card.contracts))
        return

    # --- FILLED: watching stop and target ---
    if st["phase"] == DayPhase.FILLED.value and st.get("filled_at"):
        filled_at = datetime.fromisoformat(st["filled_at"])
        hit = exit_touched(bars, card, filled_at=filled_at)
        if hit:
            kind, when = hit
            level = card.stop if kind == "stop" else card.target
            _advance(st, "exit_touched")
            _once(st, f"exit_{kind}",
                  cards.fill_prompt(instrument, kind, level,
                                    f"{when:%H:%M}", card.contracts))


def run_poll(now_et: datetime | None = None) -> dict:
    from aws import state
    now_et = now_et or datetime.now(ZoneInfo("America/New_York"))
    day = trading_day_of(now_et)

    # A Lambda without its state bucket cannot poll. Say so plainly rather
    # than raising a KeyError from deep inside the S3 client — a
    # misconfigured deploy should be readable in CloudWatch at a glance.
    if not os.environ.get("STATE_BUCKET"):
        return {"job": "poll", "date": day.isoformat(),
                "skipped": "STATE_BUCKET is not configured"}

    # The schedule runs 09:00-16:55 ET because a cron cannot express
    # "from 09:45". Nothing can happen before the opening range is both
    # complete AND visible through the delay (09:44 bar closes 09:45,
    # visible ~09:55), so return before fetching rather than making a
    # dozen pointless requests a day and courting a rate limit.
    if (now_et.hour, now_et.minute) < (9, 50):
        return {"job": "poll", "date": day.isoformat(),
                "skipped": "before the range can be visible"}

    delay = int(os.environ.get("VENUE_DELAY_MINUTES", 10))
    source = YahooDelayed(venue_delay_minutes=delay)

    for attempt in range(3):                   # ETag race: re-read, retry
        doc, etag = state.load()
        for inst in INSTRUMENTS:
            poll_instrument(inst, state.day(doc, day.isoformat(), inst),
                            day, source)
        if state.save(doc, etag):
            break
    return {"job": "poll", "date": day.isoformat(),
            "phases": {i: state.day(doc, day.isoformat(), i)["phase"]
                       for i in INSTRUMENTS}}


def run_morning(now_et: datetime | None = None) -> dict:
    """B3.1 — the pre-market card. Needs no market data: the calendar is
    the sealed 259-row file that ships in the package, so the day-universe
    is identical to the backtests by construction."""
    import os
    from pathlib import Path

    from occams.calendar import blocked_reason, load_events

    from aws import state
    now_et = now_et or datetime.now(ZoneInfo("America/New_York"))
    day = trading_day_of(now_et)
    # BOTH must be a weekday. trading_day_of maps anything before 09:00 ET
    # to the previous session, so on a Saturday morning it returns Friday
    # and the mapped date alone would happily send a Friday card two days
    # late. Caught by invoking it manually on a Saturday.
    if day.weekday() >= 5 or now_et.weekday() >= 5:
        return {"job": "morning", "skipped": "weekend"}

    events = load_events(Path(__file__).resolve().parent.parent
                         / "occams" / "data" / "economic_calendar.csv")
    reason = blocked_reason(day, events)

    if reason:
        text = (f"NO TRADE {day} - {reason}\n"
                f"Calendar block. No entries on either instrument today.")
    else:
        text = (f"Plan for {day}\n"
                f"  09:30-09:45 ET  range forms\n"
                f"  then           first breakout, then a 1m CLOSE back "
                f"inside\n"
                f"  entry          LIMIT at the boundary (protocol #4a)\n"
                f"  stop           extreme +/- 0.2 x height | target far "
                f"side\n"
                f"  risk           ${int(RISK_USD)}/trade, 30-micro cap\n"
                f"Cards arrive automatically. Reply /ack <SYM> "
                f"placed|missed <reason>.")

    if not os.environ.get("STATE_BUCKET"):
        return {"job": "morning", "text": text,
                "skipped": "STATE_BUCKET is not configured"}

    for _ in range(3):
        doc, etag = state.load()
        sent_any = False
        for inst in INSTRUMENTS:
            st = state.day(doc, day.isoformat(), inst)
            if reason:
                _advance(st, "calendar_block")
            if "morning" not in st["sent"]:
                st["sent"].append("morning")
                sent_any = True
        if state.save(doc, etag):
            break
    if sent_any:
        _send(text)
    return {"job": "morning", "date": day.isoformat(),
            "blocked": reason, "sent": sent_any}


def _export_day(doc: dict, day_str: str) -> None:
    """Copy one reconciled day into the research archive, write-once.

    Re-running the debrief must not fail on an already-exported day, so an
    existing key is a no-op rather than an error -- the archive's write-once
    refusal is the right behaviour there, not a fault to surface."""
    import json
    import tempfile
    from pathlib import Path as _P

    from occams import archive
    payload = json.dumps({day_str: doc.get(day_str, {})}, indent=1)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        fh.write(payload)
        tmp = _P(fh.name)
    try:
        archive.put(tmp, f"experiments/campaign/{day_str}.json",
                    source="campaign",
                    note="reconciled day, exported as immutable evidence")
    except FileExistsError:
        pass                                    # already exported; fine
    finally:
        tmp.unlink(missing_ok=True)


def run_evening(now_et: datetime | None = None) -> dict:
    """B3.3 — the debrief. Pulls any outstanding commands first, so a fill
    typed at 16:05 is in the recap rather than in tomorrow's."""
    import os

    from aws import commands, recap, state
    now_et = now_et or datetime.now(ZoneInfo("America/New_York"))
    day = trading_day_of(now_et)
    if not os.environ.get("STATE_BUCKET"):
        return {"job": "evening", "skipped": "STATE_BUCKET is not configured"}

    commands.run_commands(now_et)

    for _ in range(3):
        doc, etag = state.load()
        health = {"polls": 0, "last_bar_age_min": "?"}
        for inst in INSTRUMENTS:
            st = state.day(doc, day.isoformat(), inst)
            health["polls"] = max(health["polls"], st.get("polls", 0))
            if st.get("last_bar"):
                age = (now_et - datetime.fromisoformat(st["last_bar"]))
                health["last_bar_age_min"] = int(age.total_seconds() // 60)
            _advance(st, "session_close")
            _advance(st, "evening_cron")
        text = recap.daily(doc, day.isoformat(), health)
        if state.save(doc, etag):
            break
    _send(text)

    # A4: each reconciled day is exported to the DURABLE archive as
    # immutable evidence. Operational state stays in the campaign bucket --
    # it is the running system's working memory and moving it would take the
    # poller down (D0.1). This copies; it never relocates.
    try:
        _export_day(doc, day.isoformat())
    except Exception as e:                      # never fail a debrief on it
        log_note = f"archive export failed: {type(e).__name__}: {e}"
        _send(f"NOTE: {log_note}")

    # B7.5: the weekly recap auto-posts on Friday. Waiting to be asked
    # means the week you most need to see it is the week you forget.
    weekly = None
    if day.weekday() == 4:
        weekly = recap.period(doc, recap.days_back(day, 7), "week")
        _send(weekly)
    return {"job": "evening", "date": day.isoformat(),
            "polls": health["polls"], "weekly": weekly is not None}
