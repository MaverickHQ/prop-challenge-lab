# PAPER-PREREG — the fade paper campaign (Lab protocol #4)

**Status: SEALED 2026-07-09** (user instruction "seal"). On seal: hash → appended to
`PREREG.sealed` history and logged as protocol #4 in PROTOCOLS.md. This
is a **validation protocol, not a challenge protocol**: the objective is
backtest/live parity, not P(pass). It is the binding lockbox for the
fade finding — prospective data cannot be mined.

---

## 1. What is being validated

The Family-2 finding (VERDICT-2026-07-06-v3): fading failed 15-minute
opening-range breakouts carried **~+0.1R/trade net, persistent
out-of-sample**, on MES and MNQ. The question this campaign answers:
**does that survive a human executing it live?** — measured as
implementation shortfall per trade, never assumed.

## 2. The fixed configuration (chosen ex-ante, justified from the v3 read)

- **Cell: `k_stop = 0.2, width_max = None`** — the only cell that was
  best on OOS *and* lockbox on *both* instruments (MES +0.107R OOS /
  +0.141R lockbox; MNQ +0.171R OOS), and the unfiltered variant trades
  most (fastest evidence accumulation). No cell switching mid-campaign.
- Instruments: **MES and MNQ**, one setup each per day, independently.
- Risk: **$175 per trade** per instrument; sizing by the engine's
  true-risk formula; 30-micro cap.
- Calendar: FOMC/CPI/NFP days = no entries (the sealed 259-row calendar).
- Day-flat always; no re-entries; no discretion — the plan card is the
  entire decision surface.

## 3. Venue & the uniform-delay argument

**TradingView free tier, built-in paper trading** (user decision
2026-07-09). CME data on the free tier is ~10-minute delayed. This is
acceptable **because the strategy is bar-relative, not
wall-clock-relative**: breakout and failure are bar-close events, and a
uniformly delayed tape contains the same bars in the same order — acting
on TV's bars as they arrive produces the same trades as real-time,
merely shifted. Standing rules that make the argument hold:

1. **Every decision keys off TV's own chart** — never peek at a
   real-time price anywhere else during the session (contamination).
2. Orders are placed in TV paper the bar after the failure close, as the
   engine specifies; the EOD flat happens on TV's session close as TV
   shows it.
3. This argument is valid for PAPER only. Any live translation later
   requires real-time data and a fresh look at timing.

## 4. Daily procedure (the whole job, ~15 min/day)

1. **09:45 ET (TV clock):** log the 15-min range per instrument
   (`/range` once the bot exists; a dated note in the vault until then).
2. Set TV alerts at range high/low. Wait.
3. On breakout, then a 1-min bar **close** back inside the range: place
   the entry stop at the boundary with bracket — stop = extreme ±
   0.2 × height, target = far side — sized per the plan card.
4. Log every fill (`/fills` or vault note): timestamp, price, contracts.
5. **Evening:** Debrief runs parity — model-implied fills (engine applied
   to the logged range/extreme/levels) vs actual logged fills — and
   appends the parity ledger + vault daily note.

## 5. Duration, evidence bar, and kill thresholds (fixed)

- **Duration: ≥ 60 calendar days AND ≥ 40 completed trades**, whichever
  is later; hard stop at 90 days.
- **Kill thresholds (armed from trade 10, as sealed in v2 §8):**
  mean drift ≤ **−$5/trade** (live worse than model by more than the
  entire modeled round-trip friction, again) or mean |drift| >
  **$10/trade** (sign-balanced disagreement — the model is wrong even if
  the mean nets out). Kill fires → campaign over, finding did not
  survive contact, written up.
- Mid-point review at day 30 (journal note; no parameter changes —
  review is for process defects only, e.g. logging errors).

## 6. What success and failure mean (decided now)

- **Parity holds through the bar** → the finding is live-real at paper
  fidelity. Unlocks exactly one decision: whether to size a small
  personal live account (separate decision, own risk budget, NOT this
  document). It does NOT reopen the challenge (that bar stays ex-ante
  ≥ +0.25R).
- **Kill fires or expectancy lands ≤ 0 over ≥40 trades** → the finding
  is a backtest artifact at human-execution fidelity; final report gets
  an addendum; the fade closes.
- Either way: every day logged, the ledger append-only, the write-up
  from the ledger.

## 7. Costs

$0 mandatory. Optional monthly drift audit (~$1–2/mo EOD data top-up,
within the SPEND.md cap) cross-checks logged prices against vendor data.

## 8. Not committed to

No cell/sizing/threshold changes after seal; no real-time peeking; no
counting of "would have been" trades (a missed log is a missed trade,
recorded as a process defect); no early success declaration.

---

**Seal instructions:** user reads, says "seal" → commit → git blob hash
appended to `docs/PREREG.sealed` → row added to PROTOCOLS.md as
protocol #4 → campaign starts the next trading day the comms are live.
