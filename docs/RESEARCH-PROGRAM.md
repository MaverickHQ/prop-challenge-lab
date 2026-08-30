# Research programme — how this lab could actually find an edge

**Written 2026-08-01.** Prompted by *Situational Awareness* (Aschenbrenner)
and the question: can we point an automated research loop at our historical
data and find a strategy better than the one we have?

This document argues that the answer is **yes, but not in the way the essay
suggests**, and that the single most important design decision is what the
loop is *forbidden* to do.

---

## 1. What the essay actually claims, and which part transfers

Aschenbrenner's mechanism is a compounding loop: automate the researcher,
and "hundreds of millions of AGIs could automate AI research, compressing a
decade of algorithmic progress into ≤1 year." Effective compute rises ~1
OOM/year — half raw compute, half algorithmic efficiency — plus
"unhobbling" gains from turning chatbots into agents.

The loop works in AI research because the objective has four properties:

| Property | AI research | Markets |
|---|---|---|
| Stationary | val loss on held-out text is stable | **regime shifts; the DGP moves** |
| Non-adversarial | nobody removes your gain | **others arbitrage it away** |
| Cheap to evaluate | more GPUs = more evaluations | **only time produces new OOS data** |
| High signal-to-noise | a 1% loss gain is unambiguous | **a Sharpe 0.5 edge needs years to separate from zero** |

**Markets invert all four.** That is not a quibble; it reverses the sign of
the central mechanism. In Karpathy's loop, keeping the config that improves
`val_bpb` is *correct* — the signal generalises. In ours, keeping the config
that improves backtest expectancy is *usually wrong*, because with enough
configs the best one is noise by construction.

So the honest translation is uncomfortable:

> **More search over a fixed historical dataset does not produce more edge.
> It produces more overfitting.** Compute is not our binding constraint.

The part that *does* transfer is unhobbling. Our bottleneck has never been
ideas; it is the serial cost of specifying, running, and honestly judging
one experiment. That is exactly what scaffolding fixes, and it is why the
loop is still worth building — for throughput and discipline, not for
search volume.

## 2. We have already run this experiment, and it returned a negative

`crucible-autoresearcher` is the Karpathy pattern applied to constraint
optimisation, and its headline result is the most relevant evidence
available to us:

- **Positive control:** the loop reliably finds a *planted* edge.
- **Real backtest:** the loop finds nothing. Thesis scorecard reads
  *Edge NOT FOUND*.

That is a **validated instrument reporting a negative**, which is far
stronger than an unvalidated instrument reporting a positive. It is also
consistent with the three sealed verdicts here: ORB dead, fade real at
~+0.1R but roughly half the size the challenge needs.

The correct inference is not "the loop is broken." It is: **searching
harder over 1-minute OHLCV bars on two index futures is close to exhausted.**

## 3. The binding constraint is statistical budget, not compute

Every hypothesis tested spends a fixed, non-renewable resource: the
probability that our *eventual* positive result is real. `PROTOCOLS.md`
already encodes this — "any GO is judged against the number of attempts
that produced it."

An unconstrained autoresearcher run against our data would spend that
budget in an afternoon and hand back a beautiful, false GO. **The loop must
therefore be built with the alpha budget as a first-class, decrementing
resource**, not as a caveat in a footnote.

Three consequences, all non-negotiable:

1. **Every hypothesis is registered before it is evaluated.** No exceptions,
   no "just looking".
2. **The evidence bar rises as the register grows.** A finding at attempt 40
   must clear a materially higher bar than the same finding at attempt 3.
3. **The lockbox is read once, ever.** Not once per hypothesis — once.

## 4. Where genuinely new information could come from

Ranked by expected value, not by how interesting they sound.

### 4.1 Order flow — the largest unexplored axis (highest value)

**Every search we have run used `ohlcv-1m`.** That is a heavily-mined,
low-information projection of the tape. The same vendor already sells us:

- **MBO** — every book message
- **MBP-10** — ten levels of depth
- **TBBO / trades** — tick-by-tick with aggressor side

Aggressor imbalance, absorption at a level, book thinning ahead of a
breakout, size resting at the boundary — this is the information real
futures edges are built from, and we have never looked at any of it. The
failed-breakout fade is *explicitly a story about order flow* ("the
breakout had no participation behind it") that we have only ever tested
through price.

This is the one axis where I would expect a genuinely new signal to exist.

### 4.2 The objective may be wrong (highest certainty, $0)

The challenge is a **path-dependent survival problem** with a trailing
drawdown, a daily loss limit and a minimum-days rule. Maximising expectancy
is *not* the same as maximising P(pass).

A lower-expectancy, lower-variance configuration can pass more often than a
higher-expectancy, higher-variance one. **We may already hold a passing
configuration and be measuring it against the wrong target.** Re-analysing
data we already own costs nothing and cannot overfit anything new, because
the strategy is fixed and only the scoring changes.

### 4.3 Conditioning on measured world state ($0)

The series' own given-world thesis: measure the state, condition on it.
Is the fade's expectancy conditional on range width relative to ATR,
overnight gap, time-of-day of the failure close, or realised volatility?

This is a **small, fully pre-specifiable set** — not a search. Five
candidate conditioners registered in advance is a very different act from
grid-searching two hundred.

### 4.4 New instruments (approved, cheap, but a shot in the dark)

MGC/MCL, ~$19 already approved. Worth doing, but it is another draw from
the same urn, not a new urn.

### 4.5 More search over `ohlcv-1m` (negative expected value)

This is what an unconstrained loop would do by default. It is the thing the
programme exists to prevent.

## 5. How the autoresearch pattern actually plugs in

Karpathy's three-way split maps cleanly, with one addition markets demand.

| Karpathy | Here |
|---|---|
| `program.md` (human-edited) | the research charter: objective, admissible search space, budget, keep rule |
| `train.py` (agent-edited) | the hypothesis + its config — **the only writable surface** |
| `prepare.py` (fixed) | our sealed engine, folds, controls — **never agent-writable** |
| — | **the alpha ledger — the addition markets require** |

The loop:

```
propose  -> register (hash, before any evaluation)
         -> screen on DEV folds only
         -> pre-register the survivor with a stated effect size
         -> evaluate on OOS
         -> keep/discard under a multiplicity-adjusted bar
         -> append to the register, decrement the alpha budget
```

**Guardrails that make it honest rather than fast:**

- Positive control (planted edge) and negative control (dead world) in
  every batch. A batch where the positive control fails is void — the
  instrument was broken, and no result from it counts.
- The proposer sees **dev folds only**. It never sees OOS, and it never
  sees the lockbox. Not "shouldn't" — *cannot*, enforced by the harness.
- Every proposal carries an **ex-ante mechanism**: why should this work,
  stated before the number is known. Proposals without one are rejected
  unrun. This is the single best filter against dredging.
- The register is **append-only**. A hypothesis that was tested and failed
  cannot be quietly un-tested.

## 6. The hypothesis register (S3)

Append-only, one row per hypothesis, alongside an experiments table keyed
to it. JSON/JSONL in the existing state bucket — the same reasoning as
B7.3: a few thousand rows is an in-memory filter and a database would add
IAM surface and ops for nothing.

```
hypotheses/<id>.json
  id, stated_at, statement (falsifiable, one sentence),
  mechanism (why it should work, written BEFORE the result),
  information_axis (price | orderflow | objective | conditioning | instrument),
  search_space_size (how many configs this licenses),
  alpha_allocated, prereg_sha, status, outcome,
  effect_size, ci_low, ci_high, decision, superseded_by

experiments/<hypothesis_id>/<run_id>.json
  config, folds, controls_passed, metrics, artifacts, spend_usd, engine_sha
```

`engine_sha` matters: a result computed by a different engine version is a
different result. That is the X1 lesson.

## 7. The programme

Each phase gates the next. No phase starts until the prior one's gate is met.

### R0 — Trust the instrument (gate; nothing else runs first)

- **X1**: reconcile the comparator gap against the sealed engine. A lab
  whose two implementations disagree by 0.15R cannot evaluate anything.
- Stand up the register and the alpha ledger.
- Re-run the planted-edge positive control on current code.

**Gate:** positive control passes, X1 reconciled to the tick.

### R1 — Spend nothing: re-score what we already own

- **H1 — the objective is wrong.** Compute P(pass) under the real rule set
  for the *existing* fade across sizings. Prediction stated in advance:
  P(pass) is non-monotonic in size, and the maximum is at a *smaller* size
  than expectancy-maximising.
- **H2 — conditioning.** Five pre-specified conditioners, registered
  before any is evaluated.
- **H3 — MAE is predictable.** This week showed adverse excursions 5-12×
  the stop distance. Is there a pre-trade observable that separates the
  days that reclaim from the days that run?

**Gate:** at least one of H1-H3 shows an effect surviving the
multiplicity-adjusted bar, or R1 is written up as a negative and we stop
pretending price data has more to give.

### R2 — Buy one new axis: order flow

- **H4** — does aggressor imbalance at the failure close separate winners
  from losers? Quote first; smallest sample that can answer it.
- Book pressure and absorption follow only if H4 justifies them.

**Gate:** an effect on dev folds large enough to be worth an OOS read.

### R3 — Harness the loop

Only now, and only with R0's ledger live. The loop is pointed at whichever
axis R1/R2 showed life in — never at "find me something".

## 8. What I actually expect to happen

Stating this in advance so it cannot be revised afterwards.

- **H1 (objective) is the most likely to pay** and the cheapest. I would
  not be surprised if the existing fade passes more often at a smaller size
  than we have been assuming. It is also the least glamorous outcome: no
  new strategy, just correct scoring.
- **H4 (order flow) has the highest ceiling and the highest cost.** It is
  the only place I would expect a genuinely new signal.
- **H2/H3 are coin flips**, and both are prone to false positives — hence
  pre-specification.
- **The most likely single outcome of the whole programme is a
  well-evidenced negative.** That is not failure. Three sealed verdicts
  already produced two honest NO-GOs and one real finding, and the series
  is written from exactly that honesty.

**The one thing that would make this programme worthless** is running an
unconstrained search, finding something beautiful, and trading it. The
guardrails are not bureaucracy; they are the entire reason a positive
result from this lab would be worth believing.
