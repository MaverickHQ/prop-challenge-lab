# Strategy catalogue — every family, scored against the requirement

**Dated 2026-08-01.** Written before any of it is tested, so the scoring
cannot be back-fitted to results.

## The requirement being scored against

From `FEASIBILITY.md`, which mapped the frontier before any family was
built:

> net R **1.5–2.0+** · WR **≥ 45–52%** · **0.5–1 trade/day** · median pass
> ≤ ~50 days · P(pass) ≥ 0.55 (0.65 for economics) · $175 risk, 60–90 days

**Asymmetry is the lever, not hit rate.** At 2.0R the bar is WR 45%; at
1.5R it is 52.5%; at **1.0R it is 60–65%**. The classic high-win-rate,
low-R mean-reversion scalp is the *hardest* corner on the map. Any family
whose natural shape is "win small, often" is scored down on arrival — not
from taste, but because the frontier says so.

Two hard filters added since:

- **Entry obtainability** (E1/#3a). A family whose entry price cannot be
  produced by a placeable order is dead regardless of its statistics. This
  killed the fade after it had already passed a sealed verdict.
- **Cost survivability** (E3). Commission runs 0.05–0.09R per trade at our
  sizes. A family needing many trades pays it many times.

---

## Scoring key

**R-shape** — does the family *naturally* produce 2R+? · **Freq** — trades
per day near the 0.5–1 target? · **Obtainable** — can the entry be placed?
· **Data** — do we already own what it needs? · **Mechanism** — is there a
reason it should work, statable before testing? · **Crowding** — how mined
is it?

---

## A. Breakout / momentum

| family | R-shape | Freq | Obtainable | Data | Mechanism | Crowding | verdict |
|---|---|---|---|---|---|---|---|
| **Opening-range break** | good | ok | yes | own | weak | extreme | **TESTED — DEAD** (#1, #2) |
| **Prior-day high/low break** | good | low | yes (stop) | own | fair — a level with a day of memory, not 15 min | high | **TEST** |
| **Volatility contraction → expansion** | very good | low | yes (stop) | own | **HALF REFUTED** — it clusters, it does not mean-revert at 1 day | moderate | **TESTED — DEAD** (X1: r = -0.089, CI excludes zero, *wrong direction*) |
| **Session-extreme break** | good | ok | yes | own | weak — same shape as ORB | extreme | skip |

## B. Mean reversion / fade

| family | R-shape | Freq | Obtainable | Data | Mechanism | Crowding | verdict |
|---|---|---|---|---|---|---|---|
| **Failed-breakout fade** | good | ok | **NO** | own | fair | high | **TESTED — ARTIFACT** (#3a) |
| **VWAP reversion** | **poor** — wins small | high | yes (limit) | own | fair | extreme | skip — wrong corner of the frontier |
| **Band reversion** | **poor** | high | yes | own | weak | extreme | skip |
| **Gap fill** | fair | **low** | yes | own | fair — gaps statistically fill, but slowly | high | marginal |
| **Extreme-move fade (n-sigma)** | good | very low | yes (limit) | own | fair — overreaction | moderate | marginal |

## C. Trend / continuation

| family | R-shape | Freq | Obtainable | Data | Mechanism | Crowding | verdict |
|---|---|---|---|---|---|---|---|
| **Second push after failure** | good | ok | yes | own | fair | moderate | **TESTED — DEAD** |
| **Higher-TF trend + intraday entry** | **very good** | low | yes | own | **fair-strong** — conditioning on a slower signal is the classic multi-timeframe argument | moderate | **TEST** |
| **MA pullback** | fair | ok | yes | own | weak | extreme | skip |

## D. Event / time-of-day

| family | R-shape | Freq | Obtainable | Data | Mechanism | Crowding | verdict |
|---|---|---|---|---|---|---|---|
| **Overnight gap behaviour** | good | ok | yes | own | **REFUTED** — absorption IS instant here; ~23h trading means no information vacuum | moderate | **TESTED — DEAD** (X2: r = +0.002, both folklore directions die) |
| **Overnight (Globex) session** | fair | ok | yes | own | fair — thinner book, fewer participants | **low** | **TEST** |
| **Lunch-lull fade** | **poor** | ok | yes | own | fair | high | skip — wrong corner |
| **Close/MOC imbalance** | fair | low | yes | **NO** — needs imbalance feed | strong | high | blocked on data |
| **Event-day reaction** | good | very low | yes | own | fair | high | **inverts our own rule** — we currently EXCLUDE these days |

## E. Statistical / cross-sectional

| family | R-shape | Freq | Obtainable | Data | Mechanism | Crowding | verdict |
|---|---|---|---|---|---|---|---|
| **MES vs MNQ relative strength** | fair | ok | yes | own | **fair-strong** — two correlated instruments diverging is a real signal, and it is the only *cross-sectional* idea available to us | moderate | **TEST** |
| **Day-of-week / seasonality** | poor | n/a | n/a | own | **weak** — mostly data-mining | — | skip |
| **Overnight vs intraday decomposition** | n/a | n/a | n/a | own | descriptive | — | context only |

## F. Order flow — the one non-public input

| family | R-shape | Freq | Obtainable | Data | Mechanism | Crowding | verdict |
|---|---|---|---|---|---|---|---|
| **Aggressor imbalance → direction** | ? | ok | yes | own (525 sess) | **strong** | **low** | **H5 — suggestive, underpowered** |
| **Absorption at levels** | ? | low | yes | needs MBP-10 | strong | low | blocked on data (~$585) |
| **Large-print / size-distribution shift** | ? | ok | yes | own | fair | low | **TESTED — UNRESOLVED** (X3: r = +0.026, but CI runs to +0.113 — the sample cannot see a large effect) |

## G. ICT / smart-money concepts

Added 2026-08-09 from a beginner playbook naming four strategies. They are
**not four families.** Structurally:

| playbook strategy | trigger | entry |
|---|---|---|
| 2022 Mentorship Model | sweep of *any* liquidity -> MSS | limit at FVG / CE |
| Judas Swing | sweep of *session/Asia* range -> MSS | limit at FVG / CE |
| Turtle Soup | sweep of *prior day/week* extreme -> MSS | limit at FVG / CE |
| Silver Bullet | *no sweep* — first displacement in a fixed window | limit at FVG / CE |

Three differ only in **which level is swept**. All four share one fill
mechanism. So this is **two triggers and one entry**, and registering four
hypotheses would spend alpha four times for one-and-a-half questions.

**Turtle Soup is our failed-breakout fade** — the family already killed on
obtainability (#3a). ICT proposes a *different order* for it.

| family | R-shape | Freq | Obtainable | Data | Mechanism | Crowding | verdict |
|---|---|---|---|---|---|---|---|
| **Sweep -> reversal (2022 / Judas / Turtle Soup)** | **very good** — stop beyond the swept extreme, target at opposing liquidity | good — 1-2/day, well matched to our 0.5-1 target | **yes (limit)** — by construction; a retracement level is away from price in the favourable direction | own | fair — a story about resting stops, not a statistical property | **extreme** | **TESTED — DEAD** (P2: drift -0.008 ATR, CI crosses zero) |
| **Displacement -> continuation (Silver Bullet)** | very good | good — 1/window | **yes (limit)** | own | fair | **extreme** | **TESTED — DEAD** (P1: d = -0.0015) |
| **FVG / CE as an entry level** | n/a — a *fill mechanism*, not a family | n/a | **yes** | own | fair | extreme | **TESTED — DEAD.** No forward information; mirror level fills MORE often than the gap |
| **SMT divergence** | n/a — a *filter* | n/a | yes | own | fair-strong | high | **fold into E-group** as its missing definition |
| **Order Block / Breaker** | ? | ? | ? | own | **unfalsifiable** — "last candle before a powerful move"; *powerful* undefined | extreme | **declined — not mechanisable** |
| **Draw on Liquidity / HTF bias** | ? | ? | ? | own | **unfalsifiable** — "the liquidity price is *likely* to reach next" is the trader deciding, in hindsight | extreme | **declined — not mechanisable** |
| **Killzone timing** | n/a | n/a | yes | own | fair — session structure is real | extreme | **not run** — no primitive survived to condition |

### Why this is tested as primitives rather than as strategies

All four strategies enter at an FVG. **If a fair value gap carries no
forward information, all four die on one register entry** rather than four.
Same for the sweep: one measurement speaks to 2022, Judas and Turtle Soup
at once. Two hypotheses resolve eight.

Both are measured **strategy-free** — signed forward return, no entry
assumption, no stop, no target — because a P&L outcome is exactly how the
fade's defect got in.

### What is mechanisable, and what is not

FVG (3-bar imbalance, midpoint), CE, killzone clock times, OTE 62-79% and
SMT are **fully mechanical**. MSS is semi-mechanical — it needs a swing
definition, which is a free parameter and must be pinned before running.
Order Block and Draw-on-Liquidity are **not** mechanisable as stated.

**Stated up front:** the mechanised version is a *weaker* claim than the
discretionary one. A negative here does not refute ICT-as-practised; it
refutes the part of it that can be written down.

### Declined from the playbook, with reasons

- **The 14-day ramp-up plan.** "Refine rules weekly" on the same data is the
  garden of forking paths with a curriculum around it. Its good parts (one
  model, attempts cap, daily stop, day-flat) already exist in our rules and
  are tighter.
- **Scale-outs / partials at 1R.** Truncates the right tail, keeps the whole
  left tail — it *lowers* net R, and asymmetry is the lever the frontier
  identified. Also pays commission twice at 0.05-0.09R a fill.
- **"Aggressive market entry after MSS."** Z0 already priced that order:
  -0.076R MES, -0.012R MNQ.
- **Per-trade risk <=1%, daily DD 2%.** Looser than our own rules. Ours govern.

### RESULT (2026-08-09) — both primitives dead, eight strategies with them

Full write-up: [`ICT-WRITEUP.md`](ICT-WRITEUP.md).

| | primary | 95% CI | Cohen d | floor |
|---|---|---|---|---|
| **P1** FVG -> CE continuation | **-0.00036 ATR** | [-0.0104, +0.0090] | -0.0015 | 0.07 |
| **P2** sweep -> reversal *(corrected)* | **-0.00829 ATR** | [-0.0195, **+0.0026**] | -0.034 | 0.07 |

P2's raw reading was -0.159 ATR at d = -0.43 — six times the detectable
floor. **It was 94.8% reference price.** Measuring from the swept level
builds the penetration distance into the answer: a market that froze the
instant it swept would still print a large continuation reading. The control
decomposition is an exact identity, so it could not have produced a better
number.

**The prior below was written before any of this ran. It held.**

### The prior, before running

Five columns score well; two do not. **Crowding is the worst on the map** —
more followed than ORB, with FVG auto-detectors on every charting platform.
And we already own three pieces of counter-evidence: `H-STOPWIDTH` found
expectancy **flat** across a four-rung stop ladder, so "tighter stop -> better
R" has been probed on this family and did nothing; R1 measured the gross
signal at +0.02-0.04R against +0.25R needed; Z0 priced four orders on it, all
negative.

The one honest argument in its favour: crowding at a **limit** level can be
self-fulfilling — resting orders *are* the liquidity — whereas crowding at a
**breakout** is self-defeating, since every stop sits in the same place. ICT
sits on the favourable side of that asymmetry. That is the whole case.

## H. Indicator strategies — the mechanism collapse (2026-08-09)

Asked whether the lab can test moving averages, Bollinger bands and the
rest. It can — two indicators already exist and are correct (real VWAP,
`strategy.py:91`; ATR, `loader.py:72`, which never sees its own day). Build
tasks: TASKS.md §I.

**But ~20 named indicators express about four mechanisms**, and scoring
them as twenty families would spend twenty register entries on four
questions:

| mechanism | indicators | verdict |
|---|---|---|
| **volatility is compressed** | BB width, ATR ratio, Donchian width, NR7 | **live — this is X1**, the best-scoring family on the map |
| **a slower series has direction** | MA slope, ADX, HTF close vs MA | **live — this is X4** |
| **momentum state changed** | MA cross, MACD, RSI through 50 | not queued — weak mechanism, extreme crowding |
| **price is N sigma from a moving centre** | BB touch, Keltner, %B, z-score | **declined** — see B/C above |

**Two of the four queued experiments are already indicator strategies**,
named by mechanism rather than by indicator. An indicator is therefore a
**predictor swap inside an existing hypothesis, not a new one** — provided
the swap is declared before the run, because choosing the best of four
afterwards is a four-fold multiplicity charge.

**The declines stand and the reason is unchanged.** Band reversion, MA
pullback and VWAP reversion score poor on R-shape and extreme on crowding.
Asymmetry is the lever: 2.0R needs WR 45%, **1.0R needs 60-65%**, and
win-small-often is the hardest corner on the map. What is *not* declined is
the compression and conditioner readings of the same arithmetic.

**One thing worth stating in this family's favour.** A band level is
computed from prior closes, so a limit resting there is **genuinely
obtainable** — unlike the fade, whose entry no order could produce. Band
touch is one of the cleanest entries available to us. It is the *R-shape*
that kills it, not the fill.

---

## What the scoring says

**Four families are worth testing, in this order:**

1. ~~**Volatility contraction → expansion**~~ — **TESTED AND DEAD, 2026-08-09**
   ([`X1-WRITEUP.md`](X1-WRITEUP.md)). Not a null: a **reversal**. Compression
   predicts *more* compression — r = **−0.089**, CI [−0.135, −0.043],
   monotone across buckets (0.960 → 0.827 ATR from 0 to 3+ contracting
   sessions). Volatility clustering is *confirmed*; the mean-reversion half
   the strategy needed is not there at a one-day horizon. **The
   best-scoring family on the map died first**, which is what the
   catalogue's own prior said would happen.
2. ~~**Overnight gap**~~ — **TESTED AND DEAD, 2026-08-09**
   ([`X2-WRITEUP.md`](X2-WRITEUP.md)). r = **+0.002**, CI [−0.043, +0.048],
   0.04x the floor. Neither "gaps run" nor "gaps fill" survives. The gap is
   real (median 0.28 ATR) and predicts subsequent *volatility* (r = +0.163)
   but carries **no direction** — the market prices it completely at the
   bell.
3. ~~**Order-flow size/large-print**~~ — **TESTED 2026-08-09: UNRESOLVED,
   not refuted** ([`X3-WRITEUP.md`](X3-WRITEUP.md)). r = **+0.026**, but the
   CI runs to **+0.113** and the floor is 0.13 — the 525 sessions we own can
   only see a large effect. X1 and X2 were answers; **X3 is a measurement
   that ran out of data**, and it is the one place more data could still
   change an answer.
4. **Higher-timeframe trend conditioning** — the classic argument, and it
   is a *conditioner* on other families rather than a family alone.

**Then, lower confidence:** prior-day levels · MES/MNQ relative strength ·
Globex session.

**Explicitly skipped, with reasons rather than silence:** VWAP and band
reversion, lunch fade, MA pullback — all high-WR/low-R, which the frontier
identifies as the hardest corner to clear. Session-extreme break duplicates
ORB's shape. Day-of-week is dredging with a name.

**Blocked on data we have chosen not to buy:** MOC imbalance, absorption.

## The honest prior

Every family in A–E trades **public price levels on two of the most heavily
traded futures on earth**. R1 established the opening-range family carries
+0.02 to +0.04R gross against a +0.25R requirement. There is no strong
reason to expect a neighbouring family to be an order of magnitude better.

The realistic expectation is **most of these die**, and the value is that
they die cheaply, honestly, and on the record. Only **F** — order flow — is
information others are not all looking at, and it is the one axis where a
surprise is genuinely possible.
