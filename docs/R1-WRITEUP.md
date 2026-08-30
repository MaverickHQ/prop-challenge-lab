# R1 — what re-scoring what we already own actually found

**Dated 2026-08-01.** Written whether the answer was good or not, because a
programme that only writes up its positives is a marketing department.

R1 asked whether anything could be recovered from data we already held, at
zero cost, by scoring it differently rather than searching harder. Three
questions were registered. All three are now answered, and the answer to all
three is no.

---

## H1 / E2 — the objective was not the problem

**Question:** the challenge is a path-dependent survival problem, not an
expectancy problem. Were we simply scoring the right strategy the wrong way?

**Answer: no.** Scored through the sealed rules engine on every start day,
verified Zero tier:

| | P(pass) @ 90d | P(breach) |
|---|---|---|
| obtainable fade | **0.042** | 0.440 |
| sealed (unobtainable) variant | 0.258 | 0.275 |
| **G1 requires** | **≥ 0.55** | |

**Even the artifact fails.** Verdict v3's NO-GO stands twice over: once on
the number, once on the entry that produced it.

**And the registered prediction was wrong**, which turned out to be the
useful part. I predicted P(pass) would peak *below* the expectancy-maximising
size. It rises monotonically — 0.000 / 0.009 / 0.042 / 0.088 / 0.174 across
$75–$350 — because with negative expectancy the only route to a target is
variance. **An interior peak requires a positive edge**, which made the
*shape* of that curve a new edge diagnostic (E7), independent of any
expectancy estimate.

## H2 / C1 — conditioning: not run, and why

Registered but **not executed**. Conditioning searches for subsets of a
strategy that look better. When the strategy's entry cannot be obtained at
all (protocol #3a), every such subset is a subset of nothing, and each one
spends alpha to say so.

**Closed as unnecessary rather than left open.** If a strategy with a real
entry ever exists, this is worth reviving verbatim — the five conditioners
are already specified.

## H3 / C2 — adverse excursion is large, but not usefully predictable

**Question:** `H-STOPWIDTH` showed MAE is large — 77% of trades exceed the
stop, median 3×. Is it *foreseeable*?

**Answer: barely.** One of four pre-specified predictors survives:

| predictor | pooled r |
|---|---|
| **range height / ATR** | **−0.131** |
| overnight gap / ATR | −0.039 |
| 5-day mean range / ATR | +0.008 |
| minutes to breakout | −0.046 |

Consistent across both instruments and above the detectable floor. But the
stop is *defined* as `extreme ± 0.2 × height`, so stop distance scales with
height by construction while MAE scales with volatility — meaning
`MAE/stop ≈ ATR/height` is partly **algebraic rather than informative**.

That it is only −0.131, where a clean inverse would approach −1, says MAE is
dominated by day-specific noise. Which cuts both ways: not purely
definitional, but the predictable part is small. **1.7% of variance is not a
filter.**

---

## What R1 establishes

**Price data on MES and MNQ is exhausted for this setup family.** Not
"unpromising" — exhausted, in the specific sense that we have now tried:

- a different **entry rule** (reclaim: −0.26R vs −0.05R)
- a different **stop width** (four-rung ladder: expectancy flat throughout)
- a different **direction** (second push: −0.082R / −0.015R)
- a different **objective** (P(pass) 0.042 against a 0.55 gate)
- a different **conditioner set** (one weak, partly definitional signal)

and the gross signal across all of it is **+0.02 to +0.04R against a +0.25R
requirement**. Even at zero commission the family is an order of magnitude
short. No rearrangement of these price levels closes that.

## What it does not establish

- That **order flow** is exhausted. H5's first look found a consistent
  monotonic gradient (r = −0.072, terciles +0.216 / −0.030 / −0.198) in the
  exhaustion direction. Underpowered, unconfirmed, and the one genuinely
  non-public input we hold.
- That **other instruments** behave this way. MGC/MCL are untested, though
  they are another draw from the same urn.
- That the lab is wrong. It reproduced its own sealed verdict to three
  decimals (X1) and cleared ORB of the entry defect (Z0.4). The instrument
  is trustworthy; the input is not fertile.

## The honest close

R1 cost nothing and returned nothing tradeable. That is a normal result and
it was the registered expectation: *"the most likely single outcome of the
whole programme is a well-evidenced negative."*

What it did return is three findings that outlast the strategy — the
objective is not the problem, the P(pass) shape is an edge diagnostic, and
adverse excursion is large but not usefully foreseeable. Those are reusable.
A subset that looked good would not have been.
