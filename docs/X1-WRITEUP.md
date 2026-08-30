# X1 — volatility compression does not precede expansion. It precedes more compression.

**Dated 2026-08-09.** Registered before running, with both directions
interpreted in advance. First experiment on the completed maths engine
(M1–M7): every statistic from `occams.stats`, calibration-gated, with a
`calcs.json` naming which estimator produced each number.

X1 was the **best-scoring family in the catalogue** — the only one whose
mechanism is a documented statistical property rather than a story about
what participants are thinking.

---

## The result

**Primary** — consecutive contracting sessions ending at N−1, against day
N's realised RTH range ÷ trailing ATR. Prior sessions only.

| | |
|---|---|
| Spearman r | **−0.0890** |
| 95% CI (Fisher-z on n_eff) | **[−0.1345, −0.0431]** — excludes zero |
| n | 3,442 raw · **1,811 independent-equivalent** |
| against the declared floor | **−1.27× floor** |
| verdict | **detectable** |

Consistent across instruments: MES **−0.1058**, MNQ **−0.0703**.

And monotone across the pre-specified buckets:

| consecutive contracting sessions | n | mean next-day range |
|---|---|---|
| 0 | 1,674 | **0.9603 ATR** |
| 1 | 1,114 | 0.9349 ATR |
| 2 | 443 | 0.8379 ATR |
| ≥ 3 | 211 | **0.8266 ATR** |

**Every additional contracting session makes the next day quieter, not
louder.**

## What was registered, before the number existed

> **PRIMARY POSITIVE** → the mechanism holds.
> **PRIMARY NEGATIVE** → the mechanism is refuted in the sharpest way:
> compression predicts *more* compression, i.e. volatility persists across
> days rather than mean-reverting at this horizon.
> **PRIMARY ~ZERO** → compression carries no information, family dead.

The answer is the middle one. **This is not a null — it is a reversal**, and
the interpretation was fixed in the register before the run.

## Half the stated mechanism survived. The half the strategy needed did not

The registered mechanism was *"volatility clusters **and** mean-reverts"*.

- **Clustering is confirmed.** A negative correlation here *is* persistence:
  quiet states are followed by quiet states.
- **Mean reversion at a one-day horizon is refuted.** The coiled-spring
  reading — compression as stored energy about to release — is the part the
  strategy needed, and it is not there.

This distinction matters for what the result does and does not claim. It
does **not** refute volatility clustering; it confirms it, and then shows
that the trading inference usually drawn from it runs backwards.

## The confound check did exactly what it was predicted to do

The obvious predictor is today's opening range. It was registered as a
**confound check, not as evidence**, with the reason stated in advance: the
opening range and the rest of the same session are both measurements of that
day's volatility, and intraday volatility persists, so a quiet open
genuinely predicts a quiet day.

| | |
|---|---|
| opening-range ratio → same-day post-range expansion | **r = +0.3503** |
| 95% CI | [+0.3093, +0.3901] |
| against the floor | **+5.00×** |

**Five times the detectable floor, and it means nothing about the
hypothesis.** Had the primary been built on the same-day predictor, X1 would
have returned a large, robust, instrument-consistent positive — and it would
have been intraday persistence wearing the mechanism's clothes.

That is the same shape as ICT-P2: a large, significant, robustness-check-passing
number produced by the design of the measurement rather than by the market.
The difference is that this time it was **named in the registration and
routed into a control**, instead of being caught afterwards.

## Is the reverse tradeable?

**No.** r = −0.089 is about 0.8% of variance. It is a real relationship and
not a usable one, and reporting it as "an edge in the other direction" would
repeat the error the whole programme exists to avoid.

## What this closes

**Volatility contraction → expansion is dead on MES and MNQ at a one-day
horizon**, and it was the strongest-scoring family on the map. The
catalogue's own prior — *"the realistic expectation is most of these die"* —
was right about the best candidate it had.

## What this does not close

- Other horizons. This tests one day. Compression over weeks, or expansion
  measured over multiple sessions, is untested.
- Other instruments. MGC/MCL remain unbought and untested, though they are
  another draw from the same urn.
- The queue. X2 (overnight gap) and X3 (order-flow size) are structurally
  different and untouched. **Serial order stands.**

## Cost

**$0.** Register now at **16 hypotheses, alpha 0.32**. The bar for X2 rises
accordingly — which was stated before X1 ran, not after it failed.
