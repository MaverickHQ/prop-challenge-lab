"""OCO bracket-order day simulator — dollar P&L, conservative fills.

One deep function: `simulate_day(bars_1m, plan, costs) -> DayResult`.
Fill conventions (each pinned by a test):
- Entry stops trigger on the bar's high/low crossing the level; fill at the
  level (or the worse open on a gap) plus slippage against us.
- Bracket levels are relative to the actual entry fill (platform-style
  attached orders).
- Target is a limit: fills AT the limit when crossed, no slippage.
- Protective stop is a market on touch: fills at the level (or worse open on
  a gap) with slippage against us.
- Commission is charged per side, per contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from typing import TYPE_CHECKING

if TYPE_CHECKING:                      # annotations only:
    import pandas as pd                # every use here is a
                                       # type hint, and
    # `from __future__ import annotations` means none of them
    # is ever evaluated. Keeping the import at module level
    # would drag pandas into the Lambda artifact for nothing
    # (B0.3). Same modules, same logic — one deferred import.


@dataclass(frozen=True)
class Costs:
    multiplier: float
    tick_size: float
    commission_per_side: float
    slippage_ticks: int

    @property
    def slippage(self) -> float:
        return self.slippage_ticks * self.tick_size


@dataclass(frozen=True)
class DayPlan:
    buy_stop: float | None      # None = side disarmed (e.g. VWAP filter)
    sell_stop: float | None
    stop_dist: float
    target_dist: float
    contracts: int
    max_trades: int = 1
    # Our OWN daily stop (tighter than any venue guard): once the day's
    # realized P&L is at or below −daily_stop_usd, no further entries.
    daily_stop_usd: float | None = None


@dataclass
class Trade:
    side: str  # "long" | "short"
    entry_price: float
    exit_price: float | None = None
    pnl_usd: float | None = None


@dataclass
class DayResult:
    trades: list[Trade] = field(default_factory=list)
    day_pnl_usd: float = 0.0


def _close_trade(trade: Trade, exit_price: float, plan: DayPlan,
                 costs: Costs) -> None:
    trade.exit_price = exit_price
    direction = 1.0 if trade.side == "long" else -1.0
    points = (exit_price - trade.entry_price) * direction
    commissions = 2 * costs.commission_per_side * plan.contracts
    trade.pnl_usd = points * costs.multiplier * plan.contracts - commissions


def simulate_day(bars_1m: pd.DataFrame, plan: DayPlan, costs: Costs) -> DayResult:
    result = DayResult()
    open_trade: Trade | None = None
    stop_level = target_level = 0.0
    entries_dead = False   # ambiguous both-entry bar kills the day (Codex 2.4)

    def enter(side: str, level: float, bar: pd.Series) -> Trade:
        nonlocal stop_level, target_level
        if side == "long":
            fill = max(level, bar["open"]) + costs.slippage
            stop_level, target_level = fill - plan.stop_dist, fill + plan.target_dist
        else:
            fill = min(level, bar["open"]) - costs.slippage
            stop_level, target_level = fill + plan.stop_dist, fill - plan.target_dist
        return Trade(side=side, entry_price=fill)

    for _ts, bar in bars_1m.iterrows():
        if open_trade is None:
            # Both entry stops are armed while flat (OCO: a fill disarms both;
            # exits re-arm them until max_trades is spent).
            if entries_dead or len(result.trades) >= plan.max_trades:
                continue
            if plan.daily_stop_usd is not None:
                realized = sum(t.pnl_usd or 0.0 for t in result.trades)
                if realized <= -plan.daily_stop_usd:
                    continue  # own daily stop: done trading today
            # Codex 2.4: a flat-state bar touching BOTH armed entry levels is
            # unresolvable from OHLC (which side fired first?). The old code
            # silently chose long. Conservative, pre-registered rule: stand
            # aside for the rest of the day. Not triggered when one side is
            # disarmed — then only one entry could have happened.
            if (plan.buy_stop is not None and plan.sell_stop is not None
                    and bar["high"] >= plan.buy_stop
                    and bar["low"] <= plan.sell_stop):
                entries_dead = True
                continue
            if plan.buy_stop is not None and bar["high"] >= plan.buy_stop:
                open_trade = enter("long", plan.buy_stop, bar)
                result.trades.append(open_trade)
            elif plan.sell_stop is not None and bar["low"] <= plan.sell_stop:
                open_trade = enter("short", plan.sell_stop, bar)
                result.trades.append(open_trade)
            # Conservative same-bar rule (review fix #1): intra-bar order is
            # unknowable, so if the ENTRY bar also touches the protective
            # stop, assume the adverse move came after entry → stopped. The
            # target never fills on the entry bar (its favourable extreme may
            # pre-date the entry). Stop fills at the level ± slip — no gap
            # logic, because the open pre-dates the entry.
            if open_trade is not None:
                if open_trade.side == "long" and bar["low"] <= stop_level:
                    _close_trade(open_trade, stop_level - costs.slippage,
                                 plan, costs)
                    open_trade = None
                elif open_trade.side == "short" and bar["high"] >= stop_level:
                    _close_trade(open_trade, stop_level + costs.slippage,
                                 plan, costs)
                    open_trade = None
            continue

        # Exits: protective stop (market, slips) checked before target (limit)
        # — the conservative both-touched rule.
        if open_trade.side == "long":
            if bar["low"] <= stop_level:
                _close_trade(open_trade,
                             min(stop_level, bar["open"]) - costs.slippage,
                             plan, costs)
                open_trade = None
            elif bar["high"] >= target_level:
                _close_trade(open_trade, target_level, plan, costs)
                open_trade = None
        else:
            if bar["high"] >= stop_level:
                _close_trade(open_trade,
                             max(stop_level, bar["open"]) + costs.slippage,
                             plan, costs)
                open_trade = None
            elif bar["low"] <= target_level:
                _close_trade(open_trade, target_level, plan, costs)
                open_trade = None

    # Session end: never hold overnight — market-flat at the final close.
    if open_trade is not None:
        last_close = float(bars_1m.iloc[-1]["close"])
        slip = costs.slippage if open_trade.side == "long" else -costs.slippage
        _close_trade(open_trade, last_close - slip, plan, costs)

    result.day_pnl_usd = sum(t.pnl_usd or 0.0 for t in result.trades)
    return result
