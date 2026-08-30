# Q2 — why each attempt died, not just how many

**Dated 2026-08-09.** A capability demonstration on already-recorded runs,
registered at **zero alpha**: it asks nothing new of the market, it re-reads
what E2 produced.

---

## The gap

E2 reported **P(pass) 0.042** and **P(breach) 0.440**. Those do not sum to
one, so roughly half of all attempts ended in some way nobody had named.

## The decomposition — it sums to exactly 1.0000

**Obtainable limit** (the honest variant), n = 1,652:

| outcome | share | attempts |
|---|---|---|
| passed | 0.0424 | 70 |
| **breached the trailing drawdown** | **0.4395** | 726 |
| timed out, still ahead | 0.3541 | 585 |
| timed out, underwater | 0.1640 | 271 |
| | **1.0000** | |

**Sealed fade** (the artifact), same n:

| outcome | share |
|---|---|
| passed | 0.2579 |
| breached | 0.2748 |
| timed out, ahead | 0.3971 |
| timed out, underwater | 0.0702 |

## What it says that a single probability could not

**Breach is the dominant failure, at 44%.** The remedy that fits is *less
size*, not more time. A reader given only "P(pass) 0.042" might reasonably
have concluded the horizon was too short — 90 days for a 6% target — and
that conclusion would have been wrong in the most expensive possible way,
because more days on a breaching strategy produce more breaches.

**The artifact and the honest variant fail differently.** The artifact's
losses are mostly *time* (0.397 ahead-but-short); the honest one's are
mostly *drawdown* (0.440). Same strategy, one assumption apart, and the
character of the failure changes as well as its rate.

## The refinement that changed the reading

The first run put every surviving-but-short attempt into one **TIMEOUT**
bucket. Its own example detail then said:

> still alive at day 90 of 90, **4,032 short of the 3,000 target**

Which means the account was **down 1,032** — not nearly there. "Ran out of
days" reads as "nearly made it" and implies a longer horizon is the fix. For
a losing strategy it is the opposite.

Splitting it gives **0.354 ahead** versus **0.164 underwater** on the
obtainable variant. Both were hidden inside one label that would have
pointed at the wrong remedy.

**This is not estimand-shopping**, and it is worth saying why rather than
assuming it is obvious: the item is zero-alpha and descriptive, no tested
quantity changed, no threshold moved, and **r1 remains on the register**.
What changed is a bucket label that was demonstrably misleading, and the
evidence it was misleading came from r1's own printed output.

## Remaining limitation, stated rather than left to be found

"In profit" is any profit at all. One example sits at **+91** against a
3,000 target — technically ahead, practically indistinguishable from flat.
A useful next refinement would threshold it (say, halfway to target), but
that is a choice about what counts as "nearly there" and should be declared
before it is applied, not tuned until the buckets look tidy.

## The reason that exists to protect a past lesson

`NEVER_TRADED`. Verdict #1 was **void for instrument failure** — every cell
sized to zero contracts, all statistics structural zeros, no market
information revealed. A run whose equity never moves is now named as an
instrument failure rather than counted as a market result, and a test pins
it. Nothing in the current data triggers it, which is the point: it is there
so that the next time it happens, it cannot be read as a NO-GO.
