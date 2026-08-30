"""Phase 9.1 (partial) — Plan Card, Debrief and fuel gauge as pure text
builders. Transports (Telegram/Obsidian) are thin adapters added at P2/P4;
everything meaningful is testable here without a token.
"""

from __future__ import annotations

from occams.report import debrief, fuel_gauge, plan_card
from occams.sim import DayPlan
from occams.strategy import NoTrade


def test_plan_card_states_orders_and_size() -> None:
    plan = DayPlan(buy_stop=5010.25, sell_stop=4989.75, stop_dist=8.0,
                   target_dist=12.0, contracts=2, max_trades=1)
    card = plan_card(plan, day="2026-07-03")
    assert "5010.25" in card and "4989.75" in card
    assert "2 contracts" in card
    assert "stop 8.0" in card and "target 12.0" in card


def test_plan_card_no_trade_shows_reason() -> None:
    card = plan_card(NoTrade(reason="FOMC"), day="2026-07-29")
    assert "NO TRADE" in card and "FOMC" in card


def test_fuel_gauge_shows_position_between_floor_and_target() -> None:
    g = fuel_gauge(equity=51_200.0, floor=49_200.0, target_equity=53_000.0)
    assert "51,200" in g and "49,200" in g and "53,000" in g
    # halfway markers: gauge must reflect progress order (floor < eq < target)
    assert g.index("49,200") < g.index("51,200") < g.index("53,000")


def test_debrief_includes_gauge_day_pnl_and_status() -> None:
    text = debrief(day="2026-07-03", day_pnl=57.50, equity=50_057.50,
                   floor=48_000.0, target_equity=53_000.0, status="active",
                   fills_logged=False)
    assert "+$57.50" in text
    assert "active" in text
    assert "/fills" in text            # missing fills → reconcile nudge


def test_debrief_includes_parity_summary_when_supplied() -> None:
    # Codex 5.2: the exceptional-project metric belongs in the nightly record.
    text = debrief(day="2026-07-04", day_pnl=57.50, equity=50_057.50,
                   floor=48_000.0, target_equity=53_000.0, status="active",
                   fills_logged=True, parity_n=12, mean_drift=-4.25,
                   mean_abs_drift=6.10)
    assert "12 trades" in text
    assert "−$4.25" in text or "-$4.25" in text
    assert "$6.10" in text


def test_debrief_surfaces_parity_kill_reason() -> None:
    text = debrief(day="2026-07-04", day_pnl=0.0, equity=50_000.0,
                   floor=48_000.0, target_equity=53_000.0, status="active",
                   fills_logged=True, parity_kill_reason="dispersion exceeds $50")
    assert "PARITY KILL" in text and "dispersion" in text


def test_debrief_without_parity_keeps_simple_output() -> None:
    text = debrief(day="2026-07-04", day_pnl=0.0, equity=50_000.0,
                   floor=48_000.0, target_equity=53_000.0, status="active",
                   fills_logged=True)
    assert "parity" not in text.lower()
