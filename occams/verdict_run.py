"""The verdict orchestrator — the single sealed chain P1-day runs end-to-end.

Every piece already exists and is tested; this wires them in the exact
PREREG order and refuses to deviate:

  per instrument:  split walk-forward (dev / OOS / lockbox)
                   → sweep OOS + sweep lockbox (both stamped with the hash)
                   → null_baseline on each
                   → verdict(OOS, lockbox) must clear the gates on BOTH
  across instruments:  combined_verdict — every split passes independently
  on GO only:      economics gate (E[attempts]×fee vs funded value)

No new logic, only orchestration + a rendered report. The command-line
entry (Phase 8) will call `run_verdict` with real days from the loader.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from occams.harness import TradingDay, null_baseline
from occams.rules import ChallengeConfig
from occams.search import (Gates, GridAxis, Sweep, SweepCell, Verdict,
                           combined_verdict, sweep, verdict)
from occams.strategy import OrbParams, make_orb_strategy


@dataclass(frozen=True)
class Protocol:
    grid: dict[str, tuple]                 # every sealed axis (Codex #6)
    gates: Gates
    cfg: ChallengeConfig
    horizon_days: int
    risk_usd: float
    daily_stop_usd: float | None = None    # carried into plans (Codex #9)
    oos_frac: float = 0.2
    lockbox_frac: float = 0.2
    funded_value: float = 0.0              # economics gate input (Codex #8)
    # Verified 2026-07-05 (RULES.md §4.1): the cost unit is TIME — a
    # $119 subscription month plus a $109 reset per failed attempt.
    monthly_fee: float = 119.0
    reset_fee: float = 109.0
    # Family selector: "orb" (Family 1, closed) or "fade" (Family 2).
    family: str = "orb"
    # Cadence-matched funded value (PREREG v3): sealed dict keyed by
    # whether the winner is width-filtered — deterministic, no post-hoc
    # choice. None -> the flat funded_value applies.
    funded_value_by_filter: dict | None = None
    prereg_hash: str = ""
    null_seeds: tuple[int, ...] = (11, 12, 13, 14, 15)


@dataclass
class SplitReport:
    instrument: str
    verdict: Verdict
    oos_winner: object = None
    lockbox_winner: object = None
    oos_null: float = 0.0
    lockbox_null: float = 0.0
    dev_span: tuple[date, date] | None = None
    oos_span: tuple[date, date] | None = None
    lockbox_span: tuple[date, date] | None = None


@dataclass
class VerdictReport:
    decision: str
    reason: str
    prereg_hash: str
    per_instrument: dict[str, SplitReport] = field(default_factory=dict)
    economics: dict | None = None

    def render(self) -> str:
        lines = [f"# Verdict: {self.decision}",
                 f"protocol {self.prereg_hash} · {self.reason}", ""]
        for inst, sr in sorted(self.per_instrument.items()):
            w = sr.lockbox_winner
            pp = f"{w.p_pass:.2f}" if w else "—"
            lines.append(f"## {inst}: {sr.verdict.decision}")
            lines.append(f"- OOS null {sr.oos_null:.2f} · lockbox P(pass) {pp}")
            if w:
                lines.append(f"- winner params: {w.params}")
        if self.economics:
            e = self.economics
            lines += ["", "## Economics",
                      f"- E[attempts]={e['expected_attempts']:.2f} · "
                      f"median {e['median_days']}d ≈ "
                      f"{e['months_per_attempt']}mo/attempt · "
                      f"E[cost]=${e['expected_cost']:.0f} vs funded "
                      f"${e['funded_value']:.0f} "
                      f"({'clears' if e['cleared'] else 'FAILS'} 2× gate)"]
        return "\n".join(lines)


def expected_cost(p_pass: float, median_days: int,
                  monthly_fee: float, reset_fee: float) -> float:
    """Time-based attempt economics (RULES.md §4.1). Each attempt runs
    ~median_days trading days ≈ ceil(median_days/21) subscription months;
    every failed attempt buys one reset. Geometric E[attempts] = 1/p."""
    if p_pass <= 0:
        return float("inf")
    attempts = 1.0 / p_pass
    months_per_attempt = max(1, -(-median_days // 21))     # ceil, ≥1
    return attempts * months_per_attempt * monthly_fee \
        + (attempts - 1.0) * reset_fee


def funded_value_for(winner_params: dict, by_filter: dict | None,
                     default: float = 0.0) -> float:
    """Sealed cadence rule: a width-filtered winner trades ~3x less often,
    so its funded value is the 'filtered' figure; unfiltered -> 'open'."""
    if by_filter is None:
        return default
    key = "filtered" if winner_params.get("width_max") is not None else "open"
    return float(by_filter[key])


def _cell_params(cell: dict, risk_usd: float,
                 daily_stop_usd: float | None) -> OrbParams:
    """Every ORB axis from a grid cell (Codex #6/#9). range_minutes is applied
    at the loader (day split), not here."""
    return OrbParams(
        stop_range=cell["stop_range"], target_r=cell["target_r"],
        risk_usd=risk_usd, max_trades=int(cell.get("max_trades", 1)),
        vwap_filter=bool(cell.get("vwap_filter", False)),
        daily_stop_usd=daily_stop_usd)


def _axes(grid: dict[str, tuple]) -> tuple[GridAxis, ...]:
    # range_minutes is swept by re-splitting days (handled in run_verdict),
    # so it is NOT a sweep axis here.
    return tuple(GridAxis(name, vals) for name, vals in grid.items()
                 if name != "range_minutes")


def _span(days: list[TradingDay]) -> tuple[date, date]:
    return days[0].date, days[-1].date


def _gate_entries(proto, days_by_range_minutes, instruments, builder_params,
                  costs, gate) -> None:
    """Build a sample of real plans and put them through the obtainability
    gate. Default-deny: a family with no auditor raises. This is the check
    that verdict v3 would not have survived."""
    from occams.instruments import resolve_costs
    from occams.strategy import NoTrade, build_plan

    family = getattr(proto, "family", None) or "unknown"
    inst = instruments[0]
    days = next(iter(days_by_range_minutes.values()))[inst][:200]
    plans = []
    for d in days:
        try:
            p = build_plan(d.range_bars, builder_params,
                           resolve_costs(costs, d.instrument))
        except Exception:
            p = None
        plans.append(None if isinstance(p, NoTrade) else p)
    gate(family, days, plans, costs)


def run_verdict(days_by_range: dict[str, list[TradingDay]] | dict,
                proto: Protocol, costs, *, events: dict | None = None,
                days_by_range_minutes: dict | None = None) -> VerdictReport:
    """`days_by_range_minutes[rm][inst]` supplies days split at each sealed
    range_minutes; the flat `{inst: days}` form (one range) is accepted too.
    Sweeps the FULL grid including range_minutes, and gates on economics."""
    # E1 GATE: no protocol is sealed on a fill no order could produce.
    # Default-deny -- an unaudited family raises rather than passing. This
    # is what would have stopped verdict v3, whose +0.1R rested on an entry
    # price the market had already left (docs/VERDICT-...-v3-ADDENDUM.md).
    # The planted-edge control could never have caught it: a planted edge is
    # detectable whether or not its entry is reachable.
    from occams.execution import assert_entries_obtainable
    if getattr(proto, "skip_entry_gate", False):
        raise ValueError("skip_entry_gate is not an option — the gate exists "
                         "because a sealed verdict already slipped past it")

    grid = proto.grid
    range_values = tuple(grid.get("range_minutes", (None,)))
    axes = _axes(grid)
    builder_params = OrbParams(stop_range=1.0, target_r=1.5,
                               risk_usd=proto.risk_usd,
                               daily_stop_usd=proto.daily_stop_usd)

    # Normalise inputs to days_by_range_minutes[rm][inst]. The flat form
    # carries one split; reuse it for every range value (synthetic rehearsal).
    # The real CLI supplies genuine per-range splits from the loader.
    if days_by_range_minutes is None:
        days_by_range_minutes = {rm: days_by_range for rm in range_values}
    instruments = sorted(next(iter(days_by_range_minutes.values())))

    # E1 gate, called on a real sample before any cell is swept.
    _gate_entries(proto, days_by_range_minutes, instruments, builder_params,
                  costs, assert_entries_obtainable)

    per: dict[str, SplitReport] = {}
    for inst in instruments:
        oos_cells: list = []
        lock_cells: list = []
        dev0 = oos0 = lock0 = None
        for rm in range_values:
            days = days_by_range_minutes[rm][inst]
            n = len(days)
            lock_start = int(n * (1 - proto.lockbox_frac))
            oos_start = int(n * (1 - proto.lockbox_frac - proto.oos_frac))
            dev, oos, lock = (days[:oos_start], days[oos_start:lock_start],
                              days[lock_start:])
            for name, part in (("OOS", oos), ("lockbox", lock), ("dev", dev)):
                if len(part) < proto.horizon_days:
                    raise ValueError(
                        f"{inst} {name} (range={rm}) has {len(part)} days < "
                        f"horizon {proto.horizon_days}: MC would have no runs.")
            if dev0 is None:
                dev0, oos0, lock0 = _span(dev), _span(oos), _span(lock)

            def sw(cell, _rm=rm):
                cell = {**cell, "range_minutes": _rm}
                if proto.family == "fade":
                    from occams.fade import FadeParams, make_fade_strategy
                    return make_fade_strategy(
                        FadeParams(k_stop=cell["k_stop"],
                                   width_max=cell["width_max"],
                                   risk_usd=proto.risk_usd), costs)
                return make_orb_strategy(
                    _cell_params(cell, proto.risk_usd, proto.daily_stop_usd),
                    costs)
            def _stamp(cells, _rm=rm):
                # range becomes a REAL grid axis (first index) so G4
                # neighbourhoods keep true grid geometry — re-indexing to a
                # 1-D chain capped neighbourhoods at 3 and made
                # plateau_cells=5 unsatisfiable (v3 fix).
                ri = range_values.index(_rm)
                return [SweepCell(indices=(ri,) + c.indices,
                                  params={**c.params, "range_minutes": _rm},
                                  stats=c.stats) for c in cells]
            oos_cells += _stamp(list(sweep(
                oos, axes, sw, proto.cfg, costs, horizon_days=proto.horizon_days,
                events=events, prereg_hash=proto.prereg_hash).cells))
            lock_cells += _stamp(list(sweep(
                lock, axes, sw, proto.cfg, costs, horizon_days=proto.horizon_days,
                events=events, prereg_hash=proto.prereg_hash).cells))

        combined_axes = (GridAxis("range_minutes", range_values),) + axes
        oos_sweep = Sweep(tuple(oos_cells), combined_axes, proto.prereg_hash)
        lock_sweep = Sweep(tuple(lock_cells), combined_axes,
                           proto.prereg_hash)

        # Null uses the FIRST range split (its universe just needs to match a
        # sweep; the null is direction-agnostic to the range window).
        base_days = days_by_range_minutes[range_values[0]][inst]
        n = len(base_days)
        ls = int(n * (1 - proto.lockbox_frac))
        os_ = int(n * (1 - proto.lockbox_frac - proto.oos_frac))
        null_params, null_factory = builder_params, None
        if proto.family == "fade":
            from occams.fade import FadeParams, make_fade_null_strategy
            ks = sorted(proto.grid["k_stop"])
            null_params = FadeParams(k_stop=ks[len(ks) // 2],
                                     width_max=None,
                                     risk_usd=proto.risk_usd)
            null_factory = make_fade_null_strategy
        oos_null = null_baseline(base_days[os_:ls], null_params, proto.cfg,
                                 costs, horizon_days=proto.horizon_days,
                                 seeds=proto.null_seeds, events=events,
                                 factory=null_factory)
        lock_null = null_baseline(base_days[ls:], null_params, proto.cfg,
                                  costs, horizon_days=proto.horizon_days,
                                  seeds=proto.null_seeds, events=events,
                                  factory=null_factory)
        v = verdict(oos_sweep, oos_null, lock_sweep, lock_null, proto.gates)
        per[inst] = SplitReport(
            instrument=inst, verdict=v, oos_winner=v.oos_winner,
            lockbox_winner=v.lockbox_winner, oos_null=oos_null,
            lockbox_null=lock_null, dev_span=dev0, oos_span=oos0,
            lockbox_span=lock0)

    combined = combined_verdict({k: sr.verdict for k, sr in per.items()})
    econ = None
    decision, reason = combined.decision, combined.reason
    if combined.decision == "GO":
        # Bind on the weakest instrument's pass odds and the slowest median
        # attempt — conservative on both axes.
        winners = [sr.lockbox_winner for sr in per.values() if sr.lockbox_winner]
        w_bind = min(winners, key=lambda w: w.p_pass)
        p = w_bind.p_pass
        med_days = max(w.median_days for w in winners)
        ea = 1.0 / p if p > 0 else float("inf")
        months = max(1, -(-med_days // 21))
        cost = expected_cost(p, med_days, proto.monthly_fee, proto.reset_fee)
        fv = funded_value_for(w_bind.params, proto.funded_value_by_filter,
                              default=proto.funded_value)
        cleared = fv > 2 * cost
        econ = {"p_pass": p, "expected_attempts": ea,
                "median_days": med_days, "months_per_attempt": months,
                "expected_cost": cost,
                "funded_value": fv, "cleared": cleared}
        if not cleared:
            # Codex #8: gates pass but the fee math does not — real edge, not
            # worth attempting. A distinct, honest terminal state.
            decision = "GO-RESEARCH"
            reason = (f"gates cleared but economics fail: E[cost] ${cost:.0f} "
                      f"vs funded ${fv:.0f} (need >2×)")
    return VerdictReport(decision=decision, reason=reason,
                         prereg_hash=proto.prereg_hash, per_instrument=per,
                         economics=econ)
