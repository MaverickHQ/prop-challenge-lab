# X3 — print size carries no direction, and the null is weak

**Dated 2026-08-09.** Registered before running, with the power limitation
stated in the registration rather than discovered afterwards.

The only non-public axis this programme holds. Every family that has died —
ORB, the fade, second push, ICT, X1, X2 — traded price structure visible to
anyone with a chart. That is why X3 stayed queued after two price families
died in one afternoon.

---

## The result

**Primary** — share of 09:45–10:00 volume in prints at or above that
window's own 90th-percentile size, against the direction-signed forward
return over the following hour, measured from the 10:00 close.

| | |
|---|---|
| Spearman r | **+0.0260** |
| 95% CI | **[−0.0610, +0.1125]** |
| n | 970 raw · **510 independent-equivalent** (463 required) |
| against the declared floor | **+0.20×** |
| verdict | **null** |

Instruments disagree in sign (MES **+0.0262**, MNQ **−0.0024**), and the
terciles are flat: +0.00175 / +0.00095 / +0.00216 ATR from low to high
large-print share. No gradient, no ordering.

The unconditional mean signed forward return is **+0.0016 ATR** — so there
is no momentum in this window either, independent of print size.

## This null is materially weaker than X1's or X2's — as registered

The registration said, before the run:

> **X3 can only refute a LARGE effect.** A null here means "no effect big
> enough for 552 effective observations to see", which is a materially
> weaker statement than X1's or X2's nulls.

That is now the operative sentence. **The interval runs to +0.1125.** An
effect of +0.11 is not excluded, and by this programme's standards that
would be a large effect — larger than anything price data has produced.

So the honest verdict is **not refuted — unresolved at the sample we own.**

| | X1 | X2 | X3 |
|---|---|---|---|
| CI half-width | 0.046 | 0.046 | **0.087** |
| declared floor | 0.07 | 0.07 | **0.13** |
| what a null excludes | a real effect | a real effect | **only a large one** |

X1 and X2 were answers. X3 is a measurement that ran out of data.

## The registered confound did NOT appear — and that is the finding

Three experiments running, three confounds named in advance. The first two
came back large:

| | control | result |
|---|---|---|
| X1 | opening-range ratio → same-day expansion | **+0.350, 5.00× floor** |
| X2 | \|gap\| → \|forward move\| | **+0.163, 2.33× floor** |
| **X3** | large-print share → \|forward move\| | **−0.053, null** |

**My prediction was wrong.** I registered *"a chunky tape is a busy tape"*
and expected a large positive.

The reason it failed is instructive and was not spotted in advance. X1's
opening range and X2's absolute gap are **direct measures of volatility** —
of course they predict more volatility. Large-print *share* is a
**normalised distributional statistic**: a session can have a chunky size
distribution without being busy, because the share divides out the level.
Scale-free predictors do not proxy for volatility, and that is exactly why
this one did not.

Worth recording because the pattern I named after X2 — *"the confounded
measurement was the more obvious one to build"* — was drawn from two cases
and is now qualified by a third. The confound is not automatic; it comes
from predictors that **carry a level**. That is a sharper rule than the one
I had.

## What this means for the queue

**X4 is a conditioner, and there is now nothing left to condition.** All
three base families are closed. Running X4 would be conditioning on nothing,
which the plan already refuses:

> conditioning a family that has not yet shown a base effect is how a subset
> gets mistaken for a signal

**The queue as written is exhausted.**

## The one purchase that could still change an answer

The experiment plan anticipated this decision:

> Budget reopens → order-flow depth becomes the strongest available
> purchase, and **X3's result is what should decide it**.

X3 has decided it, and the answer is not "no". It is **"we could not see"**,
with an interval that still admits an effect worth having.

To bring the floor from 0.13 to 0.07 needs roughly **3× the effective
sample** — about 1,575 sessions per instrument against the 525 we own.
Extending the same `trades` schema is the cheaper route than depth data.

**No cost figure is quoted here on purpose.** Three cost estimates in this
programme have been wrong — by 4×, 1.5× and 1.5× — and the standing rule
from `SPEND.md` is that **the cap decides the sample, not the estimate**.
What can be said: it is well beyond the $21.91 of headroom remaining under
the $150 cap, so it is a cap-raise decision for the user, not a purchase
decision for me.

## Cost

**$0.** Register now at **18 hypotheses, alpha 0.42.**
