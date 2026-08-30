# Protocol #4a — entry order type (amendment to PAPER-PREREG §4 step 3)

**Dated 2026-07-31. Made at ZERO completed trades**, which is what makes
it legitimate: no result exists that this could be tuned toward. After
results accumulate the same change would be unacceptable.

## The defect

PAPER-PREREG §4 step 3 says: *"place the entry stop at the boundary with
bracket"*. The Pine aid renders that as `BUY STOP @ <boundary>` or
`SELL STOP @ <boundary>`.

**That order is never placeable at the moment the card fires**, and the
reason is structural rather than incidental. A "failure close" is
*defined* as a close back **inside** the range. So the boundary is always
on the far side of that close:

| Day | Break | Failure close | Card said | Boundary vs market |
|---|---|---|---|---|
| 2026-07-29 | DOWN | 7448.00 | BUY STOP @ 7444.25 | below → not a stop |
| 2026-07-30 | UP | 7419.75 | SELL STOP @ 7421.50 | above → not a stop |
| 2026-07-31 | DOWN | 7481.25 | BUY STOP @ 7480.25 | below → not a stop |

A buy stop below market (or a sell stop above it) is rejected by every
venue. This is not three unlucky days — it is every day, by construction.

**Consequence already paid:** two of the campaign's first three setups
were never executed. 2026-07-30 was logged as a process defect at the
time without the cause being understood; 2026-07-31 was the same defect,
diagnosed.

The engine was never wrong. `occams/fade.py` books
`entry = boundary + sgn × slip` and its comment reads *"stop-entry fill"*
— which is coherent only if the order is armed **during** the breakout,
while price is still outside the range and the boundary genuinely is a
valid stop. The card, however, fires at the failure close. So the
*model* assumed reading (a) while the *instructions* described reading
(b), and nobody could execute either.

## The amendment

**From 2026-08-03 (next trading day), the entry is a LIMIT order at the
boundary.**

- Card wording becomes `BUY LIMIT <n>x @ <boundary>` /
  `SELL LIMIT <n>x @ <boundary>`.
- Bracket is unchanged: stop = extreme ± 0.2 × height, target = far side.
- Sizing is unchanged: true-risk formula, $175, 30-micro cap.
- **Nothing about the strategy, the sealed cell, or the objective
  changes.** This is an execution-mechanics correction: it makes the card
  describe an order that can actually be placed.

Chosen over the two alternatives (user decision 2026-07-31):

- *Market on the failure close* — always fills, but every entry lands a
  tick or so worse than the model's boundary price, adding a systematic
  bias to the very number the campaign measures.
- *Arm the stop at the breakout* — most faithful to the engine, but
  requires acting before the failure close, which the Pine aid does not
  signal and which means watching continuously on a delayed feed.

## The known cost, stated in advance

A limit at the boundary **fills only if price returns to the boundary.**
The engine assumes a fill every time. So on a day where price closes back
inside and runs to target without retesting the boundary, the model books
a winner and reality books nothing.

This is a real divergence and it is **not** hidden:

- Such days are logged `/skip <SYM> no fill - limit not reached`.
- They are **not** "would-have-been" trades and are never counted as
  wins (PAPER-PREREG §8 stands).
- They are counted in the denominator, alongside process defects, as the
  operational drag number in the period recaps (B7.5).

If no-fill days turn out to be common, that is itself a finding about the
strategy's executability — and a more honest one than a model that
assumes free fills.

## The symmetry that has to hold

2026-07-31's setup would have **lost** — stop hit at 09:49 ET, four
minutes after the failure close, model −$157.50 (−0.90R). It was not
executed, so it is logged as a process defect and carries no drift.

It must not be recorded, mentioned or remembered as a loss avoided. The
rule against counting would-have-been *wins* is worth nothing if
would-have-been *losses* are quietly banked as good judgement. A defect
that happens to dodge a loser is exactly as much a defect as one that
dodges a winner, and over a small sample the flattering half is the one
that gets noticed. Both directions stay out of the P&L and in the
process-defect count.

## What this does not do

It does not reopen the cell, the sizing, the kill thresholds, the
duration, or the evidence bar. It does not license any further amendment.
Protocol #4 otherwise stands exactly as sealed (`b70989ee…`).
