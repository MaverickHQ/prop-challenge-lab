# ADDENDUM to VERDICT-2026-07-06-v3 — dated 2026-08-01

**This is an addendum, not an edit.** The verdict is append-only and its
text stands unchanged. What follows is what was learned afterwards.

## The finding

Verdict v3 recorded the failed-breakout fade as **"edge real (+0.1R,
persists OOS) but half-sized"**, with MES +0.107R OOS / +0.141R lockbox and
MNQ +0.171R OOS.

Those numbers are reproducible — re-running the sealed engine on 2026-08-01
returns them to three decimals, which is why the engine itself is trusted.

**But the entry price they assume cannot be obtained by any order.**

`occams/fade.py` books the entry at the range boundary, at the failure
close. At that moment price is **inside** the range, so the boundary is
behind the market. Every order that could actually be placed was tested on
2019-2026, both instruments:

| entry | MES | MNQ |
|---|---|---|
| sealed engine — **assumed** fill at the boundary | **+0.080** | **+0.186** |
| resting limit at the boundary, after the failure close | −0.056 | −0.009 |
| market order at the failure close | −0.076 | −0.012 |
| stop armed at the breakout, resting at the boundary | −0.119 | −0.036 |

Every implementable order is negative on both instruments. Only the
assumption is positive.

## Why

A resting stop fills **too early**: 60.3% of armed fills occur before any
failure close, and that subset returns −0.277R. A market order takes the
close, which is worse than the boundary. A limit enters on a retest, which
is late.

The engine books a fill at the boundary while conditioning on a close that
had not yet happened when price was there. The armed-stop subset where the
close *did* come first returns +0.122R (MES) / +0.226R (MNQ) — the edge is
real within that subset, but the subset is only identifiable after the fact.

**That is look-ahead, and it accounts for the entire measured edge.**

## What this changes

- **The +0.1R should be treated as an artifact**, not as a finding. The
  verdict's NO-GO at G1 stands and was correct; the reasoning beneath it
  does not.
- **Protocol #4** (the paper campaign) was validating this finding. It has
  zero completed trades, so nothing is lost by pausing it.
- **Protocol #4a** (limit at the boundary) was an attempt to fix an
  unplaceable card and is moot: no entry rule recovers the number.
- **Verdicts #1 and #2 (ORB) have never been checked for this defect** and
  must be.

## What it does not change

The data, the loader, the folds, the controls and the gates are unaffected
and were never in question. The engine reproduces its own verdict exactly.
This is a defect in one strategy's **entry assumption**, not in the
measuring apparatus — though the apparatus should have caught it, which is
the next item.

## The durable fix

An **entry-obtainability gate** in the harness, so that no protocol can be
sealed on a fill no order can produce. The planted-edge positive control
never tested for this: a planted edge is detectable regardless of whether
its entry price is reachable, so the control passed while the flaw went
through. Tracked as Z0.5.

## Provenance

Registered as `Z-ENTRY-IMPLEMENTABLE`; run
`2026-08-01-sop-verified` in the research archive carries the frozen
script, verbatim output and `engine_sha`. Reproduce with
`scripts/exp_entry_obtainable.py`.
