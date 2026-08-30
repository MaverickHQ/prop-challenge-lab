"""Tier-1 economic-calendar filter — news is a calendar problem (CONTEXT §10).

`blocked_reason(day, events)` is the whole mechanism. The seed events file
ships with published FOMC dates; the full historical assembly (NFP/CPI back
years, verified against official schedules) lands with P1 so backtests carry
zero lookahead risk.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path


def blocked_reason(day: date, events: dict[date, str]) -> str | None:
    """The name of the tier-1 event blocking `day`, or None if tradeable."""
    return events.get(day)


def load_events(csv_path: str | Path) -> dict[date, str]:
    """Read `date,event` rows (ISO dates) into the events mapping."""
    events: dict[date, str] = {}
    with open(csv_path, newline="") as fh:
        for row in csv.DictReader(fh):
            events[date.fromisoformat(row["date"].strip())] = row["event"].strip()
    return events
