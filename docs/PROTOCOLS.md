# PROTOCOLS — the multiplicity ledger

**Why this file exists:** sealing protects one protocol from peeking; it
does NOT protect twenty sealed protocols from multiple comparisons. If
each honest protocol carries even a ~5% false-GO rate, iterating until
one passes manufactures a false GO. So every sealed protocol is logged
here, and **any GO is judged against the number of attempts that
produced it** — the prospective paper gate remains the only backstop
that survives unlimited iteration (future data cannot be mined).

Rules:
1. One row per sealed protocol, appended AT SEAL TIME (before the run).
2. Outcome filled in after the single read. No row is ever edited.
3. A GO on protocol N is presented alongside N — the reader applies the
   multiplicity discount, not the author's optimism.
4. New hypotheses enter only through the intake bar: a written ex-ante
   expectancy argument (≥ +0.25R at ≥ 0.5 trades/day for challenge
   purposes) plus a feasibility-frontier placement, BEFORE any grid.

| # | Sealed | Hash | Family | Symbols | Grid | Outcome |
|---|---|---|---|---|---|---|
| 1 | 2026-07-06 | `d3fa96c0…` (blob `7cc61b51…`) | ORB (daily-ATR stops) | MES, MNQ | 128 | **VOID** — instrument defect (0 contracts); no market info revealed |
| 2 | 2026-07-06 | `12ca0a32…` (blob `e2fa9aa4…`) | ORB (range-height stops) | MES, MNQ | 128 | **NO-GO** — family never worked (best 0.187 vs 0.55; in-sample 0.03–0.04) |
| 3 | 2026-07-06 | `b6b029c3…` (blob `098c4f2c…`) | Failed-breakout fade | MES, MNQ | 9 | **NO-GO at G1** — edge real (+0.1R, persists OOS) but half-sized (best 0.41) |
| 4 | 2026-07-09 | paper (blob `b70989ee…`) **PAUSED 2026-08-01 — see #3a** | Failed-breakout fade — PAPER validation (k=0.2, unfiltered) | MES, MNQ | 1 cell | **RUNNING** — ≥60d AND ≥40 trades; kill: drift ≤ −$5 or |drift| > $10 |
| 1-2 audit | 2026-08-01 | `Z04-ORB-OBTAINABLE` | ORB | MES, MNQ | — | **CLEARED of the #3a defect.** 6,774 armed orders audited: zero unplaceable, zero fill disagreements. ORB arms stops OUTSIDE the range while price is inside it, so the order is on the correct side when placed. Verdicts #1 and #2 stand as recorded. |
| 3a | 2026-08-01 | ADDENDUM — `docs/VERDICT-2026-07-06-v3-ADDENDUM.md` | Failed-breakout fade | MES, MNQ | — | **The +0.1R is an ARTIFACT.** The entry price it assumes — the range boundary at the failure close — cannot be obtained by any order; at that moment price is inside the range. All three placeable orders are negative on both instruments (limit −0.056/−0.009, market −0.076/−0.012, armed stop −0.119/−0.036) while only the assumed fill is positive. The NO-GO stands; the reasoning beneath it does not. |
| 4a | 2026-07-31 | amendment — `docs/AMENDMENT-4a.md` | Entry order type: **stop → LIMIT at the boundary** | MES, MNQ | — | **Not a new protocol; no multiplicity cost.** Execution-mechanics fix only: a "failure close" is by definition back inside the range, so the boundary is always on the far side and the card named an order no venue accepts. Cost two of the first three setups. Made at **zero completed trades**. Strategy, cell, sizing, kill thresholds and evidence bar all unchanged. |
