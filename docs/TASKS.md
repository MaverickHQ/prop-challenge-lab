# TASKS

> **This top section is the working list.** Everything below it is the
> detailed backlog and the reasoning trail — kept because the *why* has
> repeatedly mattered more than the *what*, but not the place to look for
> what to do next.
>
> Ordered deliberately: **small admin first, strategy last.** Anything that
> takes ten minutes and unblocks or clarifies something goes above work that
> takes a week and might not pay.

# MASTER TASK LIST — consolidated 2026-08-09

Two workstreams. **A is nearly finished and its remaining items are small.
B is where the substance is.**

## Recommended sequence

**H2 → H1 → B-DECISION.1 → G1 → G3-G8 → H3/H4/H5 → A2-PUB + L-PUB**

**Revised 2026-08-30 after the level-400 review, and the order is a claim.**
H2 (unload the dead cron) is one command. H1 (CI) is the highest value per
line in the repo. **B-DECISION.1 comes before the recompute track**,
because G exists to make the register honest — it cannot find an edge that
was missed, and sequencing it ahead of the trading decision would spend a
week making a well-evidenced negative slightly better evidenced. If the
answer to B-DECISION is "stop", G is still worth doing for the essays and
the method; if it is "close X3", that runs first and G follows.

~~**A1 → L1 → L2 → L3 → F1-F4 → N1-N4 → B-DECISION → N5-N7**~~

Rationale: the essay series (L) was the highest-value unbuilt thing and
needed no new research. The front end (F) supports L. The cloud (N) supports
nothing until the queue reopens, which is B-DECISION's call.

**Updated 2026-08-30.** Both publications landed (A1, D2.2, D2.6) and all
four drafts are written (A2, L1-L3), so the head of the sequence is now
review-and-publish, which is yours rather than mine. **F1 is the first item
I can start without you.**

> **A6 never existed.** The original sequence read `A1 → A6 → L1`, but A6 is
> defined nowhere in this file — A1-A5 were superseded wholesale on
> 2026-08-01 and folded into the B-series. Recorded rather than quietly
> dropped: a phantom step in a sequence is how work gets invented to fill it.

---

# WORKSTREAM A — Crucible series

**Audited 2026-08-09 against the live Substack. Essays 8, 9 and the Outro
are PUBLISHED** (2026-07-07 / 07-09 / 07-15) and are complete and coherent
on their own terms. Nine of fourteen figures were used. **Do not rewrite
them** — retrofitting figures into published work is low-value editing.

Detail lives in `~/Documents/maverick-hq/autoresearch/05-content-status-and-open-items.md`.

- [x] **A1 DONE 2026-08-30 — PUBLISHED.**
  **https://github.com/MaverickHQ/crucible-autoresearcher** — `public-release`
  (a13dd0a) pushed to remote `main` at 11:25Z. Public, MIT, 69 files, one
  commit. **Only that branch was pushed**; `main` and `build/loop` remain
  local, and `push.default = nothing` is set there so a bare `git push`
  refuses rather than publishing the 50 commits carrying the venue name.

  **The series is now papers-with-code in fact rather than in premise.** All
  five repositories are published, and essays 8, 9 and the Outro have a
  repository behind them for the first time.

  Was: Remote configured, description and topics set. Re-audited against the
  IMPROVED patterns this repo had never been tested against — venue terms,
  account ids, cloud keys, ARNs, tokens, private keys, home paths: **all
  zero**. One command left: `git push origin public-release:main`. Before
  that: Create
  `MaverickHQ/crucible-autoresearcher`, push **`public-release` (a13dd0a)
  ONLY** — never `main` or `build/loop`, the latter being 50 commits
  carrying the venue name. Re-verified clean 2026-08-09: 69 files, 0
  forbidden terms, clean commit message. **More urgent than it looks**: the
  essays have been live for a month and the series' papers-with-code premise
  has been pointing at a repository that does not exist.
- [x] **A2 DRAFTED 2026-08-30** — `20 - Essays/10-addendum-was-it-actually-
  researching.md`, 936 words, figures F14 + F11 (both already rendered).
- [ ] **A2-PUB `[needs-user]` review and publish it.** `#status/review`.
  Your calls: standalone post vs appended to essay 8, and whether the
  self-critical close belongs under your byline. Original scope: ~800-1,200 words, two
  figures already rendered.
  **F14 is a load-bearing claim that is currently unsupported.** Essay 8 is
  titled *The Instrument Before the Experiment* and argues the loop is
  trustworthy — but the published piece never says whether the proposer is
  an LLM, random search or hill-climbing. So a sceptical reader of essay 9
  can say *"it found nothing because it is an expensive random search"*, and
  **the published series has no answer.** The answer exists and is drawn:
  proposer 0.82 vs random 0.62 vs hill-climb 0.61.
  **F11** rides along — the evaluator sets the budget, a genuinely novel
  practical finding for anyone building an LLM research loop, currently
  unused. Working title: *"Was It Actually Researching?"*

**Deliberately not doing:** F3, F6, F9 stay unused. Ordinary editorial cuts
— architecture detail, a robustness check, and a duplicate of a finding F5
and F7 already carry.

---

# WORKSTREAM B — the lab

## L. The lab essay series — NEW, replaces the single B-ESSAY

Kept **entirely separate** from the Crucible series: different project,
different instrument, different conclusion route. The sequencing constraint
is already satisfied — the Outro published 2026-07-15, so a lab essay now
reads as independent corroboration rather than spoiling its punchline.

- [x] **L1 DRAFTED 2026-08-30** — `20 - Essays/20-every-guard-is-a-scar.md`, ~1,550 words, zero venue terms, every number cross-checked against the register. `#status/review`. Original scope: Building the instrument.** Pre-registration, the obtainability
  gate, the calibration gate, the append-only register. **The spine is that
  each guard exists because something specific went wrong** — not a feature
  list. Figures: the console's controls band, plus the calibration
  dead-world/planted-world contrast.
- [x] **L2 DRAFTED 2026-08-30** — `20 - Essays/21-an-order-of-magnitude-short.md`, ~1,600 words, zero venue terms, every number cross-checked against the register. `#status/review`. Original scope: What we tested and what we found.** ORB, the fade, eight ICT
  strategies collapsed into two register entries, X1-X3. Nine distinct
  rearrangements, **+0.02-0.04R gross against +0.25R needed.** The honest
  negative. Figures: the feasibility frontier, the P(pass)-vs-size shape.
- [x] **L3 DRAFTED 2026-08-30** — `20 - Essays/22-correct-arithmetic-wrong-answer.md`, ~1,700 words, zero venue terms, every number cross-checked against the register. `#status/review`. Original scope: The three that looked real.** **The one that travels.** An entry
  price no order could produce · a reference price manufacturing a
  six-sigma effect · a tie bug that cost nothing on one result and moved
  another 28%, where the difference was luck. **Each caught by a different
  guard, each guard built because the previous was not enough.** Figure: the
  four-order table. Subject is **how research goes wrong**, which is a much
  bigger topic than futures trading and the only one a non-trading reader
  would share.

**Hard constraints:** the venue is never named (§0) · figures need drawing;
three exist, the console could be a fourth · drafts in Obsidian, never a
repo.

**Dependency:** L2 and L3 point at this repository, so **D2.6 (the push)
should land alongside them** — same papers-with-code logic as A1 and essay 9.

- [ ] **L-PUB `[needs-user]` review and publish the lab series.** All three
  are written and carry a `needs-your-call:` line naming what is yours
  rather than mine. **The series still needs a real name** — everything says
  "The Lab (working title)". Figures: all four rendered
  (`artifacts/plots/`). **L2 and L3 point at this repository**, so D2.6
  should land alongside them.

## F. Front end — the research console

Design settled against MAYA. The governing finding: **for this lab the
familiar form is not merely dated, it is a lie about what the instrument
does.** A trading dashboard asserts the question is "how much did it make?";
every equity curve this lab drew came from an entry later proved
unobtainable, and the curve looked fine throughout. So: **borrow the
familiar chassis, replace the familiar content.**

**F1-F4 DONE 2026-08-30 — published at
<https://maverickhq.github.io/occams-trader/report.html>** (Pages from
`main` `/docs`; the served bytes were verified identical to the committed
artifact, so Jekyll is passing it through untouched).

- [x] **F1 `scripts/build_report.py` + `make report`.** Reads the register,
  writes one static HTML file stamped with `engine_sha`, archivable with
  `--archive`. **Generated, not live.** `--offline` renders from a cached
  register. **Rendering the register whole exposed a defect in it:** all 20
  hypotheses carry `status: registered` and a null `outcome`, because
  `register_hypothesis` writes those fields once and nothing writes them
  back. The page states it rather than smoothing it over. Not fixed — see
  F5.
- [x] **F2 Controls-first layout.** `quickstart` grew a `controls()`
  returning the four controls as data; its `main()` prints from that and the
  page renders the same call, so terminal and page cannot disagree.
- [x] **F3 Novel elements, each with a familiar anchor.** CI-vs-floor strips
  as inline SVG (7 of them, one per scored result), band shaded and
  labelled. Alpha gauge borrowing `report.py`'s fuel-gauge metaphor, showing
  0.42 across 20 registrations as **8.4× the conventional 0.05 single-test
  allowance**. Colour encodes trust; there is no equity curve anywhere.
  Seven `Result.to_metrics()` blocks were already in the archive and F1 had
  flattened them into rows where a verdict rendered like a bar count.
- [x] **F4 One drill-down layer.** Every finding's hypothesis id links to
  its register entry — mechanism, power plan, and the frozen script's
  sha256 from the manifest. **Claimed prematurely once:** the first build
  defined 20 anchors and linked to none of them, so the content was
  reachable only by scrolling. The anchor sits *inside* the `<details>`,
  because browsers auto-expand a collapsed one only when the fragment
  target is within it. Now tested.

- [x] **F5 MECHANISM DONE 2026-08-30 — `archive.resolve_hypothesis`.**
  The design question answered itself: `hypotheses/` has been in
  `IMMUTABLE` since the start and `_put_json` refuses overwrites, so a
  resolution **appends** a separate record and cannot fill in the
  original's blanks. New `resolutions/` prefix, also immutable.

  **The numbers are read from the archived run, never passed in** — letting
  a caller supply the effect size would recreate the defect the `METRICS:`
  line exists to prevent. What the caller supplies is `decision`: what the
  programme does about the result, which is a judgement and cannot be read
  from anywhere. An empty one is refused.

  Resolving twice from different runs is allowed but never silently:
  `supersedes` must name the prior resolution, because running again until
  the answer is agreeable is optional stopping and the register's job is to
  make it visible.

  `occams/result.py` gained `blocks()` — one definition of what a `Result`
  block looks like, shared by the archive and the console, since two
  definitions is how they come to disagree about how many findings exist.

  `scripts/resolve.py` surveys what can be resolved. **Dry by default**: the
  register is append-only, so a resolution written in error cannot be
  deleted, only superseded — permanently. Writing is opt-in per hypothesis,
  never a batch.

- [x] **F5-WRITE DONE 2026-08-30 — X1 and X2 resolved, X3 deliberately
  not.** `resolutions/X1-COMPRESSION/r1.json` and
  `resolutions/X2-OVERNIGHT-GAP/r1.json`, both from the `primary` path,
  outcomes read from the archived runs and decisions taken from the
  writeups.

  **X1 resolved as `detectable`, which is the right word and the wrong
  impression** — the effect is −0.089 against a 0.07 floor, real and in the
  OPPOSITE direction to the mechanism. The verdict alone reads as a success;
  the decision field carries "this is a reversal, family closed". Good
  evidence that a bare verdict is not a finding.

  **X3 left open on purpose.** Its own writeup calls the null weak — the
  interval runs to +0.113, and an effect that size would be larger than
  anything price data produced in seven years. Recording it as `null` would
  put a settled answer in the register where the record says the question is
  open pending roughly three times the tape.

  The double-resolution guard was checked by firing it: a second resolution
  of X1 without `--supersedes` was refused.

- [x] **F5-BACKFILL DONE 2026-08-30 — 19 of 20 resolved.** The 16 split by
  *where an outcome could honestly come from*, which turned out to be the
  whole problem:

  | provenance | n | source |
  |---|---|---|
  | `scored` | 2 | a Result block in an archived run (X1, X2) |
  | `audit` | 1 | a verdict with no estimate (Z04) |
  | `superseded` | 2 | the successor's own `supersedes` pointer (H4 x2) |
  | `documented` | 14 | prose in `docs/`, pinned by sha256 |

  **`kind` is now part of the record and shown on the page.** A `documented`
  resolution carries NO effect size, interval or floor, because those were
  never computed into the register — transcribing them from a writeup is
  exactly the retyping the `METRICS:` line exists to prevent, and a page
  rendering them in the same shape as a measured result would let a sentence
  pass for a measurement. The summary states how many rest on a document
  rather than a computation; "19 resolved" would otherwise read as
  "19 measured".

  `superseded` verifies rather than asserts: the successor's record must
  actually name this hypothesis, or the resolution is refused. The H4 chain
  (H4-ORDERFLOW → H4-ORDERFLOW-v2 → H5-FLOW-PREDICTS) resolved itself from
  the register with no judgement from anyone.

  **X3-PRINT-SIZE remains deliberately open** — its own writeup calls the
  null weak. The gap block now says what that absence cannot: *unresolved is
  not the same as unanswered, and the register cannot tell you which.*

**Not building:** live queries · a trading-terminal skin · animated results
· anything needing a server, an account or a manual.
**Acceptability test:** show it to a trader who does not know the project.
**If the first thing they ask is "where's the P&L?", the anchor is too weak.**

## N. AWS research runner

Specified in full below (§N). **N4, the parity gate, is the one that
matters** and its acceptance test already exists and passes. Honest note on
priority: **the cloud changes where an experiment runs, not what it
answers**, and the queue is currently exhausted — so N is support work for a
decision that has not been taken yet.

- [ ] N1 containerise · N2 infra · N3 entrypoint · **N4 PARITY GATE**
- [ ] N5 cumulative cost guard · N6 fan-out · **N7 retire the local data copy — LAST**

## I. Indicator layer — DEFERRED 2026-08-09, with the reason

- [ ] **I1-I3 deferred, not dropped.** The mechanism map already established
  that ~20 indicators collapse into four mechanisms, and **two of those are
  X1 (dead) and X4 (never run for want of a base effect)**. Building
  predictors for closed hypotheses is work without a question. Revive if
  B-DECISION reopens the queue.

## D. Remaining strategic

- [ ] **D1 the autoresearch loop.** The biggest unbuilt thing, and the one
  I would most want to build. **It would industrialise searching a space we
  have just measured as empty.** Revive only after B-DECISION.
- [x] **D2.2 DONE 2026-08-30 — name kept, About set.** `occams-trader`, as
  recommended: it is in every doc, every commit message, and the package
  itself is `occams/`.

  **The description was rewritten rather than used as drafted.** The original
  suggestion — *"A falsification lab for trading strategies. It found nothing
  — and the reason to read it is that three results here looked real and were
  not"* — leads with the outcome, which answers *"why publish this?"* badly.
  It now reads: *"A backtesting harness designed to be hard to fool. Derives
  fills instead of assuming them, refuses uncalibrated estimators, and keeps
  an append-only experiment register. Controls run in ten seconds — no data,
  no key, no network."* Same change drove the README rewrite (`0a77e78`):
  **sell the instrument, keep the results for the essays.**

  Topics live: `backtesting` `pre-registration` `python`
  `quantitative-finance` `reproducible-research` `research-methodology`
  `futures` `monte-carlo` `research-integrity`.
- [x] **D2.6 DONE 2026-08-30 — PUBLISHED.**
  **https://github.com/MaverickHQ/occams-trader** — public, Apache-2.0,
  `ce85bfd` on remote `main`, 201 files, one squashed root commit.

  **The rebuild was necessary and proved itself.** The stale `fc1ee5a` was
  missing **eight files**, including the figure essay L3 points at. It has
  been deleted — a do-not-push branch sitting beside a should-push branch is
  a footgun at exactly the moment someone types a push command.

  **Branch layout going forward — `public` is the working line, `main` is
  not.** `public` tracks `origin/main`; local `main` holds the full
  pre-release history, is never pushed and never developed, and exists so
  the 19 commits referenced by `engine_sha` in 45 archived records keep
  resolving. Counterintuitive by construction, so it is recorded in
  CLAUDE.md where it is loaded every session.

  Audited immediately before the push: venue terms, account ids, keys, ARNs,
  tokens, private keys, secrets, emails, home paths — **all zero**, and
  `data/` and `.env` absent from the tree.

- [ ] **D3** broker paper account — its own note says "only worth doing when
  there is a strategy worth executing". There is not.
- [ ] **D4** MGC/MCL, $19.16 pre-approved and unspent — another draw from
  the same urn, but cheap, and it would reopen the queue.

## G. Register integrity — turn transcription into measurement

**Opened 2026-08-30 after a level-400 review.** 19 of 20 hypotheses carry a
resolution, but **14 are `documented`** — an outcome copied from a writeup
with null numeric fields — and only 2 are measured. A register that is
mostly transcription is a reading list.

> **This does NOT change the trading conclusion, and should not be
> sequenced as though it might.** H-RECLAIM reproduced its archived numbers
> **10/10 to three decimal places**; M5 previously reproduced H5 exactly and
> Z0 to twelve decimals. What the recompute buys is VERDICTS — several bare
> means will resolve to `null` (inside the floor) rather than "small
> negative" — not different numbers. The gap to requirement is a factor of
> ten and no interval closes it. **Do this for the lab's integrity, not for
> the edge.**

- [x] **G0 H-RECLAIM done 2026-08-30** (`4e9e9f1`). Reproduces 10/10, then
  states the estimand: filtered expectancy −0.239R [−0.291, −0.184]
  `detectable` against a sealed arm of −0.036R [−0.083, +0.013] `null`.
  Resolved `scored`, superseding its `documented` record.

- [ ] **G1 IMPORT, DO NOT TRANSCRIBE — do this before the other 12.**
  The recompute currently retypes logic out of a frozen script. On the
  first attempt that produced a clean `detectable` result at 2.33x floor
  **for a strategy that does not exist** — breakout bar conflated with the
  failure close, excursion term dropped from the stop, slippage dropped
  from sizing. The reproduction gate caught it, but the design invites the
  error. `exp_reclaim.py` already exposes `run(inst)`; import the frozen
  module and call it, so the recompute physically cannot diverge and the
  gate becomes belt-and-braces rather than the only defence.
- [ ] **G2 collapse the wrapper sprawl.** `experiment.run` executes an
  archived script with no arguments, so each hypothesis needs its own entry
  point — but 14 near-identical 4-line files is the wrong answer. Generate
  them, or give `experiment.run` an explicit argv contract.
- [ ] **G3 recompute H-STOPWIDTH · H-SECONDPUSH** (share H-RECLAIM's shape).
- [ ] **G4 recompute the three ICT runs** (P1-FVG, P2-SWEEP, P2-CONTROL) —
  the first genuinely stochastic CIs in the backfill.
- [ ] **G5 recompute E3-COSTS · X1-RECONCILE · C2 · H5** (M5 already
  re-scored the last two; needs promoting to `scored` resolutions).
- [ ] **G6 recompute E2-OBJECTIVE · Q1-PAYOUT-PATH · Q2-ATTRIBUTION** —
  Monte Carlo, so pin seeds explicitly.
- [ ] **G7 restrict `kind="documented"`.** Refuse it when an archived script
  exists for that hypothesis: if it can be run, it may not merely be
  described. Turns a judgement error into something the code refuses.
- [ ] **G8 re-run `make report` and republish** once G3-G6 land.

## H. Engineering hygiene — small, and two of them are overdue

- [x] **H1 DONE 2026-08-30 — `.github/workflows/check.yml`.** Tests, lint,
  charset, privacy and the four controls, on every push and PR. Verified by
  simulating CI locally (data/ hidden, bogus AWS credentials): 503 pass.

  **Two defects surfaced the moment the gates were pointed at a machine that
  is not this one.** The privacy scanner exited 0 with "nothing to scan"
  when `.privacy-terms` was absent — a guard reporting success while
  disarmed, which is the same shape as the test that asserted a forbidden
  term was absent while containing it. It now REFUSES unless
  `OCCAMS_PRIVACY_ALLOW_EMPTY=1` says the disarming is deliberate, and even
  then prints "DISARMED — this is not a pass".

  And `test_it_needs_no_data_no_keys_and_no_network` asserted that
  `data/MES.csv` exists and is non-empty. A test whose entire claim is about
  what a READER lacks could only pass on a machine that had the data. It
  failed the first time the suite ran without it, which was the first time
  the claim was ever tested.
- [x] **H2 DONE 2026-08-30 — launchd jobs unloaded.** `paper-morning` and
  `paper-evening` had been firing weekdays 13:30 for eight weeks past the
  campaign's conclusion. The plists are left on disk, so `launchctl load`
  reverses this if the paper track ever reopens.
- [ ] **H3 `[needs-user]` AWS teardown — ~$100/year.** ~$10.50/month for
  infrastructure with **zero Lambda invocations in 14 days**: Lambda $3.05,
  EC2-Other $1.89, Secrets $1.50, KMS $0.93, ECR $0.62, CloudWatch $0.40.
  **The archive itself — 2.11 GB, the only part with evidentiary value —
  costs $0.08.** Also **4 secrets and 13 KMS keys across three regions**
  while the configured default is a fourth (eu-north-1). Keep the bucket,
  drop the scaffolding. Gated on whether the N track is dead or paused,
  which is the same question as B-DECISION.
- [ ] **H4 make the console reproducible without S3.** `make report`,
  `make plots` and `make reproduce` all need the author's bucket, so the
  two most compelling artifacts cannot be rebuilt by anyone else. Ship the
  register cache, or let `make report` fall back to a committed snapshot.
- [ ] **H5 two one-line performance fixes.** `hm = ts.dt.hour*60+...` is
  recomputed inside the groupby loop — **32% of recompute time (2.7s of
  8.4s), 3,701 redundant timezone conversions**, and `load()` already
  computes it once and discards it. And wire up `scripts/to_parquet.py`,
  which is written and unused: 28 MB vs 200 MB, 0.3s vs 1.4s.

## B-DECISION — where to point the instrument

**"Find a strategy with an edge" is an OUTCOME, not a task**, and is not
listed as one. The programme conclusion establishes that the binding
constraint is **the input, not the instrument**.

- [ ] **B-DECISION.1** `[needs-user]` **OPEN — costed 2026-08-30, not
  decided.** Four options: close X3 (cap raise) · MGC/MCL · **less
  efficient venues — a testable research question, not advice about what to
  trade** · stop.

  **What closing X3 costs, computed rather than estimated.**
  `power.n_for_correlation(0.07)` puts the requirement at **3.14×** the
  current sample — confirming the writeup's "roughly 3×".

  | | |
  |---|---|
  | owned | 525 sessions/instrument (1,050 instrument-days, $86.97 actual) |
  | needed | 1,648 sessions/instrument |
  | **additional** | **1,124 sessions/instrument = 2,247 instrument-days** |
  | cost | **$186 (blended R2.1 rate) – $291 (part-1 rate)** |
  | headroom | **$21.91** of a $150 cap |
  | cap required | ~$315–$420 |

  Three things make that worse than it looks: the ledger's own warning that
  estimates came in **4×, 1.5× and 1.5× wrong** and per-day cost varies ~8×
  with volume (a 4× miss is ~$750); **the $125 free credit is exhausted**,
  so everything from here is real money; and R2.1 overspent its approval
  via a per-run cap bug (fixed — spend is now priced from disk first).

  **The prior, recorded before any purchase:** X3 sits at +0.026, CI
  [−0.061, **+0.113**], against a frontier needing +0.25R. The top of that
  interval is a correlation, not an expectancy — it would be the largest
  signal seven years of price data produced and still short of the rules.
  Realistic outcomes are a null that **closes the programme cleanly**, or a
  small positive that is publishable and not tradeable. **Do not spend this
  expecting a funded account.**

  **Prerequisite if it ever proceeds:** the successor hypothesis must be
  REGISTERED BEFORE THE DATA IS BOUGHT, with a hard spend cap written into
  the protocol rather than an estimate. Not drafted — deliberately, since
  drafting it would look like a decision that has not been made.
- [ ] **B-DECISION.2** The one asset that exists today and is not a
  strategy: **the method**. A business question, recorded so it is not lost,
  explicitly not scheduled as work.

---


> **One list, not three.** The master list above is the working view. The
> detailed sections below carry the original scoping and reasoning and are
> marked `[>]` — **they are reference, not a second to-do list.** They were
> briefly duplicated as open checkboxes, which double-counted every task
> and created exactly the two-copies-one-drifts problem that a stale status
> note caused in the essay track.

## A. Admin — minutes each, do these first

- [x] **A1 APPROVED BY USER 2026-08-01.** Our licensed Databento copy may
  live in our own private S3 bucket — internal use, not redistribution.
  **This is the user's determination of their own contract, not mine**; I
  raised it precisely because it carries legal weight and was not mine to
  assume. B2 and B3 are unblocked.
- [x] **A2 DONE 2026-08-01 — and it found worse than the defect audited.**
  `fetch_data.py` and `validate_feed.py` had **NO cost guard at all**;
  `aws_recon.py`'s was per-request and never accumulated. `occams/spend.py`
  is now the single cumulative guard all of them call — refuses rather than
  warns, checks the quote BEFORE any request, distinguishes quotes from
  actuals, and names who can raise the cap.
- [x] **A3 DONE 2026-08-01** — archive section appended to the vault
  runbook: put, restore-and-verify, prove-unmodified, what is immutable and
  why it is a revocable deny rather than Object Lock, and where the spend
  cap lives.
- [x] **A4 DONE 2026-08-01** — the evening job exports each reconciled day
  to the archive as immutable evidence. Copies, never relocates (D0.1);
  already-exported days are a no-op, not an error; and an export failure
  cannot take the debrief down with it. Dormant until the campaign restarts.

## B. Small builds — an hour or two each

- [x] **B1 DONE 2026-08-01 — Parquet, and NO DuckDB.** 408 MB of CSV
  becomes **70 MB** of zstd Parquet, partitioned `instrument=/year=`.
  Round trip proven, not asserted: MES 2026 reads back 179,115 rows spanning
  the right dates.
  **DuckDB dropped after checking.** I recommended it on the grounds that it
  needs no infrastructure — true — and then measured: the whole dataset is
  ~70 MB and fits in memory, so pandas (already a dependency) reads it
  through pyarrow. A dependency bought for a convenience we do not need is
  exactly what the razor is for. Revisit only if a query genuinely exceeds
  RAM.
- [x] **B2 DONE 2026-08-01 — and the restore is PROVEN, not assumed.**
  `scripts/archive_pull.py` rebuilds the local working set from the archive,
  verifying every file's sha256 on the way down. Tested into a clean
  directory: the restored vendor bars load to **1,741 trading days**, the
  same universe X1 reconciled against. `data/` is now genuinely a cache —
  deleting it costs download time, not evidence.
  **Local storage is deliberately NOT pruned by me.** Deleting 2 GB of
  paid-for data is destructive and is the user's call; the runbook carries
  the one-liner. The property B2 wanted is established by the restore
  working, not by the deletion happening.
- [x] **B3 DONE 2026-08-01 — 1,058 files, 2.1 GB in the archive.**
  Restore-tested end to end: a raw order-flow session fetched back,
  sha256 verified against the manifest, and parsed to 4,975 records with
  the aggressor side intact. **Every byte of purchased data now exists in
  more than one place for the first time.** Was: — `scripts/archive_raw.py` is uploading
  ~1.9 GB: the 2019-2026 bars, definitions, and 1,050 order-flow sessions.
  Each with sha256 and a provenance row, so a wiped machine can be rebuilt
  and any restored byte proved identical to what was bought. Unblocked by
  A1.

## C. Research we can do for nothing

- [x] **C1 CLOSED UNRUN 2026-08-01 — deliberately.** Conditioning searches
  for subsets of a strategy that look better. The strategy's entry cannot be
  obtained at all (#3a), so every subset is a subset of nothing and each one
  would spend alpha to say so. **Closed as unnecessary, not deferred** — the
  five conditioners stay specified and are worth reviving verbatim if a
  strategy with a real entry ever exists.
- [x] **C2 DONE 2026-08-01 — barely, and not usefully.** One of four
  pre-specified predictors survives: range height / ATR at **r = -0.131**
  pooled, consistent across instruments and above the detectable floor. The
  other three are noise. **But the stop is DEFINED as
  `extreme ± 0.2 × height`**, so MAE/stop is partly algebraic rather than
  informative. 1.7% of variance is not a filter, and it would be filtering a
  strategy with no obtainable entry.
- [x] **C3 DONE 2026-08-01** — `docs/R1-WRITEUP.md`, archived. Conclusion:
  **price data on MES/MNQ is exhausted for this setup family** — five
  different rearrangements tried, gross signal +0.02 to +0.04R against a
  +0.25R requirement. Explicitly does NOT claim order flow is exhausted.
- [x] **C4 CLOSED 2026-08-01 — it was never a task.** Under our own SOP a
  hypothesis without a stated mechanism is **rejected unrun**, so neither E5
  nor E6 could be registered, let alone executed. A placeholder that cannot
  pass the lab's own entry requirement should not sit on the list looking
  like work. Re-open either as a real hypothesis when someone can say why it
  should work — before knowing whether it does.

## Q. Rule-engine gaps — the half we never modelled (2026-08-09)

Four items kept from an external feature specification; the rest was
declined as a rebuild of machinery that already exists and is tested. The
spec's own core principle — *a strategy must not be called good merely
because it passes an evaluation* — is one we already hold, and E7 (the
P(pass)-vs-size shape) reaches it more cheaply than a second score would.

**Why only four.** Roughly 60-70% of the spec is already delivered:
ingestion and quality probes, contract lifecycle, sessions, the event
engine and order types, the conservative intrabar rule, measured costs, the
trailing-drawdown ratchet, the daily-guard lockout, walk-forward folds,
historical-start Monte Carlo, the experiment registry, and shadow trading.
Rebuilding it would cost months to arrive where we are. **And it would not
move the binding constraint, which is the input, not the instrument.**

- [x] **Q1 DONE 2026-08-09 — and P(pass) flatters weak strategies.**
  `occams/payout.py` (12 tests) + `harness.monte_carlo_to_payout` +
  `scripts/exp_q1_payout.py`. Write-up: [`Q1-PAYOUT.md`](Q1-PAYOUT.md).

  | | P(pass) | **P(first payout)** | qualified but never paid |
  |---|---|---|---|
  | sealed fade (artifact) | 0.2579 | **0.1659** | **36%** |
  | obtainable limit | 0.0424 | **0.0115** | **73%** |

  **The general finding is structural, not about the fade.** Qualifying is a
  ONE-TIME hurdle; getting paid requires surviving and then accumulating
  AGAIN, under a consistency rule the evaluation did not impose, on an
  account whose floor has already ratcheted. A marginal strategy scrapes the
  first and has no cushion for the second — **so the weaker the strategy,
  the worse P(pass) flatters it.** The frontier that governed the whole
  programme was calibrated on the wrong quantity.
  **Zero alpha:** the fade is already dead on obtainability, so no number
  could revive it and nothing rode on the result.
  **`[needs-user]` follow-on:** the payout parameters are **illustrative and
  unverified**. We verified the evaluation geometry and never verified the
  funded-stage terms. The result establishes direction and rough magnitude,
  not any provider's terms. Was: We model the
  EVALUATION and stop there. Two rules differ by stage and we hold only the
  first: the evaluation tier we sealed has **no** consistency requirement,
  but the qualified tier applies a **40% largest-day consistency rule to
  payout eligibility**. `rules.py::consistency_frac` is evaluation-only.
  Extend it to distinguish: evaluation consistency · payout consistency ·
  none · a breach that DELAYS qualification · a breach that DELAYS payout ·
  a hard breach. Then report **P(reaching first payout)** and **P(completing
  multiple payout cycles)** alongside P(pass).
  **Passing is not the goal; being paid is** — and we have never scored the
  second half. Cheap: `rules.py` already has the machinery.
- [x] **Q2 DONE 2026-08-09 — breach is the dominant failure, not time.**
  `occams/attribution.py` (14 tests) + `scripts/exp_q2_attribution.py`.
  Write-up: [`Q2-ATTRIBUTION.md`](Q2-ATTRIBUTION.md). **Sums to exactly
  1.0000.** Obtainable limit, n=1,652:

  | outcome | share |
  |---|---|
  | passed | 0.0424 |
  | **breached the trailing drawdown** | **0.4395** |
  | timed out, still ahead | 0.3541 |
  | timed out, underwater | 0.1640 |

  **The remedy signal is "less size", not "more time".** A reader given only
  P(pass) 0.042 might reasonably conclude the 90-day horizon was too short —
  and that would be wrong in the most expensive way, because more days on a
  breaching strategy produce more breaches.
  **The artifact and the honest variant fail DIFFERENTLY**: the artifact's
  losses are mostly time (0.397 ahead-but-short), the honest one's mostly
  drawdown (0.440). One assumption apart, and the character of the failure
  changes as well as its rate.
  **A refinement changed the reading, and r1 stays on the register.** The
  first run had one TIMEOUT bucket whose own example read "4,032 short of
  the 3,000 target" — i.e. DOWN 1,032, not nearly there. Split into
  ahead/underwater. Not estimand-shopping: zero-alpha, descriptive, no
  tested quantity changed, and the evidence the label misled came from r1's
  own output.
  **`NEVER_TRADED` exists to protect verdict #1's lesson** — a run whose
  equity never moves is an instrument failure, never a NO-GO. Nothing
  triggers it today, which is the point. Was: E2 returned P(pass) 0.042 and P(breach)
  0.440 and never said *why* each path died. Assign every failed path a
  principal reason — drawdown breached by realised loss · by floating loss ·
  daily-guard lock · target not reached in time · consistency not satisfied ·
  contract limit · position held past the forced close · insufficient
  qualifying days. Cheap, diagnostic, and it turns one number into a
  decomposition.
- [>] **Q3 → folded into D2.4** (versioned rule profiles, below).
- [>] **Q4 → folded into M7** (block bootstrap, Track M).

**Explicitly declined from the same spec, so it is on record as considered:**
a six-page dashboard (the largest chunk of work in it and the least likely
to change a decision) · a configurable intrabar traversal assumption (**a
tunable path assumption is a free parameter that moves results in a
favourable direction**; the conservative rule is what kept verdict #2
honest) · a "jump detection" data filter (our quality probe flags 13
degraded days *including the 2020-02-27/28 crash* and deliberately does not
remove them — a filter that silently drops real events is a way to launder
a strategy) · a manual-execution degradation model (a good idea, but a
second-order correction on a strategy with no first-order edge: it can only
make a result worse, never find one) · its ten-family strategy list, four of
which `STRATEGY-CATALOGUE.md` has already resolved.

**What the spec was missing, and these are the ones that have actually
caught defects here:** no pre-registration · no entry-obtainability gate
(our fade passed a sealed verdict with a fill no order could produce) ·
multiplicity as a *warning* rather than a spent budget · no reference-price
discipline (a lab built to that spec would have reported ICT-P2's artifact
as real) · ~26 reported metrics with no declared primary.

## I. Indicator layer — and the collapse that keeps it cheap (2026-08-09)

Two indicators already exist and both are correct: **real VWAP**
(`strategy.py:91` — volume-weighted, refuses to run without a volume
column) and **ATR** (`loader.py:72` — day N's ATR never sees day N).

**The reason this is a small track and not a big one:** ~20 named
indicators collapse to about **four mechanisms**. Testing them as separate
strategies would spend twenty register entries to ask four questions, which
is the exact failure the ICT run avoided when two hypotheses closed eight
strategies.

- [>] **I1 `occams/indicators.py`.** Moving averages, Bollinger, Keltner,
  RSI, MACD, Donchian, ADX, %B, rolling z-score, NR7. Each is 5-10 lines of
  pandas rolling; the work is the tests, not the maths.
  **The one rule that matters: every indicator is computed from bars
  STRICTLY BEFORE the decision bar.** `_atr_by_day` already sets the
  pattern. Get this wrong on a Bollinger band and the result is a
  look-ahead machine that looks brilliant. Tested by asserting that an
  indicator value at bar N is unchanged when bar N's own OHLC is mutated.
- [>] **I2 Entry auditor for indicator families.** `AUDITORS` at
  `execution.py:174` holds only `orb` and `fade`, and is **default-deny** —
  a new family raises rather than running. That is not friction to work
  around: **indicator strategies are precisely where entry look-ahead
  lives.**

  | signal | naive (WRONG) | honest |
  |---|---|---|
  | MA crossover | fill at the close that *produced* the cross | order placed for bar N+1, fill derived from its path |
  | Band touch | fill at the band | **legitimately obtainable** — the level is known before the bar, so a resting limit is real |
  | Close outside band, then enter | fill at that close | market at the next open |

  Band touch is one of the cleanest entries available to us — unlike the
  fade, which is the entry that broke us.
- [>] **I3 Mechanism map — record it BEFORE any indicator is tested**, so
  twenty indicators cannot quietly become twenty hypotheses:

  | mechanism | indicators that express it | where it is already tested |
  |---|---|---|
  | volatility is compressed | BB width, ATR ratio, Donchian width, NR7 | **X1** |
  | a slower series has direction | MA slope, ADX, HTF trend | **X4** |
  | momentum state changed | MA cross, MACD, RSI through 50 | *not queued* |
  | price is N sigma from a moving centre | BB touch, Keltner, %B, z-score | **declined** — wrong corner of the frontier |

  **Two of the four queued experiments are already indicator strategies**,
  named by mechanism rather than by indicator. An indicator is a *predictor
  swap* inside an existing hypothesis, not a new one — provided the swap is
  declared before the run.

**Still declined, and the reason is unchanged:** band reversion, MA
pullback and VWAP reversion score **poor on R-shape and extreme on
crowding**. Asymmetry is the lever — 2.0R needs WR 45%, **1.0R needs
60-65%** — and win-small-often is the hardest corner on the map. What is
*not* declined is the compression reading (X1) and the conditioner reading
(X4) of the same maths.

**Where the lab is already strong for this:** `search.py::sweep` plus the
**G4 plateau rule** was built for parameter grids — a winner needs >=5
neighbouring cells within 0.05 on a Chebyshev-1 neighbourhood, so a lone
spike at "MA period 43" is rejected as noise. And Phase 5 still binds:
**positive control before any real result is read.** A family that cannot
find the planted edge in `synth.py` has a meaningless null on real data.

## M. Maths engine — COMPLETE 2026-08-09 (M1-M7)

**What it cost and what it bought.** Seven modules, ~90 tests. It found
**one wrong number in the register** (C2's `mins to breakout`, 97.1% tied,
28% off on MNQ), confirmed **H5 and Z0 reproduce** (Z0 to 1e-12), made
ICT-P2's defect **impossible to commit silently** (M2) and **impossible to
ship undetected** (M4, which rejects it at 5 sigma on a world with no drift
at all), and left a `calcs.json` beside every future run naming which
estimator produced each number.

**And it taught the same lesson twice, from opposite directions:** M4's
first tolerance was tighter than its own sampling error and failed a sound
estimator; M7's block-length rule reacted to sampling error and lengthened
blocks on iid data. **Do not act inside your own noise floor** is now a
standing rule with two scars behind it.

---

## SEQUENCING REVISED 2026-08-09 — research first, infrastructure after

The gate on D5 was M1-M4. **It has lifted.** The order is now:

**X1 (D5) -> Q1 -> N1-N4 -> the rest of the queue -> N5-N7**

Why X1 rather than more building: **22 open items, and exactly one of them
can change the standing answer.** Q, I, N and most of D make the lab better
at being right; none of them finds anything. The binding constraint is the
input, not the instrument (CLAUDE.md 8a), and no amount of further
engineering moves it.

Why not **I1-I3** first, which is the counterintuitive one: building the
indicator layer would hand X1 four admissible predictors where it now has
one registered. **That creates a choice that does not need to exist.** Run
X1 with its declared predictor and there is nothing to pick; build the
alternatives first and there is. Multiplicity discipline says this order.

Why not **N** first: N4's acceptance test now exists and passes, so the
track is ready — but the cloud changes where X1 runs, not what it answers.

Why not **Q1** first, which is the closest call: X1's primary outcome is
strategy-free and never touches P(pass). Q1 becomes load-bearing only if X1
survives to a sealed protocol, and the honest prior is that it will not.
It runs alongside.

**Stated before the run:** X1 spends alpha into a register already at **15
hypotheses, 0.27 allocated** — three of them spent unplanned on ICT. The bar
for X1's survival is **higher than when the queue was written**. A marginal
positive is worth less than it would have been a week ago, and that is said
now rather than after the number arrives.

---

## M. Maths engine — hand the calculations to audited code

**Why.** Today every `scripts/exp_*.py` re-implements its own statistics. The
ICT run alone wrote the **same cluster bootstrap three times**, and
`spearman()` in `exp_flow_predicts.py` -- the function behind H5, one of only
two live signals -- has never been checked against a reference
implementation. The SOP's `METRICS:` line already stops numbers being
retyped into the record; this stops them being re-derived per script.

**What it does not fix, stated up front:** choosing the wrong estimand.
ICT-P2 was arithmetically perfect and still wrong. A module makes that choice
visible and reviewable; nothing makes it impossible.

- [x] **M1 DONE 2026-08-09 — and it found the bug it was built to find.**
  `occams/stats.py` + `tests/test_stats.py` (21 tests, two kinds).
  **Known-answer** against scipy — a **TEST-ONLY** dependency; the runtime
  stays `pandas`+`numpy` because `occams/` is imported by the Lambda and its
  dependency weight already broke a build once (B0.3). Testing against scipy
  also **pins OUR behaviour**, so a future scipy release cannot silently move
  a number already in the register.
  **The defect:** the hand-rolled `spearman()` behind H5 and C2 ranks with
  `argsort(argsort(x))`, which gives tied values arbitrary DISTINCT ranks in
  whatever order they appear — **so the answer depended on row order.**
  `stats.rankdata` averages ranks within a tie group and matches scipy to
  1e-12. A test pins the bug SHAPE so the shortcut cannot return believed
  equivalent.
  **Did it change H5? No — and that is luck, not correctness.** Re-scored on
  the same data: MES had 9 ties, MNQ 1, so the pooled r moves by 1e-6 and
  **-0.0724 reproduces exactly**. The function was wrong in general and
  happened to meet nearly tie-free data. On a bucketed or tercile predictor
  it would not have been.
  Also landed: `ppf` (Wichura AS241, ~1e-16, vs Acklam's ~1e-9 in
  `power.py` — a test pins their agreement until `power` consolidates onto
  it), Wilson `proportion_ci` (needed because Z0.4 found **0 unplaceable of
  6,940** and "0 out of 6,940" still needs an honest upper bound), and
  `mean_ci` implemented as a **special case of** `cluster_bootstrap_ci` with
  singleton clusters, so the two cannot drift apart.
  **`seed` is a required keyword with no default** — a default seed is one
  nobody writes down. Was:
- [ ] ~~**M1 `occams/stats.py` — primitives.**~~ Mean, plain and cluster
  bootstrap, effect sizes, rank correlation, proportion tests. Nothing
  domain-specific. Tested two ways: **known-answer** against an independent
  source (scipy as a TEST-ONLY oracle -- not a runtime dep; `occams/` is
  imported by the Lambda and its dependency weight already broke a build
  once, B0.3) and **property** tests (a CI contains its point estimate;
  shuffled labels give d ~ 0; scaling inputs by k scales the mean by k and
  leaves d unchanged).
- [x] **M2 DONE 2026-08-09 — the defect is now a unit test.**
  `occams/estimators.py` + `tests/test_estimators.py` (16 tests).
  `reference=` is **required with no default** — the default is precisely
  what nobody thinks about. `AT_PRICE` may be returned as a single number;
  `AT_LEVEL` and `AT_FILL` **raise `AmbiguousReference`** unless
  `decompose=True`, and the exception carries the whole lesson rather than a
  code.
  **The load-bearing test is `test_a_frozen_market_still_prints_a_reading`:**
  a series that trades up through a level and then FREEZES has zero forward
  drift by construction — measured from price, correctly 0.0; measured from
  the level, +5.0, entirely penetration, `share_positional` 1.00. **ICT-P2
  as an eight-line unit test.**
  The identity `total = positional + drift` is asserted on **every call**,
  not just in tests — it cannot fail unless the engine is wrong, which is
  why it is checked in the hot path.
  `measure_from_fill` joins E1 to M2: the caller names an **Order**, the
  fill is derived from the bars, and **there is deliberately no argument
  through which a fill price can be asserted** — that assertion is what made
  the fade's +0.1R an artifact. An unplaceable order raises before anything
  is measured; an order that never fills returns `None`, because a rule that
  produces no trade is a real outcome of the rule and not a missing
  observation.
  Day-flat truncation is explicit and **carried on the result**, since a
  sample where 40% of windows ran off the session close is a different
  sample. Measuring from the last bar raises rather than returning 0 — that
  would put a fabricated observation into the sample. Was:
- [ ] ~~**M2 `occams/estimators.py` — the domain quantities.**~~ Forward returns,
  signed outcomes, fill-derived entries. The design that prevents ICT-P2:
  `reference=` is a **required** argument with named values
  (`at_price` / `at_level` / `at_close`), and anything other than `at_price`
  **forces `decompose=True`**, returning the split rather than one number.
  The error becomes impossible to commit silently.
- [x] **M3 DONE 2026-08-09.** `occams/result.py` + `occams/audit.py` +
  `tests/test_result.py` (15 tests). Wired into the SOP: `experiment.run`
  now archives **`calcs.json`** beside `script.py` and `output.txt`.
  **`Result` renders itself both ways** — `render()` for the human,
  `to_metrics()` for the record — from the same fields, so the printed table
  and the `METRICS:` line **cannot disagree**. Every script currently builds
  those two independently and nothing checks they match.
  **The verdict is a 2x2, not a yes/no**, because significance and
  materiality are different questions:
  `detectable` · `inconclusive` · **`precise but immaterial`** · `null`.
  C2 sat in the third box and it took a paragraph of prose to say so; ICT-P2
  raw sat squarely in `detectable`, **which is exactly why a significance
  test could not save us and a control had to.** `floor_multiples` is the
  transformation that puts a correlation, a Cohen's d and an ATR-scaled
  return on one comparable axis.
  **The ledger closes a real provenance hole.** `engine_sha` pins the COMMIT
  that produced a number; it does not say which FUNCTION did, nor with what
  input. Those were the same thing while every script carried its own maths
  — they stopped being the same thing the moment M1 replaced three divergent
  bootstraps with one. `@audited` records the fully-qualified name, the
  **sha256 of the function's own source** (so a later edit shows even at the
  same commit), and each argument by **shape and content hash, never by
  value** — a ledger that inlined the inputs would be larger than the data
  and prove no more.
  **Scripts do not opt in:** the child writes the ledger on exit to the path
  `experiment.run` names, so importing the engine is enough. Bounded at
  `MAX_SAMPLES` distinct signatures per function, with a full call count, so
  a 500-iteration loop cannot blow it up. Was:
- [ ] ~~**M3 `Result` object + calculation manifest.**~~ One object carrying
  estimate, CI, n, n_eff, d and the declared floor, rendering itself so no
  script formats its own numbers. An `@audited` decorator logs every
  calculation call -- function, source hash, arguments -- and
  `experiment.run()` archives it as `calcs.json` beside the existing
  `script.py` and `output.txt`. **That is the audit trail: three years on you
  see which version of which estimator produced each number.**
- [x] **M4 DONE 2026-08-09 — and the gate has teeth.**
  `occams/calibration.py` + `tests/test_calibration.py` (13 tests).
  **ICT-P2 is now caught mechanically, with no judgement required.** Same
  data, same arithmetic, one different reference price:

  | estimator | dead world | verdict |
  |---|---|---|
  | measured from **price** | +0.0735 = **0.5 sigma** | calibrated |
  | measured from the **swept level** | +0.7040 = **5.0 sigma** | **REJECTED** |

  The dead world has no forward drift whatsoever, so a 5-sigma reading is
  the measurement rather than the market — a market that froze solid at the
  trigger would still print it.
  **Both halves are required.** An estimator returning zero for everything
  passes the dead world and is useless; one reporting an effect from noise
  passes the planted world and is dangerous. Tests pin both failure modes.
  `AT_LEVEL` is not forbidden — it is forbidden UNDECOMPOSED: the **drift**
  term passes the same gate the **total** fails, which is the M2 rule proved
  rather than asserted.
  **Self-inflicted finding worth keeping.** The first version used a fixed
  absolute tolerance of 0.15 and **failed a sound estimator**, because the
  sampling error of the check itself was 0.26. A gate whose threshold sits
  inside its own noise floor rejects at random, which is worse than no gate:
  it teaches you to ignore it. Tolerances are now in **standard errors**,
  self-calibrating, and the world build was vectorised so n can be large
  enough to be decisive.
  **Why not `synth.py`:** that plants an edge in `TradingDay`s and is the
  validated control for STRATEGIES (Phase 5) — it deliberately hides the
  trigger and direction, because a strategy should find those itself.
  Calibrating a MEASUREMENT is the opposite problem. Was:
- [ ] ~~**M4 Dead-world / planted-world calibration gate.**~~ We already own both
  controls (Phase 5, `occams/synth.py`). Every estimator must return ~0 on
  the dead world and ~the planted effect on the planted world. **This is what
  would have caught ICT-P2 automatically** -- on a zero-drift random walk a
  valid estimator returns 0 and the reference-price version returns +0.15
  ATR. No judgement required.
- [~] **M5 PRIORITY TIER DONE 2026-08-09 — and it found a wrong number.**
  `occams/backfill.py` + `tests/test_backfill.py` (9 tests) +
  `scripts/backfill_m5.py`. Write-up: [`M5-BACKFILL.md`](M5-BACKFILL.md).
  **H5 reproduces exactly** (6/6, pooled r -0.0723). **Z0 reproduces to
  1e-12** (8/8) — the NO-GO stands unmoved.
  **C2 moved, and the mechanism is exact.** Of four predictors, only
  `mins to breakout` changed — **MNQ -0.0304 -> -0.0388, a 28% shift**. It
  is the only integer-valued predictor: **94 distinct values across 3,260
  observations, 97.1% tied.** The three continuous predictors are <=1% tied
  and reproduce to the last recorded decimal. That is precisely where
  `argsort(argsort(x))` must break, and precisely where it broke.
  **The conclusion is unchanged** — `range/ATR`, the one predictor C2
  reported as surviving, reproduces EXACTLY at -0.1312 — but a recorded
  number was wrong, and the correction is **appended, not edited**
  (`C2-MAE-PREDICTABLE/2026-08-09-m5-reproduction`, zero alpha).
  **The backfill also caught its own targeting error**, which is the more
  transferable lesson: Z0 first diffed against the pre-harness record and
  reported a phantom mismatch. An experiment with several runs has a
  canonical one, and a backfill that picks the wrong record blames the
  engine for the register's history. That earlier record is the one whose
  option had no frozen script — the incident that caused
  `occams/experiment.py` to exist.
  Remaining targets: was
  One per commit, diffing against the archived `METRICS:` line.
  **Known subtlety, found while building M1 — settle it before starting.**
  The diff cannot be "bit-identical" across the board, because the new
  cluster bootstrap consumes its RNG differently from the three hand-rolled
  copies. So split the comparison: **deterministic metrics** (means, effect
  sizes, correlations, decompositions) must match EXACTLY; **stochastic
  metrics** (bootstrap CIs) need only agree within Monte Carlo error, and
  the engine's value then becomes the record. Deciding this now rather than
  mid-backfill is what stops a legitimate RNG difference being read as a
  reproduction failure — or worse, an exact-match rule being quietly
  relaxed once it starts failing. **N4's cloud parity gate is unaffected**:
  same engine, same seed, same machine-independent draw, so it stays
  bit-identical. **Priority is
  not chronological**; it is what we still lean on and what used unverified
  maths:
  1. **H5 order flow** (r = -0.072) -- our only live positive signal, resting
     on an unverified `spearman()`
  2. **C2 MAE** (r = -0.131) -- same function, and R1 already flagged the
     estimand as partly definitional
  3. **Z0 four-order table** -- the flagship result; re-verify *because* we
     rely on it
  4. E2 P(pass) / E7 shape -- Monte Carlo and seeds
  5. ORB, reclaim, stopwidth, second push, cost decomposition
  **A re-run with the SAME estimand costs no alpha** -- it is a reproduction,
  not a second look. Only a changed estimand costs, which is why ICT-P2's
  correction needed its own register entry at zero alpha.
- [x] **M6 DONE 2026-08-09 — two tiers, because one tier fails either way.**
  `tests/test_reproduction.py` (8 always-on + 4 gated), `reproduction`
  pytest marker, `make reproduce`.
  **Tier 1 pins the ENGINE on deterministic synthetic inputs.** No licensed
  data, no network, runs in `make check` every time, breaks in milliseconds
  if `spearman`, the bootstrap, `cohens_d`, `forward_return` or the
  calibration gate moves. **This is the tier that actually protects the
  archive** — an archived number can only move if an estimator moves, and
  this is what that looks like. It also pins that the calibration gate still
  *discriminates* (0.53 sigma vs 5.03 sigma); if those converge, every
  "calibrated" verdict downstream is worthless.
  **Tier 2 re-scores the REAL archive end to end** — needs 2 GB of vendor
  bars plus S3, so it is marked, excluded from the default run and wired to
  `make reproduce` (~12 min). **A test that usually skips is a test that
  rots**, so it is not left in the default suite pretending to pass. The
  archived values are also pinned as constants in the file, so the expected
  numbers are visible in the repo rather than only in a bucket.
  **Design problem it surfaced, and the trap in fixing it.** The register is
  **append-only**, so C2's pre-correction values live there forever — the
  test failed on them permanently, and the obvious "fix" is to loosen a
  tolerance until it passes. Instead `SUPERSEDED` is now a first-class kind
  in `occams/backfill.py`: corrected metrics are **named, shown, and counted
  separately**, never hidden. The check for whether that is legitimate
  rather than silencing: both superseded metrics appear in the appended
  correction record and both were reported in `M5-BACKFILL.md` before the
  exclusion list existed.
- [x] **M7 DONE 2026-08-09.** `stats.block_bootstrap_ci` +
  `stats.optimal_block_length` + `tests/test_block_bootstrap.py` (11 tests).
  Moving-block bootstrap for a series whose ORDER carries information. The
  cluster bootstrap (M1) handles dependence between observations sharing a
  LABEL — MES and MNQ on one date; this handles dependence along TIME, which
  is volatility clustering and **the run of losing days that is what
  actually breaches a trailing drawdown**. A per-observation resample treats
  such a run as independent draws and reports a confidence it has not
  earned.
  Two properties carry it, both tested: `block=1` reduces **exactly** to
  `mean_ci` on the same seed (special case, not a second implementation),
  and on an AR(1) series it is **>1.4x wider** than the plain bootstrap
  while staying within 25% of it on independent data — a correction, not a
  penalty.
  **`optimal_block_length` found M4's lesson in a second place.** The AR(1)
  plug-in rule returned a block of **3 for iid data**, because on 2,000
  independent observations the sample autocorrelation still lands near
  +/-0.02 by chance. It now requires lag-1 autocorrelation to clear ~2
  standard errors (`2/sqrt(n)`) before lengthening anything: **do not act
  inside your own noise floor.** Documented as a plug-in rule of thumb whose
  job is the right SCALE, explicitly not an optimum, and overridable.
  Original scope: We resample
  historical START dates; this resamples consecutive BLOCKS of trading days
  — 1 / 5 / 10 / 20, plus an estimated block length. Genuinely additive,
  and the reasoning is right: blocks preserve volatility clustering and
  win/loss sequencing that a per-trade shuffle destroys. Belongs in
  `occams/stats.py` beside the cluster bootstrap M1 already builds, not in
  a Monte Carlo module of its own.

## N. AWS research runner — execution moves, thinking stays

**Why, and the part that is not obvious.** Moving data off this machine
(the standing backlog item) is blocked by a hidden cost: once the local copy
goes, every run pulls 2.1 GB out of S3 and pays egress. Run compute in the
same region and **S3 -> Fargate transfer is free**. "Data only on AWS" and
"compute on AWS" are one decision, and the data deletion is its LAST step.

**Service choice.** Fargate for compute, Step Functions to orchestrate,
Lambda only for glue. Not Lambda for the runs -- the 15-minute ceiling would
breach on E2's Monte Carlo. Not Batch yet -- Step Functions Map is simpler
for ~10-30 runs; Batch becomes right past ~100.

**Separate stack** from the trading stack (`aws/template.yaml`): different
lifecycle, different blast radius, and the research runner must not be able
to reach the trading notification path.

- [>] **N1 Containerise.** Dockerfile, pinned deps, identical behaviour under
  `docker run` locally. The image **digest** is recorded next to
  `engine_sha`. **This closes a real hole:** today's provenance pins the
  commit but NOT numpy/pandas, and a version bump can shift floating-point
  results with nothing in the archive showing it.
- [>] **N2 Infra** — extend `aws/research-template.yaml`: ECR repo, ECS
  cluster, task definition, Step Functions state machine, least-privilege
  task role. The role writes new keys under `experiments/` and `provenance/`
  and does **NOT** get the write-once admin exemption; the bucket policy
  keeps denying overwrites. The privacy and charset guards already run inside
  `archive.put()`, so they are inherited.
- [>] **N3 `occams/experiment_cli.py`** — the container entrypoint. Each
  experiment **declares its inputs**, which doubles as provenance ("read
  exactly these keys") and lets the container refuse reads outside the
  declared set.
- [>] **N4 PARITY GATE — nothing in this track is done until this is green.**
  Re-run every archived experiment in the cloud and require a **bit-identical
  `METRICS:` line**. This works for free because runs are seeded, METRICS is
  rounded JSON, and the originals are archived. **The acceptance test is M5,
  executed twice** -- once locally for the baseline, once in the cloud to
  match it.
- [>] **N5 Cost guard.** Cumulative and stored in S3 — **this is the exact
  R2.1 bug**, where a per-run cap reset to zero on each invocation so two
  runs each passed a $90 check and together did not. A parallel fan-out is
  that bug's ideal habitat. Plus a budget alarm and a hard job-count cap, and
  a **separate AWS-compute line in `SPEND.md`** with its own cap: mixing it
  into the data budget would destroy the one document whose whole job is
  being right about money. (Scale: a 5-minute Fargate run is ~$0.02. The risk
  is not unit cost, it is an unbounded loop.)
  **The research runner gets NO data-vendor credentials.** Not scoped-down --
  none. Buying data stays a deliberate local action with user approval.
- [>] **N6 Fan-out** — Step Functions Map for overnight multi-experiment
  batches, completion notification on its own topic.
- [>] **N7 Retire the local `data/` copy** — closes the standing backlog item.
  **MUST BE LAST.** Re-buying that data costs $128.09 and the free credit is
  exhausted, so deleting the local copy before parity is proven is
  irreversible on a real budget.

**What does NOT move to the cloud:** the interactive part. Writing a
hypothesis, arguing about whether the estimand is right, reading a result.
ICT-P2 was caught by a judgement call about a reference price, not by
execution. Putting the thinking loop behind a container build would slow the
part that most needs to iterate.

**Sequencing:** M1-M4 -> M5 (local baseline) -> N1-N4 -> N5-N6 -> X1 -> N7.
The one hard ordering is that the maths engine precedes the cloud: migrating
unverified calculations just relocates the uncertainty.

## D. Strategic — weeks, and the real decisions

> **Research now has its own plan.** `docs/EXPERIMENT-PLAN.md` holds the
> queue (X1-X4) and `docs/STRATEGY-CATALOGUE.md` scores every family
> considered, including the ones declined and why. Kept separate on
> purpose: **an experiment asks "is this true?" and a build asks "does the
> code work?"** — different exit criteria, and mixing them is how "we
> shipped it" gets mistaken for "it works". Only build work belongs in this
> file.

- [x] **D5 CLOSED 2026-08-09 — queue exhausted, conclusion written.**
  [`PROGRAMME-CONCLUSION.md`](PROGRAMME-CONCLUSION.md): the whole scoreboard
  in one place — three sealed verdicts, 18 registered hypotheses, alpha
  0.42, **no strategy with a demonstrable edge**. Written because the plan
  committed to writing it in advance for exactly this outcome, and because
  a disappointing answer is the one that gets skipped.
  **It contains no number that was not already in the register** — that was
  the design constraint. If synthesis had produced a new finding, something
  would have gone wrong.
  **Four options are now on the table and three of them are the user's:**
  (A) raise the cap and buy order-flow depth — the only thread where more
  data changes an answer, X3's interval still admits +0.113; (B) MGC/MCL at
  $19.16 pre-approved, but explicitly another draw from the same urn;
  (C) **publish — the lab is the product, not the edge**; (D) stop, which
  the programme priced from the beginning as the most likely single outcome.

  **Detail of the queue that produced this:**
  **X3 order flow: r = +0.0260, CI [-0.0610, +0.1125], n_eff 510, floor
  0.13 — null against the floor, but NOT REFUTED**
  ([`X3-WRITEUP.md`](X3-WRITEUP.md)). The interval still admits **+0.11**,
  which by this programme's standards is a large effect. X1 and X2 were
  answers; **X3 is a measurement that ran out of data.** The power
  limitation was stated in the registration, not discovered after.
  **The registered confound did NOT appear** (-0.053, null) where X1's came
  back at 5.00x floor and X2's at 2.33x. **My prediction was wrong**, and
  the reason sharpens the rule: X1's opening range and X2's |gap| are DIRECT
  measures of volatility; large-print share is a normalised distributional
  statistic that divides the level out. **Confounds come from predictors
  that carry a LEVEL.**
  **X4 is not run: it is a conditioner and there is nothing left to
  condition.** Conditioning a family with no base effect is how a subset
  gets mistaken for a signal.
  **The one open purchase decision.** Bringing the order-flow floor from
  0.13 to 0.07 needs ~3x the effective sample (~1,575 sessions/instrument
  against 525 owned). **No cost figure is quoted** — three estimates in this
  programme have been wrong by 4x, 1.5x and 1.5x, and the standing rule is
  that the cap decides the sample. It is well beyond the $21.91 headroom, so
  it is a **cap-raise decision for the user**, not a purchase decision for
  me.
  Register now **18 hypotheses / 0.42 alpha**.

  **X1 and X2 both CLOSED DEAD 2026-08-09.**
  **X2 overnight gap: r = +0.0025, CI [-0.0433, +0.0483], 0.04x the floor —
  null** ([`X2-WRITEUP.md`](X2-WRITEUP.md)). Both folklore directions die
  together: neither "gaps run" nor "gaps fill". The gap is REAL — median
  0.28 ATR — and predicts subsequent **volatility** (control r = +0.163,
  2.33x floor, detectable) but carries **no direction**. The market prices
  the overnight news completely at the bell and leaves volatility with
  nothing in it.
  **The pattern worth naming after two runs:** two experiments, two large
  significant CONTROLS (5.00x and 2.33x the floor), neither of them evidence
  — and in both cases the confounded measurement was **the more obvious one
  to build**. A programme reaching for the obvious predictor would have
  produced two impressive results and learned nothing.
  **Two of four queued families dead, both price-based.** That strengthens
  R1 rather than adding to it: public price structure on these instruments
  is exhausted. **X3 order flow is the last structurally different thing in
  the queue** — if it dies, the honest choice is new data, new instruments,
  or stopping, which the plan already anticipated as a real outcome.
  Register now 17 hypotheses / 0.37 alpha. **Next: X3.**

  **X1 CLOSED 2026-08-09: DEAD, and not a null.**
  Volatility compression predicts **more compression**: r = **-0.089**, CI
  [-0.135, -0.043] excludes zero, **1.27x the declared floor**, consistent
  across instruments (MES -0.106, MNQ -0.070) and **monotone across
  pre-specified buckets** (0.960 -> 0.827 ATR from 0 to 3+ contracting
  sessions). Both directions were interpreted in the register before the
  run, and this is the one registered as *"refuted in the sharpest way"*.
  **Half the mechanism survived**: volatility clustering is confirmed — a
  negative here IS persistence — and the mean-reversion half the strategy
  needed is absent at a one-day horizon. **Not tradeable in reverse either**:
  0.8% of variance.
  **The confound check justified the whole design.** The same-day
  opening-range predictor returned **+0.350, five times the floor** — and
  means nothing about the hypothesis. Had the primary been built on it, X1
  would have produced a large, robust, instrument-consistent positive that
  was intraday persistence wearing the mechanism's clothes. Same shape as
  ICT-P2; the difference is it was **named as a control in the registration**
  rather than caught afterwards.
  **The best-scoring family on the map died first.** $0. Register now 16
  hypotheses / 0.32 alpha. **Next: X2 overnight gap.** Was: gated on M1-M4, so X1 lands
  audited rather than being re-done later. **I1-I3 widen the admissible
  PREDICTORS for X1 and X4** (Bollinger bandwidth, ATR ratio, Donchian
  width; MA slope, ADX) without adding hypotheses — a predictor swap
  declared before the run is not a new question. X1 volatility contraction → X2
  overnight gap → X3 order-flow size → X4 conditioning, **strictly
  serial**. Running them in parallel and reporting the best is a four-fold
  multiplicity charge dressed as efficiency. All $0.

- [>] **D1 R3 — harness the autoresearch loop (R3.1-R3.6).** The biggest
  unbuilt thing, and only now safe to build: it can be pointed at a
  registered hypothesis behind an obtainability gate, an alpha ledger and a
  power check that understands dependence. Six weeks ago it would have
  industrialised the dredging instead of the research.
### D2 — publication (gate passed; what remains is LOCKED IN below)

- [x] **D2.1 DECIDED BY USER 2026-08-09 — Apache-2.0.** `LICENSE` + `NOTICE`
  + `pyproject` metadata + README section. Chosen over MIT for the explicit
  patent grant and the modified-files notice. `NOTICE` states plainly that
  the **licensed market data is not redistributed** (`data/` is git-ignored)
  and that the repository contains no live-execution path.
- [>] **D2.2** `[needs-user]` **Venue — TBC (user, 2026-08-09).** Deferred
  deliberately; nothing else in D2 depends on it.
- [x] **D2.3 DONE 2026-08-09.** `scripts/quickstart.py` + `make quickstart`
  + `README.md` + 2 tests. Four demonstrations in ~10s with **no data, no
  API key, no network**: positive control (planted edge found, P(pass)
  1.00), negative control (dead world, 0.00, null 0.00), the **calibration
  gate** showing the same measurement from two reference prices (0.5 sigma
  vs **5.0 sigma** on a world with no drift), and the rule profile. A test
  asserts the "no data, no keys, no network" claim is TRUE rather than
  merely printed — it greps the script for `data/`, `archive`, `boto3`.
  Was: A reader must be able to run
  the planted-edge positive control and the dead-world negative control
  without buying data. This is what makes the lab checkable rather than
  merely described.
- [x] **D2.4 + Q3 DONE 2026-08-09.** `occams/profiles.py` +
  `profiles/*.json` + 8 tests. Rules load from dated external JSON with a
  `source`; **`assert_fresh` REFUSES** a snapshot older than the caller's
  tolerance rather than warning — a warning about rules is one nobody reads
  twice. A missing rule **raises rather than defaulting**, because a rule
  that silently becomes zero is a rule that never binds. JSON not YAML:
  `occams/` is imported by the Lambda and its dependency weight already
  broke a build once. Two example profiles ship, describing a **geometry**
  rather than any provider's terms, and a test asserts no shipped profile
  names a provider. Was:
  `ChallengeConfig` is already parameterised; expose it so the rules are not
  hard-coded to one venue's geometry. **Extended 2026-08-09:** make profiles
  **versioned and dated** — effective date, rule-source reference, and a
  **staleness warning** when a snapshot is older than N days, shown for
  confirmation before any run is treated as current. We hold sealed
  constants; a provider retired a plan tier on 2026-05-01 while its own
  public pages still advertised it, so a rule snapshot with no date on it is
  a silent expiry waiting to happen.
- [x] **D2.5 DONE 2026-08-09.** `scripts/make_plots.py` + `make plots` ->
  `artifacts/plots/` (PNG + SVG). **Every number is read from the register**,
  so a figure cannot drift from the record it claims to show; the frontier
  is the one exception and is recomputed through the real rules engine
  because it is a property of the rules, not of a past run. Reproduces the
  documented anchors (2.0R crosses the 0.55 gate at ~45% WR, 1.5R at ~54%).
  matplotlib is a **dev dependency only**. Fixed a latent defect while
  building it: both dynamic script loaders failed on any module defining a
  `@dataclass`, because it was not registered in `sys.modules` before exec.
  Was: Feasibility frontier · the P(pass)-vs-size
  shape that became an edge diagnostic · the four-order entry table from
  Z0, which is the most publishable single figure we have.
- [>] **D2.6** `[needs-user]` **The push — NOT YET (user, 2026-08-09).**
  Everything buildable is done and the repository is publishable; the
  remaining step is deliberately unpressed. Original scope: New public remote, full audited
  history. **T3.1 has already cleared it** — 0 hits across every commit
  message and historical blob. Re-run `scripts/prepublish_audit.py`
  immediately before pushing; a leak added after the audit is still a leak.

**Gate detail:**
- [x] **T3.1 DONE — the repository is PUBLISHABLE.**
  **T3.1 DONE:** `scripts/prepublish_audit.py` scans the FULL history —
  every commit message, every blob at every revision it existed in, plus
  charset hazards and the author list. `occams.privacy` only ever scanned
  tracked files at HEAD, and a term removed later is still public.
  **Result: 0 hits in commit messages, 0 in historical blobs, 0 charset
  hazards. PUBLISHABLE.** The sibling repo needed an orphan-branch rebuild
  for exactly this; occams-trader does not. A live test asserts it stays
  true, because a follow-up commit cannot fix a leak that is already in the
  history.
  **Still open, and they are decisions not builds:** T3.5 `[needs-user]`
  LICENSE + venue · T3.6 the push itself · T3.2 $0 synthetic quickstart ·
  T3.3 bring-your-own-rules config · T3.4 plots.
- [>] **D3 R4 — broker paper account with API fill reads.** Real fills, real
  -time data, transcription error gone. Only worth doing when there is a
  strategy worth executing.
- [>] **D4 Track 2 — campaign runner + new symbols (T2.1-T2.5).** MGC/MCL
  is $19.16 pre-approved but is another draw from the same urn; the runner
  matters more than the symbols.

## The standing question

**We have no strategy with a demonstrable edge.** The fade's was an
artifact (#3a), ORB never worked (#2), and the one live signal (H5, order
flow) is suggestive and underpowered. Every item above either makes the lab
harder to fool or prepares the ground — none of them, on their own, finds an
edge. That is worth saying plainly at the top of a task list.

---


Each phase gates the next. `[auto]` = buildable without money/keys/data;
`[needs-user]` = requires a user decision, purchase, or secret. TDD
(red→green) for all pure logic. Commit per completed task block. The venue is
never named in code, docs, or commits (CLAUDE.md §0).

Rationale for every choice: [CONTEXT.md](CONTEXT.md).

---

## P — user decisions (block later phases, not each other)

- [x] P1. **DONE** — data vendor purchased — Databento or
  FirstRateData, MES + MNQ 1-min full history (~$100–200). Deliver files into
  `data/` (git-ignored). *Blocks Phases 6–8.* **User: decide after the
  initial build** — Phases 2–5 proceed on synthetic bars meanwhile.
  **Instrument-identity checklist (sealed 2026-07-04 — run at purchase):**
  1. Databento: `GLBX.MDP3` (CME Globex's own feed) · `ohlcv-1m` ·
     continuous **`MES.v.0` + `MNQ.v.0`** (volume-based roll = "trade the
     most liquid contract", matching live behaviour) · **plus the
     `definition` schema** (instrument metadata from CME).
  2. Loader asserts tick 0.25 / multipliers $5 (MES) & $2 (MNQ) / product
     codes against the definitions — identity is a TEST, not an assumption
     (task 1.4).
  3. Spot-check 2–3 recent sessions' OHLC vs a second source (TradingView
     front-month chart, or the venue platform once the account exists).
  4. **Roll days** (~4/yr, `instrument_id` changes): flagged by the loader
     and **excluded, pre-registered** — day-flat trading makes us otherwise
     roll-immune; only the cross-roll gap pollutes that day's ATR/gap stats.
  5. Runbook rule (Phase 11): live = the highest-volume contract — exactly
     what `v.0` selected historically, so backtest and live agree by
     construction.
  6. Same data ≠ same fills: the challenge account is the firm's simulator
     on real CME prices — bracketed by our conservative fill model + the
     parity-log kill threshold in the paper gate.
  **Pre-purchase review additions (2026-07-04):**
  7. Cost verified at the quote screen 2026-07-04: **~$14.80 per product**
     (2621 days = exactly the May-2019 micro launch; $0.065/MB checks out).
     **Quote is per-symbol → buy BOTH MES and MNQ (~$30) + the tiny
     `definition` request.** The advertised $125 new-user credit did not
     appear at signup — treat as bonus if it materializes in billing, not
     as a plan. TV automation facts (v2): CME real-time non-pro bundle
     **$7/mo**; CME free at 10-min delay → a $0/mo "delayed webhook" rung
     exists, priced by a sweep variant (no entries before 10:10 ET).
  8. Download with **decimal prices + ISO/pretty timestamps** if offered;
     otherwise task 1.2 handles ns-integer timestamps and fixed-point
     (1e-9) prices at the seam. Globex is a ~23h session → quality-probe
     `min_bars` thresholds get set from real bar counts, not the RTH 390.
  9. The purchase buys **the answer, not the pass** (chained P(pass within
     ~2 attempts) ~25–40%; most likely single outcome = validated no-go at
     ~$0–25 total). Recorded so future-us can't misremember what was bought.

  **PRE-SWEEP BLOCKERS (all must close between purchase and Phase 7 seal):**
  - [ ] B-P1a. CPI/NFP calendar back-fill from the two BLS archive pages
    (browser; BLS 403s scripted fetchers) — else backtest and live trade
    different day-universes.
  - [ ] B-P1b. **Per-instrument Costs** — MNQ multiplier is **$2** (not $5);
    sweep needs per-instrument cost objects, asserted from the vendor
    definition file (folds into 1.4, TDD).
  - [ ] B-P1c. Loader seam pass on the real files (1.2/1.3 rerun: formats,
    session thresholds, roll-day list).
- [x] P2. **DONE** — Telegram bot live (BotFather), put
  `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` in `.env` (git-ignored).
  *Blocks Phase 9 only.* **User: after the build.**
- [x] P3. **Rule values CONFIRMED + plan sealed (2026-07-02, grilled):**
  $50k · target **$3,000** · EOD trailing DD **$2,000** · daily guard $1,000
  (harmless) · no eval consistency · min 1 day · 3 minis/30 micros cap.
  → `rules/config.py` at Phase 3. Plan/vendor details: `venue.local.md`
  (git-ignored) only.
- [x] P4. ✅ 2026-07-04 **Dedicated ops vault created: `~/Documents/
  occams-razor`** (structure: Templates / Debriefs / Plans / Experiments /
  Decisions / Journal / Reference; every note tagged `occams/*` + backlinked
  via `up:` to section MOCs → [[Home]]; vault README documents the scheme;
  venue never named there either). `OBSIDIAN_DEBRIEF_DIR` set in `.env` →
  `10 - Debriefs`. **One manual step:** Obsidian → "Open folder as vault"
  (app was running; its registry is rewritten on quit, so not auto-edited).
- [x] P5. **Automation policy checked (2026-07-02):** bots/full-auto
  **prohibited**; human execution of self-generated signals compliant — our
  design by construction. Funded-phase news window noted. Details in
  `venue.local.md`.

## Phase 0 — repo & plan `[auto]` ✅ 2026-07-02

- [x] Local git repo (`main`), `.gitignore` (secrets, data, `*.local.md`),
  `CLAUDE.md`, `docs/CONTEXT.md`, this task list. **No remote.**

## Phase 1 — package + data layer `[auto after P1]`

- [x] 1.1 ✅ 2026-07-02 `pyproject.toml` (py3.12, pandas/numpy, pytest+ruff),
  `Makefile` (`test`, `lint`), `occams/` package (modules land per phase).
- [x] 1.2 ✅ 2026-07-04 `occams/loader.py::read_vendor_csv` — both vendor
  shapes (UTC `ts_event` / naive `datetime` with explicit `naive_tz`, else
  loud error), validation (sorted, dup/OHLC checks), → ET-aware frames;
  `to_trading_days` (RTH filter, opening-range split, **ATR from prior days
  only — no lookahead**, short sessions excluded). Built on fixture CSVs;
  real data is plug-in. **6 TDD tests.** (Resample-to-5min dropped: ORB
  needs only the range extremes; 1-min feeds the sim directly.)
- [x] 1.3 ✅ 2026-07-04 `occams/loader.py::quality_report` — span, session
  count, short sessions, missing business days. Runs on P1 day one to set
  the usable range + lockbox span.

## Phase 2 — simulator `[auto]` (can start before P1 on synthetic bars)

- [x] 2.1 ✅ 2026-07-02 `occams/sim.py`: `simulate_day()` — OCO entry stops,
  brackets relative to fill, target-as-limit, **conservative both-touched
  rule (stop first)**, gap-through-stop at worse open, session force-flat,
  max_trades re-entry cap, dollar P&L to the cent. **10 TDD tests.**
- [x] 2.2 Equity/ledger: chain DayResults into end-of-day equity marks (the  **CLOSED 2026-08-01: delivered — the simulator has been in use since July.**
  glue between sim and rules; lands with the Phase 5/6 harness).

## Phase 3 — challenge rules engine `[auto]`

- [x] 3.1 ✅ 2026-07-02 `occams/rules.py`: `ChallengeState.record_day()` —
  EOD trailing-DD ratchet, **lock-at-start once cleared** (`min(high−dd,
  account)`), $1,000 daily guard = **intraday lockout, not a breach**
  (corrected 2026-07-04, `8832a10`), min-days gating, sticky
  terminal states; `floor` public for the fuel gauge. **7 TDD tests.**
  (No consistency check — the sealed plan has none in the eval; the funded
  40% variant lands with the funded-mode parameterization, Phase 11.)
- [x] 3.2 `rules/config.py`: the sealed values as the single source  **CLOSED 2026-08-01: delivered — rules.py + harness.py are the engine E2 scored through.**
  (currently duplicated in tests) — fold in when the harness needs them.

## Phase 4 — strategy + risk manager `[auto]`

- [x] 4.1 ✅ 2026-07-03 `occams/strategy.py::build_plan()` — ORB range→
  bracket levels 1 tick beyond, VWAP-side filter disarms the off side,
  ruin-math sizing (0 contracts → NoTrade). **6 TDD tests.**
- [x] 4.2 ✅ 2026-07-03 sim honours per-day `daily_stop_usd` (own daily
  stop suppresses further entries). Sizing lives in `build_plan`.
- [x] 4.3 ✅ 2026-07-03 `occams/calendar.py::blocked_reason()` mechanism +
  2026 FOMC seed at `occams/data/economic_calendar.csv`. **Historical
  NFP/CPI back-fill lands with P1 (needed for backtests).**

## Phase 5 — positive control `[auto]` — GATE ✅ 2026-07-03

- [x] 5.1 ✅ `occams/synth.py` (plantable-edge synthetic market) +
  `tests/test_control.py`. **Gate passed** on the synthetic edge world
  (ORB p_pass=1.00 vs null 0.73; no-edge world 0.00; +0.27 edge). The
  harness is a validated instrument.

## Phase 6 — null model `[auto after P1]` — GATE

- [x] 6.1 ✅ 2026-07-03 machinery: `occams/strategy.py::make_null_strategy()`
  (random side at first post-range bar, same risk manager, same costs).
  On synthetic no-edge world it yields 0.05 (a small non-zero floor —
  behaviour honest). **The measured no-edge floor on REAL data (P1) is the
  gate number** the PREREG G2 gate compares against — pinned when data
  lands.

## Phase 7 — pre-registered search `[auto after P1, P3]`

- [x] 7.1 ✅ 2026-07-03 `docs/PREREG.md` **DRAFT** — grid, walk-forward,
  lockbox scheme, null baseline, gates G1–G4 (P(pass)≥0.55, edge-vs-null≥
  0.15, P(breach)≤0.30, plateau ≥5 cells within 0.05). Seals when P1 data
  lands (SHA-into-provenance instructions inside).
- [x] 7.2 ✅ 2026-07-03 machinery: `occams/search.py::sweep()` (cartesian
  product enumeration; every cell MC'd on the shared day-sequence).
  **Runs against real data as a one-liner once P1 lands.**
- [x] 7.3 ✅ 2026-07-03 machinery: `find_winner()` implements G4 plateau as
  Chebyshev-distance neighbourhood — rejects lone spikes as noise.
  Robustness splits are a wrapper over `sweep()` per split; runs when data
  lands.

## Phase 8 — challenge Monte Carlo + verdict `[auto]`

- [x] 8.1 ✅ 2026-07-03 machinery: `occams/harness.py::monte_carlo()` over
  every viable start day (P(pass), P(breach), median days). Scales to
  ≥1,000 attempts when real data lands.
- [x] 8.2 ✅ 2026-07-03 machinery: `occams/search.py::verdict()` — GO iff
  both OOS AND lockbox winners clear the gates, else NO-GO with reason.
  Rehearsed on synthetic (edge→GO, no-edge→NO-GO). Economics gate (E[cost]
  vs funded value) is a small addition when P1 lands.

## Phase 9 — comms `[auto after P2, P4]` (grilled + sealed 2026-07-02)

- [x] 9.1 ✅ 2026-07-03 `occams/report.py::plan_card / debrief / fuel_gauge`
  — pure text builders, transport-agnostic. Missing fills auto-nudges
  `/fills` reconcile. **4 TDD tests.**
- [x] 9.2 ✅ 2026-07-04 `occams/obsidian.py::write_debrief_note` — sorted
  frontmatter with vault-convention `tags` + `up: [[Debriefs]]`, previous-
  day chain link (gap-aware), idempotent re-runs (replace, never duplicate);
  `debrief_dir()` reads env with .env fallback, fails loud naming P4.
  End-to-end verified: a sample note written into the real vault through
  the real report builder. **6 TDD tests.**
- [x] 9.3 **DONE as B7.1/B7.2** — human-as-sensor commands (one webhook, FitnessCore pattern):
  `/range <high> <low>` → validate vs ATR bounds → full order plan reply
  (**no live market-data feed in v1**; Databento-live = v2 escape hatch);
  `/fills <details>|none` → echo-confirm → P&L, DD state, parity.
- [x] 9.4 **DONE as B3.1/B3.2/B3.3** — cron-driven runners: CLIs (`occams morning` /
  `occams evening`) during research; evening cron always fires (fills → full
  Debrief; missing → provisional sim-view + `/fills` nudge; late fills →
  recompute + resend); morning cron nudges if no `/range` by ~15:05 London.
  **Parity log with pre-set kill threshold.**
  **Design sealed 2026-07-04 → [day-state-machine.md](day-state-machine.md)**
  (mirrored in the vault's Reference): `DayPhase` enum + pure transition
  table, cron events as idempotent self-loops, rejections as Telegram
  replies, enum-string persisted in StateStore. **No FSM library** (XState
  rejected — JS/TS + oversized; Python FSM libs — needless dependency).
  The doc's 4 invariants are the phase's acceptance tests.
- [x] 9.5 **DONE as Workstream B** — AWS lift: FitnessCore SAM
  pattern — 2 EventBridge crons + webhook Lambda → Telegram; **S3 bucket for
  trading reports** (Debriefs, parity, MC reports). No SQS/ECS/DynamoDB
  unless a concrete need appears.

## Phase 10 — 30-day paper gate `[needs-user: P5, daily ritual]`

- [x] 10.1 Run the full morning/evening workflow on live data, sim-executed,  **CLOSED 2026-08-01: moot — attached to protocol #4, stood down 2026-08-01 (Z0.2).**
  every trading day for 30 days; parity tracked per trade.
- [x] 10.2 Exit review vs pre-registered criteria → go/no-go for a live  **CLOSED 2026-08-01: moot — attached to protocol #4, stood down 2026-08-01 (Z0.2).**
  attempt.

## Phase 11 — the attempt `[needs-user: fee]`

- [x] 11.1 Written runbook BEFORE day one: fixed risk table, daily stop,  **CLOSED 2026-08-01: moot — no attempt while the strategy has no obtainable edge.**
  stop-at-target, calendar no-trade days, no discretionary overrides,
  DD-proximity de-risking; funded-mode parameterization documented.
- [x] 11.2 The attempt, run as an experiment: daily Debrief + parity;  **CLOSED 2026-08-01: moot — no attempt while the strategy has no obtainable edge.**
  outcome written up either way.

---

**Sequencing note:** Phases 2–4 are pure `[auto]` TDD and can proceed
immediately on synthetic bars; P1 (data purchase) is the only hard external
dependency for Phases 6–8. The single most important ordering rule, paid for
in the series: **Phase 5 (positive control) before any real result is read.**

---

## Autonomous-run status (2026-07-03)

**Everything \$0-buildable-in-advance is done and committed** — 42 TDD tests
green, lint clean, all machinery rehearsed on synthetic.

**Parity primitive** (`occams/parity.py`, 5 tests) — the exceptional-project
metric (CONTEXT §12): tracks per-trade backtest-vs-live drift, fires a kill
signal when |drift| exceeds a preset threshold with a minimum sample.
Consumed by the Debrief when `/fills` arrive.

**What's left, and what unblocks it:**

| Task | Blocked on | When ready, effort |
|---|---|---|
| 1.2, 1.3 data loader + quality probe | **P1** (data purchase) | ~2 hours |
| 6.1 measure the real no-edge floor | **P1** | one command against the null adapter |
| 7.2, 7.3, 8.1, 8.2 real sweep + verdict | **P1** | one command; the machinery is built |
| PREREG seal (§7.1 in the doc) | **P1** (so seal is over real data) | 1 minute |
| 9.2 Obsidian daily notes | **P4** (vault path) | ~30 min |
| 9.3, 9.4 Telegram bot + `/range`, `/fills`, cron | **P2** (bot) + Lambda pieces | ~4 hours |
| 9.5 AWS SAM lift + S3 reports | **P2** + AWS auth | ~half day, uses FitnessCore's pattern |
| 10, 11 paper gate + attempt | everything above + you | multi-week rituals |

## Code review 2026-07-03 — fixes applied

Full-tree review (10 findings filed). Pre-P1 fixes DONE, all TDD (50 tests):
- **#1 conservative same-bar stop** — entry bar touching the stop now stops
  out same-bar; target never fills on the entry bar. Kills the optimistic
  bias. Control gates re-verified green under the stricter rule.
- **#3 G4 = PREREG exactly** — median-rule plateau (Chebyshev-1, incl. cell).
- **#4 per-day null coin** + `null_baseline` (mean over ≥5 seeds) as the G2
  comparator; PREREG §3 hardened accordingly.
- **#5 tz contract** — `occams/sessions.py`: naive timestamps raise; UTC→ET
  tested both DST regimes; Phase 1.2 loader MUST route through it.
- **#10 empty-range guard** — NoTrade, never NaN levels.

Deferred fixes now DONE (2026-07-04, TDD, 63 tests total):
- **#2** ✅ `occams/state.py` — atomic JSON StateStore; ChallengeState
  snapshot/restore; day-keyed drift/processed records (re-run REPLACES,
  never double-appends); corrupt file = loud error, never a silent reset.
- **#6** ✅ ParityLog dispersion track — `mean_abs_drift` + abs threshold;
  sign-balanced disagreement now kills.
- **#7** ✅ (partial) calendar: **FOMC 2019–2026 verified from the Fed's own
  pages** (69 dates incl. 2020 emergency meetings). **CPI/NFP still TODO:**
  BLS blocks non-browser fetchers (403) — pull the two BLS archive pages via
  a browser on P1 day and append (~190 rows).
- **#8** ✅ short sessions excluded + reported by the loader.
Remaining: **#9 entry points** (Phase 9, unchanged).

## Codex reconciliation — execution record (2026-07-04)

All code items from the reconciled fix plan are CLOSED (105 tests, lint
clean, `make check` incl. live privacy scan green):

- [x] G1 `15e5aaa` — 6.1 doc honesty (dates, stale P4, overstated 7.3)
- [x] G2 `16560ad` — 1.1 identity + per-instrument costs · 1.3 calendar
  wiring · 1.2/1.4 definitions + roll days · 2.1 daily-stop wiring ·
  2.3 true-risk sizing
- [x] G3 `47f4490` — 2.4 both-entry ambiguity stand-aside · 4.1 real VWAP
- [x] G4 `9f73ad1` — 3.1 ledger-cached MC (each day simulated once) ·
  3.2 combined_verdict (independent instrument splits) · 3.3 PREREG hash
  provenance (mismatch raises)
- [x] G5 `87e6b6a` — 5.1 pure dayflow machine (sealed invariants
  executable) · 5.2 parity in Debrief · 6.2 privacy scanner + `make check` ·
  2.2 EOD-guard contract pinned

**Remaining OPEN (not closable by code):**
- [x] 2.2-confirm ✅ 2026-07-04: venue daily guard is an INTRADAY LOCKOUT
  (liquidate + lock to 6PM ET, account survives), NOT a failure — engine
  corrected (guard-as-breach removed; `8832a10`).
- [x] CPI/NFP calendar backfill — BLASTED: BLS 403s scripted fetchers AND  **CLOSED: delivered — the 259-row calendar is sealed and in use.**
  bls.gov is outside the Chrome-extension site-access allowlist. **Blocked
  on user:** grant the Claude extension site access to bls.gov (or paste
  the two archive pages) → then automatic parse+verify+commit. Guard-timing
  item is now CLOSED (below), so this is the only external calendar item.
- [x] P1 purchase · P2 bot token.  **CLOSED: delivered 2026-07-05.**

7.3 is now genuinely closable at data time: split gating exists
(`combined_verdict`); year/regime splits run as sweep-per-bucket.

## Orchestrator-trust batch (2nd Codex review, 2026-07-04)

The verdict runner drifted from the sealed protocol; closed as a batch
(122 tests, `make check` green):
- [x] #1/#2 scripts/ in lint, `occams-verdict` console script, `.PHONY` fixed.
- [x] #3 project_root() resolves from the module — cwd-independent.
- [x] #4 `occams/verdict_cli.py` FAILS CLOSED: asserts vendor definitions,
  loads the calendar, refuses to run without CSVs+definitions+calendar+hash.
- [x] #6/#9 run_verdict sweeps the FULL sealed grid (range_minutes via
  per-range day splits, vwap_filter, max_trades) with the daily stop carried.
- [x] #7 null_baseline threads `events` → same day-universe as the strategy.
- [x] #8 three-state decision GO / **GO-RESEARCH** (gates pass, economics
  fail) / NO-GO; funded_value + attempt_fee are protocol inputs.
- [x] #11 quality report renders roll-day count.
- [x] #5 S3 state adapter  **CLOSED: delivered as aws/state.py.** — forward-note, AWS lift (Phase 9.5).
- [x] #12 benchmark  **CLOSED: suite runs in ~75s; no longer a concern.**: full 128-cell × 2-instrument synthetic sweep now ~60s;
  real MES+MNQ (~1750 days) needs a timed run before trusting "one sitting"
  — `simulate_day` iterrows is the remaining hotspot, optimise only if the
  measured runtime demands it.

## Current next-actions (2026-07-04, post 2nd-review batch)

**Code: nothing left pre-P1.** Both Codex reviews closed; 122 tests;
`occams-verdict` is the sealed one-command chain and fails closed on any
missing input.

**P1-day runsheet (in order):**
1. Buy MES.v.0 + MNQ.v.0 `ohlcv-1m` **+ `definition` schema** → save as
   `data/MES.csv`, `data/MES.definition.csv`, `data/MNQ.csv`,
   `data/MNQ.definition.csv`.
2. Complete CPI/NFP backfill (bls.gov via extension grant or paste).
3. Set `funded_value` in verdict_cli Protocol (economics gate input) +
   final PREREG read → the hash seals on first run.
4. `occams-verdict` → quality reports, per-instrument sweeps, verdict at
   `data/verdict.md`. **Time it** (Codex #12): optimise simulate_day only
   if the measured runtime demands.
5. Decision: GO → Phase 9 comms build (needs P2). GO-RESEARCH / NO-GO →
   write it up; no fee, project concludes honestly at ~$30 total.

## Deep-research: rules layer landed; community layer parked (2026-07-05)

- [x] `docs/RULES.md` — verified evaluation + payout-layer rules (3-0 votes,
  official sources; quotes/URLs in venue.local.md). **Corrections: cost is
  $119/MONTH + $109/reset (not ~$79 one-time) — economics unit updated in
  Protocol; full time-based E[cost] model is a seal-time item.**
- [x] **Community-evidence research COMPLETE (2026-07-05, round 2).**
  Resumed `wf_3aa2a4fb-8fc` with cached scope/search/fetch (free), verify
  voters on Opus, synthesis in the main loop. Result: 25 claims
  adversarially verified → **24 confirmed, 1 refuted, 0 unverified**; the
  unverified community claims were salvaged from the round-1 fetch
  transcripts (no follow-up workflow needed). All three RULES.md §3
  PENDING items closed VERIFIED. Deliverables: `docs/EVIDENCE.md` (generic
  behavioral/base-rate synthesis + design-fit verdict), RULES.md §2b
  conduct rules + §3 resolution, venue.local.md provenance appendix.
  Key new inputs: funnel 16.8%/51.8%/33.3%; passers profile matches our
  design (tighter); unfiltered-ORB-no-edge prior → NO-GO is the expected
  honest outcome; funded_value formula + ~0.8 ops haircut for seal.

## P1 data purchase — DONE 2026-07-05

- [x] API key → .env; `scripts/fetch_data.py` (quote-before-spend; raw .dbn
  persisted before conversion after a $9.21 conversion-crash lesson).
- [x] Purchased: MES.v.0 + MNQ.v.0 ohlcv-1m 2019-05-01→2026-07-05 continuous
  ($9.21+$9.22) + definition ×2 ($0). Portal parent-MES ($13.99) kept as
  backup. Total P1 spend ≈ $32 incl. losses.
- [x] Identity assertions PASS: tick 0.25/0.25, multiplier 5.0/2.0, class F.
- [x] Quality probe: 1,849 sessions, 1,741 tradable days per instrument
  (2019-05-24→2026-07-02), 65 short sessions (holiday early closes),
  29 roll days excluded, missing bdays = exchange holidays only.
  Vendor condition report: 13 degraded days in range (incl. 2020-02-27/28
  COVID crash), 13 "missing" = weekend dates. No blocker.
- [x] SEAL GATE before `occams-verdict`: CPI/NFP backfill → funded_value +  **CLOSED: delivered — the CPI/NFP calendar ships in the package and E2 used it.**
  time-based E[cost] in Protocol → PREREG final read → `git rev-parse
  HEAD:docs/PREREG.md` → PREREG.sealed → run ONCE.

## Verdict #1 (2026-07-06) — VOID → PREREG v2 track

- [x] V1. Sealed verdict ran (94s): NO-GO **void for instrument defect** —
  daily-ATR-scaled stops ($213–423/contract) vs $175 risk = 0 contracts in
  all 128 cells since 2019, null included; all stats structural zeros; no
  market information revealed. Record: docs/VERDICT-2026-07-06.md.
- [x] V2.1 ✅ 2026-07-06 stop axis in ORB-native units (`stop_range` ×
  range height, {0.5..1.25}); 30-micro cap; degenerate/sub-tick guards. TDD.
- [x] V2.2 ✅ 2026-07-06 validity gate: `MCStats.traded_days` +
  `ValidityError` in sweep and null; CLI exits 2 "INSTRUMENT FAILURE". TDD.
- [x] V2.3 ✅ 2026-07-06 positive control at ATR=55 (incl. NEW true dead
  world `kick_scale=0` — the impulse alone was harvestable, edge_follow=0
  was never a negative control); dev-fold smoke: MES 86% days traded
  (1–12 contracts, med 4), MNQ 78% (1–7, med 2).
- [x] V2.4 ✅ 2026-07-06 v2 SEALED (`12ca0a32…`) → verdict #2 ran (699s):
  **validated NO-GO, both instruments, all folds** — best cell 0.187 vs
  0.55 bar (and G3-failing); in-sample bests 0.03–0.04; null 0.000 while
  trading. NO FEE PAID. Record: docs/VERDICT-2026-07-06-v2.md; vault
  E-001 + D-003. **Research phase concluded — success tier 1.**

## Wargame skill track (agreed 2026-07-06 — after v2 verdict)

- [x] W1. Create project-local `wargame-occams-trader` skill  **CLOSED 2026-08-01: not adopted — the wargame skill was never taken up.**
  (`.claude/skills/wargame-occams/`): self-contained copies of the base
  wargame templates + baked-in executor rules (venue never named; local
  git only; seal-before-read; validity-abort ≠ NO-GO; money moves =
  hand-to-user gates; make check + privacy scan as stage gates; validated
  no-go = success tier 1). Base `~/.claude/skills/wargame` stays untouched.
- [x] W2. Two mission archetypes in the skill: build mission (agent  **CLOSED 2026-08-01: not adopted.**
  executor — first use: Phase 9 comms build, only on GO) and operational
  mission (HUMAN executor — moves are daily cycles, forks keyed to fuel
  gauge/day-state observations, abort table = sealed kill thresholds).
- [x] W3. On GO: write the 30-day paper gate as an operational wargame  **CLOSED 2026-08-01: not adopted.**
  plan (Phase 10) and the attempt month as one (Phase 11 runbook) — the
  anti-discretion instrument; user is the executor.
- [x] W4. Record adopt/adapt decision in the occams-razor vault  **CLOSED 2026-08-01: not adopted.**
  (Crucible Phase-0 pattern).

## Family 2 research program (approved 2026-07-06) — "pass it or know why not"

Context: verdict #2 killed the ORB family decisively (best cell 0.187 vs
0.55, in-sample 0.03–0.04, null 0.000-while-trading). Codex's independent
review agrees: family-level failure, no massaging. This program is the
honest continuation — a NEW family under a NEW protocol, plus the two
levers the review missed: **horizon is purchasable** (no eval deadline;
time = $119/mo, already our cost unit) and **feasibility-first** (compute
the required edge before hunting for one). Guards from D-003 stay sealed:
no ORB revival, no sizing escalation, no fill-model softening, no lockbox
reuse. Prior on full success: ~20–35%; modal outcome: another validated
no-go at ~$30 more. That is a good trade against a −EV blind attempt.

- [x] **A. Feasibility map ✅ 2026-07-06 — GATE PASSED.** 2,592
  geometries × 400 MC through the real rules engine (135s; consistency
  rule added to `rules.py`, 3 TDD tests). `docs/FEASIBILITY.md`.
  Headlines: **asymmetry beats hit rate** (anchor: 2.0R needs WR 45% →
  P(pass) 0.74, E[cost] $362; 1.0R needs 60–65% — hardest corner);
  **economics binds harder than G1** (need P(pass)≥~0.65, med ≤~50d);
  horizon window 60–90d (120d prices out); **Advanced tier is worse —
  Zero confirmed, plan-shopping closed**; $175 risk stays. Family-2
  target spec: net R 1.5–2.0+ · WR ≥45–52% · 0.5–1 trade/day.
- [x] **B. Diagnostics microscope ✅ 2026-07-06 — hypothesis SURVIVES
  (marginal).** `scripts/diagnostics.py` + 3 hand-verified tests; dev
  folds only (2019-05→2023-08, event days excluded). Findings
  (`docs/DIAGNOSTICS.md`): 94% of breakouts fail → 0.93 fades/day; best
  cell 15-min/k=0.25 = true ~2.4R at ~40% WR, E[R] +0.23 both
  instruments (eod-as-loss); narrow-width condition lifts to +0.30/+0.34;
  costs ~0.06–0.11R. Sits AT the 90-day frontier, below the 60-day one —
  economics gate will bind. 30-min ranges strictly worse (dropped).
  Caveats sealed: dev numbers shrink OOS; v3 must use ABSOLUTE width
  thresholds; sim needs LIMIT-entry support (TDD, Phase C).
- [x] **C. Family 2 + PREREG v3 ✅ 2026-07-06 — BUILT, awaiting seal.**
  `occams/fade.py` (10 TDD tests): conditional-stop entry (executable
  mirror of ORB), true-risk sizing, gap/tie/EOD conservatism, 30-cap;
  fade-vs-follow coin null (G2 = direction alone); harness dispatch;
  verdict runner family branch + cadence-matched funded_value_for
  (open $1,100 / filtered $500, sealed derivations). **Bonus fix: G4 was
  structurally unsatisfiable** (combined sweeps re-indexed 1-D capped
  neighbourhoods at 3 < plateau_cells=5) — true grid geometry restored,
  regression-tested. CLI sealed to the 9-cell fade grid, horizon 90,
  range 15 only. PREREG v3 DRAFT written (family spec, null,
  contamination ledger, paper gate = binding lockbox).
- [x] **D. Data ladder — DESCOPED 2026-07-06 ($0).** Pre-2019 ES/NQ dev
  data was to provide uncontaminated hypothesis-generation ground — but
  the hypothesis is already generated; buying it after the fact adds
  nothing. Sealed instead (v3 §4): historical lockbox = advisory;
  **prospective 60–90-day paper window = the binding lockbox**.
- [x] **E. Verdict #3 ✅ 2026-07-06 — validated NO-GO at G1, WITH a real
  finding.** 30s run, validity silent, nulls ~0.00 while trading. Best
  P(pass) 0.41 (MES OOS) vs 0.55. **The edge is REAL and persists OOS**:
  34/36 fold-cells positive; MES OOS +0.107R / lockbox +0.141R (above
  dev — no overfit signature); MNQ OOS +0.171R. It is ~half the size the
  geometry demands (+$16/day vs +$33 needed). Escalations checked and
  rejected in the record. docs/VERDICT-2026-07-06-v3.md · vault
  E-002/D-004.
- [x] **F. MOOT — program CONCLUDED 2026-07-06.** Two families, three
  sealed verdicts, $0 fees, ~$32 total. Reopening bar (v4+): ex-ante
  net ≥ +0.25R/trade at ≥ 0.5 trades/day — the frontier number.

---

# THE LAB PROGRAM (founded 2026-07-09) — edge-finding instrument + timed publication

**Re-founding:** the challenge-research program concluded (D-004). The
project's new charter: **an edge-finding instrument** with two
monetization layers (personal trading now; the challenge later IF the
reopening bar — ex-ante ≥ +0.25R at ≥ 0.5 trades/day — is ever met) and
**a publication track that fires at the right time**, not now. Four
standing honesty controls govern everything below: ex-ante bar before
any grid · dev-fold-only screening · multiplicity ledger
(docs/PROTOCOLS.md) · the prospective paper gate as the only binding
lockbox.

## ROADMAP (the ordered sequence — updated 2026-07-11)

1. **NOW — paper campaign live-out** (T1.2 user: bot token + TV account;
   cron install on go). Protocol #4 runs 60–90 days.
2. **During the campaign** ($0 build work): T2.1 campaign runner ·
   T2.5 hypothesis-intake committee (borrowing the TradingAgents debate
   PATTERN — prompts/roles only, thin native build) · T3.1 pre-publish
   audit tool · T3.2 quickstart · T3.3 BYO-rules · T3.4 plots.
3. **T2.4 when ready**: MGC+MCL purchase (~$19.16 approved) + per-symbol
   plumbing → fade-on-{MGC,MCL} research protocols.
4. **AT CAMPAIGN END (~3 months), three gated decisions**:
   (a) personal-sizing decision (only if parity held);
   (b) **candidate Lab protocol #5 — "TradingAgents on the bench"**:
       prospective-only, null-controlled evaluation of the 92k-star
       agent framework as a SPECIMEN (decision D-005: neither fork nor
       foundation) — needs its own SPEND line (~$50–100 LLM spend, a
       deliberate cap raise) and its own PREREG;
   (c) **the publication gate** (T3.5/T3.6): license, essay venue,
       params-vs-generalized, user pushes.

## Track 1 — Paper campaign: live-fire validation of the fade ($0, 60–90 days)

- [x] T1.1 ✅ 2026-07-09 **PAPER-PREREG DRAFTED — awaiting user seal**
  (docs/PAPER-PREREG.md): cell k=0.2 unfiltered (only cell best on OOS
  AND lockbox on both instruments), $175 × both instruments, ≥60 days
  AND ≥40 trades (hard stop 90), kill thresholds armed from trade 10,
  TV-free uniform-delay argument documented (§3). Seals as protocol #4.
- [x] T1.2 ✅ 2026-07-28 **Bot live + venue ready.** occums_lab_bot
  created; token + chat_id in .env (never in chat/git); delivery
  verified to phone; certifi CA fix committed (515b9ad). Venue:
  TradingView free in Chrome + MOBILE APP for push alerts (4 price
  alerts/day, set after /range, deleted EOD). CRON INSTALLED as
  launchd LaunchAgents (com.occams.paper-morning/-evening): 13:30 &
  22:30 Europe/London weekdays = 08:30–09:30 / 17:30–18:30 ET
  year-round incl. DST-mismatch weeks; launchd (not crontab) so
  lid-closed missed runs fire on wake; logs →
  data/paper_cron.log. **CAMPAIGN STARTS 2026-07-29.**
  **Tooling addendum 2026-07-29** (process aid, no seal change — human
  still places orders + logs fills): `tools/fade_campaign.pine` draws
  the range, tracks the extreme, detects the failure close, and emits
  copy-paste `/range` + `/setup` alerts with sealed levels + sizing.
  **Automation rungs decided**: Rung 1 (TV Pro webhooks, ~$14/mo) =
  deferred, saves ~20s/day; **Rung 2 (AWS lift of the two cron jobs to
  EventBridge+Lambda+S3, ~$0, the FitnessCore pattern) = APPROVED
  direction, needs user AWS auth** — kills the laptop-courier fragility
  (wake-race class) permanently. Order placement is never automated.
- [x] T1.3 ✅ 2026-07-09 **Comms built, fade-adapted** (6 TDD tests on
  the pure core): `occams/paper.py` (command grammar /range /setup
  /fills /skip; model_trade = the sealed engine's prices+sizing from
  logged levels; trade_drift = actual−model, EOD isolates entry side),
  `occams/telegram.py` (stdlib-only, dormant-safe without token),
  `scripts/paper_morning.py` (calendar-aware plan card + sizing table),
  `scripts/paper_evening.py` (pull logs → parity → state → kill check →
  Debrief send + vault note; idempotent day-replace).
- [x] T1.4 ✅ 2026-07-09 Parity ledger + kill monitor wired through
  StateStore/ParityLog (kill $5/$10 from trade 10, per the seal); raw
  Telegram log = append-only audit trail (data/paper_logs.jsonl).
  Make targets `paper-morning`/`paper-evening`; crontab (user installs
  when token lands):
  `0 9 * * 1-5 cd ~/occams-trader && make paper-morning`
  `0 17 * * 1-5 cd ~/occams-trader && make paper-evening`
- [x] T1.5 Weekly human journal note (vault 50-Journal); campaign  **CLOSED 2026-08-01: moot — the campaign it journals is stood down.**
  mid-point review at day 30.

- [x] **X1 CLOSED 2026-08-01 — the entry mechanism was the whole gap.** A quick
  re-implementation of the fade over pooled 2019-2026 read **-0.046R
  (MES) / -0.025R (MNQ)** per trade, where the sealed verdict measured
  **+0.1R** on its OOS/lockbox folds. Almost certainly explained by: no
  FOMC/CPI/NFP calendar filter, pooled years instead of the sealed folds,
  and a re-implementation rather than `fade.py` itself. **But it is not
  yet proven to be those things**, and cross-implementation disagreement
  is exactly the defect class that voided verdict #1. Run the same days
  through the real engine with the calendar filter and the real folds,
  and reconcile to the tick. Until this closes, **no absolute claim about
  the fade's health should rest on either number.**

## Track E — What separates this from a leading-edge lab (2026-08-01)

The machinery is now good: sealed pre-registration, multiplicity ledger,
controls, walk-forward folds, an enforced SOP, a provenance-tracked archive,
spend governance, and three guards that have each caught a real defect.

**What is binding is no longer the instrument. It is the input.** Seven
years of 1-minute bars on two of the most heavily traded futures on earth is
public information, and it holds ~+0.03R gross against a +0.25R requirement.
Better machinery does not change that. These four gaps are what would.

- [~] **E1 IN PROGRESS — order-level gate DONE 2026-08-01**
  (`occams/execution.py` + 10 tests). A strategy now declares an ORDER —
  type, side, level, placement bar — and the fill is DERIVED from what the
  market then did. An entry price is never an input. `obtainable()` is the
  gate: could ANY order placed at the decision bar have produced this fill?
  Venue rules are enforced (a market order cannot name a level; a limit on
  the marketable side is refused; a stop on the wrong side triggers
  instantly — protocol #4a's defect, now a rule). Slippage can only hurt,
  and a gapped stop fills at the open, never at its level.
  **Wired into `verdict_run` 2026-08-01**: `_gate_entries` builds a real
  sample of plans and puts them through the gate before any cell is swept.
  **DEFAULT-DENY** — a family with no auditor raises, so a new strategy must
  supply one rather than slip past. `skip_entry_gate` raises if anyone adds
  it. Caught myself half-wiring it (imported, never called), which looks
  like protection and is not; a test now asserts the call site exists.
  **Still to do:** upgrade from bar-level to TICK-level using the trades
  tape we now own.
- [x] **E1.2 DONE 2026-08-01 — replaced with something better.**
  `tests/test_grid_geometry.py` tests the G4 plateau geometry DIRECTLY
  rather than through a fade sweep: a true 2-D interior cell has 9
  Chebyshev-1 neighbours, the same nine cells flattened to a 1-D chain have
  only 3, and `plateau_cells=5` is satisfiable on the real grid and
  **impossible** on the flattened one. That pins the BUG SHAPE — the
  re-indexing defect that made a GO unreachable in every prior run — rather
  than a strategy family that happened to exercise it, so retiring a family
  can never silently remove it again. Original scope:
- [x] ~~E1.2~~ replace the lost sweep-machinery coverage Two tests
  exercised the fade GRID (FadeParams cells, plateau geometry) and now
  assert the gate's refusal instead, because the fade cannot be swept. That
  machinery is still used by any future family and is now untested.
  Deliberately NOT solved with a gate bypass — a test-only escape hatch is
  how a gate stops meaning anything. Needs a family that declares real
  orders as the vehicle.
  Original scope: *tick-level execution simulation, the biggest one.* We proved
  the fade's entry was unobtainable **by hand, after the fact, on one
  strategy**. Nothing in the lab would have caught it. We now own the trades
  tape; the simulator should answer mechanically: given the actual sequence
  of prints, **would this order have filled, when, and at what price?**
  Converts entry-obtainability from a thing we remember to check into a
  property of the simulator, which every future verdict then inherits.
  Subsumes and supersedes Z0.5.
- [x] **E2 DONE 2026-08-01 — and it rejected my own prediction.** The
  obtainable fade scores **P(pass) 0.042 at 90 days** against a 0.55 gate,
  with P(breach) 0.440. The *unobtainable* sealed variant reaches only
  0.258, so **even the artifact would have failed G1** — verdict v3's NO-GO
  stands twice over. My registered prediction that P(pass) would peak below
  the expectancy-maximising size was **WRONG**: it rises monotonically
  (0.000 / 0.009 / 0.042 / 0.088 / 0.174 at $75-$350) because with negative
  expectancy the only route to the target is variance. **The interior peak
  I predicted requires a positive edge** — which makes the SHAPE of that
  curve a diagnostic for edge existence, independent of any expectancy
  estimate. Logged as E7.
- [x] **E7 DONE 2026-08-01** — `harness.edge_shape` classifies a strategy
  from the SHAPE of P(pass) against size, independent of any expectancy
  estimate — which matters because expectancy has misled this lab twice.
  Monotonic = variance harvesting; interior peak = real edge, and the peak
  is where to size. A boundary peak warns that the ladder, not the
  strategy, is the constraint. Original scope: — monotonic
  increasing means variance harvesting and no edge; an interior peak means a
  real edge. Add as a standard readout in the harness, alongside the
  obtainability gate. Discovered by E2 rejecting its own hypothesis.
- [x] ~~E2 original scope~~ — score against the REAL objective [$0] — everything to date is
  expectancy (R/trade). The challenge is a **path-dependent survival
  problem**: trailing drawdown, daily loss limit, minimum days, profit
  target. A lower-expectancy, lower-variance configuration can pass more
  often. **We may already hold a passing configuration and be scoring it
  wrong.** Same item as R1.1; listed here because it is a lab capability,
  not just one experiment.
- [x] **E3 DONE 2026-08-01 — measured off the tape.** MES confirmed:
  effective spread **1.00 ticks**, a 6-lot fills with 0 ticks of travel and
  sits at the p90 of print size. MNQ **optimistic**: effective spread
  **2.00 ticks median**, double the assumption; a 6-lot is large there (only
  3.6% of prints that size) and travels 1 tick median, 4 at p90. Magnitude
  stated so it is not over-read: one extra tick per side on MNQ is ~0.006R
  at one contract — real, but an order of magnitude below the 0.03R-vs-0.25R
  gap. **It changes no conclusion; it tightens the error bar.**
  `MEASURED_COSTS` added alongside the sealed dict, which is deliberately
  NOT changed: X1 established the engine reproduces verdict v3 to three
  decimals and that reproducibility is worth more than the correction. New
  work uses the measured values; any result should say which model it used.
- [x] ~~E3 original scope~~ — measure costs instead of assuming them — commission was found
  to be 0.05-0.09R per trade, decisive at this edge size, yet the cost model
  is an assumption ($1.25/side, 1 tick slippage). If real slippage is 2
  ticks at 6 contracts every net number shifts. The trades tape can measure
  it. **Until then every net figure carries an unquantified error bar.**
- [x] **E4 DONE 2026-08-01** — `occams/power.py` + a precondition in
  `experiment.run`. A hypothesis may declare a `power_plan` (test, effect,
  alpha, power); the run then **REFUSES** if the sample cannot detect the
  declared effect, because an ambiguous null costs alpha exactly as a real
  test does and then tempts a second look at a bigger sample, which is
  optional stopping. Immediate use: the R2.1 sample gives ~884 usable
  setups, detectable down to **r = 0.094** — recorded BEFORE the analysis so
  a null cannot later be read as "no signal" when it may be "not enough
  data".
- [x] **E4.1 Apply the same cumulative discipline to SPEND** — the R2.1  **-> now working-list item A2.**
  overspend ($114.82 against $81 approved) happened because the cost cap was
  per-run rather than cumulative, the same shape of defect as an
  underpowered test being run anyway. `fetch_orderflow.py` is fixed; audit
  every other spend path for the same assumption.
- [x] ~~E4 original scope~~ — power planning before alpha is spent — we run hypotheses and
  look. Required *n* should be computed FIRST, and an underpowered test
  **refused rather than run**, because an ambiguous null still costs alpha
  and still tempts a second look. Caught once by hand on H4; make it a
  precondition in `experiment.run`.
- [x] **E5 Regime conditioning** — one config across seven years, no  **-> now working-list item C4.**
  segmentation. Lower priority than E1-E4 and easy to turn into dredging,
  so it stays pre-specified and small.
- [x] **E6 Portfolio view** — a challenge may be passed by combining  **-> now working-list item C4.**
  several small uncorrelated edges rather than finding one large one. We
  have only ever evaluated single strategies in isolation.

## Track R — Research programme (founded 2026-08-01)

**Goal unchanged:** pass the challenge and trade it profitably. What
changed is the *route*. Reasoning in `docs/RESEARCH-PROGRAM.md`; the short
version is that markets invert all four properties that make an automated
research loop compound (stationary, non-adversarial, cheap to evaluate,
high SNR), so **more search over our existing price bars has negative
expected value**. The binding resource is statistical budget, not compute.

**Gated.** No phase starts until the prior gate is met. Every item carries
its cost and its information axis, because the axis is what makes a
hypothesis worth its alpha.

### R0 — Trust the instrument (gate on everything else)

- [x] **R0.1 X1 CLOSED 2026-08-01** [$0]. Re-run the comparator through the
  real `fade.py` with the calendar filter and the sealed folds; reconcile
  to the tick. A lab whose two implementations disagree by 0.15R cannot
  evaluate anything. **This is the gate, not cleanup.**
- [x] **R0.2 DONE** — hypothesis register (S3, append-only) [$0].
  `hypotheses/<id>.json` + `experiments/<hid>/<run>.json`. Fields: id,
  stated_at, falsifiable statement, **mechanism written before the
  result**, information_axis, search_space_size, alpha_allocated,
  prereg_sha, status, outcome, effect_size, ci, decision, superseded_by,
  **engine_sha**. A result computed by a different engine version is a
  different result — X1 made structural. No database (B7.3 reasoning).
- [x] **R0.3 Alpha ledger** [$0]. Multiplicity budget as a decrementing  **CLOSED 2026-08-01: delivered — alpha_allocated is a field on every registered hypothesis.**
  resource. The bar RISES as the register grows: a finding at attempt 40
  must clear more than the same finding at attempt 3. Surfaced in every
  report so no result is ever read without its attempt count.
- [x] **R0.4 Controls on current code** [$0]. Re-run the planted-edge  **CLOSED 2026-08-01: delivered — controls re-run; X1 reconciled and Z0.4 cleared ORB.**
  positive control and the dead-world negative control.
  **GATE:** controls pass AND X1 reconciles. Nothing below runs first.

### R1 — Spend nothing: re-score what we already own

*Cannot overfit anything new: the strategy is fixed, only the scoring
changes.*

- [x] **R1.1 H1 — the objective may be wrong** [$0, axis: objective].  **CLOSED: answered by E2 — P(pass) 0.042 at 90d against a 0.55 gate.**
  The challenge is a **path-dependent survival problem** (trailing
  drawdown, daily loss limit, minimum days), not an expectancy problem.
  Compute P(pass) for the EXISTING fade across sizings and day-selection
  rules. **Prediction registered in advance: P(pass) is non-monotonic in
  size and peaks BELOW the expectancy-maximising size.** Cheapest item in
  the programme and the most likely to pay. Least glamorous possible
  outcome: no new strategy, just correct scoring.
- [x] **R1.2 H2 — conditioning on measured world state** [$0, axis:  **-> now working-list item C1.**
  conditioning]. Exactly five conditioners, all registered before any is
  evaluated: range height / ATR · overnight gap · time-of-day of the
  failure close · trailing realised vol · weekday. Five pre-specified is a
  different act from grid-searching two hundred; the register enforces it.
- [x] **R1.3 H3 — is adverse excursion predictable?** [$0, axis: price].  **-> now working-list item C2.**
  Live data showed MAE **5-12x the stop distance**, and the stop sits deep
  inside ordinary intraday noise. Is any pre-trade observable separating
  the days that reclaim from the days that run? Note the *reclaim* variant
  is already tested and DEAD (-0.26R vs -0.05R over 3,328 setups) — this
  asks the prior question, not that one.
- [x] **R1.4 Write up R1 honestly**, positive or negative.  **-> now working-list item C3.**
  **GATE:** one of H1-H3 survives the multiplicity-adjusted bar, or price
  data is formally declared exhausted and we stop paying it attention.

### R2 — Buy one new information axis: order flow

- [x] **R2.1 H4 — aggressor imbalance at the failure close**  **CLOSED 2026-08-01: delivered as H5-FLOW-PREDICTS.**
  [quote first, axis: **order flow**]. Every search we have ever run used
  `ohlcv-1m`. The vendor also sells MBO / MBP-10 / TBBO. **The fade is
  explicitly an order-flow story** — "the breakout had no participation
  behind it" — that we have only ever tested through price. Smallest
  sample that can answer it; no grid.
- [x] **R2.2 Book pressure / absorption at the boundary** — runs ONLY if  **CLOSED 2026-08-01: on hold — book depth only earns its cost if H5 is confirmed, and it is not.**
  R2.1 justifies it. Not a fishing licence.
- [x] **R2.3 Cost + licence review** before any depth data is bought:  **CLOSED 2026-08-01: delivered — SPEND.md restated against vendor actuals.**
  MBP-10 is materially dearer than OHLCV and the `data/` licence terms
  bind identically. SPEND.md row before, not after.
  **GATE:** a dev-fold effect large enough to be worth an OOS read.

### R3 — Harness the autoresearch loop

*Only after R0's ledger is live, and pointed at whichever axis showed life.
Never at "find me something".*

- [x] **R3.1 Port the Karpathy three-way split**: charter (human) /  **-> now working-list item D1.**
  hypothesis+config (agent-writable, the ONLY writable surface) / engine,
  folds, controls (fixed, never agent-writable).
- [x] **R3.2 The addition markets demand** — the alpha ledger in the loop  **-> now working-list item D1.**
  itself, so the keep rule is multiplicity-aware. This is the single
  change that separates our loop from Karpathy's, and the reason his keep
  rule is right and a naive copy of it would be wrong.
- [x] **R3.3 Enforced blindness**: the proposer sees DEV folds only. Not  **-> now working-list item D1.**
  "shouldn't" — *cannot*, enforced by the harness. It never sees OOS and
  never sees the lockbox.
- [x] **R3.4 Mechanism-or-reject**: every proposal states why it should  **-> now working-list item D1.**
  work BEFORE the number is known. No mechanism, rejected unrun. The best
  single filter against dredging.
- [x] **R3.5 Controls every batch**; a batch whose positive control fails  **-> now working-list item D1.**
  is **VOID** and yields no result at all.
- [x] **R3.6 Reuse `crucible-autoresearcher`** rather than rebuild: it  **-> now working-list item D1.**
  already implements the pattern, the planted-edge control and the
  keep/discard loop. Consume it across a clean boundary — the separability
  thesis the series is arguing for.

### R4 — Execution upgrade (unblocks better measurement, not more search)

- [x] **R4.1 Broker paper account** (IBKR or Tradovate; both free, both  **-> now working-list item D3.**
  real CME futures). Trading 212 is **ruled out** — it has no futures at
  all, so a CFD proxy would carry different size, costs and hours and the
  drift number would not map to the sealed engine.
- [x] **R4.2 Read fills via API** — the human still places every order  **-> now working-list item D3.**
  (that IS the measurement, B-C2), but transcription error leaves the
  drift number entirely.
- [x] **R4.3 Real-time data dissolves B-C1.** With feed and execution both  **-> now working-list item D3.**
  real-time, delay parity stops being a constraint and cards can fire at
  09:46 instead of 09:56. Requires a dated protocol amendment (#4b).

### What would make this programme worthless

Running an unconstrained search, finding something beautiful, and trading
it. The guardrails are not bureaucracy — they are the only reason a
positive result from this lab would be worth believing.

## URGENT — the fade's entry price may be unobtainable (2026-08-01)

- [x] **Z0 SUPERSEDES Z1-Z5.** Testing all three implementable orders showed  **CLOSED 2026-08-01: delivered — VERDICT-2026-07-06-v3-ADDENDUM.md, logged as protocol #3a.**
  **every one is negative on both instruments**, while only the engine's
  assumed fill is positive:
  sealed **+0.080 / +0.186** · limit-after-close **-0.049 / -0.007** ·
  market-at-close **-0.076 / -0.012** · stop-armed-at-breakout
  **-0.119 / -0.036**.
  At the failure close price is INSIDE the range, so the boundary is a price
  that cannot be obtained: a resting stop fills earlier (60.3% of armed fills
  precede any failure close, losing -0.277R), a market order takes the worse
  close, a limit enters late. **The engine books a boundary fill while
  conditioning on a close that had not happened when price was there.**
- [x] **Z0.1 DONE 2026-08-01** — dated ADDENDUM to VERDICT-2026-07-06-v3** — never an edit; the
  verdicts are append-only. State that the +0.1R rests on an entry price no
  order can achieve, and that the finding is most likely an artifact.
- [x] **Z0.2 DONE 2026-08-01 — stood down operationally, not just on
  paper.** All four AWS schedules confirmed DISABLED; both launchd agents
  (`com.occams.paper-morning`, `com.occams.paper-evening`) unloaded — zero
  occams jobs now loaded. The record had said PAUSED for hours while the
  machinery was still armed, which is the gap between a decision and a
  change. Original scope: The campaign is validating a non-edge.
  Zero completed trades, so nothing is lost by stopping; continuing would
  spend 60-90 days measuring implementation drift against a model that
  cannot be implemented.
- [x] **Z0.3 HOLD H4 / R2.** Order flow was to improve the fade. There may  **CLOSED 2026-08-01: delivered — H4 superseded by H5; no further R2 spend.**
  be nothing to improve. The remaining ~$44 of R2.1 headroom should not be
  spent until Z0.1 is settled. **The data already bought is not wasted** —
  it becomes the input to whatever replaces the fade, and it is the one
  genuinely new information axis we hold.
- [x] **Z0.4 DONE 2026-08-01 — ORB is CLEAN.** 6,774 armed orders across
  3,482 instrument-days: **zero unplaceable, zero fill disagreements.** ORB
  arms its stops OUTSIDE the opening range while price is still inside it,
  so the order is on the correct side when placed and the fill is *produced*
  by it rather than assumed alongside it. The engine's gap handling also
  checks out — `max(level, open) + slippage` is exactly what a real stop
  produces, matching the gate on all 5,289 fills. **Verdicts #1 and #2 are
  cleared of this defect; the problem is specific to the fade, not systemic
  across the sealed record.** Original scope:
- [x] ~~Z0.4~~ re-check the OTHER sealed verdicts for the same defect. ORB
  (protocols #1/#2) used daily-ATR and range-height stops; whether their
  entries are obtainable has never been asked. Verdict #1 was already voided
  for an instrument defect — this is the same class.
- [x] **Z0.5 SUBSUMED BY E1** — entry-obtainability gate to the harness** so no future
  protocol can be sealed on a fill no order can produce. This is the durable
  fix, and it is what the positive control never tested for.

## ~~SUPERSEDED by Z0~~ — protocol #4b. CLOSED: no entry rule recovers
the number, so amending the entry is moot. Left for the record only.

- [x] ~~Z1~~ **absorbed into Z0** — the live campaign is running a variant with NO EDGE.** X1 showed
  the sealed +0.1R depends on being filled **at** the boundary as price
  crosses back through it, which needs an order already RESTING there — a
  stop armed during the breakout, while price is outside the range and the
  boundary is a valid stop. Protocol **#4a placed a LIMIT after the failure
  close instead**. That fills 95% of the time, so it is not a missed-trade
  problem, it is a TIMING problem: **MES +0.080R -> -0.049R, MNQ +0.186R ->
  -0.007R.** The entire edge.
- [x] ~~Z2~~ **moot**: entry reverts to a stop **armed at the
  breakout**, at the boundary. Dated, logged in PROTOCOLS.md, made while
  the campaign still has ZERO completed trades — which is the only thing
  that makes it legitimate, exactly as #4a was.
- [x] ~~Z3~~ **moot** — the card must fire at the BREAKOUT, not the failure close.**
  This is the operational reason #4a was chosen and it has to be solved
  rather than avoided: the poller already tracks the breakout, so it can
  emit an ARM card then and a CONFIRM card on the failure close.
- [x] ~~Z4~~ **moot** — open question for the amendment**: an armed stop can fill on a
  dip back through the boundary that never produces a failure close. The
  sealed engine requires the close. Decide and pre-register how that day is
  treated — do NOT leave it to be resolved after the first one happens.
- [x] ~~Z5~~ **moot** — Pine v2.0 + poller + cards** all follow the amendment, with the
  wording pinned by `tests/test_cards.py` as before.

## Track D — The durable research archive (defined 2026-08-01, build not started)

**Why separate.** The campaign bucket is the wrong home for two reasons that
are demonstrable, not stylistic: it carries a **90-day noncurrent-version
expiry** (an archive that deletes its own history is not an archive), and it
belongs to the `occams-campaign` stack, so **`sam delete` destroys it**. The
archive must outlive the thing that produced it.

**A result you cannot reproduce in three years is not evidence.** That is the
whole design brief.

### D0 — The rules (agree these BEFORE any bucket exists)

- [x] **D0.1 Operational state is NOT archived in place.** The campaign  **CLOSED: agreed and implemented — operational state is exported, never relocated.**
  bucket's `state/paper_state.json` and `logs/offset.txt` are the running
  system's working memory, read and written every 5 minutes. **Moving them
  breaks the live campaign.** The rule is *export a copy, never relocate*:
  operational state stays where it is; immutable evidence is exported to the
  archive. Anything else is a migration that takes the poller down.
- [x] **D0.2 `raw/` is write-once.** Vendor data is stored byte-identical to  **CLOSED: agreed and implemented — bucket policy denies deletes on raw/.**
  what was purchased, never overwritten, never deleted. Deletion denied by
  bucket policy rather than by convention. **Not** S3 Object Lock in
  compliance mode: if something we uploaded ever turned out to carry the
  venue name, compliance mode would make it *undeletable*, which converts a
  privacy slip into a permanent one. A revocable deny is the right strength.
- [x] **D0.3 The register is append-only.** A hypothesis or experiment record  **CLOSED: agreed and implemented — register is append-only, corrections use supersedes.**
  is written once. Corrections append a NEW record with `supersedes`; nothing
  is ever edited. A register that can be rewritten proves nothing.
- [x] **D0.4 No artifact without provenance.** Every object has a manifest  **CLOSED: agreed and implemented — every manifest row carries engine_sha.**
  row: sha256, created_at, source, cost_usd, **`engine_sha` (the git commit
  that produced it)** and the tool version. Without the commit pinned you
  cannot later tell which engine produced a number — the X1 lesson, made
  permanent.
- [x] **D0.5 The privacy and charset scans run on EVERY upload**, exactly as  **CLOSED: agreed and implemented — privacy+charset guards run on every upload.**
  `check_artifact.py` gates the Lambda build. Durable storage gets the same
  guard tracked files get. Upload refuses on any hit; no override flag.
- [x] **D0.6 Licence posture.** `raw/` is OUR licensed copy in a private  **-> now working-list item A1.**
  bucket we control — internal use, not redistribution, and therefore a
  different act from the `data/` gitignore rule. `[needs-user]` **Confirm
  against the Databento terms before the first raw upload.** Assume nothing.
- [x] **D0.7 Never public, ever.** All four public-access blocks on, plus a  **CLOSED: agreed and implemented — all four public blocks on, non-TLS denied.**
  bucket policy denying any principal outside this account and denying
  non-TLS transport.

### D1 — The stack

- [x] **D1.1 DONE** — separate stack `occams-research` (`occams-research`), not a
  resource in `occams-campaign`. Decoupled so the campaign teardown, or the
  wider AWS cleanup project, can never reach it.
- [x] **D1.2 DONE** — bucket `occams-research-<account-id>`: versioned, AES256, `DeletionPolicy: Retain` **and**
  `UpdateReplacePolicy: Retain`, all four public-access blocks, tagged
  `project=occams`. **No expiry lifecycle rule at all** — the deliberate
  difference from the campaign bucket.
- [x] **D1.3 DONE** — storage classes: Intelligent-Tiering on `raw/` (written once,
  read rarely); Standard on `derived/` and the register.
- [x] **D1.4 DONE** — cost guard: archive counts against the same `project=occams`
  budget. 479 MB today is ~$0.01/mo; 20 GB of order-flow depth would be
  ~$0.46/mo. Re-forecast in SPEND.md before any depth purchase, not after.

### D2 — Access policies

- [x] **D2.1 DONE (policy v3)** — extended the deploy policy. `occams-deploy` is currently scoped
  to `occams-campaign-*` and the SAM bucket, so it **cannot reach an
  `occams-research-*` bucket at all.** Add it explicitly — and verify with
  `simulate-principal-policy` **using `--resource-owner`**, since omitting it
  reports a false `implicitDeny` for S3 (learned 2026-07-31).
- [x] **D2.2 DONE** — deny deletes on the immutable prefixes** — `raw/*`,
  `hypotheses/*`, `experiments/*`, `provenance/*` — in the bucket policy.
- [x] **D2.3 DONE** — the campaign Lambda gets no access for now. Separation of
  concerns: the archive is written by local tooling. Revisit only when a job
  genuinely needs to write evidence directly.
- [x] **D2.4 DONE, live creds** — proved the negatives:, with live credentials, not simulation:
  deleting from `raw/` fails; a principal outside the account fails; plain
  HTTP fails.

### D3 — Layout and schema

- [x] **D3.1 DONE** — prefixes: `raw/` · `derived/` · `hypotheses/` ·
  `experiments/` · `artifacts/` · `provenance/`.
- [x] **D3.2 DONE** — register schema (R0.2): id, stated_at, falsifiable statement,
  **mechanism written before the result**, information_axis,
  search_space_size, alpha_allocated, prereg_sha, status, outcome,
  effect_size, ci_low, ci_high, decision, supersedes, engine_sha.
- [x] **D3.3 DONE** — experiment schema: config, folds, controls_passed, metrics,
  artifacts[], spend_usd, engine_sha, started_at, duration_s.
- [x] **D3.4 DONE** — provenance manifest: one append-only JSONL over every object.

### D4 — Tooling

- [x] **D4.1 DONE** — `occams/archive.py::put` — sha256, privacy+charset scan,
  manifest append, then upload. Refuses rather than warns.
- [x] **D4.2 DONE** — `occams/archive.py::get` — fetch and **verify sha256 against
  the manifest**. A download that does not verify is not a restore.
- [x] **D4.3 Parquet conversion** for `derived/`: 10-20x smaller than our  **-> now working-list item B1.**
  CSVs and columnar. Partition by instrument/year.
- [x] **D4.4 DuckDB query helper** reading Parquet directly from S3 — no  **-> now working-list item B1.**
  Glue, no Athena, no catalog to maintain. Same razor as the no-database
  decision (B7.3). Athena only if a real query pattern ever demands it.

### D5 — Export the campaign's evidence (NOT a migration)

- [x] **D5.1 DONE** — one-off export of the campaign bucket's `logs/*.jsonl` day
  records to `experiments/campaign/`. **The live `state/` and `offset.txt`
  stay exactly where they are** (D0.1).
- [x] **D5.2 Recurring export** from the evening job: each reconciled day  **-> now working-list item A4.**
  written once to the archive as immutable evidence.
- [x] **D5.3 Verify** the exported copy matches the source by sha256.  **-> now working-list item A4.**

### D6 — Backfill everything to date

- [x] **D6.1 DONE (19 docs)** — sealed governance: PREREG.md + `PREREG.sealed`, PAPER-PREREG,
  AMENDMENT-4a, PROTOCOLS.md, all three verdicts, SPEND.md.
- [x] **D6.2 Purchased data:** MES/MNQ csv + `.dbn` + definitions + the B0.5  **-> now working-list item B3.**
  ndjson caches, each with vendor, date, cost and sha256. **Gated on D0.6.**
- [~] **D6.3 H-RECLAIM + H-STOPWIDTH DONE, others outstanding** — experiments run but never persisted — re-run and
  capture, because right now they exist only in a chat transcript:
  the B0.5 feed validation (12/12 tick match), the B0.1 latency table, the
  MAE/MFE excursion study (7 setups), the stop-width gradient (V0/V2a-d),
  and **the reclaim test over 3,328 setups** (the one that killed the
  hypothesis: -0.26R vs -0.05R). Each gets a register entry stating its
  mechanism and outcome.
- [x] **D6.4 DONE (14 figures)** — artifacts: the 14 autoresearch figures + the series banner.
- [x] **D6.5 DONE** — live campaign record to date: every card, ack, skip and
  defect, including the three setups lost to the STOP/LIMIT defect.

### D8 — S3 as the single home for data (user request 2026-08-01)

- [x] **D8.1 S3 authoritative, local disposable.** The goal is not "never  **-> now working-list item B2.**
  on the machine" — analysis has to read the bytes from somewhere, and
  streaming 1 GB from S3 per run is slow and pointless. The goal is that
  **the local copy is a CACHE that can be deleted at any moment and
  re-fetched**, and that no artifact exists only on the laptop. Practical
  test: `rm -rf data/` must cost time, never evidence.
- [x] **D8.2 This makes D0.6 BLOCKING, not optional.** While local was  **-> now working-list item B2.**
  authoritative, the licence question only governed a convenience copy. If
  S3 becomes the only home, the vendor terms have to permit it before the
  local originals are deleted. **Do not delete anything local until D0.6
  is answered.**
- [x] **D8.3 `archive_pull`** — fetch-on-demand into `data/` by manifest  **-> now working-list item B2.**
  key, verifying sha256, so a wiped machine rebuilds its working set with
  one command.
- [x] **D8.4 Store compressed, in one form.** Order-flow tick data is 8.9x  **-> now working-list item B2.**
  smaller gzipped (6.3 GB -> 711 MB measured). Upload the compressed form
  only; the archive should not hold two encodings of the same bytes.
- [x] **D8.5 Cost re-forecast before upload.** ~1.5 GB after the R2.1  **-> now working-list item B2.**
  purchase completes is ~$0.03/month on Intelligent-Tiering — trivial, but
  it belongs in SPEND.md before it lands, not after.
- [x] **D8.6 Then, and only then, prune local** to a cache directory with  **-> now working-list item B2.**
  a documented "safe to delete" note.

### D7 — Verify the archive actually works

- [x] **D7.1 DONE** — restore test: pull a raw file, verify sha256, load it, and
  reproduce a known number (the B0.5 12/12 match is the natural target).
- [x] **D7.2 DONE** — guard test: attempt an upload carrying a planted forbidden
  term and confirm it is refused. **A guard never shown to fail proves
  nothing** — the charset guard earned its place this way.
- [x] **D7.3 Query test:** DuckDB round-trip over Parquet from S3.  **-> now working-list item B1.**
- [x] **D7.4 Runbook section** in the vault: where things live, how to put,  **-> now working-list item A3.**
  how to restore, how to prove an artifact is unmodified.

## Track 2 — The instrument: campaign runner + new symbols ($0 + capped data)

- [x] T2.1 **Campaign runner**: (family × symbol) queue → feasibility  **-> now working-list item D4.**
  screen ($0, auto) → dev-fold screen → PREREG auto-draft → **human
  seal, never automated** → verdict → ledger entry. Parallelism via
  multiprocessing only if measured runtime demands it (current verdict
  = 30s: it does not, yet).
- [x] T2.2 **Multiplicity ledger live** (docs/PROTOCOLS.md): every  **-> now working-list item D4.**
  sealed protocol logged (date, hash, family, symbol, outcome); any GO
  is judged against how many attempts produced it.
- [x] T2.3 **Spend controls live** (docs/SPEND.md): experiment budget  **-> now working-list item D4.**
  cap **$150** (user-adjustable), quote-before-buy (already in
  fetch_data.py), per-purchase user approval, running ledger.
- [x] T2.4 **Symbol expansion #1 — MGC + MCL** (micro gold, micro  **-> now working-list item D4.**
  crude; chosen over M2K/MYM which are equity-correlated with what we
  already measured): per-symbol sessions, costs, calendars (EIA/OPEC
  for crude; metals events), definition assertions; ~$10–30 data on
  approval. Fade-on-{MGC,MCL} runs as a RESEARCH protocol — the GO bar
  stays the frontier; the ex-ante case ("opening dynamics on
  less-arbitraged contracts may exceed +0.25R") is allowed to die at
  the dev screen.
- [x] T2.5 **Hypothesis intake template + committee**: no grid without  **-> now working-list item D4.**
  a written ex-ante expectancy argument + feasibility placement. New
  families enter here or not at all. **Design decision (2026-07-11,
  D-005)**: the intake stress-test borrows the TradingAgents bull/bear
  DEBATE PATTERN — prompts/roles only, implemented thin and native
  (~100 lines on our existing tooling); no LangGraph, no fork, no code
  inheritance. LLMs stay in the research loop, where the series'
  measurements put them.

## Track 3 — Publication (build now, fire later — gate ≈ paper-campaign end)

- [x] T3.1 **Pre-publish audit tool**: scan EVERY commit message and  **-> now working-list item D2.**
  blob in full history against `.privacy-terms`; verify licensed data
  and `*.local.md` excluded. (Full-history auditable seals are the
  differentiator, so the audit must be airtight.)
- [x] T3.2 **$0 quickstart**: synthetic-world demo (positive control +  **-> now working-list item D2.**
  dead world) runnable without any data purchase; public README draft
  led by the essay, not the API.
- [x] T3.3 **Bring-your-own-rules config**: ChallengeConfig + gates  **-> now working-list item D2.**
  from a user-editable file so others encode THEIR firm's geometry —
  the "prop-trading test lab" pitch.
- [x] T3.4 Plots: feasibility-frontier heatmap · fold-expectancy chart  **-> now working-list item D2.**
  · fuel-gauge sample.
- [x] T3.4b Essay contrast section: cite TradingAgents (Apache-2.0,  **-> now working-list item D2.**
  92k stars) as the canonical LLM-in-the-execution-loop framework —
  "agent framework vs $32 sealed-protocol measurement"; contamination
  argument (LLM backtests inside training windows are void; prospective
  is the only honest test) written from D-005.
- [x] T3.5 `[needs-user]` LICENSE choice + essay venue + **the  **-> now working-list item D2.**
  publication decision itself** — gated on paper-campaign resolution
  (~3 months): methodology + verdicts publish always; whether exact
  fade parameters ship or stay generalized resolves itself once the
  paper data exists (the only real IP question).
- [x] T3.6 Publish = new public remote, full audited history, **user  **-> now working-list item D2.**
  pushes** (the no-remote rule stands until T3.1 passes AND the user
  says push).

## Track 4 — Automation backlog: shadow logger + AWS lift (PARKED 2026-07-29)

**Status: PARKED — revisit when the user (a) provides AWS auth and (b)
decides the TV Pro subscription (~$14/mo → recurring SPEND.md entries).**
Design decided now so the revisit is an execution session, not a debate:
**fully headless was REJECTED** — Pine-simulated fills would turn the
sealed human-parity question into a vacuous model-vs-model comparison
(zero drift by construction, kill thresholds never fire). The approved
shape is the **shadow logger**: a headless Pine replication as an
ADDITIVE second stream; the human stream remains protocol #4's sealed
measurement. Bonus value: an independent implementation of the sealed
cell is a continuous cross-implementation audit (the defect class that
voided verdict #1) plus an effortless prospective OOS record.

> **A-SERIES SUPERSEDED 2026-08-01.** A1-A5 were designed around
> TradingView webhooks. That plan died when TV Basic proved to have **zero
> indicator alerts and no webhooks**, and Workstream B replaced it.
> A1 -> done as B1/B3. A5 -> B5.2. **A2/A3 are obsolete**: they needed TV
> Pro (~$170/yr, rejected) to emit webhooks we no longer need.
>
> **A4's purpose survives, and is already met at $0.** The point of the
> shadow stream was a continuous cross-implementation audit — the defect
> class that voided verdict #1. `occams/poller.py` is exactly that: a
> second, independent implementation of the sealed cell, computed from a
> different data source, with `test_poller_sizing_equals_the_sealed_engine`
> asserting it agrees with `fade.py`. No TV Pro, no webhook receiver, no
> shared secret to leak.

- [x] ~~A1~~ **DELIVERED as Workstream B** — AWS foundation (Rung 2, ~$0, FitnessCore SAM pattern).**
  EventBridge schedules (13:30/22:30 Europe/London equivalents in UTC
  with DST handled) → Lambda running paper_morning/paper_evening;
  state/offset/logs → S3; Telegram token via SSM Parameter Store
  (SecureString), never in the repo; idempotent day-replace preserved.
  Retires the laptop-courier fragility (wake-race class) permanently.
- [x] ~~A2~~ **OBSOLETE — webhook receiver.** API Gateway + Lambda; TV webhooks are
  unsigned → shared-secret token required in payload, reject without it;
  parsed Pine events append to the SHADOW ledger (separate S3 stream —
  never writes the sealed human stream).
- [x] ~~A3~~ **OBSOLETE (needs TV Pro) — Pine strategy replication** of the sealed cell (k=0.2,
  unfiltered, $175 true-risk sizing) with `alert_message` JSON on
  range/setup/entry/stop/target/eod events → webhooks. Requires TV Pro.
  Caveat recorded: TV strategy fills are intrabar approximations at
  1-min (bar magnifier = Premium) — fine for a cross-check stream,
  another reason it can never replace the human stream.
- [x] ~~A4~~ **MET BY THE POLLER — three-way parity reporting.** Evening debrief gains a clearly
  labeled shadow section: our model vs Pine vs human fills. SEAL GUARD:
  kill thresholds compute from the HUMAN stream only (protocol #4 §5);
  shadow divergence alerts as an implementation-audit warning instead.
- [x] ~~A5~~ **= B5.2 — cutover.** One week launchd+AWS parallel run → retire
  launchd; runbook note in vault. SPEND.md gains the TV Pro recurring
  line at subscribe time.
- Standing rejections (do not re-litigate): fully-headless protocol #4
  (voids the question — a conscious RE-SCOPE to a new forward-shadow
  protocol is the only honest headless path, accepting no execution
  evidence for any future live decision); automated order placement
  (never).

---

# TWO WORKSTREAMS (split 2026-07-30)

**A — LOCAL (running now).** Protocol #4 executes on the laptop + phone:
launchd jobs, Telegram, the Pine chart aid, TradingView Paper for fills.
Keep running, learning, improving. Small fixes land here immediately.
Everything above in this file that is not marked Workstream B belongs to A.

**B — AWS (the long-term platform).** Same engine, same seals, different
trigger: the laptop leaves the critical path and TradingView leaves the
SIGNAL path entirely (Basic tier = 0 indicator alerts). TV remains only
the paper EXECUTION venue until live, when a broker feed replaces
Databento and the broker screen replaces TV Paper.

Workstream A is never blocked by B. B is cut over only after a clean
shadow week (B5.1).

---

# WORKSTREAM B — AWS build (level-400 backlog)

## Hard constraints (inherited; violating any one voids the campaign)

- **B-C1 Delay parity.** The poller must never read bars fresher than
  the execution venue's own delay. Deciding on newer information than
  the venue fills at would flatter every fill and void the parity
  measurement (PAPER-PREREG §3). Enforced in code (B2.2), not by
  convention. The constraint dissolves at live, when feed and execution
  are both real-time.
- **B-C2 Human executes.** No order routing, ever. Lambda emits cards;
  a human places every order and logs every fill.
- **B-C3** Kill thresholds compute from the HUMAN fill stream only.
- **B-C4** Secrets in SSM SecureString. Never in the repo, never in
  plaintext env vars, never in logs.
- **B-C5** The venue is never named in code, IaC, resource names, tags,
  or logs.
- **B-C6** Hard budget alarm; every metered data call counted and
  reconciled into SPEND.md.

## B0 — Gating spikes (each can reshape or kill the design; do first)

- [x] B0.1 **Databento intraday-availability spike** — **DONE
  2026-07-31, GATE FIRED** (spend $0.000146, not the ~$1 budgeted).
  The entitlement is a rolling **8-hour wall**: true lag 480.2 min,
  refused at the quote stage above it. The 09:45 ET range would not be
  retrievable until ≈17:45 ET. **The poller (B2.3, B3.2) cannot be built
  on this data.** Everything not on the signal path is unaffected.
  Findings + costed options: `docs/AWS-RECON.md`.
- [x] B0.2 **Client vs REST** — **DONE, DECIDED: REST + stdlib.** The
  whole spike ran on `urllib` + `json`; a JSON-encoded `get_range`
  returned 30 bars in 6 KB. The Lambda ships **no `databento` client**,
  hence no numpy/pandas/zstandard.
- [x] B0.3 **Runtime shape** — **RE-OPENED then RESOLVED 2026-07-31** (an earlier note
  in this file wrongly retired it; the import graph says otherwise).
  **numpy is genuinely required** — `fade.py` uses `argmax`/`default_rng`
  at runtime; ~15 MB on arm64, no layer needed. **pandas is on the path
  but annotation-only**: `sim.py`, `harness.py` and `strategy.py` import
  it at module level while *every* use is a type annotation under
  `from __future__ import annotations`, so nothing evaluates it.
  Options: (a) bundle both ~60-80 MB; (b) `AWSSDKPandas-Python312` layer;
  **Chose (c): the three imports now sit under `if TYPE_CHECKING:`** —
  free, no behaviour change, not a B1.4 fork (same modules, one deferred
  import). Not optional in the end: the first real `sam build` showed the
  Lambda could not import its own engine without it. 173 tests pass and
  the engine imports with pandas *blocked* via `sys.meta_path`; a
  regression test pins it, since a stray module-level import would pass
  locally and break every deploy.
- [x] B0.5 **Validate Yahoo bars against CME ground truth** — **DONE
  2026-07-31, GATE PASSED. 12/12 sessions matched to the tick** (MES+MNQ,
  6 trading days, 15 bars each side, zero disagreement). MES 2026-07-30
  read 7421.50/7399.75 — exactly what was transcribed off the chart into
  Telegram that morning, so CME, Yahoo and TradingView agree. **The
  poller is rebuilt against Yahoo; B2.1-B2.3 and B3.2 are UNBLOCKED.**
  Delay parity now holds *because the source is 10.0 min delayed*, not
  because code throttles a fresher feed — a stronger guarantee, since no
  fresh data exists to leak through a bug. Billed $0.1875 against ~$0.10
  approved (no cache; re-runs re-downloaded) — logged as a process defect
  in SPEND.md and fixed. Untested: roll boundaries (none fell in the
  window) — watch during the shadow week (B5.1).

  <details><summary>original task text</summary>
  Yahoo's `MES=F`/`MNQ=F` measured **exactly 10.0 min** delayed — the
  TradingView free-tier delay, so B-C1 parity would hold *by
  construction* rather than by throttling a real-time feed, at $0.
  (Databento live is **rejected**: ~$36.50/mo non-pro ≈ $438/yr, ~3× the
  entire lab cap, to automate a 15-min/day task on a +0.1R edge.)
  Buy a ~$0.10 top-up of the last 7 sessions (quote first; inside
  PAPER-PREREG §7) and compare per session: **09:30–09:45 range high/low
  to the tick** (the number that must match), bar count/gaps, timestamp
  convention, roll behaviour. **GATE — PASS:** rebuild the poller against
  Yahoo. **FAIL:** abandon the poller; B ships schedule-only and
  intraday signals stay manual on the chart's 3 free price alerts (which
  PAPER-PREREG §4 step 2 already assumes). Note the "yfinance is DNS
  blocked locally" blocker is **stale** — it answered first try.
  </details>
- [~] B0.4 **Account + region + auth** — **read-only portion DONE
  2026-07-31.** `aws`+`sam` installed, credentials resolve: account
  `<account-id>`, IAM user `Tromso-Aura-Hunter-dev` (legacy, unrelated
  project), region **`eu-north-1`** (not the assumed `eu-west-2`).
  Baseline **~$10.51/mo** (Jul; May $11.71, Jun $10.81) — so a raw $5
  alarm would fire on day one and the `project=occams` tag filter is
  **load-bearing, not tidiness**. ~$8.60/mo ex-tax looks recoverable by
  the separate teardown brief. `[needs-user]` **remaining:** confirm
  region choice, and whether to keep the legacy IAM identity or create a
  scoped deploy user. Detail: `docs/AWS-RECON.md`.
  Standing requirement from the original B0.4, now confirmed necessary:
  **tag every resource this stack creates** (`project=occams`) so its
  budget filters on the tag, not the account. Teardown of the two retired
  projects is a SEPARATE project —
  `~/Documents/maverick-hq/10 - Projects/aws-account-cleanup.md` —
  deliberately NOT a dependency: destructive work must not share a
  session with additive work.

## Sequencing after the B0.1 gate (2026-07-31)

**Build now — none of it touches intraday market data:** B1 → B3.1
morning card (sealed local calendar) → B3.3 evening debrief (parity from
the **human** fill stream, B-C3) → B3.4 → B4 → B7. This is most of the
workstream and most of its value.

**Unblocked same day by B0.5:** B2.1–B2.3 and B3.2 — built against
Yahoo's 10-minute-delayed tape, validated 12/12 to the tick.

**Decided by the gate:** deploy identity = a **new scoped IAM user**
(user decision 2026-07-31), NOT the legacy `Tromso-Aura-Hunter-dev`.
Reusing it would couple this stack to the teardown project, which plans
to delete unused identities — exactly the dependency both briefs were
written to avoid. Region: inherit `eu-north-1` unless changed before
first deploy (reversible until then; latency is irrelevant for three
scheduled jobs).

## B1 — Foundations

- [x] B1.1 **SAM skeleton** — **DEPLOYED 2026-07-31** to `eu-north-1`,
  stack `occams-campaign`. `aws/template.yaml`,
  `aws/handler.py`, `aws/samconfig.toml`, 14 tests. One arm64 Python 3.12
  function with `morning|poll|evening|command` dispatch; unknown jobs
  raise rather than guess, so a mis-scheduled rule fails visibly. The
  handler logs an **engine fingerprint** (k_stop/risk/cap/tick) so a
  deploy running anything but the sealed cell is visible in CloudWatch.
  **Artifact packaging is an ALLOW-LIST** (`build-CampaignFunction` in
  the Makefile + `scripts/check_artifact.py`): SAM's default Python
  builder swept the whole repo into a **533 MB** artifact containing
  licensed bars, the API key, the Telegram token and the **venue name**
  (B-C5), and `.samignore` does not bind that builder. Now **48.6 MB and
  verified clean**, with the guard proven to fail on each planted
  violation. Note `occams.privacy` scans *tracked* files and so is
  structurally blind to exactly these git-ignored ones — hence a separate
  artifact guard.
- [x] B1.2 **Secrets** — **DONE 2026-07-31.** `/occams/telegram/token`
  and `/occams/telegram/chat` are SSM SecureStrings; the Lambda reads
  both (verified in a live invoke: lengths 46 and 10, values never
  logged). `scripts/push_secrets.py` is the one-way `.env` → SSM bridge,
  via **boto3** so a secret is never an argv element (visible in the
  process table) nor a temp file. Re-run it after rotating a token.
  `/occams/databento/key` is **not** pushed — B0.5 chose Yahoo for the
  signal path, so the Lambda has no reason to hold that key.
  Two bugs this surfaced, both worth keeping in mind:
  (a) `ssm:DescribeParameters` is a LIST operation with no resource-level
  control, so scoping it to `/occams/*` denied it outright — policy v2
  allows it on `*` while `GetParameter` stays path-scoped;
  (b) the Makefile allow-list copied `handler.py` and `__init__.py` **by
  name**, so `aws/secrets.py` was silently never shipped. Now `aws/*.py`.
  The health check caught it only because it reports the real error — its
  first version said "not running in Lambda", which was a comforting lie
  that hid a packaging fault.
- [~] B1.3 **State bucket** — **CREATED** (`occams-campaign-statebucket-*`):
  private (all four public-access blocks on), versioned, AES256, 90-day
  noncurrent expiry, tagged `project=occams`. The object contract below
  lands with B3; first write is the check that the S3 grant works.
  Original spec: private, versioned, lifecycle-expired.
  Objects: `state/paper_state.json`, `logs/paper_logs.jsonl`,
  `logs/offset.txt`. Single-writer by construction (schedules never
  overlap) plus ETag conditional write on the state object.
- [x] B1.4 **DONE, verified live** — engine fingerprint returned from Lambda reads k_stop 0.2 / risk 175 / cap 30 / tick 0.25. Package the engine unchanged: `occams/` ships as-is
  (sim, rules, fade, paper, calendar, instruments). **No fork** — the
  Lambda imports the very modules the local runs and the sealed
  verdicts used. Any divergence between them is a defect, not a variant.

## B2 — The signal path  ✅ UNBLOCKED (B0.5 passed) — build against Yahoo

- [x] B2.1 **DONE** — `occams/feed.py`, a **DataSource port** with adapters:
  **`YahooDelayed` (paper — the B0.5-validated source)**,
  `DatabentoHistorical` (backfill/audit only, 8h wall) and `BrokerFeed`
  (live, stub). Returns 1-minute bars for a symbol/day. TDD against
  recorded fixtures; no network in tests. Fixtures come from the B0.5
  cache, so tests assert against bars already proven tick-identical
  to CME.
- [x] B2.2 **DONE** — **delay-matching made executable (B-C1).** A
  `venue_delay_minutes` config; the feed refuses to return bars newer
  than `now - delay`, and every card states the bar timestamp it was
  computed from. TDD: assert a fresher bar can never reach the engine.
- [x] B2.3 **DONE** — **session poller**: build the day's range at 09:45 ET, then
  each poll re-runs the sealed fade logic over the day's bars so far.
  Emits exactly one `/range` card and at most one setup-or-stand-aside
  card per instrument per day (idempotent via state).
- [x] B2.4 **DONE 2026-08-01** — **card formatter shared.**
  `occams/cards.py` is the single Python source; the poller and the jobs
  both route through it. Pine cannot import Python, so its wording is
  **pinned by test**: `tests/test_cards.py` asserts the `.pine` file still
  contains every shared phrase, and a separate test asserts "BUY STOP" and
  "SELL STOP" never reappear. Change a phrase in one place without the
  other and the suite fails. Original spec:
- [x] ~~B2.4~~ **Card formatter shared with Workstream A** — one source of
  truth for the text the human types, so local and AWS cannot drift.

## B3 — The three jobs

- [x] B3.1 **DONE** — **morning card** — EventBridge **Scheduler** with a
  `America/New_York` cron. This retires the local UTC-offset hack:
  Scheduler handles DST natively, so the twice-yearly mismatch weeks
  stop being a hazard.
- [x] B3.2 **Poller** — **DEPLOYED 2026-07-31, schedule DISABLED** pending
  the B5.1 shadow check. EventBridge **Scheduler** with a native
  `America/New_York` cron (`0/5 9-16 MON-FRI`), so DST needs no handling.
  Verified live: the Lambda produced MES `long 3x @7480.25 stop 7470.75
  target 7515.25` and MNQ `long 1x @28415.0` — identical to the chart, the
  local computation and the replay. Four consecutive invokes added no new
  `sent` tags, so repeats are silent. Enable with
  `aws scheduler update-schedule --name occams-poll --state ENABLED`.
- [x] B3.3 **DONE** — **evening debrief** — pull Telegram updates, compute parity
  from the HUMAN stream, update state, kill check, send. **Vault stays
  local**: add `scripts/pull_debriefs.py` to sync S3 → Obsidian on
  demand (an EC2-free, credential-free read).
- [~] B3.4 **Idempotency**: re-running any job for a day REPLACES that  **PAUSED — AWS pipeline is built and stood down with protocol #4.**
  day's records — identical contract to the local path.

## B4 — Observability (what makes it trustworthy unattended)

- [x] B4.1 **DONE** — **dead-man's switch** — the top risk is a *silent* poller.
  The evening debrief reports poll count and last-bar age, and says so
  loudly if the morning card never ran.
- [x] B4.2 **DONE** — CloudWatch alarms on Lambda `Errors` and `Throttles`; the
  evening job also self-reports recent error metrics into the debrief,
  so a failure surfaces on the phone rather than in a console nobody
  opens.
- [x] B4.3 **DONE** — structured logs, 30-day retention. Never log secrets or full
  payloads carrying a key.
- [x] B4.4 **DONE** — **AWS Budgets alarm at $5/month** + a metered-call counter in
  state, surfaced in the debrief and reconciled into SPEND.md monthly.

## B5 — Parity, cutover, rollback

> **All four schedules are DEPLOYED but DISABLED** (2026-08-01). Arming an
> unattended job against a live campaign needs the shadow check below, not
> one afternoon's evidence. Enable with:
> `aws scheduler update-schedule --name occams-{poll,command,morning,evening} --state ENABLED --profile occams`

## B5 — Parity, cutover, rollback

- [x] B5.1 **Shadow week** — AWS and launchd run in parallel; compare  **CLOSED 2026-08-01: moot — nothing to shadow while protocol #4 is stood down.**
  the two cards daily. Because the engine is shared, ANY divergence is
  a data or timing bug and blocks cutover.
- [~] B5.2 **PAUSED — Cutover** — disable the launchd agents, keep them
  installed one further week as rollback.
- [x] B5.3 **DONE** — **runbook** in the vault (`90 - Reference/AWS runbook`): redeploy, replay a missed day, roll
  back, where state lives, how to rotate secrets.
- [~] B5.4 **PAUSED** — retire launchd; update CLAUDE.md + this file.

## B6 — Live-readiness (NOT part of the paper campaign)

- [~] B6.1 Implement `BrokerFeed` only if a live decision is ever taken.  **PAUSED — AWS pipeline is built and stood down with protocol #4.**
  The delay-matching constraint dissolves naturally when feed and
  execution are both real-time.
- [~] B6.2 Re-read the compliance posture before any live use: the  **PAUSED — AWS pipeline is built and stood down with protocol #4.**
  human places every order; this system never routes one.

## Cost model (expected)

Lambda ~1,700 invocations/month (free tier 1M) · S3 < $0.10 · SSM free ·
CloudWatch ~$0. **All-in under $1/month**, versus ~$170/yr for a
TradingView tier that would only deliver alerts.

**Revised 2026-07-31 (B0.1).** The old line "Databento ~$0.01/day ≈
$3/yr" assumed intraday access we do not have. Real market-data options
are now: **$0** (Yahoo, 10-min delayed — **validated 12/12 by B0.5**)
or **~$438/yr**
(Databento CME live, non-pro — rejected). Schedule-only jobs need no
market data at all, so the sub-$1/month figure holds for everything
outside the signal path.

## B7 — Interaction model + recaps (user-specified 2026-07-30)

Target workflow: pre-market card -> setup card with buy/stop/target ->
human acknowledges execution -> everything logged -> daily recap ->
on-demand weekly / monthly / since-inception recaps.

**Two protocol notes settled up front:**

- **B7-N1 `/ack` is an acknowledgement, NEVER a veto.** The human
  records execution reality (`placed` / `missed <reason>` /
  `partial <reason>`), not preference. A command that lets a setup be
  declined on judgement turns the sealed mechanical strategy into a
  discretionary one and voids the measurement — the five-day sample
  already showed the best-geometry trade losing and the worst winning,
  so a human veto is provably noise. Missed trades stay in the
  denominator as process defects (PAPER-PREREG §8 forbids counting
  would-have-beens).
- **B7-N2 Levels move from human transcription to engine output.** The
  card is computed from our own data instead of typed off a chart. This
  is a change to PAPER-PREREG §4 and requires a **dated amendment
  (protocol #4a)** logged in PROTOCOLS.md, made BEFORE results
  accumulate — legitimate now (zero trades), not later. The measurement
  (human fills vs model) is unchanged; the amendment only removes
  transcription error from the drift signal.

- [x] B7.1 **Command handler** — **DEPLOYED 2026-07-31, schedule
  DISABLED** with the poller, pending the B5.1 shadow check. Reuses
  `occams.paper.parse_command`, so the local and AWS grammars cannot
  drift. Commands: `/ack`, `/fills`, `/skip`, `/range`, `/setup`,
  `/status`, `/help`. A completed trade replies with a per-trade recap —
  your fills vs the model re-derived from the SAME logged levels, and the
  drift between them. The S3 offset was seeded past today's messages so
  the Lambda cannot replay commands the local evening job still owns; the
  two use separate offsets and separate state, so they do not interfere
  during the shadow period. Offset advances only AFTER the state write and
  replies land — the worst case is a duplicate reply, never a dropped
  command. Original spec follows.
- [x] ~~B7.1~~ **DELIVERED** — command handler — its own 10-minute weekday schedule.
  **Why separate:** Telegram commands are PULLED, not pushed, so a
  `/week` typed at 15:00 would otherwise sit unanswered until the
  evening job. The session poller covers market hours; this covers the
  rest of the day. Commands: `/status` (today so far), `/week`,
  `/month`, `/all`, `/help`. Still inside the Lambda free tier.
- [x] B7.2 **DONE** — **`/ack` grammar + parser** (TDD, extends `occams/paper.py`):
  `placed` | `missed <reason>` | `partial <n> <reason>`, plus the
  existing `/fills`. Unknown input is rejected loudly, never guessed.
- [~] B7.3 **Ledger schema** in S3. **DECIDED: no database.** A  **PAUSED — AWS pipeline is built and stood down with protocol #4.**
  versioned JSON plus an append-only JSONL serves hundreds of days, and
  every recap is an in-memory filter over a few hundred records;
  DynamoDB would add IAM surface, schema decisions and ops for zero
  benefit at this scale. Revisit only if a real query pattern demands
  it — the ledger shape does not change if it does. Per-day record:
  date, per instrument {range, setup or stand-aside reason, card, ack
  state, fills, drift}, plus run-health counters.
- [x] B7.4 **DONE** — **daily recap** (evening job, extends the current debrief):
  today's cards, acks, fills, per-trade drift, running parity, kill
  status, poll-health.
- [x] B7.5 **DONE** — **period recaps** shared by `/week` `/month` `/all`: trades,
  win rate, R-multiples, expectancy per trade, mean and mean-absolute
  drift, stand-aside count, **missed-trade count (the operational drag
  number)**, days elapsed vs the 60-90 day bar, and distance to the
  ≥40-trade evidence threshold. Weekly recap auto-posts Friday evening.
- [~] B7.6 **Honesty guard in every recap**: sample size stated first,  **PAUSED — AWS pipeline is built and stood down with protocol #4.**
  and any expectancy below ~20 trades carries the "early samples lie,
  optimistically" caveat with the measured +0.1R baseline alongside.
  (Live-fire example: the same week read +1.2R after 3 trades, +0.69R
  after 4, +0.35R after 5 — converging on the truth from above.)

---

## SESSION LOG 2026-07-31 — protocol #4a: the card named an impossible order

**The finding.** The Pine card and PAPER-PREREG §4 step 3 both said
"place the entry **stop** at the boundary". That order can never be
placed: a failure close is *by definition* back inside the range, so the
boundary always sits on the far side of it — a buy stop below market or a
sell stop above it. Every day, by construction, not bad luck:

| Day | Break | Failure close | Card said | Boundary |
|---|---|---|---|---|
| 07-29 | DOWN | 7448.00 | BUY STOP @ 7444.25 | below → not a stop |
| 07-30 | UP | 7419.75 | SELL STOP @ 7421.50 | above → not a stop |
| 07-31 | DOWN | 7481.25 | BUY STOP @ 7480.25 | below → not a stop |

It cost **two of the first three setups**. 07-30 was logged as a process
defect without the cause being understood; 07-31 was the same defect,
diagnosed. The engine was never wrong — `fade.py` books
`entry = boundary + sgn × slip` under a "stop-entry fill armed during the
breakout" reading, while the card fires at the failure close. The model
assumed one reading, the instructions described another, and neither was
executable.

**Resolved:** protocol **#4a** (`docs/AMENDMENT-4a.md`, logged in
PROTOCOLS.md) — entry is a **LIMIT at the boundary** from 2026-08-09.
Made at **zero completed trades**, which is what makes it legitimate.
Strategy, cell, sizing, kill thresholds and evidence bar all unchanged.
Known cost, stated in advance: a limit fills only if price returns to the
boundary, so no-fill days are logged `/skip ... no fill - limit not
reached` and counted in the operational-drag denominator, never as wins.

**Second defect, found while fixing the first:** the Pine fill-watcher's
condition was written for stop entries and is **inverted** for limits — it
tested `high >= entry` for a long, which is already true the instant the
setup fires, so it would have reported an immediate fill every day.
Fixed in v1.9 and verified against 07-31's real bars: fill 09:46, stop
09:49, matching the tape.

**07-31 outcome:** setup fired 09:45 (range 7515.25/7480.25, extreme
7477.75, long, 3 contracts), stop hit 09:49, model −$157.50 (−0.90R).
Not executed → process defect, no drift. **Explicitly not banked as a
loss avoided** — the ban on would-have-been wins is worthless if
would-have-been losses are quietly credited as judgement.

**Feed cross-check:** today's range read identically from Yahoo,
Databento and the chart — a third independent agreement after B0.5's
12/12.

---

## SESSION LOG 2026-07-30 — live day 1 + the two-workstream split

Written at session end so a fresh session can resume without this chat.

### Protocol #4 went live and produced real findings ON DAY ONE

- **Trade 1 logged** (MES, 2026-07-30): range 7421.50/7399.75 (height
  21.75), extreme 7446.50 -> SHORT 1x @ 7421.50, stop 7450.85 (place at
  7451.00 — model level is off-tick), target 7399.75. **Geometry 0.73R**
  — risk 29.6pt vs reward 21.75pt, because the breakout ran 25pt past a
  21.75pt range. Taken anyway: sealed protocol, sizing floor didn't
  reject it. Days like this are why measured expectancy is +0.1R.
- **OUTSTANDING (user):** confirm in the TV Trading Panel whether the
  bracket was actually placed. If yes -> `/fills MES entry <actual> 1`
  plus the exit. If it was never placed (plausible on day 1) -> log the
  process defect honestly: `/skip MES process defect - setup fired,
  order not placed`. **Never invent fills** (PAPER-PREREG §8). Then
  re-run `make paper-evening` (idempotent, replaces the day).

### Defects found and fixed live (each a real integrity bug)

| Fix | Why it mattered |
|---|---|
| certifi CA bundle (`515b9ad`) | python.org urllib ships no CA store; Telegram failed CERTIFICATE_VERIFY_FAILED |
| wake-race retry + cross-midnight day targeting (`af130d4`) | launchd fired the missed job at wake but DNS wasn't up; and a post-ET-midnight debrief would have filed the wrong day |
| **off-tick price rejection (`c347114`)** | `/range MES 7421.5 7399.55` parsed happily — .55 can't exist at 0.25 tick. A typo'd level corrupts range/stop/size, so drift would measure TYPING not execution |

### Pine chart aid — v1.0 -> v1.8 (`tools/fade_campaign.pine`)

Logic verified against the sealed engine on **500 real days, 469
setups, 0 mismatches** (re-run after every edit). Highlights: v1.2
per-day plots (extend-right lines stacked every historical range);
v1.4 no multi-line ternaries (Pine treats a 4-space-multiple
continuation as a new block); v1.5 ASCII-only (TradingView mangles
non-ASCII) + box off the legend; v1.6 auto-configures from
`syminfo` so switching MES1!->MNQ1! can never leave a wrong
multiplier; v1.7 entry/stop/target lines, drawn only for SIZED trades;
**v1.8 fill watcher** — prints `<YOUR FILL>` deliberately, never the
model price, because typing the model back would make drift zero by
construction and the measurement worthless.

### TradingView constraint that reshaped Workstream B

**Basic tier = 0 indicator alerts** (webhooks need a paid tier too). So
TV cannot deliver signals at any acceptable price -> Databento takes
the SIGNAL path (~$3/yr at poll cadence), TV keeps only the paper
EXECUTION venue. This DELETED the old webhook-receiver and
Pine-strategy backlog items: no API Gateway, no public endpoint, no
subscription. Simpler than the design it replaced.

### Six-day walkthrough (Wed 22 - Wed 29) — publishable material

Wed 22 −$145 · Thu 23 −$124 · Fri 24 +$420 · Mon 27 −$156 ·
Tue 28 +$282 · Wed 29 stand-aside. **The finding is the convergence:**
+1.2R after 3 trades -> +0.69R after 4 -> **+0.35R after 5**, falling
toward the measured +0.1R FROM ABOVE, win rate landing exactly on 40%.
Also: best-geometry day of the week (3.7R) LOST, worst (2.4R) WON.
Captured in `~/Documents/maverick-hq/autoresearch/05-content-status-
and-open-items.md`; feeds B7.6's mandatory honesty guard.

### Where everything stands

- **Workstream A (local):** running. Next user actions are the day-1
  fills question above, then the daily ritual.
- **Workstream B (AWS):** designed, not started. **B0.1 (Databento
  intraday-latency spike, ~$1, read-only) is the honest first move** —
  it decides whether the poller behind B2/B3/B7 is viable at all.
- **AWS account cleanup:** separate standalone brief at
  `~/Documents/maverick-hq/10 - Projects/aws-account-cleanup.md`.
  Deliberately NOT a dependency.
- **Crucible series:** assets complete (4 notes, 14 figures, banner);
  essays 8/9/Outro unwritten; `crucible-autoresearcher` is the last
  unpublished repo — push `public-release` (a13dd0a) ONLY.