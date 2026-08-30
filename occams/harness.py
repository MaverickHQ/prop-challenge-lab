"""Challenge runner + Monte Carlo — the glue from sim days to rule verdicts.

`run_challenge` chains simulate_day P&L into EOD equity marks feeding
`ChallengeState` (Phase 2.2). `monte_carlo` replays the same day-sequence
from every viable start day — passing is path-dependent, so the output is
P(pass)/P(breach)/median-days, never average return (CONTEXT §6-7).
Strategies are injected callables: TradingDay -> DayPlan | NoTrade.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from statistics import median
from typing import Callable

from typing import TYPE_CHECKING

if TYPE_CHECKING:                      # annotations only:
    import pandas as pd                # every use here is a
                                       # type hint, and
    # `from __future__ import annotations` means none of them
    # is ever evaluated. Keeping the import at module level
    # would drag pandas into the Lambda artifact for nothing
    # (B0.3). Same modules, same logic — one deferred import.

from occams.rules import ChallengeConfig, ChallengeState, Status
from occams.sim import DayPlan, simulate_day
from occams.strategy import NoTrade


@dataclass(frozen=True)
class TradingDay:
    date: date
    session_bars: pd.DataFrame          # post-range bars the sim runs on
    atr: float
    range_bars: pd.DataFrame | None = None   # the opening range (plan input)
    instrument: str = "SYN"             # identity survives the seam (Codex 1.1)


@dataclass
class ChallengeRun:
    status: Status
    final_equity: float
    days_used: int
    equity_marks: list[float] = field(default_factory=list)


MakePlan = Callable[[TradingDay], "DayPlan | NoTrade"]


def run_challenge(days: list[TradingDay], make_plan: MakePlan,
                  cfg: ChallengeConfig, costs, *,
                  events: dict | None = None) -> ChallengeRun:
    """`costs` is a single Costs or a per-instrument mapping. `events` is the
    SAME calendar mapping live uses (Codex 1.3): a blocked date advances the
    day and marks equity but never plans, never trades, never counts as a
    traded day — backtest and live share one day-universe."""
    from occams.calendar import blocked_reason
    from occams.instruments import resolve_costs

    state = ChallengeState(cfg)
    equity = float(cfg.account)
    marks: list[float] = []
    status = Status.ACTIVE
    used = 0

    for d in days:
        traded = False
        blocked = blocked_reason(d.date, events) if events else None
        if blocked is None:
            plan = make_plan(d)
            if not isinstance(plan, NoTrade):
                result = simulate_day(d.session_bars, plan,
                                      resolve_costs(costs, d.instrument))
                equity += result.day_pnl_usd
                traded = bool(result.trades)
        used += 1
        marks.append(equity)
        status = state.record_day(equity, traded=traded)
        if status is not Status.ACTIVE:
            break

    return ChallengeRun(status=status, final_equity=equity, days_used=used,
                        equity_marks=marks)


@dataclass(frozen=True)
class DayOutcome:
    """One day, simulated once (Codex 3.1): the unit the cached MC replays."""
    date: date
    pnl: float
    traded: bool


def daily_ledger(days: list[TradingDay], make_plan: MakePlan, costs,
                 *, events: dict | None = None) -> list[DayOutcome]:
    """Simulate each day exactly once. Valid because days are independent by
    construction: fixed-dollar risk, per-day plans, no cross-day state — the
    only coupling (equity) lives in the rules engine, which replays cheaply."""
    from occams.calendar import blocked_reason
    from occams.fade import FadeParams, simulate_fade_day
    from occams.instruments import resolve_costs

    out: list[DayOutcome] = []
    for d in days:
        if events and blocked_reason(d.date, events):
            out.append(DayOutcome(d.date, 0.0, False))
            continue
        plan = make_plan(d)
        if isinstance(plan, NoTrade):
            out.append(DayOutcome(d.date, 0.0, False))
            continue
        day_costs = resolve_costs(costs, d.instrument)
        if isinstance(plan, FadeParams):      # Family 2 plans carry their
            result = simulate_fade_day(d, plan, day_costs)   # own simulator
        else:
            result = simulate_day(d.session_bars, plan, day_costs)
        out.append(DayOutcome(d.date, result.day_pnl_usd,
                              bool(result.trades)))
    return out


def run_from_ledger(ledger: list[DayOutcome],
                    cfg: ChallengeConfig) -> ChallengeRun:
    """Replay the rules engine over pre-simulated days — identical to
    run_challenge by construction (equivalence pinned by test)."""
    state = ChallengeState(cfg)
    equity = float(cfg.account)
    marks: list[float] = []
    status = Status.ACTIVE
    used = 0
    for o in ledger:
        equity += o.pnl
        used += 1
        marks.append(equity)
        status = state.record_day(equity, traded=o.traded)
        if status is not Status.ACTIVE:
            break
    return ChallengeRun(status=status, final_equity=equity, days_used=used,
                        equity_marks=marks)


class ValidityError(ValueError):
    """Instrument failure — the harness produced silence, not a result
    (PREREG v2, verdict-#1 lesson): a fold whose strategies never trade
    must abort loudly and can never be read as a NO-GO."""


@dataclass(frozen=True)
class MCStats:
    n_runs: int
    p_pass: float
    p_breach: float
    median_days: int
    traded_days: int = 0    # ledger-level count — the validity signal


def null_baseline(days: list[TradingDay], params, cfg: ChallengeConfig,
                  costs, *, horizon_days: int,
                  seeds: tuple[int, ...] = (11, 12, 13, 14, 15),
                  events: dict | None = None, factory=None) -> float:
    """Mean null P(pass) over several coin-seeds (PREREG §3). `events` MUST
    match the strategy sweep (Codex #7) or G2 compares different day
    universes; one seed's luck must never move a GO/NO-GO gate. `factory`
    builds the per-seed null strategy (default: the ORB coin null; Family 2
    passes its fade-vs-follow coin)."""
    if factory is None:
        from occams.strategy import make_null_strategy as factory
    stats = [monte_carlo(days, factory(s, params, costs), cfg,
                         costs, horizon_days=horizon_days, events=events)
             for s in seeds]
    if all(st.traded_days == 0 for st in stats):
        raise ValidityError(
            "null baseline traded zero days on every seed — instrument "
            "failure (sizing/params degenerate), not a market result")
    return sum(st.p_pass for st in stats) / len(stats)


def monte_carlo(days: list[TradingDay], make_plan: MakePlan,
                cfg: ChallengeConfig, costs,
                horizon_days: int, *, events: dict | None = None) -> MCStats:
    """One attempt from every start day with a full horizon ahead of it.
    Each day is simulated ONCE (Codex 3.1); windows replay the cheap rules
    engine over ledger slices — identical results, ~horizon× faster."""
    ledger = daily_ledger(days, make_plan, costs, events=events)
    outcomes: list[ChallengeRun] = []
    for start in range(0, len(ledger) - horizon_days + 1):
        outcomes.append(run_from_ledger(ledger[start:start + horizon_days],
                                        cfg))
    n = len(outcomes)
    passes = sum(1 for r in outcomes if r.status is Status.PASSED)
    breaches = sum(1 for r in outcomes if r.status is Status.BREACHED)
    return MCStats(
        n_runs=n,
        p_pass=passes / n if n else 0.0,
        p_breach=breaches / n if n else 0.0,
        median_days=int(median(r.days_used for r in outcomes)) if n else 0,
        traded_days=sum(1 for o in ledger if o.traded),
    )


# ─── Q1: the half that was never modelled — does the money arrive? ───

@dataclass(frozen=True)
class PayoutStats:
    """P(pass) was never the objective. This is."""
    n_runs: int
    p_pass: float
    p_first_payout: float
    p_two_cycles: float
    mean_cycles_given_pass: float
    p_breach_while_funded: float
    median_days_to_payout: int

    def render(self) -> str:
        return "\n".join([
            f"  attempts              {self.n_runs:,}",
            f"  P(pass)               {self.p_pass:.4f}"
            f"        <- what we always reported",
            f"  P(first payout)       {self.p_first_payout:.4f}"
            f"        <- the actual objective",
            f"  P(two payout cycles)  {self.p_two_cycles:.4f}",
            f"  breach while funded   {self.p_breach_while_funded:.4f}"
            f"        (of those that qualified)",
            f"  median days to payout {self.median_days_to_payout}",
        ])


def monte_carlo_to_payout(days: list[TradingDay], make_plan: MakePlan,
                          cfg: ChallengeConfig, payout_cfg, costs,
                          *, horizon_days: int, funded_days: int,
                          events: dict | None = None) -> PayoutStats:
    """Chain the evaluation to the funded stage from every viable start day.

    An attempt qualifies, and then KEEPS TRADING the same strategy on the
    funded account under different rules — in particular a payout
    consistency requirement the evaluation may not have had. A strategy can
    therefore qualify comfortably and never be paid, which is exactly the
    case `ChallengeState` alone could not express.

    The funded stage replays the SAME ledger, continuing from the day after
    qualification. That is the honest continuation: it is the same strategy
    on the same market, not a fresh draw.
    """
    from occams.payout import PayoutState, PayoutStatus

    ledger = daily_ledger(days, make_plan, costs, events=events)
    n_runs = passed = first_payout = two_cycles = funded_breach = 0
    cycles_given_pass: list[int] = []
    days_to_payout: list[int] = []

    for start in range(0, len(ledger) - horizon_days + 1):
        n_runs += 1
        window = ledger[start:start + horizon_days]
        run = run_from_ledger(window, cfg)
        if run.status is not Status.PASSED:
            continue
        passed += 1

        # continue from the day AFTER qualification, same ledger
        resume = start + run.days_used
        funded = ledger[resume:resume + funded_days]
        st = PayoutState(payout_cfg)
        equity = float(payout_cfg.account)
        paid_on = None
        for i, o in enumerate(funded, start=1):
            equity += o.pnl
            status = st.record_day(equity, traded=o.traded)
            if status is PayoutStatus.PAID and paid_on is None:
                paid_on = i
            if status is PayoutStatus.BREACHED:
                funded_breach += 1
                break
        cycles_given_pass.append(st.cycles_paid)
        if st.cycles_paid >= 1:
            first_payout += 1
            days_to_payout.append(paid_on or 0)
        if st.cycles_paid >= 2:
            two_cycles += 1

    return PayoutStats(
        n_runs=n_runs,
        p_pass=passed / n_runs if n_runs else 0.0,
        p_first_payout=first_payout / n_runs if n_runs else 0.0,
        p_two_cycles=two_cycles / n_runs if n_runs else 0.0,
        mean_cycles_given_pass=(sum(cycles_given_pass) / len(cycles_given_pass)
                                if cycles_given_pass else 0.0),
        p_breach_while_funded=(funded_breach / passed if passed else 0.0),
        median_days_to_payout=(int(median(days_to_payout))
                               if days_to_payout else 0),
    )


# ─── E7: does an edge exist at all? Read it off the P(pass) curve. ───

def edge_shape(p_pass_by_risk: dict[float, float]) -> dict:
    """Classify a strategy by the SHAPE of P(pass) against risk size.

    Discovered by E2 rejecting its own hypothesis. The prediction was that
    P(pass) would peak BELOW the expectancy-maximising size; instead it rose
    monotonically (0.000, 0.009, 0.042, 0.088, 0.174 across $75-$350). The
    reason is the useful part: with NEGATIVE expectancy the only route to a
    profit target is variance, so more size buys more passes -- and far more
    breaches. An interior peak REQUIRES a positive edge, because only then
    does cutting variance preserve reach to the target while moving the
    drawdown floor further away.

    So the shape is a diagnostic for edge existence that does not depend on
    an expectancy estimate -- which matters, because expectancy is the
    quantity that has now misled this lab twice.

      monotonic increasing -> VARIANCE HARVESTING, no edge
      interior peak        -> a real edge, and the peak is where to size
    """
    if len(p_pass_by_risk) < 3:
        return {"shape": "indeterminate",
                "reason": "at least three sizes are needed to see a shape"}
    sizes = sorted(p_pass_by_risk)
    vals = [p_pass_by_risk[s] for s in sizes]
    peak = max(range(len(vals)), key=lambda i: vals[i])
    if max(vals) <= 0.0:
        return {"shape": "dead", "peak_risk": None,
                "reason": "never passes at any size"}
    if peak in (0, len(vals) - 1):
        direction = "increasing" if peak == len(vals) - 1 else "decreasing"
        return {"shape": f"monotonic {direction}", "peak_risk": sizes[peak],
                "edge": False,
                "reason": ("P(pass) is bought with variance, not edge. The "
                           "maximum sits at the boundary of the ladder, so "
                           "the ladder is measuring risk appetite rather "
                           "than skill. Widen it and the peak moves.")}
    return {"shape": "interior peak", "peak_risk": sizes[peak], "edge": True,
            "reason": ("an interior maximum implies a real edge: below the "
                       "peak the target is out of reach, above it the floor "
                       "arrives first. Size at the peak.")}
