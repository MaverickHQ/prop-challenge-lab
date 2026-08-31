# prop-challenge-lab — Project Context (CLAUDE.md)

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

## 8b. TRACK R — THE RESEARCH PROGRAMME (founded 2026-08-01)

**The goal has not changed:** pass the challenge, then trade it
profitably. What changed is the route, and why.

**The finding that reframes everything.** Aschenbrenner's automated-research
loop compounds because AI research has a *stationary, non-adversarial,
cheaply-evaluable, high-SNR* objective. **Markets invert all four.** That
reverses the sign of the mechanism: in Karpathy's loop, keeping the config
that improves `val_bpb` is correct because the signal generalises; here,
keeping the config that improves backtest expectancy is usually *wrong*,
because with enough configs the best one is noise by construction.

So: **more search over our existing 1-minute price bars has negative
expected value.** Compute is not the constraint. The binding, non-renewable
resource is **statistical budget** — every hypothesis tested lowers the
probability that our eventual positive is real.

**We have already run this experiment.** `crucible-autoresearcher` finds a
*planted* edge and finds nothing in the real backtest. That is a validated
instrument reporting a negative, which is far stronger evidence than an
unvalidated instrument reporting a positive.

**Consequence for how this repo works from here:**

1. A hypothesis is **registered before it is evaluated**. No exceptions, no
   "just looking".
2. The evidence bar **rises as the register grows**. Attempt 40 must clear
   more than attempt 3, and every report states its attempt count.
3. The lockbox is read **once, ever** — not once per hypothesis.
4. Every proposal states its **mechanism before the number is known**. No
   mechanism, rejected unrun. Best single filter against dredging.
5. Any automated proposer sees **DEV folds only**, enforced by the harness
   rather than by intention.

**Where new information can actually come from** (ranked; full reasoning in
[docs/RESEARCH-PROGRAM.md](docs/RESEARCH-PROGRAM.md)):

| Axis | Cost | Note |
|---|---|---|
| **Objective** | $0 | The challenge is a path-dependent SURVIVAL problem, not an expectancy problem. We may already hold a passing configuration and be scoring it wrong. |
| **Order flow** | quote first | Every search we have run used `ohlcv-1m`. The fade is explicitly an order-flow story tested only through price. Highest ceiling. |
| **Conditioning** | $0 | Five pre-specified conditioners, not a grid. |
| **New instruments** | ~$19 approved | Another draw from the same urn. |
| **More price search** | — | **Negative expected value. This is what the programme exists to prevent.** |

**Phases, each gating the next:** R0 trust the instrument (X1 reconciliation
+ register + alpha ledger + controls) → R1 spend nothing, re-score what we
own → R2 buy one new axis (order flow) → R3 harness the loop, pointed only
at an axis that showed life → R4 execution upgrade (broker paper account
with API fill reads; Trading 212 is ruled out — no futures).

**Recorded in advance, so it cannot be revised later:** the most likely
single outcome of the whole programme is a well-evidenced negative. Three
sealed verdicts already produced two honest NO-GOs and one real finding,
and the series is written from exactly that honesty. What would make the
programme worthless is running an unconstrained search, finding something
beautiful, and trading it.

## 8-NOW. WHERE THE PROJECT ACTUALLY STANDS (2026-08-01)

**We have no strategy with a demonstrable edge.** Said first because a task
list can otherwise read as progress:

- the fade's +0.1R was an **artifact** — its entry price cannot be obtained
  by any order (protocol #3a addendum)
- ORB never worked (#2), and has now been **audited clean** of the entry
  defect (#1-2 audit) — the problem was specific to the fade
- the one live signal, **H5 order flow**, is suggestive and **underpowered**:
  pooled r = -0.072 where the honest detectable floor is ~0.13
- protocol #4 is **stood down**, operationally as well as on paper

**What today did build** is a lab that is materially harder to fool, and
every detector came from a specific way it *had* been fooled:

| detector | the failure it came from |
|---|---|
| entry obtainability (`occams/execution.py`) | a sealed verdict resting on an impossible fill |
| power with dependence (`occams/power.py`) | a sample that looked twice its real size |
| edge-shape (`harness.edge_shape`) | expectancy misleading us twice |
| the SOP harness (`occams/experiment.py`) | a conclusion outliving its own script |
| charset + artifact guards | a stray CJK character; a 533 MB artifact carrying secrets |

**The working task list is the top section of `docs/TASKS.md`**, ordered
admin → small builds → free research → strategy. Everything below that
section is the reasoning trail, kept because *why* has repeatedly mattered
more than *what*, and not the place to look for what to do next.

**Spend:** $128.09 of a $150 cap (vendor actuals, not quotes). The $125 free
credit is exhausted; every further byte is real money.

## 8a. WHAT IS BINDING (revised 2026-08-01)

**A sealed verdict was found to rest on an entry price no order can
produce.** `fade.py` books a fill AT the range boundary at the failure
close, but at that moment price is INSIDE the range. Every placeable order
is negative on both instruments; only the assumption is positive. The +0.1R
is an artifact — see `docs/VERDICT-2026-07-06-v3-ADDENDUM.md`, logged as
protocol #3a. Protocol #4 is PAUSED.

**Consequence for how this repo thinks:** the machinery is now good, and
what is binding is no longer the instrument — it is the input. Seven years
of 1-minute bars on two of the most heavily traded futures on earth is
public information holding ~+0.03R gross against a +0.25R requirement.
Better machinery does not change that.

**The four gaps that would** (TASKS.md §Track E):

1. **E1 execution fidelity** — entry-obtainability is now a GATE
   (`occams/execution.py`): a strategy declares an ORDER and the fill is
   derived from what the market did. An entry price is never an input.
   Next: wire it into `verdict_run`, then go tick-level.
2. **E2 the real objective** — the challenge is a path-dependent SURVIVAL
   problem, not an expectancy problem. Never scored. We may already hold a
   passing configuration and be measuring it wrong.
3. **E3 measured costs** — commission is 0.05-0.09R/trade, decisive at this
   edge size, yet the cost model is an assumption. Every net number carries
   an unquantified error bar until it is measured off the tape.
4. **E4 power before alpha** — compute required n FIRST and refuse an
   underpowered test, because an ambiguous null still costs alpha.

## 8b-SOP. HOW AN EXPERIMENT RUNS — no exceptions

**Every experiment goes through `occams/experiment.py`.** Full procedure and
the reasoning: [docs/SOP-EXPERIMENT.md](docs/SOP-EXPERIMENT.md).

Six steps: state it falsifiably -> write the mechanism BEFORE the number
exists -> fix the analysis plan in the registration -> register (append-only)
-> run the analysis as a FILE through the harness -> read once and record
what it means, caveats included.

The harness enforces what a document cannot: hypothesis must be registered
first, analysis must be a file (inline cannot be archived, so it cannot be
run), script archived BEFORE it runs, stdout captured even on failure,
metrics parsed from the script's own `METRICS:` line rather than retyped,
sha256 re-checked so a silently edited script is caught. **`run()` has no
`force`, `skip` or `dry_run` — a procedure with an override is a
suggestion, and a test asserts none exists.**

Why it is code and not a checklist: on 2026-08-01 the session's biggest
finding was recorded without its script, because one variant had been run
inline. The conclusion outlived the means of checking it. The person
skipping the step is the same person who would have been reading the
checklist.

## 8d. WHO DOES THE MATHS — and where it runs (decided 2026-08-03)

**The LLM writes the estimator and argues about which estimand is right. It
does not execute arithmetic in a place nobody re-reads.** User's call, and
the evidence for it is in our own scripts: the ICT run wrote the same cluster
bootstrap **three times**, and `spearman()` -- the function behind H5, one of
only two live signals -- has never been checked against a reference
implementation.

This is the SOP rule extended one layer down. `METRICS:` already stops numbers
being **retyped** into the record (§8b-SOP); the maths engine stops them being
**re-derived** per script.

**Three layers** (TASKS.md §M):

1. `occams/stats.py` — primitives. Known-answer tested against scipy as a
   **test-only oracle**; property-tested for invariants.
2. `occams/estimators.py` — domain quantities. `reference=` is **required**
   and anything but `at_price` **forces a decomposition**.
3. `Result` + `@audited` → `calcs.json` archived beside `script.py` and
   `output.txt`, so three years on you see *which version of which estimator*
   produced each number.

**The calibration gate is the load-bearing part.** Every estimator must return
~0 on the dead world and ~the planted effect on the planted world (both
already exist, Phase 5). **This is what would have caught ICT-P2
automatically:** on a zero-drift random walk a valid estimator returns 0 and
the reference-price version returns +0.15 ATR.

**What it does not fix, and should never be sold as fixing:** choosing the
wrong estimand. ICT-P2's arithmetic was perfect. A module makes that choice
visible and reviewable; nothing makes it impossible.

**Standing rule, from ICT-P2:** before any forward-return measurement, state
where the reference price sits relative to price at the moment of
measurement, and decompose if it is not at price. Twice now an entry-price
choice has produced a result that survived every downstream test -- the
fade's unobtainable fill (#3a) and the swept level -- and neither was caught
by a significance test, because none of them asks *what price is this
measured from?*

**Where it runs (TASKS.md §N).** Execution moves to AWS; thinking does not.
Fargate for compute (Lambda's 15-minute ceiling breaches on E2's Monte
Carlo), Step Functions to orchestrate, a **separate stack** from the trading
one. The container image **digest** is recorded next to `engine_sha`, closing
a real hole: today's provenance pins the commit but not numpy/pandas.

Two things about that migration are non-negotiable:

- **The parity gate.** Every archived experiment must reproduce a
  **bit-identical `METRICS:` line** in the cloud. It works for free because
  runs are seeded and the originals are archived. Nothing else in Track N is
  complete until it is green.
- **The runner holds no data-vendor credentials.** Not scoped-down — none.
  Buying data stays a deliberate local action with user approval, and the
  cost guard is **cumulative in S3**, because a per-run cap that resets on
  each invocation is exactly the R2.1 overspend.

Deleting the local `data/` copy (N7) comes **last**. Re-buying costs $128.09
and the free credit is exhausted.

## 8e. THE PAYOUT HALF — what we have never modelled (2026-08-03)

**We score the evaluation and stop there. Passing is not the goal; being
paid is.** An external feature specification was reviewed and four items
kept (TASKS.md §Q, §M7, §D2.4); the rest was declined as a rebuild of
machinery that already exists and is tested.

The gap that matters: consistency rules differ **by stage**, and we hold
only the first. The evaluation tier we sealed has **no** consistency
requirement — but the qualified tier applies a **40% largest-day rule to
payout eligibility**. `rules.py::consistency_frac` is evaluation-only, so
every P(pass) we have ever quoted says nothing about whether the money
arrives. **P(first payout)** and **P(multiple payout cycles)** are the
honest objective, and Q1 is the cheapest high-value item on the list.

Also kept: **failure attribution** (E2 said P(pass) 0.042 / P(breach) 0.440
and never said *why* each path died) · **versioned, dated rule profiles**
with a staleness warning, because a provider retired a plan tier while its
own public pages still advertised it, and an undated rule snapshot is a
silent expiry · **block bootstrap**, which preserves the volatility
clustering a per-trade shuffle destroys.

**Why so little was kept.** ~60-70% of that spec is already delivered.
Rebuilding it costs months to arrive where we are, and it would not move the
binding constraint — **which is the input, not the instrument** (§8a).

**Three declines worth remembering as rules, not preferences:**

1. **No configurable intrabar traversal.** A tunable path assumption is a
   free parameter that moves results in a favourable direction. The
   conservative rule (adverse event first) is what kept verdict #2 honest
   and stays the only mode.
2. **No "price jump" data filter.** The quality probe flags 13 degraded days
   *including the 2020-02-27/28 crash* and deliberately does not remove
   them. A filter that silently drops real events launders a strategy.
3. **No manual-execution degradation model yet.** A good idea, but a
   second-order correction on a strategy with no first-order edge: it can
   only make a result worse, never find one. Revisit when something has an
   edge worth degrading.

**And what that spec was missing, which is the more useful lesson.** It had
strong statistical hygiene — walk-forward, purging, embargo, holdouts — and
**no epistemic hygiene**: no pre-registration, no entry-obtainability gate,
multiplicity as a dismissible *warning* rather than a spent budget, no
reference-price discipline, and ~26 reported metrics with no declared
primary. Every defect this lab has actually caught would have shipped.

## 8f. THE MATHS ENGINE IS DONE — what changes now (2026-08-03)

**M1-M7 complete.** The LLM writes the estimator and argues about which
estimand is right; it no longer executes arithmetic where nobody re-reads it
(8d). Concretely, every number from here on is produced by
`occams/stats.py` + `occams/estimators.py`, scored into a `Result` that
renders itself, logged to `calcs.json` beside the script and output, and
produced by an estimator that has passed a **dead-world / planted-world
calibration gate**.

**It earned its keep before it was finished.** It found a wrong number in
the register (C2's tied predictor, 28% off on MNQ), confirmed H5 and Z0
reproduce, and now rejects ICT-P2's reference-price artifact at **5 sigma on
a world with no forward drift at all** — mechanically, with no judgement
required.

**One rule came out of it, learned twice from opposite directions:** M4's
first tolerance was tighter than its own sampling error and failed a sound
estimator; M7's block-length rule lengthened blocks on iid data by reacting
to sampling error. **Do not act inside your own noise floor.**

### Sequencing from here

> **SUPERSEDED 2026-08-30 — kept because the reasoning still holds.** The
> sequence below is complete: M1-M7, X1-X3, Q1 and Q2 all landed, the
> experiment queue closed with a well-evidenced negative
> (`docs/PROGRAMME-CONCLUSION.md`), and both repositories are published.
> **Current sequence: A2-PUB + L-PUB (yours) → F1-F4 → N1-N4 →
> B-DECISION → N5-N7**, and `docs/TASKS.md` is the authority. The reopening
> question is B-DECISION, not the queue.

~~**X1 -> Q1 -> N1-N4 -> the rest of the experiment queue -> N5-N7.**~~

The gate on the experiment queue was M1-M4 and it has lifted. **Twenty-two
open items, and exactly one can change the standing answer** — the rest make
the lab better at being right. The binding constraint remains the INPUT, not
the instrument (8a).

Deliberately NOT first: the indicator layer, because it would hand X1 four
admissible predictors where one is registered, and **a choice that does not
need to exist should not be created**; and the cloud runner, because it
changes where X1 runs, not what it answers.

**Said before the run, not after:** the register stands at 15 hypotheses,
0.27 alpha, three of them spent unplanned on ICT. **The bar for X1 is higher
than when its queue was written.**

## 8g. PUBLICATION — the discipline, and where the writing lives
## (2026-08-30)

**Essay drafts live in `~/Documents/maverick-hq/20 - Essays/`.** Never in a
repo, never in a per-project folder alongside the research notes. Research
notes and figure assets stay with their project; only the essays are
centralised. Published essays go to Substack. **No essay text in any repo.**

**Three lab essays are drafted and `#status/review`** — written, awaiting
the author's edit. Each carries a `needs-your-call:` line naming the
decisions that are the author's rather than the drafter's, and a `voice:`
line stating plainly that the register was matched from an existing essay
and is not the author's own voice. The series still needs a real name.

### BOTH REPOSITORIES ARE LIVE (2026-08-30)

| repo | state |
|---|---|
| github.com/MaverickHQ/crucible-autoresearcher | MIT, 69 files, `a13dd0a` |
| github.com/MaverickHQ/prop-challenge-lab | Apache-2.0, `0a77e78` on `main` |

**All five repositories in the series are published**, so papers-with-code
is now true in fact rather than in premise. Four drafts (A2, L1-L3) are
written and awaiting review; **the head of the task list is now yours, not
mine.** The first item I can start unattended is F1.

### THE README SELLS THE INSTRUMENT, NOT THE RESULT (2026-08-30)

The README opened by saying the lab found nothing, which answers *"why
publish this?"* badly. Rewritten (`0a77e78`) around what the tool does:
**most frameworks optimise for expressiveness; this one optimises for
refusal.** Results cut to one short section pointing at the essays.

**Standing rule that follows from it: the repo sells the instrument, the
essays carry the results.** Anything that reads as a 1:1 log of what we did
belongs in `docs/` or an essay, not in the README.

`docs/` held 33 files, all research records, with no entry point. Added:

- `docs/ARCHITECTURE.md` — the pipeline, eight layers, why the seams sit
  where they do, extension-points table.
- `docs/USAGE.md` — testing your own strategy, in the order the gates will
  stop you.
- `docs/README.md` — an index splitting **how the lab works** from **what we
  ran through it**, saying you need none of the latter to use the former.

**Two failures worth keeping.** The charset gate rejected a Greek rho in the
design-effect formula in all three new files — the guard fired on the
documents describing the guards, which is the correct outcome. And three API
details in the first usage draft were invented: `DayPlan` takes
`buy_stop`/`sell_stop`/`stop_dist`, `Result` takes `estimate=` and requires
`n`, and `backfill.replay()` does not exist (`compare`/`render`/`all_ok`
does). **Verify every example against source before publishing a usage
guide** — on this repo especially, examples that do not run would be
self-parody.

### BRANCH LAYOUT — read this before committing (2026-08-30)

**`public` is the working line. `main` is NOT.**

    public   ->  origin/main   the published line. ALL work goes here.
    main                       full pre-release history. NEVER pushed,
                               NEVER developed. It exists so the 19
                               commits referenced by `engine_sha` in 45
                               archived records keep resolving.

This is counterintuitive and that is the point of writing it down: `git
checkout main` puts you on the **unpublished archive**, not the live line.
Local `main` and `origin/main` are unrelated histories — the remote's root
is a squashed commit, deliberately, because the pre-release history carried
an AWS account id in three commits and a leak anywhere in history is public
regardless of what HEAD says.

`push.default = nothing` is set locally, so a bare `git push` refuses rather
than publishing whatever branch you happen to be on.

**Published 2026-08-30: https://github.com/MaverickHQ/prop-challenge-lab**
(public, Apache-2.0). Everything after the root commit is ordinary history —
commit and push normally from `public`.

### The release-branch rule

**A release branch is cut fresh at push time and never maintained between
pushes.**

This was learned rather than designed. `public-release` was built, audited
clean, and then went stale in **two commits** — it would have published a
repository whose `artifacts/plots/` was missing the figure an essay points
at. A long-lived squashed branch drifts silently, and the drift is invisible
precisely because the branch was verified once and felt finished.

Cut it, audit it, push it, and let it be superseded next time.

**This applies to an INITIAL publish only.** Once the working line descends
from the published root commit, you push ordinary commits like any
repository. See TASKS.md D2.6 for the switch.

**And do NOT solve a contaminated history by starting a new repository.**
Considered and declined 2026-08-30: **45 archived records carry an
`engine_sha` referencing 19 distinct commits, all of which resolve in this
repository.** A fresh repo seeded from a squash has none of them, and the
register's provenance chain would dangle immediately. The old lineage is
kept locally as `archive/pre-release` — never pushed, never developed, but
**reachable**, which is the entire job it has.

### What the audit does and does not cover

`scripts/prepublish_audit.py` scans **full history** — every commit message
and every blob at every revision — for forbidden terms, charset hazards
**and infrastructure identifiers** (account ids, access keys, ARNs carrying
an account, bot tokens, private-key blocks). That last class was added
2026-08-30 after an AWS account id was found sitting in six files and three
commits: none of it is a credential, so no secret scanner had ever flagged
it.

**Re-run it immediately before any push.** A term removed at HEAD is still
public if it is anywhere in history, and the audit is one commit further
from its last clean run every time something lands.

**Sibling repository, already published:** `crucible-autoresearcher` went
public 2026-08-30 (single orphan commit, MIT). That is a *different
project* — the Crucible series — and its essays must not be mixed with this
lab's. The lab essays were deliberately held until after that series' Outro
so they read as independent corroboration rather than spoiling its close.

## 8c. WHERE EVIDENCE LIVES — the durable archive (defined 2026-08-01)

**A result you cannot reproduce in three years is not evidence.** Two S3
buckets exist and they are not interchangeable:

| | `occams-campaign-statebucket-*` | **`occams-research-<account-id>`** (LIVE 2026-08-01) |
|---|---|---|
| Purpose | **live operational state** | **immutable evidence** |
| Contents | `state/paper_state.json`, `logs/offset.txt` | raw data, register, experiments, artifacts |
| Lifecycle | 90-day noncurrent expiry | **no expiry, ever** |
| Owned by | the `occams-campaign` stack | its own stack, `DeletionPolicy: Retain` |
| Survives `sam delete`? | **no** | yes — that is the point |

**The rule that matters most: operational state is exported, never
relocated.** `paper_state.json` and `offset.txt` are the running system's
working memory, read and written every five minutes. Moving them takes the
poller down. Evidence is *copied* out; live state stays put.

**Archive prefixes:** `raw/` (vendor data, byte-identical, write-once) ·
`derived/` (Parquet, queryable) · `hypotheses/` + `experiments/` (the
append-only register) · `artifacts/` · `provenance/`.

**Standing rules** (full list: TASKS.md §Track D):

1. `raw/` is write-once; deletion denied by bucket policy. Deliberately
   **not** Object Lock in compliance mode — if an upload ever carried the
   venue name, compliance mode would make the slip permanent.
2. The register is **append-only**. Corrections append with `supersedes`;
   nothing is edited. A register that can be rewritten proves nothing.
3. **No artifact without provenance**: sha256, source, cost, and the
   **`engine_sha` that produced it**. Without the commit pinned you cannot
   later tell which engine produced a number.
4. The **privacy and charset scans run on every upload**, same as they gate
   the Lambda build. Refuses, never warns, no override.
5. Never public. All four blocks on, non-account principals denied,
   non-TLS denied.

**Query layer:** DuckDB over Parquet directly from S3 — no Glue, no Athena,
no catalog. Same razor as the no-database decision for the ledger.

**Tooling:** `occams/archive.py` — `put` (scan, hash, upload, then append
provenance, in that order: a manifest row for a failed upload would be a
lie) · `get` (fetch and **verify sha256**; a download that does not verify
is not a restore) · `register_hypothesis` / `record_experiment`.
Backfill: `scripts/archive_backfill.py`.

**Cost:** ~$0.01/month today; ~$0.46/month if order-flow depth data is
bought. Counts against the same `project=occams` budget.

## 9. TWO WORKSTREAMS (split 2026-07-30)

> **THIS SECTION IS A JULY SNAPSHOT — DO NOT READ IT AS CURRENT
> (marked 2026-08-30).** Protocol #4 is no longer running; the programme
> concluded 2026-07-06 with three sealed verdicts and no tradeable edge, and
> the A/B split below was superseded on 2026-08-09 by the two workstreams in
> `docs/TASKS.md` (**A = Crucible essays, B = the lab**). The B0 Databento
> spike named as "next" was answered in `docs/AWS-RECON.md`.
>
> Kept rather than deleted because the interaction-model rules (`/ack` is an
> acknowledgement not a veto; moving level production to engine output is a
> PAPER-PREREG §4 amendment; the sample-size honesty guard) are still
> binding if the paper track ever reopens. **A status section that is not
> re-checked against the world becomes an instruction to redo finished
> work** — the same trap that nearly cost three re-drafted essays.

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
