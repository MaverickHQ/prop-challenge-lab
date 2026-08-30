# PREREG v3 — the sealed evaluation protocol (Family 2: the fade)

**Status: v3 SEALED 2026-07-06** (user instruction "seal" after final
read; no OOS or lockbox data has been read for this family).

Version history (departure clause honored each time):
- **v1** (sealed 2026-07-06 am): ORB family. Verdict **void for instrument
  defect** — daily-ATR stops sized every cell to 0 contracts; no market
  information revealed (`VERDICT-2026-07-06.md`).
- **v2** (sealed 2026-07-06, hash `12ca0a32…`): ORB with range-height
  stops + validity gates. Verdict: **validated NO-GO** — family-level
  failure, best cell 0.187 vs 0.55, in-sample 0.03–0.04, null 0.000 while
  trading (`VERDICT-2026-07-06-v2.md`). Family 1 is closed forever.
- **v3** (this document): a NEW family — the failed-breakout fade —
  chosen via the feasibility-first program: FEASIBILITY.md (the required
  edge frontier) and DIAGNOSTICS.md (dev-fold screening: E[R]
  +0.23/trade unconditioned on both instruments). Grid: 9 cells vs
  Family 1's 128. Runner fix sealed with it: combined sweeps keep true
  grid geometry (1-D re-indexing had made G4's plateau_cells=5
  structurally unsatisfiable).

The seal freezes this file's git hash into every run's provenance
(`docs/PREREG.sealed`); nothing may be edited after results are read.
Departures require a new dated version and a re-run.

---

## 1. What we optimize (fixed — unchanged since v1)

The **literal challenge rules** as scored objective. `ChallengeState`
implements them; every run's EOD ledger feeds the same state machine.
Reported together, never in isolation: P(pass) · P(breach) · median days
to outcome · profit distribution · fuel-gauge trajectory.

Rule values (verified; RULES.md): account $50,000 · target **+$3,000** ·
EOD trailing DD **$2,000** (locks at start once cleared) · daily guard
$1,000 = intraday lockout, never a failure · min 1 trading day · no eval
consistency · 30-micro position cap. **Tier confirmed by measurement**
(FEASIBILITY.md): the sibling "Advanced" geometry clears fewer
feasibility cells (110/144 vs 123/144) — plan-shopping is closed.

## 2. Strategy family (fixed): the failed-breakout fade

Semantics (implemented in `occams/fade.py`, 10 TDD tests, mirroring the
dev screening one-for-one):

- **Setup**: the 15-minute opening range forms (30-minute ranges measured
  strictly worse on dev folds — excluded). The first side to break
  defines the setup; one setup per day, day-flat.
- **Breakout**: first bar high strictly above the range high (or low
  below the low). **Failure**: first bar close back inside the range.
  The extreme includes the failure bar.
- **Entry**: stop order at the boundary, armed only after the breakout —
  fills on the re-cross (fade short at high − slippage; mirrored long).
  Executable live: the breakout alert arms the order; no screen-watching.
- **Stop**: extreme ± `k_stop` × height (gap-opens fill worse).
  **Target**: the far side of the range (no price-improvement credit).
  Same-bar stop+target = stop first. EOD force-flat at the last close.
- **Sizing**: true per-contract loss (stop distance from actual entry +
  exit slippage + both commissions); risk **$175**; stand-aside floor;
  30-micro cap. Sub-tick stops and degenerate ranges are stand-asides.

The sealed grid — **9 cells** (both axes dev-motivated, DIAGNOSTICS.md):

| Param | Grid | Notes |
|---|---|---|
| `range_minutes` | {15} | fixed — 30 was strictly worse everywhere on dev |
| `k_stop` | {0.2, 0.25, 0.33} | stop beyond the extreme, in range heights |
| `width_max` | {None, 0.30, 0.25} | ABSOLUTE height/ATR ceiling — sealed numbers, never in-sample quantiles; None = unfiltered |

Fixed, not searched: risk $175 · one trade/day (by construction) ·
target = far side (mid rejected: FEASIBILITY.md says asymmetry is the
lever; mid halves R) · **horizon 90 trading days** (Phase A: the 90-day
frontier is where this family's dev expectancy lands; 120 prices out).

## 3. Baselines (fixed)

1. **The fade-vs-follow coin null** (`make_fade_null_strategy`): at the
   SAME failure moment, with the SAME distances and sizing, a per-day
   deterministic coin (seed, date) picks fade or follow. G2 therefore
   measures the **directional edge alone** — geometry, timing, and risk
   management are identical by construction. Sealed null parameters:
   k_stop = 0.25 (the grid median), width_max = None. Mean over seeds
   {11, 12, 13, 14, 15}.
2. **Do-nothing** — P(pass) = 0, for the plots.

## 4. Data, folds & the contamination ledger (fixed)

- **Instruments:** MES and MNQ, both mandatory, judged independently.
- **Folds:** identical arithmetic to v2 — per instrument, first 60% dev ·
  next 20% OOS · final 20% lockbox (2019-05 → 2026-07 continuous 1-min).
- **Contamination ledger (read before sealing):**
  - v1/v2 verdicts exposed ORB per-fold statistics on ALL folds
    (2019–2026). Family-conditional leakage into Family 2: weak.
  - Phase B read **dev folds only** for the fade (that is what dev folds
    are for); OOS and lockbox have never been read for this family.
  - Consequence, sealed: the historical lockbox is **advisory** for
    Family 2; the **binding lockbox is prospective** — the 60–90-day
    paper window (§8), data that cannot have been mined because it has
    not happened. A pre-2019 ES/NQ purchase was considered and
    **descoped**: the hypothesis is already generated, so fresh dev
    ground adds nothing after the fact.

## 4b. Validity gates (carried from v2, unchanged)

Zero-traded-day sweeps or nulls abort (`ValidityError`) as INSTRUMENT
FAILURE — never a NO-GO. Positive controls run at realistic volatility
with a true dead world (`kick_scale=0`).

## 5. Robustness splits (fixed)

Winner's P(pass) reported by year bucket, volatility tercile, and
instrument; MES and MNQ must clear the gates independently.

## 6. Go/no-go gates (fixed BEFORE results — unchanged values since v1)

All four on OOS **and** the (advisory) lockbox:

- **G1**: P(pass) ≥ **0.55** · **G2**: ≥ null + **0.15** ·
  **G3**: P(breach) ≤ **0.30** · **G4**: plateau ≥ **5** neighbours
  within **0.05** (true grid geometry — the 3×3 grid's interior cell has
  9 Chebyshev-1 neighbours; the v3 runner fix makes G4 honest).

Fail any → validated no-go. A GO additionally requires the paper gate
(§8) before any fee.

## 7. Economics gate (only if G1–G4 hold)

- `E[attempts] = 1/P(pass)` (weakest instrument) ·
  `months_per_attempt = ceil(median_days/21)` (slowest instrument) ·
  `E[cost] = E[attempts] × months × $119 + (E[attempts]−1) × $109`.
- **funded_value is cadence-matched and sealed as a deterministic rule**
  (`funded_value_for`): keyed on whether the winning cell is
  width-filtered — never a post-hoc choice.
  - **open** (unfiltered, ~1.8 setups/day across both instruments,
    green-day rate ≈ 0.55/day): 5×$200 days per ~9 trading days → ~2
    payout cycles/month × ~$235/request × ~3-month funded median × 0.8
    operational haircut ≈ **$1,100**.
  - **filtered** (~0.6 setups/day): cycle ≈ 19 trading days → ~3.3
    cycles over 3 months × ~$200 × 0.8 ≈ **$500**.
- Proceed only if `funded_value > 2 × E[cost]`. Stated implication: a
  filtered winner must be FAST and NEAR-CERTAIN (E[cost] < $250);
  an open winner needs E[cost] < $550. GO is meant to be hard.

## 8. What ends or advances the project (fixed)

- Any gate fails on OOS → validated no-go; write it up; no fee.
- Gates pass, economics fail → **GO-RESEARCH**: documented, no fee.
- GO → **the prospective paper gate is the true lockbox**: 60–90
  calendar days, ≥ 10 trades, parity kill thresholds as sealed in v2
  (mean drift ≤ −$5/trade or mean |drift| > $10/trade after ≥10 trades →
  no live attempt). Only paper-gate survival buys the first month.
- Live attempt, either way → written up as an experiment.

## 9. What this document does NOT commit to

Any parameter value inside the grid; any belief about which regime
works; any post-hoc gate, threshold, or funded-value adjustment after
results are read.

---

**Seal instructions:** commit, then `git rev-parse HEAD:docs/PREREG.md`
into `docs/PREREG.sealed`. Every report carries the content hash; a
mismatch voids the run.
