"""Paper-campaign morning card (cron ~09:00 ET) — PAPER-PREREG §4.

Sends the day's checklist via Telegram (dormant-safe) and prints it.
Calendar-blocked days send an explicit NO-TRADE card — same day-universe
as the sealed backtests, by construction.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from occams.calendar import blocked_reason, load_events  # noqa: E402
from occams.instruments import COSTS_BY_INSTRUMENT  # noqa: E402
from occams.paper import K_STOP, RISK_USD, model_trade  # noqa: E402
from occams.telegram import send  # noqa: E402


def sizing_table(inst: str) -> str:
    """Contracts at representative range heights (extreme = boundary, the
    best case — the card reminds that a larger extreme shrinks size)."""
    costs = COSTS_BY_INSTRUMENT[inst]
    rows = []
    for h in (3, 5, 10, 15, 25, 40):
        m = model_trade(range_high=100.0 + h, range_low=100.0,
                        extreme=100.0 + h, side="short", costs=costs)
        rows.append(f"  height {h:>4} pts → {m.contracts} contracts")
    return "\n".join(rows)


def main() -> int:
    et = ZoneInfo("America/New_York")
    today = datetime.now(et).date()
    events = load_events(ROOT / "occams" / "data" / "economic_calendar.csv")
    reason = blocked_reason(today, events)
    if reason:
        card = (f"PLAN {today} — NO TRADE ({reason})\n"
                f"Calendar-blocked day. Do not log a range; the campaign "
                f"clock still runs.")
        send(card)
        print(card)
        return 0
    card = (
        f"PLAN {today} — fade campaign (protocol #4, k={K_STOP}, "
        f"${RISK_USD:.0f}/trade)\n"
        f"1. 09:45 TV clock: log ranges —\n"
        f"   /range MES <high> <low>\n"
        f"   /range MNQ <high> <low>\n"
        f"2. Alerts at both boundaries. Wait for breakout, then a 1-min\n"
        f"   CLOSE back inside → /setup INST short|long <extreme>\n"
        f"   and place: entry stop AT the boundary; stop = extreme ± "
        f"0.2×height; target = far side.\n"
        f"3. Log every fill: /fills INST entry|stop|target|eod "
        f"<price> <contracts>\n"
        f"   No setup by the close → /skip INST <reason>\n"
        f"Sizing quick-look (extreme at boundary; bigger extreme = fewer):\n"
        f"MES:\n{sizing_table('MES')}\nMNQ:\n{sizing_table('MNQ')}\n"
        f"Rules: TV bars only (no real-time peeking) · one setup per "
        f"instrument · day-flat."
    )
    send(card)
    print(card)
    return 0


if __name__ == "__main__":
    sys.exit(main())
