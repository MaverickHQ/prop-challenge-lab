"""Phase 7 — grid sweep and gated verdict, on the synthetic edge world.

Rehearses the sweep machinery so that when real data lands (P1) the whole
pipeline is `sweep(...) → find_winner(...) → verdict(...)` with the sealed
gates from docs/PREREG.md §6.
"""

from __future__ import annotations

from occams.harness import null_baseline
from occams.rules import ChallengeConfig
from occams.search import Gates, GridAxis, Sweep, find_winner, sweep, verdict
from occams.sim import Costs
from occams.strategy import OrbParams, make_orb_strategy
from occams.synth import make_days

COSTS = Costs(multiplier=5.0, tick_size=0.25, commission_per_side=1.25,
              slippage_ticks=1)
CFG = ChallengeConfig(account=50_000, target=3_000, trailing_dd=2_000,
                      daily_guard=1_000, min_days=1)
EDGE = make_days(120, seed=7, edge_follow=0.75, drift_pts=15.0)
NOEDGE = make_days(120, seed=7, edge_follow=0.50, drift_pts=0.0)

# A tiny 2×2 rehearsal grid — smoke-tests the machine without slowing CI.
GRID: tuple[GridAxis, ...] = (
    GridAxis("stop_range", (0.75, 1.0)),
    GridAxis("target_r", (1.0, 1.5)),
)


def _build(cell: dict) -> object:
    p = OrbParams(stop_range=cell["stop_range"], target_r=cell["target_r"],
                  risk_usd=200.0, max_trades=1, vwap_filter=False)
    return make_orb_strategy(p, COSTS)


def test_sweep_covers_the_full_cartesian_grid() -> None:
    result = sweep(EDGE, GRID, _build, CFG, COSTS, horizon_days=40)
    assert result.n_cells == 4
    assert {(c.params["stop_range"], c.params["target_r"]) for c in result.cells} == {
        (0.75, 1.0), (0.75, 1.5), (1.0, 1.0), (1.0, 1.5)}
    for c in result.cells:
        assert 0.0 <= c.stats.p_pass <= 1.0


def test_find_winner_requires_all_gates_including_plateau() -> None:
    edge_sweep = sweep(EDGE, GRID, _build, CFG, COSTS, horizon_days=40)
    null_p = null_baseline(EDGE, OrbParams(1.0, 1.5, 200.0), CFG, COSTS,
                           horizon_days=40)
    # REHEARSAL gates: this synthetic edge world hands a huge random-direction
    # drift to ANY taker, so the null's baseline is high (~0.86) and the true
    # ORB-over-null margin is ~0.14. edge_vs_null=0.10 here reflects that
    # measured world; the REAL-DATA gate stays 0.15 in PREREG §6.
    gates = Gates(p_pass_min=0.55, edge_vs_null=0.10, p_breach_max=0.30,
                  plateau_cells=2, plateau_slack=0.10)
    winner = find_winner(edge_sweep, null_p, gates)
    assert winner is not None
    # Winner must clear every gate individually.
    assert winner.p_pass >= gates.p_pass_min
    assert winner.p_pass - null_p >= gates.edge_vs_null
    assert winner.p_breach <= gates.p_breach_max
    assert len(winner.plateau) >= gates.plateau_cells


def test_no_edge_world_yields_no_winner_not_a_hero() -> None:
    noedge_sweep = sweep(NOEDGE, GRID, _build, CFG, COSTS, horizon_days=40)
    null_p = null_baseline(NOEDGE, OrbParams(1.0, 1.5, 200.0), CFG, COSTS,
                           horizon_days=40)
    gates = Gates(p_pass_min=0.55, edge_vs_null=0.10, p_breach_max=0.30,
                  plateau_cells=2, plateau_slack=0.10)
    assert find_winner(noedge_sweep, null_p, gates) is None


def test_verdict_combines_oos_and_lockbox_go_only_if_both_pass() -> None:
    def _sw(days) -> Sweep:
        return sweep(days, GRID, _build, CFG, COSTS, horizon_days=40)

    def _null(days):
        return null_baseline(days, OrbParams(1.0, 1.5, 200.0), CFG, COSTS,
                             horizon_days=40)

    gates = Gates(p_pass_min=0.55, edge_vs_null=0.10, p_breach_max=0.30,
                  plateau_cells=2, plateau_slack=0.10)
    assert verdict(_sw(EDGE), _null(EDGE), _sw(EDGE), _null(EDGE),
                   gates).decision == "GO"
    assert verdict(_sw(EDGE), _null(EDGE), _sw(NOEDGE), _null(NOEDGE),
                   gates).decision == "NO-GO"
    assert verdict(_sw(NOEDGE), _null(NOEDGE), _sw(EDGE), _null(EDGE),
                   gates).decision == "NO-GO"


def test_sweep_aborts_when_nothing_trades() -> None:
    # PREREG v2 validity gate: a fold where every cell trades ZERO days is an
    # instrument failure (the verdict-#1 defect), never a NO-GO. risk_usd=1
    # makes every cell size to 0 contracts -> silence -> loud abort.
    import pytest

    from occams.harness import ValidityError

    def broke_strategy(cell):
        p = OrbParams(stop_range=cell["stop_range"], target_r=cell["target_r"],
                      risk_usd=1.0)
        return make_orb_strategy(p, COSTS)
    with pytest.raises(ValidityError, match="zero"):
        sweep(EDGE, GRID, broke_strategy, CFG, COSTS, horizon_days=40)


def test_mcstats_counts_traded_days() -> None:
    from occams.harness import monte_carlo
    p = OrbParams(1.0, 1.5, 200.0)
    stats = monte_carlo(EDGE, make_orb_strategy(p, COSTS), CFG, COSTS,
                        horizon_days=40)
    assert stats.traded_days > 0


def test_null_baseline_aborts_when_null_never_trades() -> None:
    import pytest

    from occams.harness import ValidityError
    with pytest.raises(ValidityError, match="null"):
        null_baseline(EDGE, OrbParams(1.0, 1.5, 1.0), CFG, COSTS,
                      horizon_days=40, seeds=(11, 12))
