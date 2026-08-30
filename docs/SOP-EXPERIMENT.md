# SOP — hypothesis to test to record

**Every experiment in this lab runs this way. There is no other way.**

Not because procedure is virtuous, but because on 2026-08-01 the session's
most consequential finding — that no placeable order reproduces the sealed
engine's entry — was recorded *without its script*, because one of the three
variants had been run inline. The conclusion sat in the register while the
means of checking it did not exist. Nobody noticed until a question forced
a look.

A written procedure would not have caught that: the person skipping the step
is the same person who would have been reading the procedure. So the SOP is
`occams/experiment.py`, and this document explains what it enforces.

---

## The six steps

### 1. State it so it can be wrong

One sentence, falsifiable. *"The reclaim filter improves per-trade
expectancy"* — not *"look at reclaims."*

### 2. Write the mechanism BEFORE the number exists

Why should this work? A hypothesis without one is **rejected unrun** —
`register_hypothesis` raises. This is the single best filter against
dredging, and it is worthless if it can be back-filled afterwards.

### 3. Fix the analysis plan, in writing, in the registration

Predictor · outcome · statistical test · **sample size** · what is excluded
and why. Fixed *before* the data exists, so that a gigabyte of ticks landing
on disk cannot turn the analysis into a search.

### 4. Register

```python
from occams import archive
archive.register_hypothesis(hid="H-EXAMPLE", statement=..., mechanism=...,
                            information_axis=..., search_space_size=...,
                            alpha_allocated=...)
```

Append-only. Corrections append a new record with `supersedes`; nothing is
edited. A register that can be rewritten proves nothing.

### 5. Write the analysis as a FILE and run it through the harness

```python
from occams import experiment
experiment.run(hypothesis_id="H-EXAMPLE",
               script="scripts/exp_example.py",
               run_id="2026-08-01-full-history",
               config={...}, note="what the outcome means",
               controls_passed=True)
```

The harness, in order: checks the hypothesis is registered → archives the
script → runs it → archives stdout → reads the metrics → records the
experiment referencing both artifacts. **Any step failing aborts all of it,
and there is no flag to skip one.**

The script ends with:

```python
from occams import experiment
experiment.emit({"mes_r": -0.049, "mnq_r": -0.007, "n": 3295})
```

That printed line — not a human reading the table above it — becomes the
record. It removes transcription from the loop entirely.

### 6. Read once, and write down what it means

`note` carries the interpretation *and the caveats*. If controls did not
pass, say so in `controls_passed` and explain in the note. A caveat recorded
inside the experiment survives; a caveat mentioned in conversation does not.

---

## The rules that have teeth

| Rule | Enforced by |
|---|---|
| No mechanism, no hypothesis | `register_hypothesis` raises |
| No inline analysis | `experiment.run` requires a file that exists |
| No result without its script | script archived *before* the run |
| No result without its output | stdout captured and archived, even on failure |
| No retyped metrics | parsed from the script's own `METRICS:` line |
| No silently edited script | sha256 re-checked against the archived copy |
| No rewriting the register | write-once prefixes; `supersedes` instead |
| No skipping a step | `run()` has no `force`, `skip` or `dry_run` — asserted in tests |

## Frozen evidence

`scripts/exp_*.py` are excluded from `ruff` on purpose. They are archived
byte-for-byte as the artifact that produced a registered result, so
reformatting one breaks the guarantee that the archived copy is the script
that ran.

## What is still on the human

The harness cannot check that your mechanism is *honest*, that your sample
size was fixed for a reason, or that you are not proposing your fortieth
hypothesis against the same data and calling the survivor a discovery. That
is what the alpha ledger and `PROTOCOLS.md` are for — and the bar rises as
the register grows.

## Reading a record later

Every experiment carries `engine_sha`, the commit that produced it. A number
computed by a different engine version **is a different number** — that is
the X1 lesson, and it is why the field exists rather than being inferred
from a date.
