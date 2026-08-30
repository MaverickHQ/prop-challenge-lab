"""B2.1/B2.2 — the DataSource port and its delay-matched adapters.

**B-C1, delay parity, is enforced here and nowhere else.** PAPER-PREREG §3
rule 1 forbids acting on any price the venue's own delayed tape has not yet
shown. The paper venue is TradingView's free tier, ~10 minutes behind, so
the poller must never see a bar fresher than that — a fresher bar would
flatter every fill and void the parity measurement the campaign exists to
make.

The chosen source makes that nearly free rather than merely enforced:
Yahoo's `MES=F`/`MNQ=F` are themselves delayed ~10.0 minutes (measured,
B0.1), and their 09:30-09:45 opening range matched CME to the tick on 12
of 12 sessions (B0.5). So parity holds by construction and `_cutoff` is a
backstop against a source that speeds up, not the mechanism.

Stdlib only — no `databento` client, no pandas (B0.2/B0.3).
"""

from __future__ import annotations

import json
import ssl
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Protocol
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
VENUE_DELAY_MINUTES = 10
_YAHOO = ("https://query1.finance.yahoo.com/v8/finance/chart/"
          "{sym}?interval=1m&range={days}d")
SYMBOLS = {"MES": "MES=F", "MNQ": "MNQ=F"}


@dataclass(frozen=True)
class Bar:
    """One 1-minute bar. `ts` is the bar's OPEN time, in ET — the same
    convention the Pine aid and the sealed engine use, so a bar in
    [09:30, 09:45) belongs to the opening range."""
    ts: datetime
    open: float
    high: float
    low: float
    close: float

    @property
    def closed_at(self) -> datetime:
        return self.ts + timedelta(minutes=1)


class DataSource(Protocol):
    def bars(self, instrument: str, day: date) -> list[Bar]:
        """1-minute bars for `day`, never fresher than the venue delay."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DelayMatched:
    """Mixin holding the one rule every adapter must obey."""

    def __init__(self, *, venue_delay_minutes: int = VENUE_DELAY_MINUTES,
                 now: Callable[[], datetime] = _utcnow) -> None:
        self.venue_delay_minutes = venue_delay_minutes
        self._now = now

    def _cutoff(self) -> datetime:
        return self._now() - timedelta(minutes=self.venue_delay_minutes)

    def _visible(self, bars: list[Bar]) -> list[Bar]:
        """A bar is visible only once it has CLOSED at or before the
        cutoff. Using the open time would leak the final `delay` minutes
        of a bar that is still forming."""
        cutoff = self._cutoff()
        return [b for b in bars if b.closed_at <= cutoff]


class YahooDelayed(DelayMatched):
    """Paper-campaign source (B0.5). Delayed ~10 min at origin."""

    def __init__(self, *, lookback_days: int = 1, **kw) -> None:
        super().__init__(**kw)
        self.lookback_days = lookback_days

    def _fetch(self, instrument: str) -> list[Bar]:
        sym = SYMBOLS.get(instrument.upper())
        if sym is None:
            raise ValueError(f"unmapped instrument {instrument!r}")
        url = _YAHOO.format(sym=urllib.parse.quote(sym),
                            days=self.lookback_days)
        req = urllib.request.Request(url, headers={"User-Agent":
                                                   "Mozilla/5.0"})
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            res = json.loads(r.read())["chart"]["result"][0]
        return _rows_to_bars(res["timestamp"], res["indicators"]["quote"][0])

    def bars(self, instrument: str, day: date) -> list[Bar]:
        rows = [b for b in self._fetch(instrument) if b.ts.date() == day]
        return self._visible(rows)


class ReplaySource(DelayMatched):
    """Deterministic source over pre-recorded bars — tests and the
    historical replay that verifies the poller against known days. No
    network, so a test can never depend on what the market did today."""

    def __init__(self, bars_by_instrument: dict[str, list[Bar]], **kw) -> None:
        super().__init__(**kw)
        self._bars = bars_by_instrument

    def bars(self, instrument: str, day: date) -> list[Bar]:
        rows = [b for b in self._bars.get(instrument.upper(), [])
                if b.ts.date() == day]
        return self._visible(rows)


def _rows_to_bars(stamps, quote) -> list[Bar]:
    out: list[Bar] = []
    for i, ep in enumerate(stamps):
        o, hi, lo, c = (quote["open"][i], quote["high"][i],
                        quote["low"][i], quote["close"][i])
        if None in (o, hi, lo, c):
            continue                      # Yahoo pads gaps with nulls
        out.append(Bar(datetime.fromtimestamp(ep, tz=timezone.utc)
                       .astimezone(ET), float(o), float(hi), float(lo),
                       float(c)))
    return out


def bars_from_fixture(payload: dict) -> dict[str, list[Bar]]:
    """{'MES': [[epoch, o, h, l, c], ...]} -> {'MES': [Bar, ...]}"""
    return {
        inst: [Bar(datetime.fromtimestamp(r[0], tz=timezone.utc)
                   .astimezone(ET), r[1], r[2], r[3], r[4]) for r in rows]
        for inst, rows in payload.items()
    }
