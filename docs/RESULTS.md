# Results — what this lab was pointed at, and what it found

**A closed programme.** One year, 24 registered hypotheses, three sealed
verdicts, $128.09 of market data, no fee ever paid to a funded-account
provider, and no money ever placed at risk in a market.

This is the results record. The narrative versions are
[essays](https://harveygill.substack.com/); this is the part that has to be
checkable, and every number below resolves to a record in
[the register](https://maverickhq.github.io/prop-challenge-lab/report.html).

---

## 1. The question

Could a mechanical strategy clear a funded-account evaluation — reach a
profit target before a trailing drawdown ratchets up behind it, inside a
time limit, under a consistency rule?

**We never entered one.** The instrument answered a better question first.

## 2. What was required

Computed before anything was hunted, which is the step almost nobody takes.

The rules are arithmetic: feed synthetic trade streams through the literal
constraints — win rate crossed with payoff ratio crossed with frequency
crossed with risk — and the shape of what is needed falls out before any
market data is touched.

**Asymmetry is the lever, not hit rate.** At a 2.0R payoff the rules clear
at a **45%** win rate. At 1.0R they need **60–65%** — the corner where most
retail strategies live.

Translated: roughly **+0.25R per trade at half a trade a day**, sustained.

**That number was later found to be one contract's geometry, not a law.**
See §5.

## 3. What was measured

Nine rearrangements of seven years of 1-minute bars on two index futures.
Not nine strategies — nine *axes*, each changing a different dimension after
the last one died.

| axis | result |
|---|---|
| opening-range breakout | family never worked |
| failed-breakout fade | +0.1R, and the entry was **unobtainable** |
| entry rule (reclaim filter) | −0.046R → **−0.262R**; confirmation costs the move |
| stop width ladder | flat on MNQ, monotone on MES (see §5) |
| second push | gross +0.011R → **net −0.082R**; costs ate it |
| objective (survival vs expectancy) | P(pass) 0.042 vs a 0.55 gate |
| conditioners (adverse excursion) | 1.7% of variance, partly algebraic |
| volatility compression | **reversed** — compression begets compression |
| overnight gap | null; fully priced at the bell |
| a whole technical methodology | 8 named strategies closed by 2 register entries |

**Gross signal across all of it: +0.02 to +0.04R per trade.** Against costs
of 0.05–0.09R. **The costs alone exceed everything the strategies produced.**

## 4. Three results that looked real and were not

Each survived every statistical check available. Each was caught by
something that is not a statistical test.

**An unobtainable entry.** A family cleared its sealed protocol at ~+0.1R,
out-of-sample, on both instruments, 34 of 36 fold-cells positive. Then
someone asked which order would have produced the fills. Price sat on the
far side of the level. **Every placeable order lost money**; the assumed
fill was the only positive one. Caught by an imperative — *show me the
order* — now a gate.

**A number containing its own answer.** A measurement came back at
*d* = −0.43, six times its detectable floor, significant on both
instruments, both sides, both horizons. It was measured from a level price
had already passed. Decomposed exactly: **94.8% was the distance already
travelled.** A market that froze solid would have printed most of it. Caught
by a prior, now mechanised as a calibration gate that reads the artefact at
**5.0 sigma on a world where nothing is happening.**

**A broken estimator that met forgiving data.** A hand-written rank
correlation ranked ties by row order. On one result: reproduced to four
decimals. On another — 97.1% tied values — **a recorded number moved 28%**.
Same defect, same session; the only difference was the shape of the data.

> *We checked and it was fine* and *we checked and it was fine by luck*
> carry entirely different information about everything never checked.

## 5. What the closing analysis changed

Done at wrap-up, and it corrected the programme's own record.

**The frontier was mis-stated.** +0.25R is one contract's geometry measured
against a 0.55 P(pass) gate. Priced as expected value across a real
13-contract menu, the break-even edge spans **two orders of magnitude** —
from **+0.003R** to +0.162R. Nine families were judged against a number that
applied to one of thirteen options.

**Trade geometry matters more than any signal found.** Moving the target
outward at a fixed stop moved net R by **+0.0816R** across a declared
ladder — *larger than the entire gross signal nine families produced.* It
had never been searched: the sealed grid recorded *"Fixed, not searched:
target = far side."*

**Cost burden is selectable, and it cleared a floor.** Cost in R is fixed
per-contract cost over per-contract risk — invariant to position size,
varying 15× with stop distance, and known **before** the trade. Filtering on
it improved expectancy monotonically and **cleared its detectable floor**
(+0.0811R against 0.0695R): the first registered primary this programme
satisfied.

**And the strategy still loses.** Best rung −0.0218R, interval crossing
zero.

**A design parameter was wrong for months.** The intra-cluster correlation
was asserted at 0.9 and never measured. Measured on 1,637 paired days:
**0.3818**. Every floor was ~15% too high. Re-scored across all 20 archived
blocks — **nothing changed verdict.** The correction is real and its
consequences for the register are nil, which could not have been assumed.

**One correction to published text:** *"stop width did not matter at all"*
is wrong on MES, where the archived ladder is a monotone 3.5× improvement.
It is right on MNQ. Neither had an interval, so neither was established.

## 6. Why we stopped before entering

Two independent lines arrived at the same place.

**From inside**, the instrument said the constraint is the adversary, not
the market: ~50% of the modelled failures breach the trailing drawdown, and
geometry moved results more than any signal did.

**From outside**, base rates from a major provider's own performance
disclosure — regulatory-style, cutting against its marketing, adversarially
verified 3-0:

| | |
|---|---|
| evaluation attempts that pass | **16.8%** |
| funded traders who receive a payout | **33.3%** |
| **attempts ending in a paid trader** | **~5.6%** |
| average payout | ~4% of nominal |
| average cumulative spend per trader | **$4,270**, ~60% lose it |
| **evaluation fees as share of provider revenue** | **70–95%** |

**That last row is the business model.** The product is the fee.

**So the instrument was built to find out whether we could pass, and it told
us not to try.** That is the result. No fee was ever paid.

## 7. What is not settled

**X3 — order-flow print size.** Estimate +0.026 with an interval running to
**+0.113**, which would be larger than anything seven years of price data
produced, on the one non-public axis held. **Inconclusive, not refuted.**
Closing it needs 3.14× the effective sample — $186–291 against $21.91 of
remaining budget. **Closed unresolved**, and recorded as such so the
register never reads as though it were answered.

## 8. The honest total

**No edge.** Public price structure on these two instruments is exhausted at
this resolution — not "unpromising", *exhausted*, in the specific sense that
nine distinct rearrangements were measured and the gap to what the rules
require is a factor of ten.

**One hundred and twenty-eight dollars of market data. No provider fee. No
money at risk.**

That is what the instrument was for. It was built to be able to say this
sentence and have it mean something.
