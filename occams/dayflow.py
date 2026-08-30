"""The trading-day state machine — pure core (docs/day-state-machine.md).

One tiny machine per trading date, driven by an unreliable human + retrying
crons. Explicit transitions make the idempotency provable: cron events are
self-loops, late /fills is a self-loop on RECONCILED, and every illegal
event is a Reject whose reason becomes a friendly Telegram reply. No FSM
library (XState rejected: wrong language, oversized; Python FSM libs: a
dependency for ~50 lines). The persisted value is the enum string, never an
object. Webhook/cron handlers are thin adapters around `transition`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DayPhase(Enum):
    IDLE = "idle"
    NO_TRADE = "no_trade"
    PLANNED = "planned"
    # --- closed loop (2026-07-31): PLANNED used to span the whole session,
    # so nothing existed between "range known" and "session closed". These
    # three split that span so the poller can drive a card -> ack -> fill ->
    # exit cycle and tell the human when to look.
    CARDED = "carded"            # setup fired, card sent, awaiting /ack
    WORKING = "working"          # acked placed; watching the entry limit
    FILLED = "filled"            # entry fill reported; watching stop/target
    AWAITING_FILLS = "awaiting_fills"
    RECONCILED = "reconciled"


@dataclass(frozen=True)
class Transition:
    phase: DayPhase
    actions: tuple[str, ...] = ()


@dataclass(frozen=True)
class Reject:
    reason: str


def transition(phase: DayPhase, event: str) -> Transition | Reject:
    P, T, R = DayPhase, Transition, Reject

    if phase is P.IDLE:
        if event == "morning_cron":
            return T(P.IDLE, ("nudge_range",))              # self-loop
        if event == "poll":
            # The poller runs from 09:45 and is what DETECTS the range, so
            # it necessarily fires at least once while the day is still
            # idle. Erroring there would make the first poll of every day
            # a failure.
            return T(P.IDLE, ())                            # idempotent no-op
        if event == "calendar_block":
            return T(P.NO_TRADE, ("announce_no_trade",))
        if event == "range":
            return T(P.PLANNED, ("issue_plan",))
        if event == "session_close":
            return T(P.NO_TRADE, ("mark_no_range",))
        if event == "fills":
            return R("no plan was issued today")

    elif phase is P.PLANNED:
        if event == "range":
            return T(P.PLANNED, ("replace_plan", "warn"))   # self-loop
        if event in ("morning_cron", "poll"):
            return T(P.PLANNED, ())                         # idempotent no-op
        if event == "setup":
            return T(P.CARDED, ("issue_card", "notify"))
        if event == "skip":
            return T(P.AWAITING_FILLS, ("record_skip",))
        if event == "session_close":
            return T(P.AWAITING_FILLS, ())
        if event == "fills":
            return R("session isn't closed yet")

    elif phase is P.CARDED:
        if event == "poll":
            return T(P.CARDED, ())                          # idempotent no-op
        if event == "setup":
            return T(P.CARDED, ())        # one setup/day — never re-card
        if event == "ack_placed":
            return T(P.WORKING, ("watch_entry",))
        if event == "ack_missed":
            # B7-N1: an ack records reality, never preference. A missed
            # setup is a process defect and stays in the denominator; it is
            # NOT a trade avoided, whichever way the day then went.
            return T(P.AWAITING_FILLS, ("record_defect",))
        if event == "skip":
            return T(P.AWAITING_FILLS, ("record_skip",))
        if event == "session_close":
            return T(P.AWAITING_FILLS, ("record_defect",))
        if event == "fills":
            return R("acknowledge the card first: /ack <SYM> placed|missed")

    elif phase is P.WORKING:
        if event in ("poll", "ack_placed"):
            return T(P.WORKING, ())                         # idempotent no-op
        if event == "entry_touched":
            # The poller saw the limit level trade. It does NOT know or
            # record your fill — reporting a computed price would make
            # drift zero by construction. This only says "go look".
            return T(P.WORKING, ("notify_check_entry_fill",))  # self-loop
        if event == "fills_entry":
            return T(P.FILLED, ("watch_exit",))
        if event == "skip":
            return T(P.AWAITING_FILLS, ("record_no_fill",))
        if event == "session_close":
            return T(P.AWAITING_FILLS, ("nudge_fills",))

    elif phase is P.FILLED:
        if event in ("poll", "fills_entry"):
            return T(P.FILLED, ())                          # idempotent no-op
        if event == "exit_touched":
            return T(P.FILLED, ("notify_check_exit_fill",))    # self-loop
        if event == "fills_exit":
            # The trade is complete: book it and send the per-trade recap
            # immediately. The DAY still reconciles at the evening cron.
            return T(P.AWAITING_FILLS,
                     ("book_trade", "send_trade_recap"))
        if event == "session_close":
            return T(P.AWAITING_FILLS, ("nudge_eod_exit_fill",))

    elif phase is P.AWAITING_FILLS:
        if event in ("poll", "session_close"):
            return T(P.AWAITING_FILLS, ())                  # idempotent no-op
        if event in ("fills_entry", "fills_exit"):
            return T(P.AWAITING_FILLS, ("record_late_fill",))
        if event == "evening_cron":
            return T(P.AWAITING_FILLS,                      # self-loop
                     ("provisional_debrief", "nudge_fills"))
        if event == "fills":
            return T(P.RECONCILED,
                     ("book_pnl", "record_day", "update_parity",
                      "send_debrief"))
        if event == "range":
            return R("too late for today's session")

    elif phase is P.NO_TRADE:
        if event == "evening_cron":
            return T(P.RECONCILED, ("record_day", "send_debrief"))
        if event == "range":
            return R("NO TRADE today")
        if event == "fills":
            return R("NO TRADE today — no fills expected")
        if event in ("session_close", "poll"):
            return T(P.NO_TRADE, ())                        # idempotent no-op

    elif phase is P.RECONCILED:
        if event == "fills":
            return T(P.RECONCILED,                          # self-loop
                     ("replace_fills", "recompute", "resend_debrief"))
        if event in ("evening_cron", "session_close", "morning_cron",
                     "poll"):
            return T(P.RECONCILED, ())                      # idempotent no-op
        if event == "range":
            return R("day is finalised")

    return R(f"event {event!r} is not valid in phase {phase.value!r}")
