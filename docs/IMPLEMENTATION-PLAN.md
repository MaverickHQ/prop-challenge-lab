# Implementation Plan — occams-trader

Kiro-style spec-driven task list. **Requirements and design live elsewhere**
— this file is *what to build, in order*:

- Requirements & scope: `CLAUDE.md`, `docs/RESEARCH-PROGRAM.md`
- Backlog and blocking decisions: `docs/TASKS.md`
- Architecture: `docs/ARCHITECTURE.md`

> **One authority, not two.** `TASKS.md` is the BACKLOG — what exists and
> why. This file is the EXECUTION ORDER, and task state lives here. Stated
> because this project has already been bitten by a status document that
> stopped being re-checked.

---

# Revision 2026-08-30 — the lab is repointed

**Settled in a grilling session against a six-stage AI-trading-agent
pipeline** (Research → Build → Optimise → Forward Test → Risk → Live Trade).
Eight decisions, each recorded with what it rules out, because a decision
whose alternatives are lost reads later as an assumption.

| # | Decision | Rules out |
|---|---|---|
| 1 | **Alpha is budgeted** | the unbudgeted search the reference pipeline uses |
| 2 | Point at an unexhausted market | more rearrangements of MES/MNQ price |
| 3 | **No crypto.** MGC/MCL → backlog ($19.16) | free-data crypto markets |
| 4 | **Pipeline first, validated on owned data** | building straight onto a new market |
| 5 | It lives in **`occams-trader`** | a third repository |
| 6 | **Two-stage, lockbox-gated; bar corrected by declared search size** | per-config alpha (unusable) and no correction (dishonest) |
| 7 | **Declared indicator space**, registered before the search | free-form idea generation, which cannot be alpha-budgeted |
| 8 | **Terminate at approval; a human places every order** | an autonomous execution agent |

**The user's framing, kept verbatim because it is the design principle:**
*"a higher bar is the point"*, and the deliverable is **trustworthy negatives
faster**.

## What the reference pipeline is, and what we already own

| Reference stage | Here | State |
|---|---|---|
| 1. Research Agent (searches the internet) | — | **replaced by a declared space (decision 7)** |
| 2. Developer AI (builds + backtests) | `strategy.py`, `sim.py`, `harness.py` | exists |
| 3. Optimisation Agent | `search.py` — `GridAxis`, `Sweep`, `sweep()` | exists |
| ◆ GOOD SETUP? | `find_winner()`, `Gates`, the **plateau rule** | exists, stronger |
| 4. Forward Testing | walk-forward folds, lockbox, paper campaign | exists |
| 5. Risk Management | `rules.py`, `payout.py`, `power.py`, `execution.py` | exists, much stronger |
| 6. Live Trading Agent | `cards.py` + a human | **deliberately a person (decision 8)** |

**Stages 2-5 already exist and are built harder than the reference.** What is
missing is the loop that drives them, and the one primitive that makes an
automated loop honest.

## The finding that defines this work

`RESEARCH-PROGRAM.md` §3 declared, as non-negotiable:

> *"The loop must therefore be built with the alpha budget as a first-class,
> decrementing resource, not as a caveat in a footnote."*

**It was never built.** Every module in the sibling autoresearcher was
searched for alpha, multiplicity, Bonferroni, family-wise, multiple
comparison: **zero matches.** Its `budget.py` budgets *dollars* — API spend
with a kill-switch — not statistical alpha.

So the sibling loop, as built, **is** the reference pipeline: an LLM proposer
and a Latin-hypercube sampler searching an 8-field space and keeping winners,
with no multiplicity accounting at all. The only reason it never produced a
false positive is that it found nothing, which is luck rather than a guard.

**Building that ledger is the work.** It is the single thing separating this
lab from a slower copy of a p-hacking machine.

## The bar this sets, stated before it is inconvenient

Under decisions 6 and 7, a search over ~500 declared configurations pushes
the per-test bar from alpha=0.05 to roughly **alpha=0.0001** — an effect around
**1.5× larger** than a single pre-registered test needs. Nine hand-picked
families produced **+0.02 to +0.04R** against a frontier needing **+0.25R**.

**This pipeline is therefore very unlikely to find a winner.** It makes
searching cheap and winning harder. That is the intended trade.

---

## Conventions

- **Gated.** Phase A gates B–F. Phase D gates E: an unvalidated loop pointed
  at real data produces an uninterpretable result, because "found nothing"
  and "cannot find anything" are indistinguishable from outside.
- **Declared before searched.** A correction by `search_space_size` is only
  honest if that number was fixed before results were seen. A space the
  proposer can widen mid-run, or one counted afterwards, makes the
  correction decoration.
- **Dev folds are free; the lockbox is read once, ever.** Not once per
  hypothesis — once.
- **Frozen evidence is never edited.** `scripts/exp_*.py` are archived
  byte-for-byte. Recomputes import them; they do not reformat or retype them.
- **Append, never overwrite.**
- **Commit per phase**, ending each message with:
  `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`
- **Autonomy legend.** `[auto]` = code, tests, owned data, $0, no new egress.
  `[needs-user]` = money, a research judgement, repo settings, publication.

---

## Phase A — the alpha ledger `[auto]` — GATES EVERYTHING

The primitive that does not exist in either repository.

- [ ] **A.1 `occams/alpha.py` — a decrementing family-wise budget.**
  A ledger holding total allocated alpha, each registered search with its
  declared `search_space_size`, and the corrected per-test bar. Šidák rather
  than Bonferroni (less conservative, same guarantee, and the space size is
  known exactly rather than bounded).
  **Verify:** a unit test shows the corrected bar falling as registered
  searches accumulate, and `spend()` refusing once the budget is exhausted.

- [ ] **A.2 Refuse a search whose space was not declared first.**
  `register_search(space_size=, mechanism=, ...)` must precede any
  evaluation, and the ledger must reject a `search_space_size` that
  disagrees with the enumerated space it was given.
  **Verify:** a test proves a search cannot be registered after its results
  exist, and that widening the space mid-run raises rather than re-corrects.

- [ ] **A.3 Wire the ledger into `archive.register_hypothesis`.**
  `search_space_size` is already a field and is currently only *recorded*.
  Make it *applied*: the hypothesis's admissible bar comes from the ledger,
  not from a constant.
  **Verify:** re-scoring an existing registered hypothesis reproduces its
  recorded verdict when the space size is 1.

- [ ] **A.4 Show it on the console.** The alpha gauge currently reports
  consumption against a conventional 0.05 reference. Replace with the real
  ledger: allocated, spent, corrected bar, and remaining.
- [ ] **A.5 Commit:** `A: the alpha budget RESEARCH-PROGRAM promised`

## Phase B — the declared search space `[auto]`

- [ ] **B.1 `occams/indicators.py` (I1).** Moving averages, Bollinger,
  Keltner, and the admissible parameter ranges for each. **Enumerable**: the
  module must expose the exact count of configurations it admits.
  Deferred in 2026-08 with a reason that still holds — *"a choice that does
  not need to exist should not be created"* — so the space is small and
  justified, not everything that could be computed.
- [ ] **B.2 Mechanism map (I3), written before any indicator is tested.**
  For each family, why it should work, stated in advance. A family with no
  mechanism does not enter the space.
- [ ] **B.3 Entry auditors for indicator families (I2).** `AUDITORS` is
  default-deny: an unaudited family cannot be tested at all. Every family in
  B.1 needs one, or it is not admissible.
  **Verify:** `assert_entries_obtainable` raises for a family added to the
  space without an auditor.
- [ ] **B.4 Register the space.** One hypothesis, its mechanism, its exact
  `search_space_size`, its power plan — archived **before** Phase C runs.
- [ ] **B.5 Commit:** `B: the declared indicator space, registered unrun`

## Phase C — the loop `[auto]`

Port from the sibling repo rather than rewriting; it is built and green.

- [ ] **C.1 Port `ConfigMutator` + Latin-hypercube proposer** against the
  Phase B space. `FROZEN_FIELDS` carries over: risk per trade and the daily
  stop are not the agent's to tune.
- [ ] **C.2 Port `KeepDecision` and `MetaLoop`**, with the keep rule reading
  the Phase A corrected bar rather than a fixed threshold.
- [ ] **C.3 Dev/lockbox separation, enforced in code.** The loop may read
  dev folds without limit and must be physically unable to touch the lockbox
  outside a single confirmatory call.
  **Verify:** a test proves a second lockbox read raises.
- [ ] **C.4 `ExperimentStore` → the existing archive.** Do not add a second
  store; every run lands in the register with its `calcs.json`.
- [ ] **C.5 Commit:** `C: the budgeted propose-evaluate-keep loop`

## Phase D — planted-edge validation `[auto]` — GATES PHASE E

The positive control, and this repository's own first principle: *"A harness
that cannot find a planted edge cannot be trusted to report its absence
either."*

- [ ] **D.1 The loop must find a planted edge.** Run against `synth.py`'s
  edge world. It must converge on the planted configuration and clear its
  corrected bar.
- [ ] **D.2 The loop must report nothing on the dead world**, with
  `kick_scale=0` — the correction that made an earlier "no-edge" world a
  real negative control.
- [ ] **D.3 The loop must not beat its own bar by searching harder.** Run
  the dead world with a 10× larger space; the false-positive rate must not
  rise. **This is the test that proves the ledger works** — without it,
  Phase A is a claim.
- [ ] **D.4 Add all three to `make quickstart`.**
- [ ] **D.5 Commit:** `D: the loop finds a planted edge and cannot cheat`

## Phase E — first real run `[auto]`, owned data

- [ ] **E.1 Run the loop on MES/MNQ over the declared space.** Dev folds
  only. Expected outcome, recorded in advance: **nothing clears the
  corrected bar.**
- [ ] **E.2 One lockbox read**, if and only if a candidate survives E.1.
- [ ] **E.3 Resolve the registered search** — `scored`, whichever way it
  lands. A null here is the deliverable, not a failure.
- [ ] **E.4 Commit:** `E: first budgeted search over the indicator space`

## Phase F — the terminus `[auto]`

- [ ] **F.1 Approval card.** A surviving configuration emits a setup card
  via `cards.py` — entry, stop, target, size — with its obtainability audit
  and its corrected bar attached. **A human places every order.**
- [ ] **F.2 No execution path.** A test asserts the package contains no
  order-placing code and no broker credential handling.
- [ ] **F.3 Commit:** `F: approval terminates at a card, not an order`

---

## Track G — register integrity, SHRUNK

**Reduced 2026-08-30.** With the lab repointed at a declared indicator
search, recomputing twelve dead mechanical strategies is archaeology. The
loophole still needs closing, because the register is public and cited.

- [x] **G0** H-RECLAIM recomputed and resolved `scored` (`4e9e9f1`).
- [ ] **G1 Import the frozen scripts instead of transcribing them.**
  **Note, found while grilling: five frozen scripts have no `__main__` guard
  and execute on import** — `exp_reclaim`, `exp_stopwidth`, `exp_secondpush`,
  `exp_x1_reconcile`, `exp_armed_stop`. Importing them runs the experiment
  and prints into the stdout that `experiment.run` parses `METRICS:` from.
  So "just import it" does not work for exactly the scripts Phases 1-2 of the
  old plan needed. Use AST extraction of the function definitions, or an
  exec'd namespace — **never edit the frozen file.**
- [ ] **G7 Restrict `kind="documented"`.** Refuse it when an archived script
  exists: if it can be run, it may not merely be described.
- [ ] **G8 Republish the console.**

~~G2–G6: recompute the remaining twelve.~~ **Dropped.** They reproduce to
three to twelve decimal places; what they would buy is verdicts on families
that are already closed, and the lab is no longer pointed at them. Their
`documented` resolutions stand, and the console labels them as
document-sourced with the numeric fields null — which is honest, and now
permanent rather than transitional.

## Track H — engineering hygiene

- [x] **H1** CI, green (`1e2545d`). Found six defects in three runs.
- [x] **H2** launchd jobs unloaded (`84376de`).
- [ ] **H4** Make the console rebuildable without S3.
- [ ] **H5** Hoist the timezone conversion out of the groupby loop (32% of
  recompute time); wire up `scripts/to_parquet.py` (28 MB vs 200 MB).

## Blocked — decisions, not engineering

- [ ] **B-DECISION.1** `[needs-user]` **OPEN.** Closing X3 needs 3.14× the
  sample at **$186–291** against **$21.91** headroom. Costed in `TASKS.md`.
- [ ] **MGC/MCL** `[needs-user]` **$19.16, pre-approved, fits the cap.** The
  first real market for the pipeline once Phase D passes. Adding metals and
  energy multiplies effective sample by **1.85×** and drops the detectable
  floor from 0.0654 to 0.0481, because MES and MNQ at rho=0.9 are nearly one
  instrument wearing two names. Register the first hypotheses against the
  **event axis** — crude's scheduled weekly inventory release is a mechanism
  equity index does not have — rather than re-running dead families on new
  symbols.
- [ ] **H3** `[needs-user]` AWS teardown, ~$100/year, zero invocations in 14
  days. Keep the bucket ($0.08/month); drop the scaffolding.
- [ ] **A2-PUB / L-PUB** `[needs-user]` four essay drafts awaiting review.
  **The lab series still has no name.**
