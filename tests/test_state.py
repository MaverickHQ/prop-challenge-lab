"""Review findings #2 (persistence + idempotency) and #6 (parity dispersion).

The live path runs as two separate daily processes, so all state must
round-trip through a file, and re-running a day must REPLACE its records
(the grill decision: late /fills → recompute + resend), never double-append.
"""

from __future__ import annotations

import pytest

from occams.parity import ParityLog
from occams.rules import ChallengeConfig, ChallengeState, Status
from occams.state import StateStore

CFG = ChallengeConfig(account=50_000, target=3_000, trailing_dd=2_000,
                      daily_guard=1_000, min_days=1)


def test_challenge_state_snapshot_restore_roundtrip() -> None:
    s = ChallengeState(CFG)
    s.record_day(50_800.0)
    s.record_day(51_600.0)
    restored = ChallengeState.restore(CFG, s.snapshot())
    assert restored.floor == s.floor
    # The restored state continues identically: same pass on the same equity.
    assert restored.record_day(53_050.0) == Status.PASSED


def test_store_roundtrips_state_through_a_file(tmp_path) -> None:
    store = StateStore(tmp_path / "live.json")
    state = store.load()                        # missing file → fresh state
    state.challenge = ChallengeState(CFG)
    state.challenge.record_day(50_800.0)
    state.set_day_drifts("2026-07-06", [-5.0, -7.5])
    state.record_processed("2026-07-06", eod_equity=50_800.0, fills_logged=True)
    store.save(state)

    # A brand-new process (fresh store object) sees identical state.
    reloaded = StateStore(tmp_path / "live.json").load(cfg=CFG)
    assert reloaded.challenge.floor == state.challenge.floor
    assert reloaded.day_drifts["2026-07-06"] == [-5.0, -7.5]
    assert reloaded.processed_days["2026-07-06"]["eod_equity"] == 50_800.0


def test_rerunning_a_day_replaces_not_appends(tmp_path) -> None:
    store = StateStore(tmp_path / "live.json")
    state = store.load(cfg=CFG)
    state.set_day_drifts("2026-07-06", [-5.0])
    state.set_day_drifts("2026-07-06", [-5.0])      # cron double-fire
    state.set_day_drifts("2026-07-06", [-6.0])      # late /fills recompute
    log = state.parity_log(kill_threshold_usd=50.0, min_trades_before_kill=1)
    assert log.n == 1                                # replaced, not appended
    assert log.mean_drift == -6.0                    # latest wins


def test_corrupt_state_file_is_a_loud_error(tmp_path) -> None:
    p = tmp_path / "live.json"
    p.write_text("{not json")
    with pytest.raises(ValueError, match="corrupt"):
        StateStore(p).load(cfg=CFG)


def test_parity_dispersion_kills_on_balanced_disagreement() -> None:
    # Review #6: sign-balanced ±$200 drift has mean $0 but the sim clearly
    # does not describe live — dispersion must fire the kill.
    log = ParityLog(kill_threshold_usd=50.0, min_trades_before_kill=3)
    for sign in (1, -1, 1, -1):
        log.record(sim_pnl=100.0, live_pnl=100.0 + sign * 200.0)
    assert log.mean_drift == 0.0
    assert log.mean_abs_drift == 200.0
    assert log.kill is True
    assert "dispersion" in log.reason.lower()


def test_small_balanced_noise_does_not_kill() -> None:
    log = ParityLog(kill_threshold_usd=50.0, min_trades_before_kill=3)
    for sign in (1, -1, 1, -1):
        log.record(sim_pnl=100.0, live_pnl=100.0 + sign * 10.0)
    assert log.mean_abs_drift == 10.0
    assert log.kill is False
