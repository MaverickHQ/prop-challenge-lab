"""Vendor CSV loader + data-quality probe (Phase 1.2/1.3).

Built before the purchase so P1 is plug-in. One boundary, three jobs:
1. `read_vendor_csv` — parse either vendor shape (UTC `ts_event` or naive
   `datetime`), enforce the tz contract (naive requires an explicit
   `naive_tz` — review fix #5), validate (sorted, no duplicates, sane OHLC),
   and return an America/New_York-aware frame.
2. `to_trading_days` — RTH-filter, split the opening range, size the ATR
   from PRIOR days only (no lookahead), exclude short sessions.
3. `quality_report` — what P1's first hour looks at: span, per-day bar
   counts, short sessions, missing business days.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd

from occams.harness import TradingDay
from occams.sessions import rth_only, split_opening_range, to_eastern

_TIME_COLUMNS = ("ts_event", "datetime", "timestamp", "date")
_OHLCV = ["open", "high", "low", "close", "volume"]


def read_vendor_csv(path: str | Path, naive_tz: str | None = None
                    ) -> pd.DataFrame:
    raw = pd.read_csv(path)
    raw.columns = [c.strip().lower() for c in raw.columns]
    tcol = next((c for c in _TIME_COLUMNS if c in raw.columns), None)
    if tcol is None:
        raise ValueError(f"no timestamp column found (looked for {_TIME_COLUMNS})")

    ts = pd.to_datetime(raw[tcol])
    if ts.dt.tz is None:
        if naive_tz is None:
            raise ValueError(
                "naive timestamps in vendor file: pass naive_tz explicitly "
                "(e.g. 'America/New_York' for FirstRate-style files) — "
                "refusing to guess (review fix #5)")
        ts = ts.dt.tz_localize(naive_tz)

    missing = [c for c in _OHLCV if c not in raw.columns]
    if missing:
        raise ValueError(f"missing OHLCV columns: {missing}")

    keep = _OHLCV + [c for c in ("symbol", "instrument_id") if c in raw.columns]
    df = raw[keep].copy()
    df.index = pd.DatetimeIndex(ts)
    df = df.sort_index()
    if df.index.duplicated().any():
        dupes = df.index[df.index.duplicated()][:3]
        raise ValueError(f"duplicate timestamps in vendor file: {list(dupes)}")

    bad = (df["high"] < df[["open", "close"]].max(axis=1)) | \
          (df["low"] > df[["open", "close"]].min(axis=1)) | \
          (df[["open", "high", "low", "close"]] <= 0).any(axis=1)
    if bad.any():
        raise ValueError(f"impossible OHLC rows at {list(df.index[bad][:3])}")

    return to_eastern(df)


def _daily_frames(df_eastern: pd.DataFrame) -> dict[date, pd.DataFrame]:
    rth = rth_only(df_eastern)
    return {d: g for d, g in rth.groupby(rth.index.date)}


def _atr_by_day(daily: dict[date, pd.DataFrame], period: int) -> dict[date, float]:
    """SMA of daily true range, using PRIOR days only — day N's ATR never
    sees day N (no lookahead)."""
    days = sorted(daily)
    tr: list[float] = []
    out: dict[date, float] = {}
    prev_close: float | None = None
    for i, d in enumerate(days):
        if len(tr) >= period:
            window = tr[-period:]
            out[d] = sum(window) / period
        g = daily[d]
        hi, lo, cl = g["high"].max(), g["low"].min(), float(g["close"].iloc[-1])
        ranges = [hi - lo]
        if prev_close is not None:
            ranges += [abs(hi - prev_close), abs(lo - prev_close)]
        tr.append(max(ranges))
        prev_close = cl
    return out


def _roll_days(daily: dict[date, pd.DataFrame]) -> list[date]:
    """Days whose dominant instrument_id differs from the previous day's —
    the contract rolled into this session (Codex 1.2). Day-flat trading is
    otherwise roll-immune; only the cross-roll gap pollutes stats."""
    out: list[date] = []
    prev_id = None
    for d in sorted(daily):
        g = daily[d]
        if "instrument_id" not in g.columns:
            return []
        cur = g["instrument_id"].iloc[-1]
        if prev_id is not None and cur != prev_id:
            out.append(d)
        prev_id = cur
    return out


def to_trading_days(df_eastern: pd.DataFrame, *, range_minutes: int,
                    atr_period: int = 14, min_bars: int = 300,
                    instrument: str | None = None) -> list[TradingDay]:
    if instrument is None:
        if "symbol" in df_eastern.columns:
            symbols = set(df_eastern["symbol"].unique())
            if len(symbols) != 1:
                raise ValueError(
                    f"frame holds {sorted(symbols)} — to_trading_days takes a "
                    f"single instrument; split by symbol first (Codex 1.1)")
            instrument = str(symbols.pop())
        else:
            instrument = "SYN"
    daily = _daily_frames(df_eastern)
    atr = _atr_by_day(daily, atr_period)
    rolls = set(_roll_days(daily))
    days: list[TradingDay] = []
    for d in sorted(daily):
        g = daily[d]
        if d in rolls:
            continue                     # roll day — excluded, reported
        if len(g) < min_bars:
            continue                     # short session — excluded, reported
        if d not in atr:
            continue                     # no full prior-ATR window yet
        range_bars, session_bars = split_opening_range(g, range_minutes)
        if range_bars.empty or session_bars.empty:
            continue
        days.append(TradingDay(date=d, session_bars=session_bars,
                               atr=atr[d], range_bars=range_bars,
                               instrument=instrument))
    return days


def check_definitions(defs: pd.DataFrame, instrument: str, costs) -> None:
    """Assert vendor definition metadata against our Costs — identity is a
    test, not an assumption (Codex 1.2 / task 1.4)."""
    col = "symbol" if "symbol" in defs.columns else "raw_symbol"
    rows = defs[defs[col].astype(str).str.startswith(instrument)]
    if rows.empty:
        raise ValueError(f"definition missing for {instrument!r}")
    row = rows.iloc[0]
    tick = float(row["min_price_increment"])
    mult = float(row["multiplier"])
    if tick != costs.tick_size or mult != costs.multiplier:
        raise ValueError(
            f"definition mismatch for {instrument}: vendor says tick={tick} "
            f"multiplier={mult}, Costs say tick={costs.tick_size} "
            f"multiplier={costs.multiplier}")


@dataclass(frozen=True)
class QualityReport:
    first_day: date
    last_day: date
    n_days: int
    short_sessions: list[date] = field(default_factory=list)
    missing_days: list[date] = field(default_factory=list)
    roll_days: list[date] = field(default_factory=list)

    def render(self) -> str:
        return (f"{self.first_day} → {self.last_day}: {self.n_days} sessions, "
                f"{len(self.short_sessions)} short, "
                f"{len(self.roll_days)} roll days excluded, "
                f"{len(self.missing_days)} missing business days")


def quality_report(df_eastern: pd.DataFrame, *, min_bars: int = 300
                   ) -> QualityReport:
    daily = _daily_frames(df_eastern)
    days = sorted(daily)
    rolls = _roll_days(daily)
    short = [d for d in days if len(daily[d]) < min_bars and d not in rolls]
    expected = [ts.date() for ts in
                pd.bdate_range(days[0], days[-1])]
    missing = [d for d in expected if d not in daily]
    return QualityReport(first_day=days[0], last_day=days[-1],
                         n_days=len(days), short_sessions=short,
                         missing_days=missing, roll_days=rolls)
