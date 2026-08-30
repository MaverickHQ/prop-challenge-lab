# RULES — verified rule reference (evaluation + funded/payout layer)

Deep-research passes 2026-07-05 (two rounds; round 2 completed the votes cut
by the session cap): every item below marked **VERIFIED** survived 3-0
adversarial verification against the venue's **official help center and
site** (the strongest evidence class). Source URLs and exact quotes live in
git-ignored `venue.local.md` — this file stays generic per the privacy rule.
Behavioral/base-rate evidence (the community layer) is synthesized in
[EVIDENCE.md](EVIDENCE.md).

---

## 1. Evaluation — $50k "Zero-tier" plan (ours, P3)

| Rule | Value | Status |
|---|---|---|
| Profit target | **$3,000** | VERIFIED |
| Maximum Loss Limit (EOD trailing) | **$2,000** — trails EOD balance high; locks at start once cleared | VERIFIED (2026-07-02/04) |
| Daily Loss Guard (intraday) | **$1,000** — real-time incl. unrealized; liquidation + lock until 6PM ET; **not a failure** | VERIFIED (2026-07-04; engine corrected `8832a10`) |
| Max position | **3 contracts** (minis; micros scale 10:1) | VERIFIED |
| Min trading days | **1** — no consistency rule in evaluation; a one-day pass is allowed | VERIFIED |
| **Cost** | **$119/month subscription** + **$109 per reset** | VERIFIED — *corrects our earlier ~$79 one-time assumption* |
| Sibling plans (eval) | Premium/Advanced carry a **50% consistency rule** in evaluation | VERIFIED |

## 2. Funded ("Qualified") — the payout layer

This is the layer we lacked before the research pass. All VERIFIED:

| Rule | Value |
|---|---|
| Payout qualification | **5 winning trading days of ≥ $200 profit each** per request (non-consecutive OK) |
| Request frequency | up to **4 payout requests/month** |
| Request size | **≤ 50% of profits** per request · min $200 · **cap $1,500 per payout on 50k** ($1,000–$2,500 range by account size; Advanced reaches $15k) |
| Consistency (funded, Zero only) | **40% rule** — no single day ≥ 40% of net profits *since last payout request*; blocks *payout eligibility* only. VERIFIED (3-0): violation **delays, never breaches** — keep trading to dilute the big day below 40%; the rule **resets after each payout request** |
| News restriction (funded, Zero only) | **no entries ±2 min around high-impact calendar events**; evaluations and Premium/Advanced funded have none |
| Senior-tier promotion | at **+$40,000 payable balance or 5 payout cycles**, review for the firm's senior program |

## 2b. Conduct rules that void payouts or accounts (VERIFIED primary unless noted)

| Rule | Value | Our compliance |
|---|---|---|
| Automation | **Full automation (AI/bots) prohibited on all account types.** Semi-automated signals allowed **only if a human places, monitors, and manages every order** | By construction — human executes every order |
| Tick-scalping | Pattern ban: holds **< 2 min AND < 10 ticks** profit (pattern-of-behavior rule, not per-trade) | 1.5R targets hold far longer; re-check fill logs at paper gate |
| Session flat | **All positions closed by 4:20 PM ET daily**; no overnight/weekend holds (halt Fri 5PM–Sun 6PM ET) | Day-flat by design |
| News (funded, Zero only) | No orders ±2 min around high-impact calendar events; **first violation = window profits voided + payout denied, account survives with warning**; repeats breach | Whole-day calendar blocks exceed the window |
| MLL mechanics | Starts **−4%** of balance; trails **EOD only, never intraday**; **locks permanently at starting balance**. Nuance: floating equity touching the MLL level intraday DOES liquidate — the *level* only moves EOD | Engine implements exactly this (`rules.py`) |
| Activity floor (funded) | ≥ 1 trade every 10 trading days — SECONDARY, unverified |  |
| Funded-account reset | ≈ **$499** (vs $109 evaluation reset) — SECONDARY, unverified | Feed worst-case into funded economics |

One aggregator claims our tier's max-loss is **fixed** (non-trailing) — contradicted 3-0 by the venue's own MLL doc ("EOD trailing on all accounts"). Engine follows the primary; if the aggregator were somehow right, our model is strictly conservative.

## 3. Resolved by research round 2 (2026-07-05) — formerly PENDING

- **VERIFIED (3-0, two primary pages):** Premium/Advanced *funded* accounts have **no consistency rule at all** — the funded consistency gate is unique to Zero (the mirror of evaluation, where Premium/Advanced carry 50% and Zero carries none).
- **VERIFIED (3-0):** consistency violation on funded Zero **delays payout eligibility only** — account not breached, payout button disabled until the ratio is satisfied; rule resets per payout request.
- **VERIFIED:** industry calibration from a major competitor firm's own 2025 disclosure — **16.8%** of evaluation attempts completed (3-0) · **51.8%** of individuals passed at least once, i.e. ~3 attempts per passer (3-0) · **33.3%** of funded traders received a payout in-window (2-1; dissent only on "never" phrasing). Full funnel analysis in [EVIDENCE.md](EVIDENCE.md) §1.

## 4. What this changes for our design (level-400 implications)

1. **Cost model is time-based, not per-attempt.** E[cost] = months × **$119** + resets × **$109** — a fast fail is cheaper than a slow one, and a slow *pass* costs more than a quick one. The economics gate (`Protocol.attempt_fee`) now carries $119/month as the unit; the full subscription-time model is a **seal-time rework item**.
2. **Our cadence fits the payout gate almost perfectly.** One clean 1.5R win at our sizing ≈ $220–290 net — clears the **$200 winning-day bar** in a single trade. Qualification ≈ any 5 green days; the 40% funded-consistency rule favors exactly our many-small-days profile.
3. **The $1,500/payout cap bounds `funded_value`.** Realistic funded EV = (payout cadence achievable at our cadence) × $1,500-capped requests × 50%-of-profit rule × **~0.8 operational haircut** (payout latency, KYC/review friction, conduct-classification risk — EVIDENCE.md §4) — now computable from verified numbers instead of a placeholder. Feed into the economics gate at seal.
4. **Funded news rule already satisfied**: our whole-day calendar blocks exceed the ±2-min window.
5. **Evaluation has NO consistency rule** — a lucky big day may pass early; our design doesn't rely on it but doesn't need to avoid it either.
