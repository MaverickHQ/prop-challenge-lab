# CONTEXT — Level-400 analysis (the why behind every design choice)

Private, local-only. The venue is never named in this repo (CLAUDE.md §0).
This document is the distilled blank-sheet analysis that produced the design;
[TASKS.md](TASKS.md) is the execution order.

---

## 1. Mission

Pass a single-step futures prop-firm evaluation: reach the profit target
before an end-of-day trailing max-drawdown ratchets the account out.
**Rule set CONFIRMED 2026-07-02 (P3 sealed)** — the chosen $50k plan (name and
vendor details in git-ignored `venue.local.md` only):

| Rule | Value ($50k account) |
|---|---|
| Profit target | **+$3,000** (6%) |
| Trailing max drawdown (**EOD**) | **−$2,000** (4%) — trails EOD balance high, not intraday; locks at start balance once cleared |
| Intraday daily-loss guard | $1,000 — **intraday lockout, NOT a failure** (confirmed 2026-07-04: liquidate + lock until 6PM ET, account survives); our own ~$500 stop binds first |
| Consistency (evaluation) | none |
| Min trading days | 1 |
| Max position | 3 minis / 30 micros — far above our 1–3 contracts |
| Funded phase (differs) | 40% payout consistency, **$1,500/payout cap, ≤50% of profit, 5×$200-day qualification, ≤4 req/mo**, no entries ±2 min around tier-1 news — full verified payout layer: [RULES.md](RULES.md) |

Chosen over the sibling plans because the eval geometry ties the cheaper one
(target:DD = 1.5 in both; the third plan is 2.29 — materially harder) and our
cadence makes the dropped consistency/guard rules free. Funded-phase terms are
weaker but upgradeable after the strategy proves real. **Automation policy
(P5, checked): bots/full-auto prohibited; self-generated signals executed by a
human are compliant — which is our design by construction.**

The EOD-trailing plan family is chosen deliberately: every binding rule
settles on the daily close, which simplifies both the sim and live management.

## 2. The physics (what dominates everything else)

**2.1 The geometric floor.** The challenge is a two-barrier ruin problem.
A zero-edge trader with disciplined fixed-risk sizing has
P(hit +$3,000 before −$2,000) ≈ 2000/5000 = 40% static, degraded by the
trailing ratchet and cost drag to roughly **~28–35% P(pass) with NO edge at
all** (the confirmed $2,000 barrier is tighter than the −$2,500 first
assumed; risk-per-trade re-derives to ~0.3–0.4% ≈ $150–200, i.e. 10–13R of
barrier room). Two consequences:

- The firm's fee model prices exactly this — most entrants lose to risk
  behaviour, not signal quality.
- **Any claimed edge must be measured as P(pass) above this floor**, which is
  why the random-entry null model is the project's central experiment.

**2.2 Cost drag — the hardest number in the system.** MES round trip
(commission ≈ $2.50 + 1-tick slippage/side ≈ $2.50) ≈ **$5 ≈ 1 full ES
point per trade**. A strategy must clear >1 pt/trade gross to be a coin flip.
Every backtest runs with these costs; an optimistic-fill result is void.

**2.3 The arithmetic must reach the target.** At 0.3–0.5% fixed risk
($150–250/trade), 1.5R targets, ~55% win rate, ~40 trades ≈ +$2,300–3,000.
The dynamic range works — this is the direct fix for the Crucible's central
blocker (a %-based daily backtest range-bound at ±2–3% where the rules could
never bind).

**2.4 Probability tree (honest, pre-commitment):**

| Stage | Estimate |
|---|---|
| P(research finds a real OOS edge passing the gates) | ~30–50% (ORB is well-known → partly decayed; coin-flip prior) |
| P(pass per attempt · gates passed) | ~55–70% → 1–2 attempts expected |
| P(project ends in a passed challenge ≤ 2 attempts) | **~25–40%** |
| P(project ends in knowing the truth for ~$200–400) | ~certain |

The single most likely outcome of the honest process is a **validated no-go
with no fee paid** — that is the process succeeding.

*Calibration (research pass 2026-07-05, [EVIDENCE.md](EVIDENCE.md)):* the
population base rate is ~16.8% per attempt (verified competitor-firm
disclosure) and published backtests found no unfiltered-ORB edge after costs
— both consistent with this tree's low prior on the first row and with
no-go as the modal outcome. Only ~a third of funded traders ever get paid,
which is why the funded phase is designed before attempt one (§8) and
`funded_value` carries an operational haircut at seal.

## 3. Inheritance from The Crucible (what transfers, what dies)

| Asset | Verdict | Reason |
|---|---|---|
| Methodology stack: pre-registration, walk-forward + sealed lockbox, positive control, null baseline, honest reporting | **REUSE — the crown jewels** | Zero lines of code; the entire defence against believing our own backtest |
| Literal-rules-as-objective (ChallengeObjective concept) | **REUSE** (rewritten in dollars) | The series' hardest-won design lesson |
| ATR (stops/sizing); regime concept | ATR now; regime = v2 filter only | ATR is load-bearing; regime is second-order |
| Ports/adapters seams, spend-metering discipline | REUSE as habits | Cheap, proven |
| MetaLoop + LLM proposer | **DISCARD (shelved)** | Validated on an 8-dim space, but the razor shrinks the space to ~5 params where grid search is complete and free. "Validated" ≠ "necessary" |
| LLM player/coach in execution; per-bar enricher | **DISCARD (measured)** | 40–90× fewer trades, no quality gain (2/5 vs always-trading baseline), cost, latency, non-determinism |
| %-based daily backtest, yfinance daily bars | **DISCARD** | The ±2–3% ceiling — root cause of the series' negative result |

Net: from three repos, what survives is almost entirely **discipline, not
code** (~1,500–2,000 fresh lines replace it, most of which are tests).

## 4. Architecture

Four components + comms (see CLAUDE.md §2 for the table). Key inversions
vs the series:

| Layer | The Crucible | occams-trader |
|---|---|---|
| Execution (per bar) | LLM player (~$0.003/bar, slow, stochastic) | **Deterministic rules — fast, free, reproducible** |
| Research (per experiment) | Mostly deterministic proposer | Grid search (LLM proposer shelved; space is small) |
| Evaluation | %-based daily backtest | **Contract-level intraday dollars** |
| Coach | Per-decision adversary | **Evening coach (v2, only if it proves value)** — per-day review, advisory only, no execution path |

## 5. Strategy specification

**One family: Opening-Range Breakout (ORB), RTH, MES/MNQ, 5-min bars.**

- Entry: stop order on break of the first N-minute range (N ∈ {15, 30});
  optional VWAP-side filter (long only above VWAP, short only below).
- Stop: k × ATR (k ∈ ~{0.75–1.5}); Target: fixed R multiple (~{1.0–2.0});
  time exit: flat by session close. Max trades/day ∈ {1, 2}.
- **~5 parameters total** — small grid, small overfitting surface; the razor
  and the lockbox pull the same direction.

Why ORB and not an indicator stack (MAs + 61.8% fib + volume): structural
rationale (overnight information release at the open), best-documented
intraday futures family, and — decisive — **its cadence fits the rules**:
1–2 fixed-risk trades/day produces many small days, exactly what the
consistency rule and min-days demand. A retracement zone may appear in a v2
pullback family as *one searched parameter bound* (38–79%), not a belief.

**The risk manager is half the strategy** (and is exactly how the passing
minority actually trades):
fixed risk 0.3–0.5%/trade · hard daily loss stop (~1%) · stop the day at
target-passed · max 2 trades/day · **calendar filter** (no entries within a
window around tier-1 releases; flat into FOMC) · DD-proximity throttle (v2).

**Execution model:** once the opening range forms, place resting OCO
brackets, walk away. **The stop orders are the alert** — zero reaction
latency, no screen-watching. This is why there is no alerting problem to
solve and no dashboard to build.

## 6. The quant layer (where the sophistication actually lives)

Not indicators — four things:

1. **Sizing from ruin math.** Risk-per-trade derived from the trailing
   barrier and a target P(survive to target); ~0.3–0.5% falls out. Not
   Kelly: Kelly with *uncertain* edge systematically overbets into a
   trailing barrier.
2. **Multiple-testing discipline.** A few-hundred-combo grid guarantees
   lucky maxima. Requirements: report the full grid *distribution*; select
   only from **parameter plateaus** (lone spike = noise, plateau =
   structure); the sealed lockbox is the sole final arbiter.
3. **The Monte Carlo ruin model.** P(pass), median days, P(breach) as a
   function of (WR, R, trades/day, costs, ratchet), over ≥1,000 random
   start dates — because passing is path-dependent: the same strategy
   passes or fails depending on which Monday you start. Cross-check with the
   semi-analytic two-barrier approximation.
4. **Cost modelling** (§2.2) — held fixed and conservative in every run.

## 7. Backtesting approach

- **Data:** one-off purchase — Databento or FirstRateData, MES/MNQ 1-min
  history (~$100–200), resampled to 5-min for signals, 1-min retained for
  stop/target resolution. Local files, git-ignored, licensed — never
  redistributed. TradingView is *disqualified* as data source/backtester
  (no bulk export, optimistic fills, can't express the validation stack) but
  *valuable* as an independent Pine reimplementation for signal-parity
  checking, plus charts/alerts.
- **Simulator:** bespoke (~400 lines), bar-loop, event-honest. Conservative
  intrabar rule: if stop and target are both touched in a bar, **the stop
  fills first**. Dollar P&L with commissions + slippage. No backtesting
  framework — opaque fill models cost more complexity than they save.
- **Validation stack (all mandatory):** anchored walk-forward (select
  in-sample, score OOS only) · sealed lockbox = final ~20%, opened once ·
  robustness splits by year and vol-regime · Monte Carlo over start dates ·
  the null model as the comparator for every claim.

## 8. Experiment pipeline (strict order; each step gates the next)

1. **Positive control** ($0, day one): plant a known edge in the sim; the
   harness must find and report it. No result is interpretable before this
   passes. (Series lesson: we ran it last; never again.)
2. **Null model** ($0): random entries + the full risk manager → measures
   the geometric floor (~30–40%) directly. Every subsequent claim is
   "+X points above null".
3. **Pre-registered grid sweep** ($0 compute): seal PREREG (params, folds,
   null, thresholds) *before* running; sweep the ~5-param grid; select from
   OOS plateaus only.
4. **Challenge Monte Carlo** on the one survivor: ≥1,000 simulated attempts,
   dev + lockbox. **Go/no-go gate (pre-registered): P(pass) ≥ 55% AND
   ≥ null + 15 points.** Then the economics: E[attempts] × fee vs funded
   value.
5. **30-day paper gate** (locked commitment): live data, sim execution, the
   real morning/evening workflow, **parity logged per trade** with a kill
   threshold. Pass → one live attempt run as an experiment, with a written
   runbook (fixed risk table, daily stop, stop-at-target, no discretionary
   overrides).
6. **Funded-stage parameterization** designed *before* attempt one — most
   challenge-passers blow the funded account because they trained on
   pass-geometry; we validate both modes up front.

## 9. Comms & UI (an information ration, not an application)

Two decision moments/day → two pushed documents/day. **No dashboard** — a
live P&L screen induces watching, watching induces intervention, and
intervention is the #1 discipline failure. Boredom is a feature.

| Moment | Artifact | Contents | Channel |
|---|---|---|---|
| ~10:00 ET (15:00 London) | **Plan Card** | levels (buy/sell stops, SL, target, size) or "NO TRADE: <reason>" | Telegram |
| Evening (~22:15 London, post-settle) | **Debrief** | parity log (live vs sim, cumulative shortfall), **fuel gauge** (equity vs ratchet line vs target, days), challenge state | Telegram + Obsidian daily note; S3 copy once on AWS |

**Human-as-sensor (grilled + sealed 2026-07-02).** The system needs exactly
two live facts per day, and both come from the human, who is at the platform
anyway (the venue bans automation):
- `/range <high> <low>` after the opening range forms → bot validates against
  ATR bounds, applies no-trade filters, replies with the full order plan
  (entries, stop, target, size from the ruin math). **No live market-data
  feed exists in v1** — the entire vendor/entitlement/feed-reliability
  problem is deleted. Databento-live is the v2 escape hatch only if the
  manual step proves error-prone in the paper gate.
- `/fills <details>` (or `none`) after the close → echoed back for
  confirmation, then P&L, trailing-DD state, and parity update.

**Cron-driven, command-fed (the FitnessCore reminder pattern).** The
scheduled runs own the artifacts; the commands merely feed them. Evening cron
always fires: fills logged → full Debrief; missing → provisional sim-view
Debrief + "reply /fills to reconcile" nudge; a late `/fills` recomputes and
resends the final. Morning symmetrically: no `/range` by ~15:05 London → the
cron sends a reminder instead of silence. The human can never *silently*
break the record.

**Deployment (grilled + sealed 2026-07-02):** runners are plain CLIs
(`occams morning` / `occams evening`) throughout research; lifted into the
FitnessCore SAM pattern — 2 EventBridge crons + one webhook Lambda (for
`/range`+`/fills`) → Telegram — as the *first act* of the 30-day paper gate,
so the gate rehearses the production path. **S3 becomes the durable store for
trading reports** (Debriefs, parity logs, MC reports) at that lift. No SQS,
no ECS, no DynamoDB unless a concrete need appears (SignalFlow's machinery
explicitly rejected as overkill for 2 runs/day).

The fuel gauge renders as Telegram text/emoji first (razor); PNG only if
text proves insufficient. The same gauge appears in backtest MC reports so
live trading *feels* rehearsed. Research-phase UI = generated Markdown
reports + PNG plots per run; Jupyter for exploration. No database until a
concrete need appears (results are CSV/parquet).

## 10. News & ingestion

**News is a calendar problem, not a feed problem.**

- v1 = a **~40–50 row/year CSV of tier-1 scheduled releases** (FOMC, CPI,
  NFP, PPI, GDP) from official published schedules (BLS, Fed), refreshed
  quarterly; historical dates are archived → the filter is backtestable with
  zero lookahead. Enters the grid as one boolean + one window parameter.
- **Breaking news: deliberately nothing.** Resting stops bound the loss per
  event to one R (already priced into the ruin math); news reaction is
  either sub-second (not our game) or regime-level — and **ATR sizing is
  already the regime/news-reaction mechanism** (wilder tape → wider stop →
  smaller size). A news feed would cost more than the edge and import
  temptation to intervene.
- **LLM news/sentiment in signals: cut** on epistemological grounds — you
  cannot backtest what the LLM would have said in 2019 without point-in-time
  archives (institutional cost) and a frozen model; an untestable input is a
  belief, not a signal (the series lesson, restated). If ever revisited
  (funded-stage v2, and only if it demonstrates value): filter-only — may
  reduce size or skip a day, may never add or enlarge a trade. The evening
  coach may quote the day's news in the Debrief (advisory prose, no
  execution path, no parity requirement).

## 11. Budget

| Item | Cost |
|---|---|
| Historical 1-min data (one-off) | ~$100–200 list; **~$0–25 net after the verified $125 new-user credit (2026-07-04)** |
| Compute / LLM | ~$0 (deterministic; LLM = collaborator only) |
| Telegram bot | $0 |
| Challenge fee (only if gates pass) | ~$100–170/attempt, 1–2 attempts expected |
| **Total to a truth** | **~$200–400 without an attempt; ~$400–700 including one** |

## 12. What would make this exceptional (kept from the analysis)

1. **Measured live/backtest parity** with a pre-set kill threshold — the
   habit that separates desks from retail.
2. **Designed for the funded account, not just the pass** (two validated
   parameterizations before attempt one).
3. **The null model as the public enemy** of every claim.
4. **Pre-registered kill criteria** — the project is allowed to end in a
   validated *no*, and that ending is a success.

---

## 13. Addendum (2026-07-06): the verdict, and the Family-2 program

The sealed run answered the question this document was written to ask:
**validated NO-GO** — the ORB family misses the gates by 3–10× in every
fold, on both instruments, with the null at 0.000 *while trading* (no
pass-by-luck channel at disciplined sizing). §2.4's probability tree
resolved to its modal branch; per §12.4 that is the project succeeding.
Records: `VERDICT-2026-07-06.md` (v1, void for instrument defect — a
lesson in validity gates), `VERDICT-2026-07-06-v2.md` (the real answer),
vault E-001/D-003.

The continuation is the **Family-2 research program** (TASKS.md §Family-2):
feasibility-first (compute the required WR × R × frequency × horizon ×
plan-geometry frontier before hunting edge — horizon is purchasable, the
eval has no deadline), dev-fold diagnostics, ONE new family under PREREG
v3 (prior: opening-range-failure / VWAP-reclaim mean reversion), and the
paper gate promoted to true lockbox because the 2019–2026 historical folds
are now weakly contaminated by the ORB read. Everything in §§1–12 —
architecture, rules engine, harness, discipline — carries forward
unchanged; only the strategy family died.

## 14. Addendum (2026-07-09): the re-founding — from answer to instrument

The challenge question is answered (§13, three sealed verdicts, $0 fees).
What remains is more valuable than the question: a validated laboratory —
rules-as-objective engine, feasibility frontier, sealed-protocol workflow
with validity gates, and one real out-of-sample-persistent finding. The
re-founded charter runs it as an **edge-finding instrument** with two
monetization layers (personal trading via the paper campaign now; the
challenge later only past the sealed +0.25R bar) and a **timed
publication track** (the methodology and verdicts are the publishable
IP; the fade finding's parameters are the only alpha question, and it
resolves itself once paper data exists — decide at the gate, ~3 months).
The honest-iteration problem is named and governed: sealing one protocol
prevents peeking; only the multiplicity ledger (PROTOCOLS.md) plus the
prospective paper gate prevent sealing-until-it-passes. Tracks and
tasks: TASKS.md §Lab-Program.
