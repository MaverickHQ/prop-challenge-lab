# Programme conclusion — what a year of this established

**Dated 2026-08-09.** Written because the experiment plan committed to
writing it, in advance, for exactly this outcome:

> X1–X3 all die → price and cheap order flow are exhausted on these
> instruments, and the choice becomes new instruments, new data, or
> stopping. **That is a real outcome and should be written up as one.**

That is where the programme is. Nothing here is new analysis. Every number
below is already in the register; this document exists because none of them
could previously be seen in one place.

> **Dating correction, 2026-08-09.** These documents were first written
> carrying the date 2026-08-03, taken from a working note rather than
> checked against the clock. The register's own `stated_at` timestamps —
> which come from the machine, not from prose — say **2026-08-09**, and
> those are correct. The prose has been corrected to match. Recorded rather
> than fixed silently, because a repository whose argument is provenance
> does not get to quietly repair its own dates.

**Position:** 18 registered hypotheses · alpha 0.42 spent · three sealed
verdicts · $128.09 of a $150 data budget · 1,216 archived objects, 2.11 GB ·
427 tests green. **No strategy with a demonstrable edge.**

---

## 1. The scoreboard

Sealed verdicts, which predate the register:

| | family | result |
|---|---|---|
| **#1** | ORB | **VOID** — instrument defect, no market information revealed |
| **#2** | ORB | **NO-GO**, validated. Best cell P(pass) 0.187 vs a 0.55 gate; null 0.000 while trading |
| **#3** | failed-breakout fade | **NO-GO** at G1 (0.41 vs 0.55) — with a real-looking edge that later proved an artifact |

The register, in the order it was written:

| hypothesis | axis | result | cause of death |
|---|---|---|---|
| H-RECLAIM | price | −0.046 → −0.262 R | the filter made it strictly worse |
| H-STOPWIDTH | price | ladder flat, 77.5% exceed stop | expectancy unchanged at every stop width |
| H-SECONDPUSH | price | gross +0.011 → net **−0.082 R** | costs ate the whole signal |
| H4-ORDERFLOW ×2 | order flow | not run | closed unrun — moot once the fade's entry failed |
| X1-RECONCILE | instrument | reproduces verdict #3 to 3 d.p. | *instrument trusted* |
| **Z-ENTRY-IMPLEMENTABLE** | instrument | assumed +0.080/+0.186 R; **all four placeable orders negative** | **the entry was unobtainable** |
| E2-OBJECTIVE | objective | P(pass) **0.042** vs 0.55 gate | fails twice over — even the artifact reaches only 0.258 |
| E3-COSTS | order flow | MES spread 1.0 tick, MNQ **2.0** | assumption was optimistic; tightened the error bar |
| Z04-ORB-OBTAINABLE | instrument | 6,940 orders, **0 unplaceable** | ORB cleared — the defect was fade-specific |
| H5-FLOW-PREDICTS | order flow | r = −0.072 | **underpowered** (n_eff 474, floor 0.131) |
| C2-MAE-PREDICTABLE | conditioning | range/ATR r = **−0.131** | partly algebraic; 1.7% of variance |
| ICT-P1-FVG | price | −0.00036 ATR, d −0.0015 | no forward information |
| **ICT-P2-SWEEP** | price | −0.159 ATR, d −0.43 | **artifact — 94.8% reference price** |
| ICT-P2-CONTROL | price | drift −0.008, CI crosses zero | the corrected reading |
| **X1-COMPRESSION** | price | r = **−0.089**, CI [−0.135, −0.043] | **reversed** — compression begets compression |
| **X2-OVERNIGHT-GAP** | price | r = **+0.002**, CI [−0.043, +0.048] | null; fully priced at the bell |
| **X3-PRINT-SIZE** | order flow | r = **+0.026**, CI [−0.061, **+0.113**] | **unresolved** — ran out of data |

Plus eight named ICT strategies closed by two register entries, because all
four shared one entry and three shared one trigger.

## 2. What is established

**Public price structure on MES and MNQ is exhausted at this resolution.**
Not "unpromising" — exhausted, in the specific sense that the following have
all been tried and measured:

- a different **entry rule** (reclaim)
- a different **stop width** (four-rung ladder)
- a different **direction** (second push)
- a different **objective** (P(pass) rather than expectancy)
- a different **conditioner set** (four predictors, one weakly surviving)
- a different **family** (fade, after ORB)
- a different **statistical property** (volatility compression)
- a different **information event** (the overnight gap)
- a different **school of thought entirely** (eight ICT strategies)

Across all of it the gross signal is **+0.02 to +0.04R against a +0.25R
requirement**. That is an order of magnitude short, before costs of
0.05–0.09R per trade. No rearrangement of these price levels closes it.

**The machinery is trustworthy.** It reproduced its own sealed verdict to
three decimals from a clean restore, cleared ORB of the entry defect on
6,940 orders, and has caught three defects that would each have produced a
publishable-looking false positive.

## 3. What is not established

- **Order flow is not refuted.** X3's interval still admits **+0.113** —
  larger than anything price data has produced. It is unresolved at 525
  sessions, not answered.
- **Other instruments are untested.** MGC/MCL remain unbought. They are
  another draw from the same urn, and that is a prior, not a result.
- **Other horizons are untested.** Everything here is intraday or one-day.
- **This says nothing about discretionary trading.** What was tested is the
  part that can be written down as a rule. That was stated before ICT ran,
  and it applies to the whole programme.

## 4. The findings that outlast the strategies

These are the durable output. A strategy would not have been.

**An entry price is never an input.** The fade passed a sealed verdict at
+0.1R with a fill no order could produce. Four placeable orders were all
negative. This is now a default-deny gate: a family without an auditor
cannot be swept at all.

**Ask what price a number is measured from.** ICT-P2 read −0.159 ATR at
d = −0.43 — six times its detectable floor, significant on both instruments,
both sides and both horizons. **94.8% of it was the reference price.** No
significance test asks that question. A calibration gate now does,
rejecting it at 5 sigma on a world with no drift at all.

**The shape of P(pass) against size is an edge diagnostic.** Monotonic means
variance harvesting; an interior peak requires a positive edge. Independent
of any expectancy estimate — which matters, because expectancy has misled
this programme twice.

**Confounds come from predictors that carry a level.** Three experiments,
three confounds registered in advance. X1's returned 5.00× the floor, X2's
2.33×, X3's nothing. The difference is that the first two were *direct
measures of volatility* and the third was scale-free. That rule was wrong
after two cases and right after three.

**Pooling correlated instruments is not free.** H5 was read as n=901 when
its effective n was nearer 474. Every power gate now applies the design
effect.

**Do not act inside your own noise floor.** Learned twice in one day: a
calibration tolerance tighter than its own sampling error, and a block-length
rule reacting to sampling error on independent data.

**A hand-rolled statistic is a liability even when it happens to be right.**
The `spearman()` behind two results ranked ties by row order. On H5 it cost
nothing — the data was nearly tie-free. On C2 it moved a recorded number
**28% on MNQ**. The difference was luck.

## 5. The decision

Four options. This is the section that is actually for the user.

**A — Buy more order-flow data.** The only thread where more data could
change an answer. Bringing X3's floor from 0.13 to 0.07 needs roughly **3×
the effective sample** — about 1,575 sessions per instrument against the 525
owned. **No cost figure is quoted:** three estimates in this programme have
been wrong by 4×, 1.5× and 1.5×, and the standing rule is that the cap
decides the sample, not the estimate. It is well beyond the $21.91 of
headroom, so it is a **cap-raise decision**.
*Odds: the honest read of X3 is a small positive that would not clear the
frontier even if confirmed.*

**B — New instruments.** MGC/MCL, $19.16 already approved and unspent.
Cheap. But explicitly *another draw from the same urn* — the same public
price structure on different tickers.

**C — Publish.** The repository is audited and publishable; the audit
returned zero hits across every commit message and historical blob. **The
lab is the product, not the edge.** Pre-registration, a multiplicity ledger
priced as a depleting resource, an obtainability gate, a calibration gate
that rejects its own artifacts, and a register of eighteen honest negatives
is a more unusual artifact than a working strategy would have been — because
working strategies are claimed constantly and almost never come with the
register that would let you check.

**D — Stop.** A defensible outcome, and one the programme priced from the
beginning: *"the most likely single outcome of the whole programme is a
well-evidenced negative."* That is what was delivered, for **$128.09**, with
**no fee ever paid** to a funding provider and **no money ever put at risk
in a market.**

## 6. Was it worth doing?

On its stated goal, no: there is no edge, and the challenge is not passable
with anything built here.

On the goal it actually served, yes. The programme spent $128 to establish —
with evidence that survives inspection — that a specific, widely believed
space is empty. That is worth more than the same $128 spent discovering the
same thing one attempt fee at a time, and considerably more than the
alternative outcome, which was to find an edge that was not there and fund
it.

**Three separate results in this programme looked real and were not.** Each
was caught by a different guard, and each guard was built because the
previous one was not enough. That is the thing worth keeping.
