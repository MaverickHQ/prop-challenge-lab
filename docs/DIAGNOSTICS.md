# DIAGNOSTICS — failed-breakout anatomy (Phase B, dev folds ONLY)

Universe: dev fold = first 60% of tradable days per instrument (verdict split), event days excluded — the same day-universe the sealed pipeline trades. Conservative outcomes: same-bar stop+target = loss; 'eod' = neither hit by close.

## MES · 15-min range · dev 2019-05-24 → 2023-08-24 (911 days)

- breakout: 910/911 days (100%) · **failure rate: 851/910 (94%)** · no-breakout 1
- setups/day (fade frequency): 0.93

| stop k | naive R | win | loss | eod | WR | mean ext | **true mean R** | **E[R]/trade** | E[R] eod=loss |
|---|---|---|---|---|---|---|---|---|---|
| 0.25 | 4.0R | 327 | 499 | 25 | 39.6% | 0.31 | **2.38R** | **+0.274** | +0.237 |
| 0.33 | 3.0R | 342 | 479 | 30 | 41.7% | 0.31 | **1.96R** | **+0.190** | +0.148 |
| 0.5 | 2.0R | 392 | 414 | 45 | 48.6% | 0.31 | **1.43R** | **+0.164** | +0.102 |

Width/ATR conditioning (k=0.25):
- narrow (n=284): WR 43.2% · E[R]=+0.296
- mid (n=283): WR 38.8% · E[R]=+0.261
- wide (n=284): WR 36.6% · E[R]=+0.154

Width/ATR conditioning (k=0.5):
- narrow (n=284): WR 53.4% · E[R]=+0.211
- mid (n=283): WR 47.4% · E[R]=+0.095
- wide (n=284): WR 44.7% · E[R]=-0.000

## MNQ · 15-min range · dev 2019-05-24 → 2023-08-24 (916 days)

- breakout: 916/916 days (100%) · **failure rate: 858/916 (94%)** · no-breakout 0
- setups/day (fade frequency): 0.94

| stop k | naive R | win | loss | eod | WR | mean ext | **true mean R** | **E[R]/trade** | E[R] eod=loss |
|---|---|---|---|---|---|---|---|---|---|
| 0.25 | 4.0R | 319 | 497 | 42 | 39.1% | 0.26 | **2.51R** | **+0.291** | +0.228 |
| 0.33 | 3.0R | 335 | 475 | 48 | 41.4% | 0.26 | **2.05R** | **+0.206** | +0.139 |
| 0.5 | 2.0R | 384 | 402 | 72 | 48.9% | 0.26 | **1.49R** | **+0.194** | +0.094 |

Width/ATR conditioning (k=0.25):
- narrow (n=286): WR 44.4% · E[R]=+0.341
- mid (n=286): WR 36.2% · E[R]=+0.176
- wide (n=286): WR 36.4% · E[R]=+0.166

Width/ATR conditioning (k=0.5):
- narrow (n=286): WR 54.0% · E[R]=+0.221
- mid (n=286): WR 45.3% · E[R]=+0.037
- wide (n=286): WR 47.0% · E[R]=+0.024

## MES · 30-min range · dev 2019-05-24 → 2023-08-24 (911 days)

- breakout: 909/911 days (100%) · **failure rate: 850/909 (94%)** · no-breakout 2
- setups/day (fade frequency): 0.93

| stop k | naive R | win | loss | eod | WR | mean ext | **true mean R** | **E[R]/trade** | E[R] eod=loss |
|---|---|---|---|---|---|---|---|---|---|
| 0.25 | 4.0R | 275 | 517 | 58 | 34.7% | 0.22 | **2.62R** | **+0.195** | +0.113 |
| 0.33 | 3.0R | 301 | 471 | 78 | 39.0% | 0.22 | **2.13R** | **+0.183** | +0.074 |
| 0.5 | 2.0R | 341 | 407 | 102 | 45.6% | 0.22 | **1.53R** | **+0.136** | -0.000 |

Width/ATR conditioning (k=0.25):
- narrow (n=284): WR 36.7% · E[R]=+0.147
- mid (n=283): WR 33.0% · E[R]=+0.050
- wide (n=283): WR 34.4% · E[R]=+0.143

Width/ATR conditioning (k=0.5):
- narrow (n=284): WR 48.0% · E[R]=+0.093
- mid (n=283): WR 42.6% · E[R]=-0.046
- wide (n=283): WR 46.2% · E[R]=-0.049

## MNQ · 30-min range · dev 2019-05-24 → 2023-08-24 (916 days)

- breakout: 910/916 days (99%) · **failure rate: 849/910 (93%)** · no-breakout 6
- setups/day (fade frequency): 0.93

| stop k | naive R | win | loss | eod | WR | mean ext | **true mean R** | **E[R]/trade** | E[R] eod=loss |
|---|---|---|---|---|---|---|---|---|---|
| 0.25 | 4.0R | 239 | 521 | 89 | 31.4% | 0.19 | **2.73R** | **+0.121** | +0.004 |
| 0.33 | 3.0R | 255 | 489 | 105 | 34.3% | 0.19 | **2.21R** | **+0.070** | -0.063 |
| 0.5 | 2.0R | 289 | 426 | 134 | 40.4% | 0.19 | **1.58R** | **+0.029** | -0.133 |

Width/ATR conditioning (k=0.25):
- narrow (n=283): WR 35.1% · E[R]=+0.135
- mid (n=283): WR 30.3% · E[R]=+0.003
- wide (n=283): WR 28.5% · E[R]=-0.127

Width/ATR conditioning (k=0.5):
- narrow (n=283): WR 42.7% · E[R]=-0.016
- mid (n=283): WR 40.1% · E[R]=-0.123
- wide (n=283): WR 37.9% · E[R]=-0.260


## Phase B synthesis (2026-07-06) — HYPOTHESIS SURVIVES, marginally

**The setup exists at the right frequency and shape.** Breakouts happen
on ~100% of days and **~94% of them fail** (re-enter the range before
close) — the fade fires ~0.93 setups/day, exactly the 0.5–1/day the
frontier wants. The naive "2R" framing was corrected: entry at the
boundary with the stop k x height BEYOND the extreme makes true risk
(ext + k) x height; mean extension ~0.19–0.31 heights.

**Where the numbers land (conservative: eod-as-loss):**

- Best geometry: **15-min range, k=0.25** — true R ~2.4–2.5, WR ~39–40%,
  E[R] +0.23 (MES) / +0.23 (MNQ) per trade, sign-positive on BOTH
  instruments and every k on 15-min ranges. 30-min ranges are strictly
  worse everywhere → dropped.
- **Width condition adds real lift**: narrow-width days (height/ATR
  bottom tercile) run WR 43–44% at ~2.4R → E[R] +0.30/+0.34; wide days
  decay toward zero. Monotone-ish on MES; consistent sign on MNQ.
- **Costs** take ~0.06–0.11R/trade → net unconditioned ≈ +0.13–0.17R;
  net narrow-conditioned ≈ +0.20–0.28R.

**Frontier placement (the honest part):** the 60-day frontier needs
~+0.35R/trade at this shape — the fade does NOT reach it unconditioned.
It sits **at/near the 90-day frontier (~+0.20–0.25R needed)**, where
Phase A also warned the economics gate binds (E[cost] $600–800). So the
modal verdict-#3 outcome is still no-go or GO-RESEARCH — but the
hypothesis has genuinely earned its grid: positive dev expectancy,
right shape, both instruments, structural mechanism (94% of breakouts
trap someone).

**Dev-mining caveats, recorded now:** (1) all numbers are dev-fold and
will shrink OOS; (2) tercile cutoffs are in-sample — PREREG v3 must seal
ABSOLUTE width thresholds (e.g. height/ATR <= 0.25/0.30), never
quantiles; (3) eod-as-loss is conservative, real EOD exits add back a
little; (4) first setup per day only, no re-entries.

**Family-2 grid this implies (Phase C, ~3 axes, 12–18 cells):**
15-min range fixed · k in {0.2, 0.25, 0.33} · width filter in {off,
<=0.30, <=0.25} · target = far side (mid rejected: feasibility says
asymmetry, and mid halves R) · max_trades=1 by construction · horizon
90d · both instruments mandatory. **Build item: the simulator needs
LIMIT-entry support (fade enters on a limit as price returns; the
engine currently models stop entries only) — TDD.**
