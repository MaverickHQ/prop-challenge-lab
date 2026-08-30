"""The verdict orchestrator (occams/verdict_run.py) — the single sealed chain
that P1-day runs end-to-end. Tested against the synthetic worlds so the wiring
and the pre-registered ORDER are proven before real data lands: split →
walk-forward (dev/OOS/lockbox) → seal hash → null baseline → per-instrument
sweeps → combined verdict on OOS AND lockbox → economics.
"""

from __future__ import annotations

from occams.rules import ChallengeConfig
from occams.search import Gates
from occams.sim import Costs
from occams.synth import make_days
from occams.verdict_run import Protocol, run_verdict

COSTS = Costs(multiplier=5.0, tick_size=0.25, commission_per_side=1.25,
              slippage_ticks=1)
CFG = ChallengeConfig(account=50_000, target=3_000, trailing_dd=2_000,
                      daily_guard=1_000, min_days=1)
# Rehearsal grid + gates (synthetic-calibrated; real gates live in PREREG).
GATES = Gates(p_pass_min=0.55, edge_vs_null=0.10, p_breach_max=0.30,
              plateau_cells=2, plateau_slack=0.10)
# Full 5-axis grid shape (Codex #6) — small values keep the rehearsal fast.
GRID = {"range_minutes": (15, 30), "stop_range": (0.75, 1.0),
        "target_r": (1.0, 1.5), "vwap_filter": (False,), "max_trades": (1, 2)}


def _proto(**kw) -> Protocol:
    base = dict(grid=GRID, gates=GATES, cfg=CFG, horizon_days=40,
                risk_usd=200.0, oos_frac=0.2, lockbox_frac=0.2,
                daily_stop_usd=250.0, funded_value=100_000.0,
                monthly_fee=119.0, reset_fee=109.0, prereg_hash="test-seal",
                null_seeds=(11, 12, 13))
    base.update(kw)
    return Protocol(**base)


def _worlds(edge_follow, drift):
    # Two instruments so the split logic is exercised; label them MES/MNQ.
    mes = make_days(300, seed=7, edge_follow=edge_follow, drift_pts=drift)
    mnq = make_days(300, seed=8, edge_follow=edge_follow, drift_pts=drift)
    for d in mes:
        object.__setattr__(d, "instrument", "MES")
    for d in mnq:
        object.__setattr__(d, "instrument", "MNQ")
    return {"MES": mes, "MNQ": mnq}


def test_edge_world_yields_go_across_both_instruments() -> None:
    report = run_verdict(_worlds(0.75, 15.0), _proto(), COSTS)
    assert report.decision == "GO"
    assert set(report.per_instrument) == {"MES", "MNQ"}
    # Each instrument reports an OOS and a lockbox winner.
    for split in report.per_instrument.values():
        assert split.oos_winner is not None
        assert split.lockbox_winner is not None
    assert report.prereg_hash == "test-seal"


def test_no_edge_world_yields_no_go_and_pays_no_fee() -> None:
    report = run_verdict(_worlds(0.50, 0.0), _proto(), COSTS)
    assert report.decision == "NO-GO"
    assert report.economics is None            # economics only computed on GO


def test_one_failing_instrument_blocks_the_whole_go() -> None:
    worlds = _worlds(0.75, 15.0)
    worlds["MNQ"] = _worlds(0.50, 0.0)["MNQ"]   # MNQ has no edge
    report = run_verdict(worlds, _proto(), COSTS)
    assert report.decision == "NO-GO"
    assert "MNQ" in report.reason


def test_walk_forward_partitions_are_disjoint_and_ordered() -> None:
    report = run_verdict(_worlds(0.75, 15.0), _proto(), COSTS)
    for split in report.per_instrument.values():
        dev, oos, lock = split.dev_span, split.oos_span, split.lockbox_span
        assert dev[1] <= oos[0] and oos[1] <= lock[0]   # no overlap, in order


def test_report_renders_markdown_without_naming_the_venue() -> None:
    report = run_verdict(_worlds(0.75, 15.0), _proto(), COSTS)
    md = report.render()
    assert "GO" in md and "P(pass)" in md
    assert "alpha" not in md.lower()           # privacy holds in the artifact


def test_horizon_longer_than_a_split_is_a_loud_error() -> None:
    import pytest
    worlds = _worlds(0.75, 15.0)
    # horizon 200 > any split of a 300-day history → refuse, don't return 0 runs.
    with pytest.raises(ValueError, match="horizon"):
        run_verdict(worlds, _proto(horizon_days=200), COSTS)


def test_full_grid_is_swept_including_range_and_max_trades() -> None:
    # Codex #6: the runner must sweep every sealed axis, not a subset.
    report = run_verdict(_worlds(0.75, 15.0), _proto(), COSTS)
    for split in report.per_instrument.values():
        params = split.lockbox_winner.params
        assert set(params) >= {"range_minutes", "stop_range", "target_r",
                               "vwap_filter", "max_trades"}


def test_null_baseline_respects_calendar_blocks() -> None:
    # Codex #7: passing events must reach the null, or G2 compares different
    # day universes. Blocking most days collapses the null's day-count and
    # thus its p_pass — proving events threaded through.
    days = _worlds(0.75, 15.0)["MES"]
    every_other = {d.date: "FOMC" for i, d in enumerate(days) if i % 2 == 0}
    from occams.harness import null_baseline
    from occams.strategy import OrbParams
    pr = OrbParams(1.0, 1.5, 200.0)
    unblocked = null_baseline(days, pr, CFG, COSTS, horizon_days=40)
    blocked = null_baseline(days, pr, CFG, COSTS, horizon_days=40,
                            events=every_other)
    assert blocked != unblocked        # events changed the null's universe


def test_economics_failure_yields_go_research_not_go() -> None:
    # Codex #8: gates pass but funded value fails the 2x economics gate →
    # a distinct GO-RESEARCH / NO-ATTEMPT decision, never a plain GO.
    report = run_verdict(_worlds(0.75, 15.0), _proto(funded_value=1.0), COSTS)
    assert report.decision == "GO-RESEARCH"
    assert report.economics is not None
    assert report.economics["cleared"] is False


def test_go_requires_both_gates_and_economics() -> None:
    report = run_verdict(_worlds(0.75, 15.0), _proto(funded_value=1_000_000.0),
                         COSTS)
    assert report.decision == "GO"
    assert report.economics["cleared"] is True


def test_expected_cost_is_time_based() -> None:
    # RULES.md §4.1: the fee unit is a subscription MONTH ($119) plus a reset
    # ($109) per failed attempt — a slow pass costs more than a fast one.
    from occams.verdict_run import expected_cost

    # p=0.5 → E[attempts]=2; 40 trading days ≈ 2 months per attempt:
    # 2 attempts × 2 months × $119 + 1 reset × $109 = $585.
    assert expected_cost(0.5, 40, 119.0, 109.0) == 585.0
    # Certain pass in under a month: exactly one subscription month, no reset.
    assert expected_cost(1.0, 10, 119.0, 109.0) == 119.0
    # Exactly 21 trading days still fits one month (ceil boundary).
    assert expected_cost(0.5, 21, 119.0, 109.0) == 347.0
    # Zero pass probability → infinite cost, never a division crash.
    assert expected_cost(0.0, 40, 119.0, 109.0) == float("inf")


def test_economics_report_carries_time_components() -> None:
    report = run_verdict(_worlds(0.75, 15.0), _proto(), COSTS)
    assert report.decision == "GO"
    e = report.economics
    assert e["months_per_attempt"] >= 1
    assert e["expected_cost"] > 0


def test_generated_params_carry_the_daily_stop() -> None:
    # Codex #9: daily_stop_usd must reach the plan (matters at max_trades=2).
    from occams.strategy import OrbParams
    from occams.verdict_run import _cell_params
    p = _cell_params({"range_minutes": 30, "stop_range": 1.0, "target_r": 1.5,
                      "vwap_filter": False, "max_trades": 2},
                     risk_usd=175.0, daily_stop_usd=250.0)
    assert isinstance(p, OrbParams)
    assert p.daily_stop_usd == 250.0
    assert p.max_trades == 2


def test_fade_family_is_now_REFUSED_by_the_entry_gate() -> None:
    """Was: an end-to-end fade sweep. The fade family as implemented declares
    no ORDER -- it assumes a fill at the range boundary at the failure close,
    a price already behind the market -- so there is nothing to audit and it
    cannot be sealed (VERDICT-2026-07-06-v3-ADDENDUM).

    COVERAGE NOTE: this test previously exercised the fade GRID machinery
    (FadeParams cells, plateau geometry). That coverage is now lost and needs
    a replacement vehicle -- logged as E1.2. Deliberately not solved with a
    gate bypass: a test-only escape hatch is how the gate stops meaning
    anything."""
    import pytest as _pytest
    from occams.execution import UnobtainableEntry
    with _pytest.raises(UnobtainableEntry, match="not obtainable"):
        _legacy_fade_sweep()


def _legacy_fade_sweep() -> None:
    # Family 2 wiring: proto.family="fade" sweeps FadeParams cells, uses
    # the fade-vs-follow coin null, and reports winner params with the
    # fade grid keys. Synthetic worlds carry range_bars, so the whole
    # sealed chain runs unchanged.
    proto = _proto(grid={"range_minutes": (15,), "k_stop": (0.25, 0.5),
                         "width_max": (None, 0.6)},
                   family="fade")
    report = run_verdict(_worlds(0.75, 15.0), proto, COSTS)
    assert report.decision in ("GO", "GO-RESEARCH", "NO-GO")
    for split in report.per_instrument.values():
        if split.lockbox_winner:
            assert set(split.lockbox_winner.params) >= {"k_stop",
                                                        "width_max"}


def test_funded_value_by_filter_picks_the_winner_cadence() -> None:
    # Sealed dict, keyed on whether the winner is width-filtered — a
    # deterministic rule, never a post-hoc choice.
    from occams.verdict_run import funded_value_for
    assert funded_value_for({"width_max": None},
                            {"open": 1100.0, "filtered": 550.0}) == 1100.0
    assert funded_value_for({"width_max": 0.25},
                            {"open": 1100.0, "filtered": 550.0}) == 550.0
    assert funded_value_for({"width_max": None}, None, default=900.0) == 900.0


def test_combined_sweep_geometry_is_now_gated_too() -> None:
    """Same story: the geometry assertion rode on a fade sweep. See E1.2."""
    import pytest as _pytest
    from occams.execution import UnobtainableEntry
    with _pytest.raises(UnobtainableEntry, match="not obtainable"):
        _legacy_geometry_sweep()


def _legacy_geometry_sweep() -> None:
    # G4 regression: re-indexing combined cells to a 1-D chain caps a
    # Chebyshev-1 neighbourhood at 3 — the production plateau_cells=5
    # could NEVER pass. The combined sweep must keep true grid indices
    # (range as one axis), so a 3x3 fade grid's centre sees 9 neighbours.
    from occams.search import _neighbourhood

    proto = _proto(grid={"range_minutes": (15,), "k_stop": (0.2, 0.25, 0.33),
                         "width_max": (None, 0.6, 0.4)},
                   family="fade",
                   gates=Gates(p_pass_min=0.55, edge_vs_null=0.10,
                               p_breach_max=0.30, plateau_cells=5,
                               plateau_slack=0.10))
    captured = {}
    import occams.verdict_run as vr
    orig = vr.verdict

    def spy(oos, oos_null, lock, lock_null, gates):
        captured["oos"] = oos
        return orig(oos, oos_null, lock, lock_null, gates)
    vr.verdict = spy
    try:
        run_verdict(_worlds(0.75, 15.0), proto, COSTS)
    finally:
        vr.verdict = orig
    sw = captured["oos"]
    assert sw.n_cells == 9
    sizes = sorted(len(_neighbourhood(c, sw)) for c in sw.cells)
    assert max(sizes) == 9          # centre cell sees the full 3x3
    assert min(sizes) >= 4          # corners see 2x2
