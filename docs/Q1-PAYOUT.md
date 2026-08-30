# Q1 — P(pass) was never the objective, and it flatters weak strategies

**Dated 2026-08-09.** A capability demonstration, registered at **zero
alpha**: the fade is already dead on obtainability, so no number here can
revive it and nothing rides on the result.

---

## The gap that was open

`ChallengeState` scored the evaluation and stopped at qualification. But
consistency rules differ **by stage**, and the engine held only the first:
the tier we sealed has *no* evaluation consistency requirement, while the
qualified tier applies a largest-day rule to **payout eligibility**.

So a strategy could qualify comfortably and never be paid — and every
P(pass) this programme ever quoted (E2's 0.042, the 0.55 gate, the whole
feasibility frontier) measured **getting through the door**.

## What it shows

| | P(pass) | **P(first payout)** | qualified but never paid |
|---|---|---|---|
| sealed fade *(the artifact)* | 0.2579 | **0.1659** | **36%** |
| obtainable limit *(the real one)* | 0.0424 | **0.0115** | **73%** |

Of accounts that qualified on the artifact, **51% breached while funded**.
P(two payout cycles) on the obtainable variant is **zero**.

## The general finding, and it is not about the fade

**P(pass) systematically flatters a weak strategy, and the weaker it is the
worse the flattery.** The artifact loses 36% of its qualifiers; the honest
variant loses 73%.

The reason is structural, not incidental. Qualifying is a **one-time
hurdle** — you need one good run. Getting paid requires **surviving and
then accumulating again**, under a consistency rule the evaluation did not
impose, on an account whose drawdown floor has already ratcheted. A
marginal strategy scrapes the first and has no cushion for the second.

This means the frontier that governed the whole programme was calibrated on
the wrong quantity. E2's verdict — 0.042 against a 0.55 gate — was
decisive anyway, but the true figure is **0.0115**, and the gate itself was
set against a number that overstates.

## What this does not show

**The payout parameters are illustrative and unverified.** We verified the
evaluation geometry. We never verified the funded-stage terms — the
withdrawal threshold, the minimum funded days, the exact consistency
fraction. Every number above is conditional on parameters a user must
confirm.

That is why this is a *capability* result: it establishes that the engine
can now ask the question, and it establishes the **direction and rough
magnitude** of the correction. It does not describe any provider's terms.

**Verifying those parameters is the natural follow-on**, and it is a user
task rather than a build.

One display artifact worth naming so nobody reads it as data: the archived
output prints `median days to payout 0`. The standalone script's chained
runner does not track that field — `harness.monte_carlo_to_payout` does.
It is a zero because nothing filled it, not because payouts arrived on day
zero. It is absent from the recorded metrics.

## The design decision worth keeping

`PayoutState` deliberately **mirrors** `ChallengeState` — breach checked
before payout, a floor that trails the equity high and locks at the funded
balance, sticky terminal states, consistency that *delays* rather than
breaches. Two places it must differ, and both are modelling choices stated
as such:

**A withdrawal is not a loss.** When money leaves, the equity high moves
down with it. Leaving the floor where it was makes every successful payout
instantly breach the account — the single easiest way to model this wrongly,
and a test pins it.

**The input convention, which cost a wrong answer while building it.**
`record_day` takes **cumulative** equity — the running mark a simulator
produces, which knows nothing about withdrawals and never drops when money
is taken out. Passing broker-balance equity instead double-counts every
payout and breaches the account the day after its first success. The
ambiguity was real enough to break three tests before it was named, so it is
now named in the module docstring rather than implied.
