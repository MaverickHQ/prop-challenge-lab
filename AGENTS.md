# occams-trader — Project Context (AGENTS.md)

A private, **LOCAL-ONLY** build (publication is a gated future step — §0).
**Charter (re-founded 2026-07-09): an edge-finding instrument.** The original
goal — pass a futures prop-firm evaluation ("**the venue**", never named
here) — concluded 2026-07-06 in two validated no-gos and one real finding
(§7). The lab now hunts edges under sealed protocols; the challenge is one
possible monetization layer, reopened only if the sealed bar (ex-ante
≥ +0.25R/trade at ≥ 0.5 trades/day) is met. Occam's razor governs; The
Crucible survives here as **discipline, not code**.

**The one-line design:** deterministic dollars in the execution loop, the LLM
in the research loop, the literal challenge rules as the objective, judged
against a random-entry null through Monte Carlo — and a UI that is two pushed
documents a day, not an application.

Full analysis: [docs/CONTEXT.md](docs/CONTEXT.md) · Task list:
[docs/TASKS.md](docs/TASKS.md)

---

## 0. Privacy & publication rules (hard — read first)

- **Local git only.** No remote, no push, ever, without the user's explicit
  instruction. **Publication track (T3) does not weaken this**: a public
  remote exists only after the full-history privacy audit (T3.1) passes
  AND the user pushes personally. Until then everything below applies
  unchanged.
- **The venue is never named in any tracked file** — not in code, docs,
  comments, or commit messages. Say "the venue" / "the challenge". (Lesson
  paid for in the series: scrubbing a name out of git history later cost an
  orphan-branch rebuild. Keep it out from commit one.)
- Venue-specific notes, if ever needed, go in `*.local.md` (git-ignored).
- **No live trading from this repo.** It emits signals and documents; a human
  places every order. A **30-day paper gate** precedes any live attempt.
- Secrets (Telegram bot token, data-vendor API keys) live in `.env`
  (git-ignored). Never paste keys into chat or commit them.

## 1. Design principles (ranked; ties break toward the razor)

1. **Occam's razor** — the fewest components that can answer the question.
2. **The objective is the literal rule set**, never a proxy (trailing DD,
   consistency, min days — as executable code, in dollars).
3. **Null model before edge claims** — every result is measured against
   random entries under the same risk manager (the ~30–40% geometric floor).
4. **Positive control before interpretation** — plant a known edge; the
   harness must find it before any real result counts. Day one, not last.
5. **Pre-register, then run** — protocol sealed before results are seen;
   lockbox opened exactly once.
6. **Backtest/live parity is a measured metric** (implementation shortfall
   per trade), never an assumption.
7. **The UI rations information** — two decision moments/day, two documents/
   day. No dashboard: screen-watching induces intervention, the #1 discipline
   failure. Boredom is a feature.

## 2. Architecture (4 components + comms, ~1.5–2k lines total incl. tests)

| Component | Job | Notes |
|---|---|---|
| `sim/` | Intraday contract-level simulator | 5-min MES/MNQ bars (1-min for stop/target resolution), **dollar P&L**, commissions + 1-tick slippage, conservative intrabar rule (stop fills before target) |
| `rules/` | The challenge rules engine | EOD trailing DD ratchet, consistency check, min trading days — the literal spec, CONFIRM values in config |
| `strategy/` | ORB + the risk manager | One family; the risk manager is half the strategy |
| `harness/` | Experiments | Grid sweep, walk-forward + lockbox, null model, positive control, Monte Carlo over start dates; results to CSV/parquet |
| `comms/` | Telegram + Obsidian | Morning **Plan Card** (levels, size, no-trade flags) and evening **Debrief** (parity log, **fuel gauge**, challenge state) pushed via Telegram; Debrief also written as an Obsidian daily note |

**LLM placement (measured in the series, not assumed):** never in the
execution loop (40–90× fewer trades, no quality gain); the proposer is shelved
(grid search is complete on a ~5-param space); research-collaborator role
stands; the **evening coach** (LLM reads the day's log and flags discipline
drift) is **v2, gated on demonstrated value** — user is explicitly lukewarm.

## 3. Locked decisions (2026-07-02 — revisit only with cause)

- **Strategy family: ORB only** (opening-range breakout, RTH), ~5 params:
  range window, ATR stop multiple, target R, max trades/day, VWAP-side filter.
  MAs/fib-retracement/volume stack rejected (parameter surface ≫ evidence).
- **Instruments:** MES/MNQ. **Data:** one-off vendor purchase of 1-min
  history (Databento or FirstRate, ~$100–200), local files, git-ignored.
  TradingView is charting/alerts + an independent Pine parity check — never
  the data source or the backtester.
- **Sizing:** fixed-fractional from ruin math (~0.3–0.5%/trade), hard daily
  stop, stop-at-target, max 2 trades/day. Not Kelly (overbets a trailing
  barrier under edge uncertainty).
- **News = a calendar problem:** a ~40-row/year CSV of tier-1 releases
  (FOMC/CPI/NFP…, from official schedules), backtestable with zero lookahead.
  No breaking-news feed (resting stops bound the loss; **ATR sizing is the
  news-reaction mechanism**). No LLM news/sentiment in signals — untestable
  point-in-time input (series lesson).
- **Execution model:** resting OCO bracket orders placed once after the
  opening range forms — the stop orders ARE the alert. Telegram is
  belt-and-braces attention, not reaction.
- **Storage:** CSV/parquet result files first; a database only when a
  concrete need appears (user decision).
- **No dashboard, no Streamlit, no web UI.** Fuel gauge goes via Telegram.

## 4. Definition of done / success

Success has three tiers, all honest:
1. **A validated no-go** — gates fail, no fee paid, truth cost ≈ $200. This
   outcome is the process *working*.
2. **Gates pass → challenge attempted** per the runbook (P(pass|gates) est.
   55–70%/attempt; full probability tree in CONTEXT §2).
3. **Funded-stage survival** — separate parameterization, designed before
   attempt one (CONTEXT §8).

Pre-registered go/no-go gate: **P(pass) ≥ 55% AND ≥ null + 15 points** on
lockbox + OOS Monte Carlo, from a parameter *plateau* (never a lone spike).

## 5. Status & next actions

- **Phase 0 (repo, docs, plan): DONE 2026-07-02.**
- **Grill review DONE 2026-07-02** — deployment + comms + plan selection
  sealed (CONTEXT §1/§9): confirmed rule set **$3,000 target / $2,000 EOD
  trailing DD / $1,000 guard / no eval consistency / min 1 day** ($50k; plan
  details in git-ignored `venue.local.md`); venue bans full automation →
  human executes, by construction; **human-as-sensor** `/range` + `/fills`
  commands (no live data feed in v1); **cron-driven, command-fed** runners
  (FitnessCore reminder pattern); CLIs during research → **FitnessCore SAM
  lift (EventBridge + webhook Lambda + S3 reports) at paper-gate start**;
  SignalFlow's ECS/SQS explicitly rejected as overkill.
- **Deferred by user until after the initial build:** P1 (data purchase),
  P2 (Telegram bot), P4 (Obsidian path).
- **Phases 2–7 + Phase 9.1 + parity: DONE 2026-07-03 (42 tests green, lint
  clean, all \$0).** `sim.py`, `rules.py`, `strategy.py` (ORB + risk +
  VWAP filter + own daily stop), `calendar.py`, `harness.py` (equity
  chaining + Monte Carlo), `synth.py` (plantable-edge market), `search.py`
  (grid sweep + gated winner incl. plateau rule + verdict), `report.py`
  (Plan Card + Debrief + fuel gauge), `parity.py` (drift + kill signal),
  `docs/PREREG.md` (draft, seals when P1 lands). **The positive control
  gate passed** on the synthetic edge world (ORB p_pass=1.00 vs null 0.73;
  no-edge world 0.00). The autonomous run is complete for every task that
  does not need external inputs.
- **Code review 2026-07-03 + all pre-P1 fixes DONE 2026-07-04** (63 tests):
  conservative same-bar stop, G4 median plateau (= PREREG exactly),
  per-day null coin + multi-seed `null_baseline`, tz contract
  (`sessions.py`), loader (`loader.py`: both vendor shapes, no-lookahead
  ATR, short-session handling, quality probe), persistence/idempotency
  (`state.py`: atomic JSON, day-keyed, replace-not-append),
  parity dispersion kill, FOMC calendar 2019–2026 verified (69 dates).
- **P4 DONE 2026-07-04** (occams-razor vault + Debrief writer, 6 tests).
- **P1 DATA: DONE 2026-07-05** ($27.64 incl. one lost stream + a $13.99
  portal parent-product backup). Vendor continuous MES.v.0/MNQ.v.0 ohlcv-1m
  2019-05-05→2026-07-03 via `scripts/fetch_data.py` (API; portal can't
  express continuous — parent product = all expirations = duplicate
  timestamps = loader refuses). **Identity asserted**: tick 0.25 both,
  multipliers $5/$2, class F outrights. **Probe**: 1,849 sessions/inst,
  **1,741 tradable days** each (65 short + 29 roll excluded), missing
  bdays = holidays only; vendor condition: 13 degraded days in range
  (2020 COVID crash days among them), 13 "missing" = weekends. Raw `.dbn`
  kept beside CSVs; `data/` stays git-ignored (licensed).
- **CPI/NFP backfill DONE 2026-07-05** (`0d9dc40`): 95 CPI + 95 NFP + 69
  FOMC = 259 rows, from official per-year schedule pages saved by hand
  (BLS 403s bots; `scripts/backfill_bls.py` = the extractor). 2025 is
  11+11 by reality (Oct–Nov shutdown moved/canceled releases) — actual
  release days, zero lookahead.
- **VERDICT (2026-07-06): validated NO-GO — project research phase
  CONCLUDED at success tier 1.** Two sealed runs the same day:
  - **v1 (hash `d3fa96c0…`): VOID for instrument defect** — daily-ATR stop
    units sized every cell to 0 contracts; 0% pass AND 0% breach exposed
    it; no market information revealed. `docs/VERDICT-2026-07-06.md`.
  - **v2 (hash `12ca0a32…`): REAL NO-GO** — ORB-native stops, validity
    gates armed and silent (78–86% of days traded, 1–12 contracts). Best
    cell anywhere: P(pass) 0.187 (vs G1 0.55) with P(breach) 0.519 (vs G3
    0.30); in-sample bests 0.03–0.04 (nothing to overfit); null 0.000
    WHILE TRADING (no luck channel at this cadence). Both instruments,
    all folds. `docs/VERDICT-2026-07-06-v2.md` · vault E-001/D-003.
  - **No fee is paid.** Total project spend ≈ $32 (data). Any future
    attempt = a NEW strategy family under a new dated PREREG — never more
    parameters on this one (sweep-until-it-passes is the refused failure).
  - Phases 9–11 (comms, paper gate, attempt) are MOOT on this family. P2
    (Telegram) not needed. Wargame-skill W3 operational missions moot;
    W1/W2 optional documentation work only.
- **FAMILY 2 RESEARCH PROGRAM — CONCLUDED 2026-07-06 (see below).** The honest
  continuation after the ORB kill; full phase plan + rationale in
  [docs/TASKS.md](docs/TASKS.md) §Family-2. **What:** feasibility map →
  dev-fold diagnostics → ONE new family (prior: opening-range-failure /
  VWAP-reclaim mean reversion) under PREREG v3 → verdict #3 → paper gate
  as the TRUE lockbox → only then a fee. **Why this shape:** (a) verdict
  #2 says the challenge is only passable with real per-trade edge — no
  luck channel exists at disciplined sizing (null 0.000 while trading);
  (b) two cheap levers were unexploited: **horizon is purchasable** (no
  eval deadline; time = $119/mo = our cost unit) and **plan geometry is
  choosable** (sibling tiers have different target/DD/consistency — the
  rules engine parameterizes them); (c) feasibility-first: compute the
  required (WR × R × frequency × horizon × plan) frontier BEFORE hunting
  edge, so hypotheses are screened against a number, not a vibe.
  **Contamination ledger:** ORB per-fold stats on 2019–2026 were read
  (verdicts #1–2); 2024–2026 lockbox is weakly contaminated → binding
  final gate is prospective (60–90-day paper window). Dev ground for
  family 2 extends to ES/NQ 2010–2019 (~$10–30, Phase D). **Sealed
  guards (D-003):** no ORB revival, no sizing escalation, no fill-model
  softening, no lockbox reuse. Honest prior: ~20–35% full success; modal
  outcome: another validated no-go at ~$30 — still the right trade vs a
  −EV blind attempt (population base rate 16.8%/attempt).
  AWS auth unlocks 9.5; Phases 10+11 need everything above.
- **PRE-SEAL GATE: CLOSED 2026-07-04** — both Codex reviews fully landed
  (G1–G5 + the orchestrator-trust batch; **122 tests**, `make check` green).
  Guard timing RESOLVED (intraday lockout, never a failure — engine
  corrected, `8832a10`). The P1 command is **`occams-verdict`**
  (`occams/verdict_cli.py`): cwd-independent, FAILS CLOSED without
  CSVs+definitions+calendar+PREREG hash, sweeps the FULL sealed 128-cell
  grid (range_minutes via per-range splits), event-matched null, three-state
  decision **GO / GO-RESEARCH / NO-GO** with the economics gate live.
- **Benchmark note (Codex #12):** full-grid synthetic sweep ≈ 60s; real
  MES+MNQ (~1,750 days) = minutes-to-tens-of-minutes. Time it on P1 day;
  optimise `simulate_day` (iterrows) only if measured runtime demands.
- **Deep research COMPLETE 2026-07-05** (2 rounds, 24 claims verified 3-0):
  rules layer in `docs/RULES.md` (incl. §2b conduct rules — automation,
  tick-scalping, 4:20PM ET flat); behavioral/base-rate layer in
  `docs/EVIDENCE.md` (funnel 16.8% per-attempt / 33.3% funded-ever-paid;
  paid-cohort profile matches our design; unfiltered-ORB-no-edge prior →
  a validated NO-GO is the expected outcome; funded_value formula + ~0.8
  ops haircut for the seal). Venue-named provenance in `venue.local.md`.

## 6. Conventions

- Python 3.12, `pytest` + `ruff`; TDD (red→green) for all pure logic —
  the rules engine, sizing math, and fill logic especially.
- Commit per completed task block; imperative commit messages; no venue name
  in commits.
- Plans/analysis live in `docs/`; keep CLAUDE.md's status section current as
  phases complete.

## 7. Final program status (2026-07-06)

**The project is CONCLUDED at success tier 1, twice over.** Three sealed
verdicts in one day: v1 void (instrument defect, self-caught), v2
validated NO-GO (ORB never worked), v3 validated NO-GO at G1 **with the
project's real finding** — the failed-breakout fade carries a genuine,
out-of-sample-persistent ~+0.1R/trade net edge (34/36 fold-cells
positive; OOS above dev on MES) that is ~half the size the challenge
geometry demands. Fees paid: $0. Total spend ≈ $32. Records:
docs/VERDICT-2026-07-06*.md · vault E-001/E-002/D-003/D-004.
**Reopening bar (PREREG v4+):** an ex-ante hypothesis with net per-trade
expectancy ≥ +0.25R at ≥ 0.5 trades/day (FEASIBILITY.md is the standing
frontier). Rejected escalations (sized-up, both-instruments-as-one,
longer horizon, more parameters) are recorded in the v3 verdict doc —
do not re-litigate them.

## 8. THE LAB PROGRAM — ACTIVE (founded 2026-07-09)

The user's directive: **both** — publish at the right time AND build the
edge-finding instrument. Full task list: [docs/TASKS.md](docs/TASKS.md)
§Lab-Program. Three tracks:

- **T1 — Paper campaign** ($0, 60–90 days): live-fire validation of the
  fade finding (k=0.2 unfiltered candidate) on both instruments via
  PAPER-PREREG (drafted → user-sealed), human-as-sensor comms (Plan
  Card / `/range` / `/fills` / Debrief), parity ledger with the sealed
  kill thresholds. Parity holds → personal-sizing decision; kill fires
  → written up. Needs from user: Telegram bot token + paper account.
- **T2 — The instrument**: campaign runner ((family × symbol) →
  feasibility → dev screen → PREREG draft → **human seal, never
  automated** → verdict → ledger). Governance now live:
  [docs/PROTOCOLS.md](docs/PROTOCOLS.md) (multiplicity ledger — a GO is
  judged against how many sealed attempts produced it) and
  [docs/SPEND.md](docs/SPEND.md) ($150 cap, quote-first, per-purchase
  approval). First expansion: MGC + MCL (chosen over equity-correlated
  M2K/MYM).
- **T3 — Publication** (build now, fire at ~paper-campaign end):
  full-history privacy audit tool, $0 synthetic quickstart,
  bring-your-own-rules config, plots, essay from the Final Report.
  License/venue/params-vs-generalized = user decisions at the gate.

Standing honesty controls for every future protocol: ex-ante bar before
any grid · dev-fold-only screening · multiplicity ledger · the
prospective paper gate as the only binding lockbox.

## 9. TWO WORKSTREAMS (split 2026-07-30)

**LIVE STATUS 2026-07-30 (session end).** Protocol #4 is RUNNING —
trade 1 logged (MES short 1x @ 7421.50, a 0.73R setup; the outstanding
user action is confirming in the Trading Panel whether the bracket was
actually placed, then either logging real fills or logging the process
defect — never inventing fills). Day 1 also produced three integrity
fixes, the sharpest being **off-tick price rejection**: a typo'd level
would have made drift measure typing rather than execution. The Pine
aid reached v1.8 (fill watcher; logic verified against the sealed
engine on 500 real days, 0 mismatches). **Next on B: the B0.1
Databento latency spike** — it decides whether the poller behind
B2/B3/B7 is viable at all. Full session log: TASKS.md §Session-Log.

**A — LOCAL, running now.** Protocol #4 executes on laptop + phone:
launchd jobs → Telegram, `tools/fade_campaign.pine` as the chart aid,
TradingView Paper for fills. Keep running, learning, improving; small
fixes land here immediately. Never blocked by B.

**B — AWS, the long-term platform.** Same engine, same seals, different
trigger. Level-400 backlog (B0–B6, 26 items) in TASKS.md §Workstream-B.
**What changed the design (2026-07-30):** TradingView Basic gives **0
indicator alerts**, so TV cannot deliver signals at any acceptable
price. Databento (already owned, ~$3/yr at poll cadence) replaces the
SIGNAL path; TV remains only the paper EXECUTION venue until live, when
a broker feed replaces Databento and the broker screen replaces TV
Paper. This DELETES the old Track-4 webhook receiver and Pine-strategy
items — a simpler architecture than the shadow-logger design it
supersedes (no API Gateway, no public endpoint, no subscription).

**Six hard constraints on B** (any violation voids the campaign):
delay-parity — the poller may never read bars fresher than the
execution venue's delay, enforced in code, or every fill is flattered
and parity is meaningless (PAPER-PREREG §3); the human places every
order and logs every fill; kill thresholds compute from the human
stream alone; secrets in SSM only; the venue is never named in code,
IaC, resource names or logs; a hard budget alarm with metered calls
reconciled to SPEND.md.

**Gating spikes first (B0):** Databento intraday-availability latency
decides whether a poller is viable at all; REST-vs-client decides the
Lambda package; region/auth is `[needs-user]`. Cutover only after a
clean shadow week (B5.1) with launchd retained a week as rollback.

**Interaction model (B7, specified 2026-07-30):** pre-market card ->
engine-computed setup card (buy/stop/target/size) -> human `/ack` ->
S3 ledger -> daily recap, with `/status` `/week` `/month` `/all` on
demand. Two rules govern it: **`/ack` is an acknowledgement, never a
veto** (`placed` / `missed <reason>` / `partial <reason>`) — a
judgement veto would turn the sealed mechanical strategy discretionary
and void the measurement, and missed trades stay in the denominator as
process defects; and **moving level production from human
transcription to engine output is a PAPER-PREREG §4 change** requiring
a dated amendment (protocol #4a) made before results accumulate —
legitimate at zero trades, not later. Every recap carries a
sample-size honesty guard: the live-fire week read +1.2R after 3
trades, +0.69R after 4, +0.35R after 5, converging on the measured
+0.1R from above, so any sub-20-trade expectancy prints that caveat
beside it. No database — S3 JSON/JSONL, recaps as in-memory filters.

Standing rejections carried forward: fully-headless protocol #4 (voids
the sealed question) and automated order routing (never).

**External-framework policy (D-005, 2026-07-11 — TradingAgents review):**
the 92k-star multi-agent LLM trading framework is **neither fork nor
foundation** — its chassis (LLM in the execution loop, non-point-in-time
data, daily equities) contradicts this lab's measured lessons, and LLM
backtests inside training windows are void by contamination. Three
sanctioned uses only: (1) its bull/bear debate PATTERN (prompts/roles,
thin native build) for the T2.5 hypothesis-intake committee; (2) a
candidate **protocol #5 "TradingAgents on the bench"** — prospective-
only, null-controlled specimen evaluation, post-paper-campaign, own
PREREG + SPEND line (~$50–100, deliberate cap raise); (3) the canonical
contrast citation in the publication (T3.4b). The lab is the instrument;
external frameworks are specimens or citations, never the chassis. The
ordered sequence lives in TASKS.md §ROADMAP.
