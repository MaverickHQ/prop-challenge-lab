# SPEND — experiment budget ledger

**Cap: $150 total experiment budget** (Lab Program, founded 2026-07-09;
user-adjustable — a cap change is a ledger entry, not an edit). Every
purchase: quote first (`scripts/fetch_data.py` pattern), explicit user
approval, then a row here. No row is ever edited; corrections append.

Standing rules:
- Data files are licensed → `data/` stays git-ignored, never committed,
  never redistributed.
- Purchases that would exceed the cap are refused until the user raises
  it here.

| Date | Item | Quoted | Spent | Approved by | Running total |
|---|---|---|---|---|---|
| 2026-07-05 | MES.v.0+MNQ.v.0 ohlcv-1m 2019–2026 + definitions (API) | $18.43 | $18.43 | user | $18.43 |
| 2026-07-05 | Lost stream (conversion crash before persist — process lesson, fixed) | — | $9.21 | — | $27.64 |
| 2026-07-05 | Portal parent-product MES (pre-API purchase; kept as backup) | $13.99 | $13.99 | user | $41.63 |
| 2026-07-09 | APPROVAL: MGC.v.0 full history 2010→ ($12.98) + MCL.v.0 2021→ ($6.18) ≈ $19.16 — purchase executes at T2.4 start | $19.16 | 0 (pending) | user | $41.63 |
| 2026-07-31 | B0.1 latency probes (7 samples, 30 bars metered) | $0.0001 | $0.0001 | user (B0 spike) | $41.63 |
| 2026-07-31 | B0.5 Yahoo-vs-CME validation top-up, MES+MNQ last 7 sessions | $0.0625 | $0.0625 | user | $41.69 |
| 2026-07-31 | **OVERSPEND (process defect):** same top-up re-billed twice — script had no cache, so each re-run re-downloaded. Approved ~$0.10, actual $0.1875. Fixed: `validate_feed.py` now persists to git-ignored `data/` and re-runs cost $0. Same class as the $9.21 lost stream; the lesson existed in `fetch_data.py` and was not carried across. | — | $0.1250 | — | $41.82 |
| 2026-08-01 | APPROVAL: R2.1 order-flow `trades` tape, MES+MNQ, 09:45-10:15 ET breakout leg, most-recent-first from 2026-07-03. Estimate unreliable (three attempts came in 4x, 1.5x and 1.5x wrong; per-day cost varies ~8x with volume), so the **$90 HARD CAP decides the sample**, not the estimate. Approved $81, cap $90. | ~$81 | superseded by the row above | user | — |
| 2026-08-01 | **OVERSPEND (process defect, $33.82 over approval):** R2.1 completed at **$114.82** against $81 approved and a $90 cap. Cause: the cap in `fetch_orderflow.py` was PER-RUN, not cumulative — `spent` reset to zero on each invocation, so run 1 ($46.16) and run 2 ($68.66) each passed a $90 check and together did not. Same root cause as the B0.5 re-bill: a guard that does not know what already happened. Fixed: prior spend is now priced from disk before anything is bought, and the run refuses outright if the cap is already reached. **This takes the programme to $156.64 against the $150 cap — $6.64 over. No further purchase until the user rules on the cap.** | $81 | $114.82 | user approved $81; overspend NOT approved | $156.64 |
| 2026-08-01 | R2.1 part 1: 356 instrument-days (178 sessions x2, 2025-10-29..2026-07-03) at 09:45-10:15 ET. Exact cost priced from the request list, not estimated. Stored gzipped after an uncompressed first pass filled 6.3 GB. | — | $46.16 | user | $87.98 |
| | **Remaining under $150 cap** (incl. pending approval: $19.16 MGC/MCL + up to $43.84 remaining R2.1) | | | | **$62.02** |


---

## RESTATEMENT 2026-08-01 — quotes were being recorded as charges

**The ledger above overstated spend by ~22%.** Every row was written from
`metadata.get_cost`, which returns a **quote**. Databento bills on data
actually delivered, and the two are not the same. Vendor actuals, read from
the portal's Data usage page (GLBX.MDP3, 100% of usage):

| | ledger said | vendor actual |
|---|---|---|
| July (bars, lost stream, portal, probes) | $41.82 | **$41.12** |
| 2026-08-01 R2.1 order-flow tape | $114.82 | **$86.97** |
| **TOTAL EVER** | $156.64 | **$128.09** (3.69 GB) |

**Corrected position:**

- **Programme total $128.09 against the $150 cap — $21.91 of headroom.**
  The earlier claim that we were $6.64 OVER the cap was wrong; it came from
  quote-based accounting, not from the vendor.
- **R2.1 actual $86.97 against $81 approved — over by $5.97**, not the
  $33.82 first reported. The per-run cap bug was real and did let more
  through than approved; the magnitude was not what I said.
- **Free credit: $125, essentially exhausted.** $128.09 total means roughly
  **$3.09 has crossed into paid**, and everything from here is real money.
  Credits expire six months from signup (~2026-12).
- MGC/MCL at ~$19.16 would take the total to ~$147.25 — still inside the
  $150 cap, but ~$22 of it real money rather than credit.

**Method change, effective now:** this ledger records **vendor actuals**.
Quotes are for the pre-spend decision only and are explicitly labelled as
estimates. A quote recorded as a charge is a wrong number in the one
document whose entire job is to be right about money.


## Data durability, 2026-08-01

All $128.09 of purchased data is now in `occams-research-<account-id>`:
1,058 files, 2.1 GB, each with a sha256 and a provenance row naming its
vendor, purchase date and the engine commit current at archive time.

Until today it existed on one laptop with no second copy. Re-buying it would
cost the full $128.09 again — and the $125 free credit that covered most of
the original purchase is now exhausted, so a re-buy would be entirely out of
pocket.
