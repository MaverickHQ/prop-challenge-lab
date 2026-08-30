"""Parity log — the exceptional-project metric (CONTEXT §12).

For every real trade we record (sim_pnl, live_pnl); the tracker exposes the
running per-trade drift and fires a kill signal when the drift breaches a
pre-set threshold. Pure logic: `/fills` feeds it during the paper gate.
"""

from __future__ import annotations

from occams.parity import ParityLog


def test_perfect_parity_reports_zero_drift() -> None:
    log = ParityLog(kill_threshold_usd=50.0, min_trades_before_kill=3)
    for _ in range(5):
        log.record(sim_pnl=100.0, live_pnl=100.0)
    assert log.mean_drift == 0.0
    assert log.kill is False


def test_drift_is_signed_and_averaged_per_trade() -> None:
    # live consistently $10 worse per trade → mean_drift = −$10.
    log = ParityLog(kill_threshold_usd=50.0, min_trades_before_kill=3)
    for _ in range(4):
        log.record(sim_pnl=100.0, live_pnl=90.0)
    assert log.mean_drift == -10.0
    assert log.kill is False    # under $50 threshold


def test_kill_fires_when_average_drift_exceeds_threshold() -> None:
    log = ParityLog(kill_threshold_usd=50.0, min_trades_before_kill=3)
    for _ in range(4):
        log.record(sim_pnl=100.0, live_pnl=25.0)  # −$75 drift each
    assert log.mean_drift == -75.0
    assert log.kill is True
    assert "drift" in log.reason.lower()


def test_kill_requires_minimum_trade_count() -> None:
    # A single terrible trade must not fire kill — need a sample.
    log = ParityLog(kill_threshold_usd=50.0, min_trades_before_kill=3)
    log.record(sim_pnl=100.0, live_pnl=-500.0)
    assert log.mean_drift == -600.0
    assert log.kill is False   # too few trades yet
    log.record(sim_pnl=100.0, live_pnl=100.0)
    log.record(sim_pnl=100.0, live_pnl=100.0)
    assert log.kill is True    # threshold breached AND min sample met


def test_positive_drift_also_signals_a_broken_model() -> None:
    # If live is systematically BETTER than sim by a lot, the sim is wrong
    # too — parity means agreement in both directions.
    log = ParityLog(kill_threshold_usd=50.0, min_trades_before_kill=3)
    for _ in range(4):
        log.record(sim_pnl=50.0, live_pnl=150.0)
    assert log.mean_drift == 100.0
    assert log.kill is True
