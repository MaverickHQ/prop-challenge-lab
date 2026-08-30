# Codex Review Fix Plan

Read-only review date: 2026-07-04  
Scope: architecture, functionality, validation approach, and readiness for the challenge.  
Rule: keep the venue unnamed in tracked files; use "the venue" / "the challenge".

## Executive Verdict

This is a strong research harness, not yet a challenge-ready operating
system. The approach is fundamentally sound: literal rules as objective,
deterministic dollar simulation, positive control, random-entry null,
pre-registration, lockbox, and a deliberately boring UI.

Gate decision: pass-with-conditions for architecture; hold for live attempt
readiness.

The highest-value next step is not broad refactoring. It is to close a small
number of boundary and parity gaps before the real-data PREREG seal:

1. Make instrument identity and per-instrument costs first-class.
2. Ensure the calendar/no-trade universe is identical in backtest and live.
3. Wire the intended risk controls into plans and rule evaluation.
4. Remove simulator ambiguity that could bias results.
5. Make the sweep engine fast enough for real MES/MNQ history.
6. Reconcile documentation/status before sealing any protocol.

## Group 1: Data, Instrument Identity, and Day Universe

Goal: minimize churn by keeping file-format parsing in `occams/loader.py`,
day metadata in `occams/harness.py`, and cross-instrument gating in
`occams/search.py`.

### Fix 1.1: Carry instrument identity through the data seam

Finding: `TradingDay` has no instrument field, while `read_vendor_csv` drops
symbol/definition metadata. This blocks the PREREG requirement that MES and
MNQ both pass independently, and it risks applying MES costs to MNQ.

Likely files:

- `occams/loader.py`
- `occams/harness.py`
- `occams/search.py`
- `tests/test_loader.py`
- `tests/test_harness.py`
- `tests/test_search.py`

Implementation direction:

- Add `instrument: str` to `TradingDay`.
- Preserve or pass instrument identity from vendor files into `to_trading_days`.
- Introduce an explicit cost lookup keyed by instrument.
- Require real sweeps/verdicts to report and gate MES and MNQ independently.

TDD specs:

- `test_loader_attaches_instrument_to_each_trading_day`: a fixture CSV with
  `symbol=MES` produces `TradingDay.instrument == "MES"`.
- `test_loader_rejects_unknown_instrument_when_costs_required`: unknown symbol
  raises before sweep.
- `test_mnq_uses_two_dollar_multiplier_not_mes_multiplier`: an MNQ day uses
  multiplier `2.0`, while MES uses `5.0`.
- `test_verdict_requires_each_instrument_split_to_clear_gates`: combined
  performance cannot pass if one instrument split fails G1-G4.

### Fix 1.2: Assert vendor definitions and roll-day behavior

Finding: the plan calls for vendor definition metadata, tick/multiplier checks,
and roll-day exclusion, but the current loader only validates OHLCV shape.

Likely files:

- `occams/loader.py`
- `tests/test_loader.py`

Implementation direction:

- Parse or accept a small definition table at the loader boundary.
- Assert product code, tick size, and multiplier before producing days.
- Detect roll days by instrument-id/contract changes.
- Exclude roll days from trading days and report them in the quality report.

TDD specs:

- `test_definition_asserts_mes_tick_and_multiplier`: valid MES metadata passes.
- `test_definition_mismatch_is_loud`: wrong tick size or multiplier raises.
- `test_roll_day_is_excluded_and_reported`: fixture with an instrument-id change
  excludes that date and includes it in `QualityReport.roll_days`.
- `test_quality_report_counts_roll_days_separately_from_short_sessions`: roll
  exclusion is not hidden as missing/short data.

### Fix 1.3: Integrate the economic calendar into backtests

Finding: `blocked_reason()` exists, but `run_challenge()` never applies it.
Real results would trade a different day universe than the intended live
workflow unless this is wired before PREREG seal.

Likely files:

- `occams/calendar.py`
- `occams/harness.py`
- `tests/test_harness.py`
- `tests/test_strategy.py`

Implementation direction:

- Add an optional calendar/no-trade filter to the strategy adapter or harness.
- Ensure blocked days advance time but do not trade and do not count as traded
  days.
- Complete CPI/NFP backfill before any real sweep.

TDD specs:

- `test_calendar_block_suppresses_plan_and_trade`: a blocked date returns
  `NoTrade("calendar: <event>")` and no simulation occurs.
- `test_calendar_block_advances_attempt_day_count`: blocked days consume a
  calendar day in the challenge window.
- `test_calendar_block_does_not_count_as_traded_min_day`: blocked days do not
  satisfy min trading day logic.
- `test_backtest_and_live_calendar_use_same_events_mapping`: same event map
  drives historical sweep and daily plan generation.

## Group 2: Rule Parity, Risk Controls, and Fill Conservatism

Goal: keep executable challenge logic in `occams/rules.py`, execution fills in
`occams/sim.py`, and plan/risk sizing in `occams/strategy.py`.

### Fix 2.1: Wire own daily stop into produced plans

Finding: `DayPlan.daily_stop_usd` exists and is tested in the simulator, but
`build_plan()` never sets it. The intended tighter daily stop is therefore not
active in generated ORB plans.

Likely files:

- `occams/strategy.py`
- `tests/test_strategy.py`

Implementation direction:

- Add `daily_stop_usd` to `OrbParams`.
- Pass it into `DayPlan`.
- Keep the simulator's existing behavior unchanged.

TDD specs:

- `test_build_plan_sets_daily_stop_from_params`: generated plan carries
  `daily_stop_usd`.
- `test_default_orb_params_do_not_silently_disable_daily_stop`: the chosen
  production params include a non-null daily stop.
- `test_daily_stop_blocks_second_orb_trade_from_generated_plan`: use
  `build_plan()` plus `simulate_day()` to prove the second entry is suppressed.

### Fix 2.2: Confirm and model daily guard timing literally

Finding: `ChallengeState.record_day()` checks the daily guard from EOD equity
only. If the venue's daily loss guard is intraday, this is not literal-rule
parity.

Likely files:

- `occams/rules.py`
- `occams/harness.py`
- `occams/sim.py`
- `tests/test_rules.py`
- `tests/test_harness.py`

Implementation direction:

- First confirm whether the daily guard is intraday or EOD in local notes.
- If EOD, add an explicit test and comment naming that contract.
- If intraday, expose worst intraday realized/equity excursion from
  `simulate_day()` or `DayResult`, then feed it to the rules engine.

TDD specs:

- `test_daily_guard_contract_is_explicit`: documents whether the guard is EOD
  or intraday through executable behavior.
- If intraday: `test_intraday_daily_guard_breaches_even_if_eod_recovers`.
- If EOD: `test_intraday_dip_does_not_breach_when_rule_is_eod_only`.
- `test_harness_feeds_daily_guard_metric_to_rules`: challenge outcome uses the
  same guard timing as the confirmed rule.

### Fix 2.3: Size contracts using true dollars-at-risk

Finding: `build_plan()` sizes from `stop_dist * multiplier` only. Actual
stopped loss includes commissions, exit slippage, and potentially entry
slippage already embedded in the fill. This can overstate safe size.

Likely files:

- `occams/strategy.py`
- `tests/test_strategy.py`

Implementation direction:

- Add a helper for conservative per-contract stop-loss dollars.
- Include commissions and expected stop slippage.
- Decide whether to include a gap buffer as a parameter or leave gap risk to
  the parity/paper gate.

TDD specs:

- `test_sizing_includes_commissions_and_stop_slippage`: contract count is lower
  when costs are included.
- `test_one_contract_rejected_when_true_risk_exceeds_budget`: no-trade when
  stop distance plus costs exceeds risk budget.
- `test_sizing_helper_matches_simulated_stop_loss_for_basic_long`: generated
  risk estimate equals or exceeds a simple stopped-trade loss.

### Fix 2.4: Define conservative behavior for two-sided entry ambiguity

Finding: while flat, `simulate_day()` checks buy-stop before sell-stop. If a
single 1-minute bar touches both entry levels, the simulator always chooses
long. That can bias results.

Likely files:

- `occams/sim.py`
- `tests/test_sim.py`

Implementation direction:

- Add an explicit conservative rule for both-entry-touched bars.
- Options:
  - reject the bar/day as ambiguous and no-trade,
  - choose the side with worse same-bar outcome,
  - or use a pre-registered deterministic rule.
- Prefer the simplest conservative rule that can be tested and explained.

TDD specs:

- `test_both_entry_stops_touched_same_bar_is_not_biased_long`: current long
  preference is removed.
- `test_both_entry_stops_touched_rule_is_symmetric`: mirrored data does not
  change expected conservatism.
- `test_both_entry_stops_touched_with_one_side_disarmed_uses_armed_side`: VWAP
  disarming still works when only one side is active.

### Fix 2.5: Keep target-on-entry-bar conservatism pinned

Finding: the existing same-bar target rule is good and should remain protected
while simulator ambiguity is fixed.

Likely files:

- `tests/test_sim.py`

Implementation direction:

- Preserve current behavior: target never fills on entry bar, protective stop
  can fill same-bar.
- Add regression coverage near the new ambiguity tests if needed.

TDD specs:

- `test_target_still_never_fills_on_entry_bar_after_entry_ambiguity_fix`.
- `test_entry_bar_stop_still_fills_before_any_target_logic`.

## Group 3: Sweep Scalability and Statistical Integrity

Goal: optimize by separating daily P&L generation from challenge-path scoring.
This should mostly touch `occams/harness.py` and `occams/search.py`, plus tests.

### Fix 3.1: Cache per-day P&L before Monte Carlo

Finding: `monte_carlo()` reruns `simulate_day()` for every start window, and
`sweep()` repeats this for every grid cell. The tiny synthetic suite already
takes several minutes; real data over the full grid will be painful.

Likely files:

- `occams/harness.py`
- `occams/search.py`
- `tests/test_harness.py`
- `tests/test_search.py`

Implementation direction:

- Add a function that evaluates a strategy once per day into a daily ledger.
- Run challenge Monte Carlo by slicing/chaining that ledger instead of
  re-simulating bars.
- Keep old direct path only if useful for small tests, or replace it outright.

TDD specs:

- `test_daily_ledger_matches_run_challenge_equity_marks`: cached path and direct
  path produce identical status/equity.
- `test_monte_carlo_cached_matches_uncached_on_same_days`: P(pass), P(breach),
  and median days are identical.
- `test_sweep_simulates_each_day_once_per_cell`: use a counting strategy/sim
  seam to prove no repeated simulation per start window.
- `test_empty_horizon_returns_zero_runs`: preserve current edge behavior.

### Fix 3.2: Add split-level reporting and gates

Finding: PREREG requires robustness splits by year, volatility regime, and
instrument, but current `verdict()` only sees aggregate sweeps.

Likely files:

- `occams/search.py`
- `occams/harness.py`
- `tests/test_search.py`

Implementation direction:

- Add a split result object that stores aggregate and per-split winners/stats.
- Require instrument splits to pass independently.
- Report year/regime splits as diagnostics, with explicit pass/fail criteria if
  they become gates.

TDD specs:

- `test_instrument_split_failure_blocks_go_verdict`.
- `test_year_split_stats_are_reported_for_winner`.
- `test_volatility_regime_split_uses_prior_atr_terciles`.
- `test_split_report_preserves_aggregate_winner_params`.

### Fix 3.3: Seal and verify PREREG provenance

Finding: `docs/PREREG.md` describes hash sealing, but no code enforces or
records it yet.

Likely files:

- `occams/search.py`
- new report/provenance helper only if needed
- `tests/test_search.py`

Implementation direction:

- Include PREREG hash in sweep/verdict output.
- Refuse to compare runs with different protocol hashes.
- Keep this local-only; no remote publication.

TDD specs:

- `test_sweep_result_carries_prereg_hash`.
- `test_verdict_rejects_mismatched_prereg_hashes`.
- `test_missing_prereg_hash_is_loud_after_seal`.

## Group 4: Strategy Semantics

Goal: avoid expanding the strategy family; make current parameters mean exactly
what they say.

### Fix 4.1: Make VWAP either real VWAP or rename it

Finding: the current `vwap_filter` uses an unweighted typical-price mean,
despite volume being required by the loader. That is not VWAP.

Likely files:

- `occams/strategy.py`
- `tests/test_strategy.py`

Implementation direction:

- Use `sum(typical_price * volume) / sum(volume)` when volume exists.
- If volume is unavailable in synthetic tests, use a clearly named fallback or
  require volume for this filter.
- Keep the grid axis name honest.

TDD specs:

- `test_vwap_filter_uses_volume_weighted_price`: high-volume late bars move the
  VWAP as expected.
- `test_vwap_filter_rejects_missing_volume_when_enabled`: no silent fallback
  for real strategy use.
- `test_vwap_filter_disabled_does_not_require_volume`: no extra burden when
  the filter is off.

### Fix 4.2: Stop-at-target and DD-proximity behavior need a home

Finding: the docs describe stop-at-target and future DD-proximity de-risking,
but the executable strategy/rules path does not yet model them.

Likely files:

- `occams/strategy.py`
- `occams/harness.py`
- `tests/test_strategy.py`
- `tests/test_harness.py`

Implementation direction:

- Clarify whether "stop-at-target" means stop trading after reaching a daily
  target or challenge target.
- If daily, make it a plan/risk-manager parameter.
- If challenge-level, make the harness stop as soon as pass is achieved, which
  it already does through `ChallengeState`.

TDD specs:

- `test_daily_profit_stop_suppresses_later_entries_after_target_pnl`.
- `test_challenge_pass_stops_run_immediately`: already likely covered; keep it
  pinned if refactoring harness.
- `test_dd_proximity_throttle_reduces_or_skips_size_when_enabled`: only if v2
  is intentionally pulled into scope.

## Group 5: Live Workflow and State Machine

Goal: keep live orchestration thin. Implement the sealed state-machine design
as pure logic first, then attach Telegram/AWS later.

### Fix 5.1: Implement the day state machine before Telegram glue

Finding: the state-machine design is good but not executable yet. Without it,
cron retries and late fills can corrupt the day record.

Likely files:

- a small new module such as `occams/dayflow.py`
- `occams/state.py`
- `tests/test_state.py` or new `tests/test_dayflow.py`

Implementation direction:

- Add `DayPhase` enum.
- Add pure `transition(phase, event)` returning actions or rejection.
- Persist enum strings per day in `StateStore`.
- Keep webhook/cron handlers as adapters around this pure core.

TDD specs:

- `test_terminal_trade_day_ends_reconciled`.
- `test_terminal_no_trade_day_ends_reconciled`.
- `test_cron_double_fires_are_idempotent_self_loops`.
- `test_late_fills_on_reconciled_replace_and_resend`.
- `test_rejections_leave_state_unchanged`.
- `test_record_day_called_once_per_date`.

### Fix 5.2: Include parity metrics in Debrief

Finding: `ParityLog` exists and is strong, but the current `debrief()` builder
does not include parity summary fields.

Likely files:

- `occams/report.py`
- `tests/test_report.py`

Implementation direction:

- Add optional parity summary to `debrief()`.
- Include trade count, mean drift, mean absolute drift, and kill reason when
  triggered.

TDD specs:

- `test_debrief_includes_parity_trade_count_and_mean_drift`.
- `test_debrief_includes_mean_abs_drift`.
- `test_debrief_surfaces_parity_kill_reason`.
- `test_debrief_without_parity_keeps_current_simple_output`.

## Group 6: Documentation and Status Hygiene

Goal: avoid spending money or sealing a protocol against stale state.

### Fix 6.1: Reconcile status dates and blockers before PREREG seal

Finding: the session date is 2026-07-04, but some docs contain future-dated
2026-07-06 status entries. Other docs disagree on whether P4 is blocked or
complete. This is not a code bug, but it matters before operational decisions.

Likely files:

- `CLAUDE.md`
- `docs/TASKS.md`
- `docs/PREREG.md`

Implementation direction:

- Pick one source of truth for current project state.
- Ensure blockers reflect reality: P1 data, P2 Telegram bot, P4 Obsidian path,
  AWS auth, paper gate.
- Do this before buying data or sealing PREREG.

TDD specs:

- Documentation-only fix; use checklist tests rather than code tests:
  - no future-dated status entries,
  - P-task statuses agree across docs,
  - PREREG status is still DRAFT until real data lands,
  - blocked items are listed exactly once.

### Fix 6.2: Keep privacy constraints enforced

Finding: the repository successfully avoids naming the venue in tracked files.
That should become an explicit pre-commit/search check before more docs are
added.

Likely files:

- `Makefile`
- optional small script/test

Implementation direction:

- Add a local check that fails if forbidden venue-identifying strings appear in
  tracked files.
- Keep `*.local.md` ignored for private notes.

TDD specs:

- `test_privacy_scan_finds_forbidden_name_in_tracked_text`: fixture-based test
  around the scanner, not real venue text in repo.
- `test_privacy_scan_allows_local_ignored_notes`: scanner scope is tracked
  files only.
- `make lint` or a new `make check` runs the privacy scan.

## Recommended Fix Batches

These batches minimize file churn and reduce risk.

### Batch A: Pre-P1 hard blockers

1. Instrument identity and per-instrument costs.
2. Vendor definitions and roll-day exclusion.
3. Calendar integration plus CPI/NFP backfill.
4. Documentation/status reconciliation.

Primary files: `loader.py`, `harness.py`, `calendar.py`, `search.py`, docs.

### Batch B: Simulator and risk parity

1. Wire daily stop into `OrbParams`.
2. Confirm/model daily guard timing.
3. Size by true dollars-at-risk.
4. Resolve two-sided entry ambiguity.

Primary files: `strategy.py`, `sim.py`, `rules.py`, `harness.py`.

### Batch C: Real-data sweep performance

1. Per-day ledger cache.
2. Cached Monte Carlo.
3. Split-level reporting/gating.
4. PREREG hash provenance.

Primary files: `harness.py`, `search.py`.

### Batch D: Paper-gate readiness

1. Pure day state machine.
2. Parity metrics in Debrief.
3. Telegram command adapters.
4. Cron runners and AWS lift.

Primary files: new dayflow module, `state.py`, `report.py`, comms adapters.

## What Is Already Strong

- The simulator is compact and well-tested around OCO behavior, gaps,
  slippage, same-bar conservatism, force-flat, and dollar P&L.
- The challenge rules engine is readable and directly models the target,
  trailing drawdown, daily guard, min days, and terminal states.
- The positive-control and null-model discipline is the right defense against
  believing a lucky backtest.
- The no-dashboard/two-documents-per-day UI directly targets the most likely
  human failure mode: intervention.
- Persistence and parity primitives are correctly boring: atomic state,
  idempotent day keys, corrupt-state loud failure, mean and dispersion drift.

## Bottom Line

The project is pointed in the right direction. It is much better framed than a
normal retail backtester because it asks whether the system can pass the
literal challenge rules above random-entry geometry, not whether an equity
curve looks attractive.

Do not trust a GO result until the pre-P1 blockers are closed, the current
venue rules are re-confirmed in local notes, real data is loaded with
instrument metadata, and the sweep engine is made scalable. Then run:

1. data quality probe,
2. PREREG seal,
3. null floor,
4. OOS/lockbox sweep,
5. verdict,
6. 30-day paper gate,
7. one live attempt only if the gate holds.
