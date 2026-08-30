# ICT primitives — what the two measurements found

**Dated 2026-08-09.** Registered before running, run under the SOP harness,
written up whether the answer was good or not.

A beginner playbook naming four ICT strategies was assessed against the
catalogue. It collapses to **two triggers and one entry**: 2022 Model, Judas
Swing and Turtle Soup differ only in *which level is swept*, and all four
enter with a limit at a fair value gap or its 50% (consequent encroachment).

So the entry was tested once, and the sweep was tested once. **Two register
entries in place of eight**, both $0 on data already owned: 1,849 RTH
sessions per instrument, MES and MNQ, 2019-05-06 to 2026-07-03.

Both outcomes are strategy-free signed forward returns — no stop, no target,
no assumed fill. The touch is *derived* from what the market did, never
supplied as an input. This is the #3a discipline: the fade's defect entered
through a P&L outcome that carried an entry assumption inside it.

---

## ICT-P1 — the fair value gap carries no forward information

**Claim tested:** after price returns to a gap's midpoint, the move continues
in the direction of the displacement that created the gap.

Primary, pooled, conditional on the CE actually being touched (n = 3,159;
independent-equivalent 1,662 after the MES/MNQ cluster discount, against
1,602 required):

| | value |
|---|---|
| mean signed 30-min forward return | **−0.00036 ATR** |
| 95% CI (bootstrap, clustered by date) | [−0.01040, +0.00903] |
| Cohen's d | **−0.0015** |
| declared detectable floor | 0.07 |

**Zero, to four decimal places, on a sample built to detect an effect fifty
times larger.** The CI is almost exactly symmetric about zero.

The pre-specified secondaries agree and add something the primary cannot:

| | MES | MNQ |
|---|---|---|
| CE fill rate | 0.921 | 0.894 |
| **mirror fill rate** (equal distance, opposite side) | **0.929** | **0.906** |

Price is *marginally more likely to extend an equal distance than to return
to the gap*. The "price comes back to rebalance the imbalance" claim is not
merely absent — it points very slightly the wrong way. Without the mirror
control a 92% fill rate would have read as strong confirmation, when all it
says is that price moves.

Unconditional reading (a limit resting at CE all session, no touch = no
trade = 0): −0.00033 ATR, CI [−0.00956, +0.00859]. Same answer.

**One asymmetry worth stating, because it strengthens the null rather than
weakening it.** Measuring from CE carries a small *positive* bias by
construction: conditional on a bar dipping to the level, that bar's close
tends to sit on the far side of it, in the signed direction, for both gap
directions. The true drift is therefore **at or below** the measured value,
and the measured value is zero. No further run is needed to establish that;
it follows from how the touch is defined.

## ICT-P2 — the sweep looked significant, and was measurement

**Claim tested:** a sweep of the prior session's extreme reverses.

The first reading was large and, on its face, highly significant:

| | value |
|---|---|
| mean reversal-signed 30-min return | −0.15853 ATR |
| 95% CI | [−0.17500, −0.14229] |
| Cohen's d | −0.4318 |

Negative reversal-signed means *continuation*: +0.159 ATR with the break.
Nowhere near zero, on both instruments, on both sides (high sweeps −0.157,
low sweeps −0.160), and holding to the session close.

**It was not believed, and it should not have been.** R1 established the
gross signal on these instruments at +0.02 to +0.04R. An effect six times
the declared detectable floor, appearing suddenly on the family already
killed twice, is far likelier to be an artifact than a discovery.

The defect is visible from construction alone, without any data. P2 measured
the forward move from the **swept level**. On an up-sweep, price is already
*above* that level when the bar closes. So

```
C[end] − level  =  (C[i] − level)  +  (C[end] − C[i])
                    penetration        forward drift
                    positive by        the thing the
                    construction       claim is about
```

**A market that froze solid the instant it swept would still print a
positive continuation reading.** ICT-P2-CONTROL decomposes the identity —
which cannot manufacture a better number, because the parts must sum to the
original:

| term | mean (ATR) | share of headline |
|---|---|---|
| total (reproduces P2 r1 exactly) | −0.15853 | 100% |
| **penetration** | **−0.15023** | **94.8%** |
| **forward drift** — the actual claim | **−0.00829** | 5.2% |

Drift CI [−0.01953, **+0.00256**] — **crosses zero**. Cohen's d = −0.034,
less than half the declared floor. Median sweep excursion 0.057 ATR.

**Corrected verdict: null.** The sweep of a prior-day extreme carries no
usable directional information at 30 minutes — neither the reversal ICT
claims nor a tradeable continuation.

---

## What this establishes

**All four playbook strategies are refuted at their shared component.** The
FVG entry is the only thing 2022 Model, Silver Bullet, Judas Swing and Turtle
Soup have in common, and it carries no forward information. The sweep trigger
shared by three of them carries none either. Two register entries, eight
strategies, zero dollars.

This is the payoff from testing primitives rather than strategies. Had each
been built and backtested, each would have produced a P&L curve requiring its
own entry audit, its own cost model and its own multiplicity charge — four
times the alpha for a worse answer.

**Turtle Soup is our failed-breakout fade under another name**, and it is now
dead for a second, independent reason: the entry was unobtainable (#3a), and
the trigger carries no signal.

## What this does not establish

- That ICT-as-practised is refuted. Order Block and Draw-on-Liquidity are
  **not mechanisable** — "the last candle before a powerful move", "the
  liquidity price is *likely* to reach next" — and were declined for that
  reason. What was tested is the part that can be written down. That is a
  weaker claim than the discretionary one, and it was stated as such before
  running, not after.
- That killzone timing is irrelevant. It was queued as a *conditioner*, to be
  tested only if a primitive survived. Neither did, so it was not run —
  conditioning a family with no base effect is how a subset gets mistaken for
  a signal.
- Anything about horizons other than 30 minutes, or levels other than the
  prior-day extreme.

## The finding that outlasts the strategies

**A reference price can manufacture an effect six times your detectable
floor.** P2 was significant on both instruments, on both sides, and at both
horizons — every robustness check a normal process would run, all passed,
all meaningless, because they were robustness checks on an arithmetic
identity rather than on a market.

This is the second time in this programme that an entry-price choice
produced a result that survived every downstream test: first the fade's
unobtainable fill (#3a), now the swept level. Both were caught by asking
*what price is this number measured from?* — a question no significance test
asks.

**Added to the standing checklist:** before any forward-return measurement,
state where the reference price sits relative to price at the moment of
measurement, and decompose if it is not at price.
