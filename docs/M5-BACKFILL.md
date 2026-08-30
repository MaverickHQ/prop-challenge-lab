# M5 — re-scoring the archive through the audited engine

**Dated 2026-08-09.** Not an experiment: no hypothesis was registered and no
alpha spent. A re-run with the **same estimand** is a reproduction, not a
second look.

Each target imports the **original frozen script** and calls its own setup
functions, so the data and the setup logic are held constant and the only
thing that changes is the estimator. Re-implementing the setups here would
risk introducing a different bug and then blaming the engine for it.

Two kinds of target, and keeping them apart is the design:

| | meaning | a difference is |
|---|---|---|
| **reproduction** | same estimator, run again | a **defect** |
| **estimator swap** | M1 replaced the function | a **finding** |

---

## 1. H5 order flow — reproduces exactly

Our only live positive signal, and it rested on the `spearman()` that ranked
ties by row order. **6/6 metrics match**, pooled r = **−0.0723** unchanged.

Already known from M1, now on the record through the harness: the function
was wrong in general and met nearly tie-free data. Luck, not correctness.

## 2. C2 adverse excursion — one predictor moved, and the mechanism is exact

**11/15 reproduce. The four that moved are all the same predictor.**

| predictor | % tied | archived | re-scored | verdict |
|---|---|---|---|---|
| range / ATR | 1.0% | −0.1312 | **−0.1312** | exact |
| overnight gap / ATR | 0.7% | −0.0387 | **−0.0387** | exact |
| 5-day mean range / ATR | 0.1% | +0.0076 | +0.0075 | 1e−4 |
| **minutes to breakout** | **97.1%** | **−0.0459** | **−0.0440** | **moved** |

Per instrument the move is larger: **MNQ −0.0304 → −0.0388, a 28% change.**

The mechanism is not a guess. *Minutes to breakout* is the only
integer-valued predictor in the set — **94 distinct values across 3,260
observations**. The three continuous predictors are ≤1% tied and reproduce
to the last recorded decimal. `argsort(argsort(x))` hands tied values
arbitrary distinct ranks in whatever order they appear, so a 97%-tied column
is where it must break, and it is exactly where it broke.

**The conclusion is unchanged.** `range/ATR` — the one predictor C2 reported
as surviving — reproduces exactly at −0.1312. *Minutes to breakout* was
noise before and is noise now. But **a number in the register was wrong**,
and the correction is appended rather than edited.

This is the vindication of M1, and it is the case M1's own commit predicted
in advance: *"on a bucketed or tercile predictor it would not have been."*

## 3. Z0 entry obtainability — reproduces to 12 decimal places

The flagship, re-verified **because** we rely on it. **8/8 match at 1e−12** —
not to rounding, to full float precision.

| order | archived | re-scored |
|---|---|---|
| sealed engine (assumed fill) | +0.08015 / +0.18622 | identical |
| limit after close | −0.05590 / −0.00913 | identical |
| market at close | −0.07555 / −0.01243 | identical |
| stop armed at breakout | −0.11880 / −0.03567 | identical |

**The NO-GO stands, unmoved.**

### What the backfill caught on the way

The first Z0 run diffed against `2026-08-01-three-orders` and reported a
mismatch on `a_limit_after_close` (−0.049 vs −0.0559). That was **not** an
engine defect: the register holds two Z0 runs, and the earlier one predates
the SOP harness. Its own note says so.

**An experiment with several runs has a canonical one, and a backfill that
picks the wrong record blames the engine for the register's history.** The
target now names the SOP-verified run and the reason is in the code.

Worth noting what that near-miss was: the pre-harness record is the one
whose option had no frozen script — the exact incident that caused
`occams/experiment.py` to exist. **The backfill's first act was to rediscover
the record that the SOP was written because of.**

---

## Tolerances — two of them, for two different reasons

**Rounding.** The register stores values already rounded, so an exact match
is impossible in principle. The honest test is agreement *to the precision
at which it was recorded*. Inference from the stored value is a **lower
bound** (0.080 is stored as `0.08`), so it is conservative: it can miss a
drift smaller than the recorded precision, never invent one.

**Monte Carlo.** A bootstrap CI cannot match exactly — M1's cluster
bootstrap consumes its RNG differently from the three hand-rolled copies it
replaced. Both are correct; the draws differ. Declaring which metrics are
stochastic **before** running is what stops a legitimate RNG difference
reading as a reproduction failure, or an exact-match rule being quietly
relaxed the first time it fails.

## Still to backfill

Priority tier is done. Remaining, in order: **E2 / E7** (Monte Carlo,
seeded) · **X1-RECONCILE** · **Z04-ORB-OBTAINABLE** · **E3-COSTS** ·
**H-RECLAIM · H-STOPWIDTH · H-SECONDPUSH** · the three **ICT** runs, whose
CIs are the first genuinely stochastic comparison and will exercise the
split above.
