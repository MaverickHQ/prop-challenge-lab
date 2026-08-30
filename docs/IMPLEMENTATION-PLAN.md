# Implementation Plan — occams-trader

Kiro-style spec-driven task list for the work opened by the level-400 review
of 2026-08-30. **Requirements and design live elsewhere** — this file is
*what to build, in order*:

- Requirements & scope: `CLAUDE.md`, `docs/RESEARCH-PROGRAM.md`
- The review that opened this work: `docs/TASKS.md` §G and §H
- Design decisions (the "why"): `docs/CONTEXT.md`, `docs/M5-BACKFILL.md`
- Architecture: `docs/ARCHITECTURE.md`

> **One authority, not two.** `docs/TASKS.md` is the BACKLOG — what exists
> and why. This file is the EXECUTION ORDER for tracks G and H. Task state
> lives here; `TASKS.md` points at it. The two-copies-one-drifts problem
> already cost this project a stale status note that nearly caused three
> published essays to be rewritten, so it is stated rather than assumed.

## Conventions

- **Gated.** Phase 1 blocks Phases 2–5. It removes the failure mode that has
  already occurred once, so running the recomputes ahead of it repeats a
  known error twelve more times.
- **Reproduce before you measure.** Every recompute task begins by
  reproducing the archived run through `reproduces()`. A recompute that does
  not reproduce is a measurement of something else, and no statistic derived
  from it is admissible. This is an acceptance criterion, not a nicety.
- **Frozen evidence is never edited.** `scripts/exp_*.py` are archived
  byte-for-byte as the artifact that produced a registered result and are
  excluded from lint deliberately. Recomputes IMPORT them; they do not
  reformat, refactor or retype them.
- **Append, never overwrite.** Every resolution supersedes rather than
  replaces. `hypotheses/` and `resolutions/` are write-once.
- **Commit per phase**, ending each message with:
  `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`
- **Autonomy legend.** `[auto]` = completable unattended: code, tests, local
  data, $0, no new network egress. `[needs-user]` = requires money, a
  judgement about the research, repo settings, or publication.

## Scope note — what this work does and does not buy

**Track G does not change the trading conclusion and is not sequenced as
though it might.** H-RECLAIM reproduced its archived numbers 10/10 to three
decimal places; M5 previously reproduced H5 exactly and Z0 to twelve
decimals. What the recompute buys is **verdicts** — bare means resolving to
`null` (inside the floor) rather than "small negative" — not different
numbers. The gap to the requirement is a factor of ten and no confidence
interval closes it.

Do this to make the register honest. Do not do it expecting an edge.

---

## Phase 1 — Make the recompute safe `[auto]` — GATES PHASES 2-5

- [ ] **1.1 Import the frozen scripts instead of transcribing them.**
  Replace `backfill_f5._reclaim_rows` with a call into
  `scripts/exp_reclaim.py`'s own `run(inst)`. The frozen scripts are
  importable modules; loading one and calling its function makes divergence
  **impossible** rather than merely detectable.
  **Why this is first:** transcription already produced a clean
  `detectable` result at 2.33x floor for a strategy that does not exist —
  breakout bar conflated with the failure close, excursion term dropped
  from the stop, slippage dropped from sizing. `reproduces()` caught it.
  The gate should be the second line of defence, not the first.
  **Verify:** H-RECLAIM still reproduces 10/10 and its primary still reads
  −0.239R [−0.291, −0.184]; delete the transcribed copy and the numbers do
  not move.

- [ ] **1.2 A loader for frozen scripts.** `backfill_f5.frozen(name)` —
  imports `scripts/exp_<name>.py` by path without executing its top-level
  side effects where possible, and raises a clear error naming the script
  when its shape does not permit import.
  **Verify:** a unit test loads two frozen scripts and asserts the loaded
  module's `__file__` matches the archived sha256 in the manifest.

- [ ] **1.3 Collapse the entry-point sprawl.** `experiment.run` executes an
  archived script with **no arguments**, so each hypothesis needs its own
  entry point — but fourteen near-identical four-line files is the wrong
  answer. Generate them from a template at build time, or give
  `experiment.run` an explicit argv contract that is recorded in the run's
  `config` so the archived script remains re-runnable.
  **Verify:** re-running the archived entry point for H-RECLAIM reproduces
  its recorded metrics byte-for-byte.

- [ ] **1.4 Hoist the timezone conversion out of the groupby loop** (H5,
  first half). `hm = ts.dt.hour*60 + ts.dt.minute` is recomputed per day
  group — **2.7s of 8.4s, 3,701 redundant conversions** — while `load()`
  already computes it once and discards it.
  **Verify:** profile shows `_local_timestamps` gone from the top ten; the
  reproduction gate still passes 10/10.

- [ ] **1.5 Commit:** `G1: import the frozen scripts, do not transcribe them`

## Phase 2 — The H-family `[auto]`

Two hypotheses sharing H-RECLAIM's shape. Runs first because the pattern is
already proven on one of them.

- [ ] **2.1 H-STOPWIDTH.** Four-rung stop ladder. Estimand: expectancy per
  rung with a cluster-bootstrap CI, and the ladder's flatness stated as a
  measured claim rather than an observation. Archived: ladder flat, 77.5%
  exceed stop.
- [ ] **2.2 H-SECONDPUSH.** Archived: gross +0.011 → net −0.082 R. The
  estimand is the NET expectancy; the gross figure is a comparator.
  **Watch for:** this is the family where costs consumed the whole signal,
  so the cost model must come from `Costs`, not be re-derived.
- [ ] **2.3** Record both via `experiment.run`; resolve `scored` with
  `supersedes` naming each `documented` record.
- [ ] **2.4 Commit:** `G3: H-STOPWIDTH and H-SECONDPUSH recomputed`

## Phase 3 — The ICT family `[auto]`

Three runs, and **the first genuinely stochastic comparison in the
backfill** — every prior one was deterministic. Expect `backfill.compare`'s
stochastic tier to be exercised for the first time.

- [ ] **3.1 ICT-P1-FVG.** Archived: −0.00036 ATR, d −0.0015. Note the frozen
  script carries its own `cluster_boot` — import it, then compute the
  statistics through `occams.stats` and report BOTH, because a difference
  here is a finding about the old function (an estimator swap), not a
  defect.
- [ ] **3.2 ICT-P2-SWEEP.** Archived: −0.159 ATR, d −0.43, **94.8%
  reference price**. The recompute must use `estimators.forward_return`
  with `reference=AT_LEVEL, decompose=True` so the positional term is
  visible in the record rather than in prose.
- [ ] **3.3 ICT-P2-CONTROL.** The corrected reading. Must supersede 3.2's
  resolution explicitly.
- [ ] **3.4 Commit:** `G4: the three ICT runs recomputed`

## Phase 4 — Instrument and costs `[auto]`

- [ ] **4.1 X1-RECONCILE.** Archived: reproduces verdict #3 to 3 d.p. This
  one's estimand IS agreement, so it resolves `audit`, not `scored` — do
  not manufacture an effect size for a reconciliation.
- [ ] **4.2 Z04-ORB-OBTAINABLE.** Already resolved `audit` from its archived
  verdict. **Verify only** that the recompute path agrees; do not
  re-resolve.
- [ ] **4.3 E3-COSTS.** Archived: MES spread 1.0 tick, MNQ 2.0. Proportions,
  so use `stats.proportion_ci` (Wilson), not a mean shift.
- [ ] **4.4 C2-MAE-PREDICTABLE and H5-FLOW-PREDICTS.** M5 already re-scored
  both through the audited engine (`scripts/backfill_m5.py`). This task
  **promotes those results to `scored` resolutions** — it is bookkeeping,
  not new computation. H5 must resolve `inconclusive`, not `null`: its
  n_eff is 474 against a 0.131 floor.
- [ ] **4.5 Commit:** `G5: instrument, costs and the M5 promotions`

## Phase 5 — The Monte Carlo three `[auto]`

Seeded, so reproduction is exact or the seed is wrong.

- [ ] **5.1 E2-OBJECTIVE.** Archived: P(pass) 0.042 vs a 0.55 gate. Pin the
  seed explicitly in `config`; a Monte Carlo whose seed is not recorded is
  not reproducible even by its author.
- [ ] **5.2 Q1-PAYOUT-PATH.** P(pass) 0.042 vs P(first payout) 0.012.
  Proportions with Wilson intervals. **`payout.record_day` takes CUMULATIVE
  equity** — the sharpest edge in the API and the first thing to check if
  the numbers look wrong.
- [ ] **5.3 Q2-ATTRIBUTION.** Four proportions summing to 1: 4.2% pass,
  44.0% breach, 35.4% timeout ahead, 16.4% timeout underwater. Assert the
  sum in the recompute — a partition that does not sum is a defect no
  interval will reveal.
- [ ] **5.4 Commit:** `G6: the Monte Carlo three recomputed`

## Phase 6 — Close the loophole `[auto]`

- [ ] **6.1 Restrict `kind="documented"`.** Refuse it when an archived
  script exists for that hypothesis: **if it can be run, it may not merely
  be described.** This turns the judgement error that produced fourteen
  transcribed resolutions into something the code refuses.
  **Verify:** a test asserts `resolve_hypothesis(kind="documented")` raises
  for a hypothesis with an archived script, and succeeds for one without.
- [ ] **6.2 Audit the register.** Assert every hypothesis with a scored
  result resolves `scored`, and report any remaining `documented` record
  with the reason it is still legitimate.
- [ ] **6.3** `make report` and republish; verify the served page is
  byte-identical to the committed artifact.
- [ ] **6.4 Commit:** `G7/G8: documented is now refused where a script exists`

## Phase 7 — Remaining hygiene `[auto]`

- [ ] **7.1 Wire up the parquet layer** (H5, second half).
  `scripts/to_parquet.py` is written and unused; `data/derived/` does not
  exist. **28 MB vs 200 MB, 0.3s vs 1.4s.** pyarrow is now a declared
  dependency, so this is wiring, not new work.
- [ ] **7.2 Make the console rebuildable without S3** (H4). `make report`,
  `make plots` and `make reproduce` all require the author's bucket, so the
  two most compelling artifacts cannot be regenerated by anyone else. Ship
  the register cache, or let `make report` fall back to a committed
  snapshot.
  **Verify:** `make report-offline` succeeds in a clean clone with no AWS
  credentials.
- [ ] **7.3 Commit:** `H4/H5: parquet wired, console rebuildable offline`

---

## Blocked — needs a decision, not engineering

- [ ] **B-DECISION.1** `[needs-user]` **OPEN.** Costed 2026-08-30: closing
  X3 needs **3.14x** the sample = 1,124 additional sessions/instrument at
  **$186–$291** against **$21.91** of headroom, requiring the cap to rise to
  ~$315–$420. Estimates have historically landed 4x, 1.5x and 1.5x wrong.
  The free credit is exhausted. **The prior, recorded before any purchase:**
  a null that closes the programme cleanly, or a small positive that is
  publishable and not tradeable. Details in `TASKS.md`.
- [ ] **H3** `[needs-user]` **AWS teardown, ~$100/year.** $10.50/month with
  zero Lambda invocations in 14 days; the archive itself is $0.08. Also 4
  secrets and 13 KMS keys across three regions while the configured default
  is a fourth. Keep the bucket, drop the scaffolding. Gated on whether the
  N track is dead or paused — the same question as B-DECISION.
- [ ] **A2-PUB** `[needs-user]` review and publish the addendum.
- [ ] **L-PUB** `[needs-user]` review and publish the three lab essays.
  **The series still has no name.**

## Done

- [x] **G0** H-RECLAIM recomputed, resolved `scored` (`4e9e9f1`).
- [x] **H1** CI — `.github/workflows/check.yml`, green (`1e2545d`). Found
  six defects on its first three runs, every one invisible while the checks
  only ever ran on the machine that had everything.
- [x] **H2** launchd jobs unloaded (`84376de`); plists kept, reversible.
- [x] **F1-F5** the research console, published and verified.
