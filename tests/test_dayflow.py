"""Codex 5.1 — the pure day-state machine (design: docs/day-state-machine.md).

The four sealed invariants become executable here; every rejection is a
friendly reply, and cron double-fires are idempotent BY SHAPE (self-loops),
not by care.
"""

from __future__ import annotations

from occams.dayflow import DayPhase, Reject, Transition, transition


def walk(events):
    phase = DayPhase.IDLE
    actions: list[str] = []
    for e in events:
        out = transition(phase, e)
        assert not isinstance(out, Reject), f"{e} rejected in {phase}: {out.reason}"
        phase = out.phase
        actions.extend(out.actions)
    return phase, actions


def test_terminal_trade_day_ends_reconciled() -> None:
    phase, actions = walk(["morning_cron", "range", "session_close",
                           "evening_cron", "fills"])
    assert phase is DayPhase.RECONCILED
    assert actions.count("record_day") == 1
    assert "issue_plan" in actions and "send_debrief" in actions


def test_terminal_no_trade_day_ends_reconciled() -> None:
    for opener in (["calendar_block"], ["session_close"]):
        phase, actions = walk(opener + ["evening_cron"])
        assert phase is DayPhase.RECONCILED
        assert actions.count("record_day") == 1        # traded=False path


def test_cron_double_fires_are_idempotent_self_loops() -> None:
    base = ["range", "session_close", "evening_cron", "fills"]
    noisy = ["morning_cron", "morning_cron", "range", "session_close",
             "evening_cron", "evening_cron", "evening_cron", "fills",
             "evening_cron"]
    p1, a1 = walk(base)
    p2, a2 = walk(noisy)
    assert p1 is p2 is DayPhase.RECONCILED
    # The invariant that matters: record_day exactly once, both paths.
    assert a1.count("record_day") == a2.count("record_day") == 1


def test_late_fills_on_reconciled_replace_and_resend() -> None:
    phase, _ = walk(["range", "session_close", "evening_cron", "fills"])
    out = transition(phase, "fills")                   # late correction
    assert out.phase is DayPhase.RECONCILED
    assert "recompute" in out.actions and "resend_debrief" in out.actions
    assert "record_day" not in out.actions             # never re-recorded


def test_rejections_leave_state_unchanged_and_are_friendly() -> None:
    cases = [
        (DayPhase.IDLE, "fills", "no plan"),
        (DayPhase.PLANNED, "fills", "closed"),
        (DayPhase.AWAITING_FILLS, "range", "too late"),
        (DayPhase.RECONCILED, "range", "finalised"),
        (DayPhase.NO_TRADE, "range", "NO TRADE"),
    ]
    for phase, event, fragment in cases:
        out = transition(phase, event)
        assert isinstance(out, Reject)
        assert fragment.lower() in out.reason.lower()


def test_replace_plan_pre_close_warns() -> None:
    out = transition(DayPhase.PLANNED, "range")
    assert out.phase is DayPhase.PLANNED
    assert "replace_plan" in out.actions and "warn" in out.actions


# ─── closed loop (2026-07-31): card -> ack -> fill -> exit -> recap ───

HAPPY = ["range", "setup", "ack_placed", "entry_touched", "fills_entry",
         "exit_touched", "fills_exit", "evening_cron", "fills"]


def test_closed_loop_reaches_reconciled_and_recaps_the_trade():
    phase, actions = walk(HAPPY)
    assert phase is DayPhase.RECONCILED
    assert "issue_card" in actions            # poller told the human
    assert "send_trade_recap" in actions      # per-trade recap on completion
    assert "send_debrief" in actions          # day recap at the evening cron


def test_poller_touch_events_never_book_a_price():
    """The measurement depends on this. A touch event may only ever ask the
    human to look — if it could book, drift would be zero by construction
    and the whole campaign would measure nothing."""
    for phase, event in ((DayPhase.WORKING, "entry_touched"),
                         (DayPhase.FILLED, "exit_touched")):
        r = transition(phase, event)
        assert isinstance(r, Transition)
        assert r.phase is phase, "a touch must not advance the phase"
        for a in r.actions:
            assert a.startswith("notify_"), f"{a!r} does more than notify"
        assert not any(x in r.actions for x in
                       ("book_trade", "book_pnl", "record_late_fill"))


def test_repeated_touches_and_polls_are_idempotent():
    """The poller fires every 5 minutes and a level can stay touched for
    hours. Invariant 2: replaying with double-fires yields the same state."""
    plain, _ = walk(HAPPY)
    noisy, _ = walk([e for ev in HAPPY
                     for e in (["poll", ev, "poll", ev]
                               if ev.endswith("_touched") else ["poll", ev])])
    assert plain is noisy is DayPhase.RECONCILED


def test_a_missed_card_is_a_defect_not_a_trade():
    phase, actions = walk(["range", "setup", "ack_missed"])
    assert phase is DayPhase.AWAITING_FILLS
    assert actions[-1] == "record_defect"
    assert "book_trade" not in actions


def test_a_working_order_that_never_fills_is_recorded_not_assumed():
    """Protocol #4a's stated cost: a limit fills only if price returns to
    the boundary. A no-fill is a real outcome, never a would-have-been."""
    phase, actions = walk(["range", "setup", "ack_placed", "skip"])
    assert phase is DayPhase.AWAITING_FILLS
    assert "record_no_fill" in actions and "book_trade" not in actions


def test_fills_before_acking_the_card_is_rejected_with_guidance():
    r = transition(DayPhase.CARDED, "fills")
    assert isinstance(r, Reject) and "/ack" in r.reason


def test_every_new_phase_survives_session_close_to_a_terminal_day():
    """Invariant 1: the equity record has no holes, from any phase."""
    for p in (DayPhase.CARDED, DayPhase.WORKING, DayPhase.FILLED):
        r = transition(p, "session_close")
        assert isinstance(r, Transition)
        assert r.phase is DayPhase.AWAITING_FILLS
        assert transition(r.phase, "fills").phase is DayPhase.RECONCILED
