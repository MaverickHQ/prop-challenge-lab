# Experiment plan — the research queue

**This is not a build plan.** A build test plan asks *"does the code do
what it says?"* and exits when tests pass. An experiment asks *"is this
true?"* and exits when the answer is known, including when the answer is
no. They have different owners, different exit criteria, and mixing them is
how "we shipped it" gets mistaken for "it works".

Build work lives in `TASKS.md`. Only research lives here.

---

## The rules every experiment below inherits

Enforced by `occams/experiment.py`, not by memory:

1. **Registered before run**, with a mechanism written before any number
   exists. No mechanism → rejected unrun.
2. **Powered before run.** The sample must be able to detect the declared
   effect, discounted for MES/MNQ dependence. Underpowered → refused, not
   run-and-caveated.
3. **Entry obtainable.** The family declares an ORDER; a fill is never an
   input. Default-deny for any family without an auditor.
4. **One look.** No extending a sample after seeing a result.
5. **Alpha is spent, and the bar rises.** Nine hypotheses are already on
   the register. Each new one makes the next survivor less believable.

**Every experiment below is $0** and uses data already owned.

---

## Standing definition of success

An experiment SUCCEEDS if it returns a **defensible answer**, not if it
finds an edge. Five well-evidenced negatives is a successful quarter; one
unreplicable positive is not.

A family only advances to a sealed protocol if it clears the frontier:
net R ≥ 1.5, WR ≥ 45–52%, 0.5–1 trade/day, **P(pass) ≥ 0.55**.

---

## X1 — Volatility contraction → expansion — **CLOSED 2026-08-09: DEAD**

**Result: r = −0.089, CI [−0.135, −0.043], excludes zero, 1.27x the floor.**
The relationship exists and runs the WRONG WAY: compression predicts more
compression. Monotone across pre-specified buckets. Half the registered
mechanism survives (clustering) and the half the strategy needed does not
(mean reversion at one day). Full write-up: [`X1-WRITEUP.md`](X1-WRITEUP.md).

The confound check earned its place: the same-day opening-range predictor
returned **+0.350, five times the floor, and means nothing about the
hypothesis** — intraday persistence wearing the mechanism's clothes. It was
named as a control in the registration rather than caught afterwards, which
is the ICT-P2 lesson applied in advance.

**Next: X2, overnight gap.** Serial order stands.

### Original registration (unchanged)


**Mechanism (pre-stated):** volatility clusters and mean-reverts. A
compressed range is a low-volatility state, and low-volatility states are
followed by higher-volatility ones more often than chance. This is a
documented statistical property, not a story about what traders think —
which makes it the strongest prior available to us.

**Predictor:** today's opening-range height ÷ trailing 20-day median, and
the count of consecutive contracting sessions.
**Admissible alternatives (declare before the run, TASKS.md §I3):**
Bollinger bandwidth, ATR ratio, Donchian width, NR7. These are the same
mechanism expressed by different indicators — **a predictor swap, not a new
hypothesis** — but the choice must be named in the registration, because
picking the best of four afterwards is a four-fold multiplicity charge.
**Entry:** stop order beyond the compressed range — **obtainable by
construction**, arms while price is inside.
**Outcome:** realised day range ÷ ATR, and the sealed P(pass).
**Power:** ~1,700 setups/instrument; effective n ~1,780; detects r ≈ 0.066.
**Kill:** no relationship between compression and subsequent expansion.

## X2 — Overnight gap behaviour — **CLOSED 2026-08-09: DEAD**

**r = +0.0025, CI [−0.0433, +0.0483], 0.04x the floor. Null.** Both folklore
directions die together. The gap is real (median 0.28 ATR) and predicts
subsequent VOLATILITY (control r = +0.163, 2.33x floor) but carries no
direction: the market prices it completely at the bell.
Full write-up: [`X2-WRITEUP.md`](X2-WRITEUP.md).

**Two experiments, two large significant CONTROLS, neither of them
evidence.** X1's confound came back at 5.00x the floor, X2's at 2.33x — and
in both cases the confounded measurement was the MORE OBVIOUS one to build.
A programme reaching for the obvious predictor would have produced two
impressive results and learned nothing.

**Next: X3, order-flow size — the last structurally different thing in the
queue.**

### Original registration (unchanged)


**Mechanism:** the gap prices everything that happened while the market was
shut. Absorption is not instantaneous, so the first session hour should
behave differently after a large gap than after a flat open.

**Predictor:** |open − prior close| ÷ ATR, signed.
**Entry:** declared per direction; must pass the gate.
**Outcome:** signed forward return to a fixed horizon, strategy-free — the
same shape as H5, deliberately, because a P&L outcome is how the fade's
defect entered.
**Kill:** gap size carries no information about the subsequent session.

## X3 — Order-flow size distribution — **CLOSED 2026-08-09: UNRESOLVED**

**r = +0.0260, CI [-0.0610, +0.1125], floor 0.13, n_eff 510.** Null against
the declared floor — but **the interval still admits +0.11**, which by this
programme's standards would be a large effect. **Not refuted: unresolved at
the sample we own.** Full write-up: [`X3-WRITEUP.md`](X3-WRITEUP.md).

**The registered confound did NOT appear** (-0.053, null) where X1's came
back at 5.00x the floor and X2's at 2.33x. My prediction was wrong, and the
reason sharpens the rule: X1's opening range and X2's |gap| are DIRECT
measures of volatility; large-print share is a **normalised distributional
statistic** that divides the level out. **Confounds come from predictors
that carry a LEVEL** -- a sharper rule than "the obvious predictor is
confounded".

**X4 is a conditioner and there is nothing left to condition.** All three
base families are closed, so the queue as written is exhausted.

### Original registration (unchanged)


**Mechanism:** aggressor *identity* is invisible, but aggressor *size* is
not. A breakout carried by a few large prints is a different event from one
carried by many small ones. Uses the 525 sessions already bought.

**Predictor:** share of breakout-leg volume in prints ≥ the 90th percentile.
**Outcome:** strategy-free forward return, as X2.
**Note:** the only non-public axis we hold. **H5 already spent alpha here** —
this is a *different question of the same data*, and the register must show
both so the multiplicity is visible.

## X4 — Higher-timeframe trend as a conditioner

**Mechanism:** a slower signal conditions a faster one. Classic, widely
believed, and therefore heavily mined — scored lower for that reason, not
higher.

**Not a family on its own.** Runs as a conditioner over whichever of X1–X3
survives. **Deliberately queued last:** conditioning a family that has not
yet shown a base effect is how a subset gets mistaken for a signal.

---

## ICT primitives — RUN AND CLOSED 2026-08-09

Inserted ahead of X1 at the user's direction; the serial rule was kept.
Registered `ICT-P1-FVG` and `ICT-P2-SWEEP` before any number existed, plus
`ICT-P2-CONTROL` at zero alpha as a validity check on the instrument.

**Both null. Four named strategies refuted at their one shared component,
for $0.** See [`ICT-WRITEUP.md`](ICT-WRITEUP.md).

The transferable finding is not about ICT: **a reference price manufactured
an effect six times the detectable floor**, significant on both instruments,
both sides and both horizons. Every robustness check passed because they
were robustness checks on an arithmetic identity. Now a standing rule —
state where the reference price sits relative to price before measuring any
forward return, and decompose if it is not at price.

Three hypotheses are now spent that were not in the original queue. **The bar
for X1-X4 rises accordingly**; that is the register working, not a cost to
be regretted.

---

## Sequencing, and why it is strictly serial

**X1 → X2 → X3 → (X4 only if something survives).**

Serial, not parallel. Running four at once and reporting the best is a
four-fold multiplicity charge disguised as efficiency — the exact failure
the register exists to price. Each finishes and is written up before the
next registers.

## Explicitly not queued

VWAP and band reversion, lunch fade, MA pullback — all high-WR/low-R, the
frontier's hardest corner. Session-extreme break duplicates ORB. Day-of-week
is dredging. MOC imbalance and absorption need data we have chosen not to
buy. Reasons recorded so a future reader knows they were **considered and
declined**, not overlooked.

## What would change this plan

- **X1–X3 all die** → price and cheap order flow are exhausted on these
  instruments, and the choice becomes new instruments, new data, or
  stopping. That is a real outcome and should be written up as one.
- **Something survives** → it goes to a sealed protocol under `PROTOCOLS.md`
  rule 4, with its own ex-ante expectancy argument, and the multiplicity
  discount is applied against every attempt that preceded it.
- **Budget reopens** → order-flow depth (MBP-10, ~$585) becomes the
  strongest available purchase, and X3's result is what should decide it.
