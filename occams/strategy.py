"""ORB plan builder + risk sizing — pure functions (CONTEXT §5).

`build_plan(range_bars, params, costs)` turns a completed opening range into
a sized `DayPlan`, or a `NoTrade(reason)`. Sizing is the ruin math made
concrete: fixed dollar risk ÷ dollar stop distance, floored, capped at the
venue position limit. PREREG v2: the stop is ORB-native — a multiple of the
opening-range HEIGHT — so stop and risk budget share intraday units at any
volatility (verdict #1 was voided by daily-ATR stops sizing to 0 contracts).
"""

from __future__ import annotations

from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:                      # annotations only:
    import pandas as pd                # every use here is a
                                       # type hint, and
    # `from __future__ import annotations` means none of them
    # is ever evaluated. Keeping the import at module level
    # would drag pandas into the Lambda artifact for nothing
    # (B0.3). Same modules, same logic — one deferred import.

from occams.sim import Costs, DayPlan


@dataclass(frozen=True)
class OrbParams:
    stop_range: float      # stop distance as a multiple of the range HEIGHT
    target_r: float        # target as a multiple of the stop distance
    risk_usd: float        # fixed dollar risk per trade (from the ruin math)
    max_trades: int = 1
    vwap_filter: bool = False
    # The risk manager's own daily stop (Codex 2.1) — carried into every
    # generated plan so the sealed control is ACTIVE, not aspirational.
    daily_stop_usd: float | None = None
    # Venue position limit: 3 minis = 30 micros (P3 sealed values). Narrow
    # ranges size UP under fixed-$ risk; the cap must bind in the builder.
    max_contracts: int = 30


def per_contract_risk(stop_dist: float, costs: Costs) -> float:
    """TRUE dollars lost by one stopped contract (Codex 2.3): stop distance
    plus exit slippage, in dollars, plus both commissions. (Entry slippage is
    already inside the fill; the bracket is relative to the fill.)"""
    slip_pts = costs.slippage_ticks * costs.tick_size
    return (stop_dist + slip_pts) * costs.multiplier + 2 * costs.commission_per_side


@dataclass(frozen=True)
class NoTrade:
    reason: str


def _sized(stop_dist: float, params: OrbParams, costs: Costs) -> int | NoTrade:
    """Shared sizing guardrail: sub-tick stops are unexecutable, zero
    contracts is a stand-aside, the venue cap always binds."""
    if stop_dist < costs.tick_size:
        return NoTrade(reason="stop below one tick — unexecutable")
    contracts = int(params.risk_usd // per_contract_risk(stop_dist, costs))
    if contracts < 1:
        return NoTrade(reason="true risk per contract exceeds risk budget")
    return min(contracts, params.max_contracts)


def build_plan(range_bars: pd.DataFrame, params: OrbParams,
               costs: Costs) -> DayPlan | NoTrade:
    if range_bars.empty:
        return NoTrade(reason="empty opening range")   # review fix #10: no NaNs
    range_high = float(range_bars["high"].max())
    range_low = float(range_bars["low"].min())
    height = range_high - range_low
    if height <= 0:
        return NoTrade(reason="degenerate opening range (zero height)")
    stop_dist = params.stop_range * height
    contracts = _sized(stop_dist, params, costs)
    if isinstance(contracts, NoTrade):
        return contracts

    buy_stop: float | None = range_high + costs.tick_size
    sell_stop: float | None = range_low - costs.tick_size
    if params.vwap_filter:
        if "volume" not in range_bars.columns:
            raise ValueError(
                "vwap_filter requires a volume column — refusing a silent "
                "time-weighted fallback (Codex 4.1); real vendor bars carry "
                "volume, synthetic fixtures must add it")
        typical = (range_bars["high"] + range_bars["low"] + range_bars["close"]) / 3
        vol = range_bars["volume"].astype(float)
        vwap = float((typical * vol).sum() / vol.sum())   # actual VWAP
        last_close = float(range_bars["close"].iloc[-1])
        if last_close > vwap:
            sell_stop = None   # trade only with the VWAP side
        elif last_close < vwap:
            buy_stop = None

    return DayPlan(
        buy_stop=buy_stop,
        sell_stop=sell_stop,
        stop_dist=stop_dist,
        target_dist=params.target_r * stop_dist,
        contracts=contracts,
        max_trades=params.max_trades,
        daily_stop_usd=params.daily_stop_usd,
    )


def make_orb_strategy(params: OrbParams, costs):
    """TradingDay -> plan adapter for the harness (plans off day.range_bars).
    `costs` may be a single Costs or a per-instrument mapping (Codex 1.1)."""
    from occams.instruments import resolve_costs

    def make_plan(day):
        if day.range_bars is None or day.range_bars.empty:
            return NoTrade(reason="no opening range available")
        day_costs = resolve_costs(costs, day.instrument)
        return build_plan(day.range_bars, params=params, costs=day_costs)
    return make_plan


def make_null_strategy(seed: int, params: OrbParams, costs: Costs):
    """Random entries under the SAME risk manager — the null model. A coin
    flips the side; the entry stop sits 1 tick beyond the first post-range
    price so it triggers in ordinary noise; stop/target/sizing identical to
    ORB. Any P(pass) this achieves is geometry, not edge (CONTEXT §2.1).

    Review fix #4: the coin is a pure function of (seed, calendar date) —
    the same day always gets the same side, so overlapping Monte-Carlo
    windows agree, results are replayable, and ORB-vs-null is day-pairable."""
    import numpy as np

    from occams.instruments import resolve_costs

    def make_plan(day):
        day_costs = resolve_costs(costs, day.instrument)
        if day.range_bars is None or day.range_bars.empty:
            return NoTrade(reason="no opening range available")
        height = (float(day.range_bars["high"].max())
                  - float(day.range_bars["low"].min()))
        if height <= 0:
            return NoTrade(reason="degenerate opening range (zero height)")
        first_open = float(day.session_bars.iloc[0]["open"])
        stop_dist = params.stop_range * height
        contracts = _sized(stop_dist, params, day_costs)
        if isinstance(contracts, NoTrade):
            return contracts
        day_rng = np.random.default_rng([seed, day.date.toordinal()])
        go_long = bool(day_rng.random() < 0.5)
        return DayPlan(
            buy_stop=first_open + day_costs.tick_size if go_long else None,
            sell_stop=None if go_long else first_open - day_costs.tick_size,
            stop_dist=stop_dist,
            target_dist=params.target_r * stop_dist,
            contracts=contracts,
            max_trades=params.max_trades,
        )
    return make_plan
