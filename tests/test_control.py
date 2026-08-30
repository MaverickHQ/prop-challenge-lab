"""Phase 5 — the positive control GATE (+ Phase 6 machinery rehearsal).

No result from this harness is interpretable unless it (a) finds a planted
edge, (b) reports ~nothing in a no-edge world, and (c) beats the random-entry
null in the same world. Recalibrated 2026-07-03 after the review fixes
(conservative same-bar stop; per-day null coin): edge-world ORB 1.00 vs
5-seed null baseline 0.857; no-edge ORB 0.00 vs baseline 0.062. This synth
world's huge random-direction drift rewards ANY taker, so the ORB-over-null
margin is structurally thin here (~0.14) — the real-data G2 gate stays 0.15
in PREREG §6. Deterministic; runs in seconds; $0.
"""

from __future__ import annotations

from occams.harness import monte_carlo, null_baseline
from occams.rules import ChallengeConfig
from occams.sim import Costs
from occams.strategy import OrbParams, make_orb_strategy
from occams.synth import make_days

COSTS = Costs(multiplier=5.0, tick_size=0.25, commission_per_side=1.25,
              slippage_ticks=1)
CFG = ChallengeConfig(account=50_000, target=3_000, trailing_dd=2_000,
                      daily_guard=1_000, min_days=1)
PARAMS = OrbParams(stop_range=1.0, target_r=1.5, risk_usd=200.0, max_trades=1)
HORIZON = 40

EDGE_DAYS = make_days(120, seed=7, edge_follow=0.75, drift_pts=15.0)
# v2: kick_scale=0 — the only TRUE dead world (the impulse alone is
# harvestable by breakout timing; edge_follow only randomizes direction).
NOEDGE_DAYS = make_days(120, seed=7, edge_follow=0.50, drift_pts=0.0,
                        kick_scale=0.0)


def test_positive_control_finds_the_planted_edge() -> None:
    stats = monte_carlo(EDGE_DAYS, make_orb_strategy(PARAMS, COSTS), CFG,
                        COSTS, horizon_days=HORIZON)
    assert stats.p_pass >= 0.90            # measured 1.00


def test_no_edge_world_reports_no_pass() -> None:
    stats = monte_carlo(NOEDGE_DAYS, make_orb_strategy(PARAMS, COSTS), CFG,
                        COSTS, horizon_days=HORIZON)
    assert stats.p_pass <= 0.10            # measured 0.00 — costs bite, honestly


def test_strategy_beats_the_null_only_where_edge_exists() -> None:
    orb_edge = monte_carlo(EDGE_DAYS, make_orb_strategy(PARAMS, COSTS), CFG,
                           COSTS, horizon_days=HORIZON)
    null_edge = null_baseline(EDGE_DAYS, PARAMS, CFG, COSTS,
                              horizon_days=HORIZON)
    # In the edge world the aligned strategy must beat the MULTI-SEED null
    # baseline (review fix #4 follow-through: one coin-seed's luck must not
    # move a gate). Measured 2026-07-03: ORB 1.00 vs baseline 0.857 — the
    # margin is structurally thin here because this synth world's huge
    # random-direction drift rewards ANY taker; PREREG's real-data G2 stays
    # at 0.15.
    assert orb_edge.p_pass >= null_edge + 0.10

    # …and the null machinery itself behaves (Phase 6 rehearsal): its no-edge
    # baseline is a small-but-honest geometric floor, not 0/1 degenerate.
    null_noedge = null_baseline(NOEDGE_DAYS, PARAMS, CFG, COSTS,
                                horizon_days=HORIZON)
    assert 0.0 <= null_noedge <= 0.30                   # measured 0.062


def test_positive_control_at_realistic_volatility() -> None:
    # PREREG v2 (verdict-#1 lesson): the control must run at REAL scale —
    # median MES daily ATR is ~55pts, ~7x the old synthetic default of 8.
    # At this scale the harness must (a) actually trade — the validity gate
    # passes, (b) still detect the planted edge over the null.
    from occams.harness import monte_carlo, null_baseline
    from occams.strategy import make_orb_strategy
    from occams.synth import make_days

    edge = make_days(220, seed=21, edge_follow=0.75, drift_pts=15.0, atr=55.0)
    p = OrbParams(1.0, 1.5, 200.0, daily_stop_usd=500.0)
    stats = monte_carlo(edge, make_orb_strategy(p, COSTS), CFG, COSTS,
                        horizon_days=40)
    assert stats.traded_days > 100          # it trades — silence impossible
    null_p = null_baseline(edge, p, CFG, COSTS, horizon_days=40,
                           seeds=(11, 12, 13))
    assert stats.p_pass > null_p            # planted edge detected over null

    # True negative control = DEAD world (kick_scale=0): pure noise, no
    # impulse. edge_follow=0 alone is NOT dead — the direction-random kick
    # is still harvestable by breakout timing at realistic ATR (v2 finding).
    dead = make_days(220, seed=22, edge_follow=0.0, drift_pts=0.0, atr=55.0,
                     kick_scale=0.0)
    stats0 = monte_carlo(dead, make_orb_strategy(p, COSTS), CFG, COSTS,
                         horizon_days=40)
    assert stats0.traded_days > 50          # noise still triggers entries
    assert stats0.p_pass <= null_baseline(dead, p, CFG, COSTS,
                                          horizon_days=40,
                                          seeds=(11, 12, 13)) + 0.05
