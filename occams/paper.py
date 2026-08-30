"""Paper-campaign core (PAPER-PREREG, protocol #4) — pure logic.

The human is the sensor: `/range`, `/setup`, `/fills`, `/skip` messages
are the day's ground truth. The model side re-derives what the sealed
engine (k_stop = 0.2, unfiltered) would have done from the SAME logged
levels, and drift = actual P&L − model P&L per completed trade. IO
(Telegram, state, vault) lives in the scripts; everything here is
deterministic and tested.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from occams.sim import Costs

K_STOP = 0.2          # sealed cell (PAPER-PREREG §2) — never changed here
RISK_USD = 175.0
MAX_CONTRACTS = 30


def trading_day_of(now_et: datetime) -> date:
    """The trading day an evening debrief should process. A debrief that
    fires on next-morning wake (after ET midnight) must target YESTERDAY,
    not the calendar date at runtime: anything before 09:00 ET belongs to
    the previous session (now − 9h)."""
    return (now_et - timedelta(hours=9)).date()


# ─── Telegram command grammar ───

@dataclass(frozen=True)
class RangeLog:
    instrument: str
    high: float
    low: float


@dataclass(frozen=True)
class SetupLog:
    instrument: str
    side: str             # "short" (faded up-break) | "long"
    extreme: float


@dataclass(frozen=True)
class FillLog:
    instrument: str
    event: str            # "entry" | "stop" | "target" | "eod"
    price: float
    contracts: int


@dataclass(frozen=True)
class SkipLog:
    instrument: str
    reason: str


@dataclass(frozen=True)
class AckLog:
    """Execution reality for a card — NEVER a veto (B7-N1).

    `placed` / `missed <reason>` / `partial <n> <reason>` record what
    happened, not what was preferred. A command that let a setup be
    declined on judgement would turn the sealed mechanical strategy into a
    discretionary one and void the measurement: the first week already
    showed the best-geometry trade losing and the worst winning, so a human
    veto is provably noise. Missed cards stay in the denominator as process
    defects.
    """
    instrument: str
    state: str            # "placed" | "missed" | "partial"
    contracts: int | None = None
    reason: str = ""


TICK = 0.25          # MES and MNQ both quote in 0.25 increments


def _on_tick(*prices: float) -> bool:
    """Prices must sit on the instrument's tick grid. A typo'd level
    (live catch 2026-07-30: 7399.55) would silently corrupt the model's
    range, stop and size, making drift measure typing rather than
    execution."""
    return all(abs(round(p / TICK) * TICK - p) < 1e-9 for p in prices)


def parse_command(text: str):
    """One Telegram message → one log record, or None (never guess)."""
    parts = text.strip().split()
    if not parts:
        return None
    try:
        cmd = parts[0].lower()
        if cmd == "/range" and len(parts) == 4:
            hi, lo = float(parts[2]), float(parts[3])
            if not _on_tick(hi, lo):
                return None
            return RangeLog(parts[1].upper(), hi, lo)
        if cmd == "/setup" and len(parts) == 4 \
                and parts[2].lower() in ("short", "long"):
            ext = float(parts[3])
            if not _on_tick(ext):
                return None
            return SetupLog(parts[1].upper(), parts[2].lower(), ext)
        if cmd == "/fills" and len(parts) == 5 \
                and parts[2].lower() in ("entry", "stop", "target", "eod"):
            px = float(parts[3])
            if not _on_tick(px):
                return None
            return FillLog(parts[1].upper(), parts[2].lower(), px,
                           int(parts[4]))
        if cmd == "/skip" and len(parts) >= 3:
            return SkipLog(parts[1].upper(), " ".join(parts[2:]))
        if cmd == "/ack" and len(parts) >= 3:
            state = parts[2].lower()
            if state == "placed" and len(parts) == 3:
                return AckLog(parts[1].upper(), "placed")
            if state == "missed" and len(parts) >= 4:
                return AckLog(parts[1].upper(), "missed",
                              reason=" ".join(parts[3:]))
            if state == "partial" and len(parts) >= 5:
                # a partial must say how many AND why — an unexplained
                # partial is indistinguishable from a typo'd size
                return AckLog(parts[1].upper(), "partial",
                              contracts=int(parts[3]),
                              reason=" ".join(parts[4:]))
            return None                    # unknown ack: reject, never guess
    except ValueError:
        return None
    return None


# ─── The model side (must equal occams/fade.py arithmetic) ───

@dataclass(frozen=True)
class ModelTrade:
    side: str
    entry: float
    stop_level: float
    target: float
    contracts: int
    _slip: float

    def exit_price(self, event: str) -> float | None:
        adverse = self._slip if self.side == "short" else -self._slip
        if event == "stop":
            return self.stop_level + adverse
        if event == "target":
            return self.target + adverse
        return None                    # eod: model books the actual price


def model_trade(*, range_high: float, range_low: float, extreme: float,
                side: str, costs: Costs,
                k_stop: float = K_STOP, risk_usd: float = RISK_USD
                ) -> ModelTrade:
    """The sealed engine's prices/sizing from logged levels — mirrors
    fade.simulate_fade_day: entry at the boundary with adverse slippage,
    stop = extreme ± k×height, target = the far side, true-risk sizing."""
    height = range_high - range_low
    slip = costs.slippage
    if side == "short":
        boundary, sgn = range_high, -1.0
    else:
        boundary, sgn = range_low, 1.0
    ext = (extreme - range_high) if side == "short" \
        else (range_low - extreme)
    stop_dist = ext + k_stop * height
    entry = boundary + sgn * slip
    stop_level = boundary - sgn * stop_dist
    target = boundary + sgn * height
    loss_pts = abs(stop_level - entry) + slip
    per_contract = loss_pts * costs.multiplier \
        + 2 * costs.commission_per_side
    contracts = min(int(risk_usd // per_contract), MAX_CONTRACTS)
    return ModelTrade(side=side, entry=entry, stop_level=stop_level,
                      target=target, contracts=contracts, _slip=slip)


def _pnl(side: str, entry: float, exit_: float, contracts: int,
         costs: Costs) -> float:
    direction = 1.0 if side == "long" else -1.0
    points = (exit_ - entry) * direction
    return contracts * (points * costs.multiplier
                        - 2 * costs.commission_per_side)


def trade_drift(model: ModelTrade, *, entry_actual: float,
                exit_event: str, exit_actual: float, contracts: int,
                costs: Costs) -> float:
    """Implementation shortfall for one completed trade: actual P&L minus
    the model's P&L for the SAME events. EOD exits carry no model price
    (we don't hold the venue's closing tape) — the model books the actual
    exit, so EOD drift isolates the entry side."""
    model_exit = model.exit_price(exit_event)
    if model_exit is None:
        model_exit = exit_actual
    actual = _pnl(model.side, entry_actual, exit_actual, contracts, costs)
    modeled = _pnl(model.side, model.entry, model_exit, contracts, costs)
    return actual - modeled
