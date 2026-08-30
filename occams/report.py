"""Plan Card, Debrief and the fuel gauge — pure text builders (CONTEXT §9).

The UI is two pushed documents a day, not an application. These builders are
transport-agnostic: Telegram/Obsidian adapters (P2/P4) just send the strings.
"""

from __future__ import annotations

from occams.sim import DayPlan
from occams.strategy import NoTrade

GAUGE_WIDTH = 20


def plan_card(plan: DayPlan | NoTrade, day: str) -> str:
    if isinstance(plan, NoTrade):
        return f"📋 Plan {day}\nNO TRADE: {plan.reason}"
    lines = [f"📋 Plan {day} — {plan.contracts} contracts"]
    if plan.buy_stop is not None:
        lines.append(f"  ▲ buy stop {plan.buy_stop}")
    if plan.sell_stop is not None:
        lines.append(f"  ▼ sell stop {plan.sell_stop}")
    lines.append(f"  bracket: stop {plan.stop_dist} / target {plan.target_dist}"
                 f" · max {plan.max_trades} trade(s)")
    return "\n".join(lines)


def fuel_gauge(equity: float, floor: float, target_equity: float) -> str:
    """Where equity sits between the ratchet floor and the target — the one
    graphic the whole system revolves around. Reads left→right as floor →
    equity → target so the eye lands on the number that's moving."""
    span = max(target_equity - floor, 1e-9)
    pos = min(max((equity - floor) / span, 0.0), 1.0)
    filled = round(pos * GAUGE_WIDTH)
    bar = "█" * filled + "░" * (GAUGE_WIDTH - filled)
    return (f"⛽ floor {floor:,.0f} · equity {equity:,.0f} · "
            f"target {target_equity:,.0f} ({pos:.0%})\n"
            f"   |{bar}|")


def debrief(day: str, day_pnl: float, equity: float, floor: float,
            target_equity: float, status: str, fills_logged: bool,
            parity_n: int | None = None, mean_drift: float | None = None,
            mean_abs_drift: float | None = None,
            parity_kill_reason: str | None = None) -> str:
    sign = "+" if day_pnl >= 0 else "−"
    lines = [
        f"🌙 Debrief {day} — {status}",
        f"   day P&L {sign}${abs(day_pnl):,.2f}",
        fuel_gauge(equity, floor, target_equity),
    ]
    if parity_n is not None:
        dsign = "−" if (mean_drift or 0) < 0 else "+"
        lines.append(
            f"🎯 parity over {parity_n} trades: drift {dsign}$"
            f"{abs(mean_drift or 0):,.2f}/trade · dispersion $"
            f"{mean_abs_drift or 0:,.2f}/trade")
    if parity_kill_reason:
        lines.append(f"🛑 PARITY KILL: {parity_kill_reason}")
    if not fills_logged:
        lines.append("⚠️ no fills logged — this is the sim-only view; "
                     "reply /fills to reconcile")
    return "\n".join(lines)
