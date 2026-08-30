# X2 — the overnight gap is fully priced at the bell

**Dated 2026-08-09.** Registered before running, with both directions and
the confound interpreted in advance. Second experiment on the completed
maths engine.

---

## The result

**Primary** — signed gap against the signed forward return over the first
session hour, measured from the close of the 09:30–09:31 bar.

| | |
|---|---|
| Spearman r | **+0.0025** |
| 95% CI | **[−0.0433, +0.0483]** — spans zero, near-symmetric |
| n | 3,480 raw · 1,831 independent-equivalent |
| against the declared floor | **+0.04×** |
| verdict | **null** |

**Secondary**, same predictor held to the session close: r = **−0.0022**,
CI [−0.0481, +0.0436]. Also null, and the sign flips — which is what noise
does.

The instruments disagree in sign (MES **+0.0170**, MNQ **−0.0111**), and the
pre-specified gap deciles show no pattern at all: the largest gaps down
average −0.009 ATR forward, the largest gaps up +0.006 ATR, with the middle
deciles scattered either side of zero.

## Both folklore readings die together

The registration committed to interpretations in advance:

> **POSITIVE** → incomplete absorption; the mechanism holds.
> **NEGATIVE** → overreaction; gaps fade rather than extend.
> **~ZERO** → the gap is fully priced at the bell. Family dead.

At +0.04× the floor, it is the third. **Neither "gaps run" nor "gaps fill"
survives** — and both are widely believed, which is exactly why the
direction was committed to beforehand.

## The gap is real. It just isn't directional

Worth separating, because "no effect" and "no gap" are different claims:

- Median |gap| is **0.28 ATR** — these are substantial moves, not rounding.
- Gap size **does** predict subsequent movement: the control returns
  **r = +0.163, 2.33× the floor, detectable.**
- Gap *direction* predicts nothing.

That is a coherent picture rather than an absence of one: **the market
prices the overnight news completely at the bell, and what is left over is
volatility with no direction in it.** A large gap tells you the day will be
busy. It tells you nothing about which way.

## The confound behaved exactly as registered

The control — |gap| against |forward move| — was named before the run as
volatility persistence rather than information, with the note that *a large
positive is expected even if the primary is zero*.

It came back at **+0.163, detectable**. In X1 the analogous control came
back at **five times the floor** while the hypothesis was refuted. Two
experiments running, two large significant controls, neither of them
evidence for anything.

**That is now the pattern worth naming.** In both cases the confounded
measurement was the *more obvious* one to build. A programme that reached
for the obvious predictor would have produced two impressive results and
learned nothing.

## The prior was right, and cheaply so

Registered before the run: *"I expect approximately zero. Index futures
trade nearly 23 hours, so the 'overnight' gap on MES and MNQ is a gap
across a brief maintenance break rather than a genuine information vacuum
— the structural argument that makes gap strategies work in equities is
much weaker here."*

That held. It is worth recording, but not worth much: a correct prior on a
null is cheap, and the reason to run it anyway was that it was structurally
different from everything that had already failed.

## Where the queue now stands

**Two of four queued families are dead, and both were price-based.**

| | |
|---|---|
| **X1** volatility contraction | DEAD — and reversed |
| **X2** overnight gap | DEAD — null |
| **X3** order-flow size | untested — **the only non-public axis we hold** |
| **X4** conditioning | queued last, and there is now nothing to condition |

This strengthens R1's conclusion rather than adding to it: **public price
structure on MES and MNQ is exhausted.** Five rearrangements failed in R1;
two structurally different families have now failed on top of that.

**X3 is the last genuinely different thing in the queue.** If it dies, the
honest conclusion is that these two instruments have been read out at this
resolution, and the choice becomes new data, new instruments, or stopping —
which the experiment plan already anticipated as a real outcome.

## Cost

**$0.** Register now at **17 hypotheses, alpha 0.37.**
