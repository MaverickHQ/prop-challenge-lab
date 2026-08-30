"""Phase 3 — the challenge rules engine, tested through ChallengeState only.

Sealed rule set (P3, 2026-07-02): $50k account, +$3,000 target, $2,000 EOD
trailing drawdown (locks at start balance once cleared), $1,000 daily guard,
min 1 trading day. The floor is public state: the fuel gauge reads it.
"""

from __future__ import annotations

from occams.rules import ChallengeConfig, ChallengeState, Status

CFG = ChallengeConfig(account=50_000, target=3_000, trailing_dd=2_000,
                      daily_guard=1_000, min_days=1)


def test_floor_starts_below_account_and_ratchets_with_eod_highs() -> None:
    s = ChallengeState(CFG)
    assert s.floor == 48_000.0
    assert s.record_day(50_800.0) == Status.ACTIVE
    assert s.floor == 48_800.0            # trails the new EOD high


def test_floor_locks_at_start_balance_once_cleared() -> None:
    # Trailing stops at the start balance: once EOD equity ≥ 52,000 the floor
    # locks at 50,000 and never trails higher.
    s = ChallengeState(CFG)
    s.record_day(51_500.0)
    assert s.floor == 49_500.0            # still trailing
    s.record_day(52_100.0)
    assert s.floor == 50_000.0            # locked at start, not 50,100
    s.record_day(52_500.0)
    assert s.floor == 50_000.0            # stays locked


def test_eod_equity_at_or_below_floor_breaches() -> None:
    s = ChallengeState(CFG)
    assert s.record_day(47_900.0) == Status.BREACHED
    # A breached account stays breached.
    assert s.record_day(51_000.0) == Status.BREACHED


def test_reaching_target_with_min_days_met_passes_and_sticks() -> None:
    s = ChallengeState(CFG)
    s.record_day(51_600.0)
    assert s.record_day(53_050.0) == Status.PASSED   # ≥ 53,000, min 1 day met
    assert s.record_day(40_000.0) == Status.PASSED   # terminal: sticky


def test_daily_loss_guard_does_not_fail_the_account() -> None:
    # CONFIRMED 2026-07-04 (venue.local.md): the daily guard is an INTRADAY
    # lockout — positions liquidated, locked until 6PM ET — "you do not lose
    # your account". A big losing day therefore does NOT breach; only the
    # trailing-DD floor kills. (Old model breached here — too harsh, killing
    # MC attempts the venue would only pause.)
    s = ChallengeState(CFG)
    s.record_day(52_500.0)
    assert s.record_day(51_450.0) == Status.ACTIVE     # −$1,050 day: locked, alive
    # The floor still kills: drop through it and the account is gone.
    assert s.record_day(49_900.0) == Status.BREACHED   # ≤ locked floor 50,000


def test_min_trading_days_gates_the_pass() -> None:
    cfg2 = ChallengeConfig(account=50_000, target=3_000, trailing_dd=2_000,
                           daily_guard=1_000, min_days=2)
    s = ChallengeState(cfg2)
    assert s.record_day(53_100.0) == Status.ACTIVE    # target hit, days unmet
    assert s.record_day(53_150.0) == Status.PASSED    # second traded day
    # Non-traded days never count toward min_days.
    s2 = ChallengeState(cfg2)
    assert s2.record_day(53_100.0, traded=False) == Status.ACTIVE
    assert s2.record_day(53_100.0, traded=False) == Status.ACTIVE


def test_floor_never_moves_down() -> None:
    s = ChallengeState(CFG)
    s.record_day(50_800.0)
    s.record_day(50_300.0)                # losing day
    assert s.floor == 48_800.0            # ratchet holds


def test_daily_guard_timing_contract_is_explicit() -> None:
    # Codex 2.2 — RESOLVED 2026-07-04: the venue guard is an intraday
    # LOCKOUT (incl. unrealized P&L), never an account failure. This engine
    # therefore applies NO guard-based breach at all; the lockout is
    # structurally unreachable for us anyway (own $500 daily stop +
    # max 2 trades ≈ $450 planned worst day ≪ $1,000). Any EOD loss above
    # the floor leaves the account ACTIVE.
    s = ChallengeState(CFG)
    assert s.record_day(49_100.0) == Status.ACTIVE     # −$900 day: fine
    assert s.record_day(48_200.0) == Status.ACTIVE     # −$900 again: fine


def test_eval_consistency_delays_pass_until_diluted() -> None:
    # Sibling plans (Phase A): the 50% evaluation consistency rule gates the
    # PASS — no single day's profit may exceed frac x net profit at pass
    # time. It DELAYS, never breaches (verified: RULES.md sibling rows).
    cfg = ChallengeConfig(account=50_000, target=3_000, trailing_dd=2_000,
                          daily_guard=1_000, min_days=1,
                          consistency_frac=0.5)
    s = ChallengeState(cfg)
    # One monster day reaches the target alone: 3,200 profit, 3,200 > 50%
    # of net 3,200 -> pass BLOCKED, account stays ACTIVE.
    assert s.record_day(53_200.0) is Status.ACTIVE
    # Grind: +600/day. Net rises; the big day's share falls below 50% only
    # when net >= 6,400.
    assert s.record_day(53_800.0) is Status.ACTIVE   # net 3,800 · 3,200>1,900
    assert s.record_day(54_400.0) is Status.ACTIVE   # net 4,400 · 3,200>2,200
    assert s.record_day(55_000.0) is Status.ACTIVE   # net 5,000 · 3,200>2,500
    assert s.record_day(55_600.0) is Status.ACTIVE   # net 5,600 · 3,200>2,800
    assert s.record_day(56_200.0) is Status.ACTIVE   # net 6,200 · 3,200>3,100
    assert s.record_day(56_800.0) is Status.PASSED   # net 6,800 · 3,200<=3,400


def test_consistency_none_is_the_verified_zero_tier_default() -> None:
    cfg = ChallengeConfig(account=50_000, target=3_000, trailing_dd=2_000,
                          daily_guard=1_000, min_days=1)
    s = ChallengeState(cfg)
    assert s.record_day(53_200.0) is Status.PASSED   # one-day pass allowed


def test_consistency_state_survives_snapshot_roundtrip() -> None:
    cfg = ChallengeConfig(account=50_000, target=3_000, trailing_dd=2_000,
                          daily_guard=1_000, min_days=1,
                          consistency_frac=0.5)
    s = ChallengeState(cfg)
    s.record_day(53_200.0)
    s2 = ChallengeState.restore(cfg, s.snapshot())
    # The restored state remembers the 3,200 monster day: still blocked.
    assert s2.record_day(53_800.0) is Status.ACTIVE
