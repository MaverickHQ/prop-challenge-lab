# EVIDENCE — how traders actually pass this class of challenge and get paid

Deep-research synthesis, 2026-07-05. Method: 5-angle web sweep → 18 sources
fetched → 90 falsifiable claims extracted → top 25 adversarially verified
(3 independent skeptic votes each) → **24 confirmed, 1 refuted**. Claims that
did not reach the verification round are labeled by evidence class below
(testimony / survey / affiliate) — they inform, they do not decide.
Venue-named citations live in git-ignored `venue.local.md`; rule values are
in [RULES.md](RULES.md). This file is the *behavioral and base-rate* layer.

Evidence classes used: **[V]** verified 3-0 against primary sources ·
**[V:2-1]** verified with one dissent · **[S]** secondary/survey, plausible
but unverified · **[T]** testimony (forum/review), unverified ·
**[A]** affiliate-conflicted, discount heavily.

---

## 1. The funnel — base rates every success story sits on top of

The only firm-disclosed numbers in the industry come from a major competitor
firm's own 2025 performance disclosure (regulatory-style disclaimer, cuts
against its marketing — credible floor):

- **16.8% of evaluation attempts** were completed successfully. **[V]**
- **51.8% of individuals** who attempted at least once passed at least once
  — the gap means the median passer buys **~3 attempts**. Persistence, not
  a first-try edge, produces most passes. **[V]**
- **33.3% of traders who reached funded status received a payout** in the
  measured window — i.e. roughly two-thirds of "funded traders" were never
  paid. **[V:2-1]** (dissent: "never" overstates — late-2025 cohort hadn't
  finished a payout cycle yet; it is "not paid in-window").

Independent aggregates agree on the shape: across ~300k accounts at 10 firms
(evaluation-platform vendor data), **~14% pass and ~7% of all challenge
buyers ever reach a payout**, with the average payout ≈ **4% of nominal
account size** [S]. Note the numbers compose: 16.8% × 33.3% ≈ **5.6% of
attempts end in a paid trader** — consistent with the ~7%-of-buyers figure.

Survivorship-bias mechanics, so we never argue from testimonials:
evaluation fees are **70–95% of revenue** at most retail prop firms [S];
average cumulative spend per trader ≈ **$4,270** with ~60% losing it [S];
review platforms mix solicited reviews and failed evaluators rarely
review [T]. Every public success story is drawn from the ~5% tail.

**Design implication:** our economics gate already treats E[attempts] > 1 as
the base case; these numbers say the honest prior on P(pass per attempt) for
the population is ~0.15–0.2, and our G1 bar (P(pass) ≥ 0.55) demands we be
*several times better than the population* before paying a fee. That is the
correct asymmetry.

## 2. What the paid minority does differently (behavioral layer)

All survey/testimony grade — no adversarial verification possible — but
three independent sources converge [S]:

| Behavior | Evidence | Our design |
|---|---|---|
| Trade **less** | passers ≈ 3.2 trades/day vs 6.8 for failures | ≤ 2/day, hard cap |
| **Under-risk** vs allowed | passers risk 0.5–1.0%/trade when rules permit 2–3× | 0.3–0.4% ($150–200 on $50k) |
| Self-imposed daily stop under the guard | recommended ≈ half the intraday limit | $500 vs $1,000 guard — exactly half |
| Respect the trailing floor mechanics | "most failures are floor-misunderstanding, not strategy failure" [S] | floor math is executable code (`rules.py`), not intuition |
| Buffer-building phase | reduce size when buffer < 30–40% of daily limit; stop when < one loss | fuel-gauge + daily stop; revisit sizing-by-buffer at funded stage |

Failure-mode split among failed evaluations [S, single survey]: **~50% hit
the trailing max-loss, ~20% hit the daily limit** — survival design, which
is our whole architecture, addresses the top two causes directly. Funded
mortality: **~half of funded accounts are dead or idle within ~90 days** [S].

**The behavioral evidence says our design already sits in the paid cohort's
profile — tighter, in fact.** Nothing here required a change.

## 3. The uncomfortable ORB evidence (read before P1)

The most load-bearing *skeptical* finding [S, quant blog with published
backtests]: **plain, unfiltered opening-range breakout showed no tradeable
edge after costs** in that site's backtests on the S&P 500 — best variant
≈ 0.04%/trade — and the same negative result on Nasdaq, gold, silver, and
crude futures. The same authors report the edge has degraded as the strategy
was popularized, and that only *filtered* variants retained edge (their
filtered NQ variant: 65% win rate, profit factor 2, 198 trades, live).

This is one source and their cost/parameter choices are not ours — it is
not a verdict on our grid. But it is the correct prior:

1. **A validated NO-GO is the expected outcome**, not a disappointment.
   The harness exists to measure exactly this, on our instruments, our
   costs, our objective (P(pass), not avg-return-per-trade).
2. It independently motivates the **vwap_filter axis** in the sealed grid —
   the one filter we allowed — since filtering is where any residual ORB
   edge appears to live.
3. G2 (edge ≥ null + 0.15) is precisely the test this evidence demands.
   Discipline cannot rescue a strategy that fails it (see §6).

## 4. The payout layer in practice (venue testimony, 2026)

From the venue's review stream and a due-diligence review [T]:

- **Payouts are real.** Multiple independent reviewers report first and
  repeat payouts completing, including one whose two denied requests were
  followed by an approved one once rule-compliant — denial is per-request,
  conduct-driven, and recoverable.
- **The dominant complaint is latency, not denial**: "approved" ≠ paid —
  reports of 4, 10, 16-day waits vs advertised ~1 day, plus accounts frozen
  "under review" blocking both payout and trading.
- **Operational risk exists independent of trading skill**: an admitted
  mass-termination error on funded accounts (later restored), KYC stalls of
  2+ weeks post-pass, one alleged suspension right at the payout-qualification
  threshold [T, single reviewer, uncorroborated].
- One payout denial for **tick-scalping stood despite video appeal** [A —
  affiliate source, but the anecdote is against-interest]. Conduct
  classification is the firm's call; the appeal process is not a safety net.

**Design implication:** `funded_value` at seal should carry an operational
haircut (latency + friction + classification risk) — multiply the modeled
payout stream by ~0.8 rather than assuming rulebook-perfect conversion, and
never model payout cadence faster than qualification + processing reality.

## 5. Conduct rules that void payouts (now in the engine's world-model)

Verified primary unless marked [RULES.md](RULES.md) §2b has the table:
no full automation (semi-automated is compliant **only if a human places,
monitors, manages every order** — our architecture by construction);
tick-scalping pattern ban (<10 ticks and <2 min holds); **flat by 4:20 PM
ET**; no weekend holds; funded-only news window (±2 min, our whole-day
blocks exceed it); ≥1 trade per 10 days activity floor [S]; funded-account
reset ≈ $499 [S, unverified]. One aggregator claims the 50%-of-profit
withdrawal cap relaxes after 30 cumulative winning days [S, single source,
unverified — treat as upside, don't model it].

**Contradiction flagged and resolved:** one discount-aggregator states our
tier's max-loss is *fixed* (non-trailing). The venue's own primary doc says
EOD-trailing on **all** accounts, locking at the starting balance — two
primary pages, 3-0 verified. The engine follows the primary. (If the
aggregator were right, our implementation is *conservative* — a fixed floor
is strictly easier than a trailing one.)

## 6. Discipline vs edge — the honest split (question 5)

The evidence separates cleanly:

- **Discipline is the survival variable.** It dominates evaluation failure
  (drawdown breaches ≈ 70% of failures) and funded mortality. It is fully
  engineerable, and ours is engineered: sizing from ruin math, hard daily
  stop at half the guard, ≤2 trades/day, day-flat, calendar blocks.
- **Edge is the qualification variable.** The payout gate (5 × $200+ days
  per request) cannot be reached by discipline alone — repeatedly clearing
  $200+ net on green days at our sizing (~$220–290 per clean 1.5R win)
  requires positive expectancy. §3 says expectancy is not free for bare ORB.
- Testimony that "risk management matters more than strategy" is true for
  *not dying* and silent on *getting paid*. Both gates bind. Our G1–G4
  test edge; our architecture supplies discipline. Neither substitutes.

## 7. Tier differences (question 4)

Rule differences are fully verified (RULES.md): our tier trades a monthly
fee + intraday guard + funded 40% consistency + funded news window against
the siblings' evaluation-phase 50% consistency + activation fee + higher
payout caps. **No outcome data distinguishing tiers exists anywhere in the
evidence** — no per-plan pass or payout rates. The one refuted claim of the
research pass (0-3) was an aggregator mangling exactly these tier details
(split percentage and first-withdrawal cap). Choose by rule fit, not by
claimed outcomes: our many-small-days profile is the one the 40% funded
consistency rule *favors*, and the $1,500/request cap is the binding
constraint on funded EV — both already in the design.

## 8. What this changes

1. **Nothing in the harness.** The verified rules were already encoded; the
   behavioral evidence matches the design we built. This pass adds
   calibration, not architecture.
2. **PREREG expectation-setting**: population P(pass) ≈ 0.15–0.2 per
   attempt; G1 demands ≥ 0.55. A NO-GO verdict would agree with the base
   rates, not contradict the project.
3. **`funded_value` at seal**: model = P(qualify: 5×$200 days) ×
   min($1,500, 50% × profit) per cycle, ≤4 cycles/month in principle but
   realistically 1–2 at our cadence, × ~0.8 operational haircut (§4),
   bounded by the 40% consistency rule (structurally satisfied by our
   profile). All inputs are now verified numbers.
4. **Conduct compliance is closed by construction** — human execution,
   day-flat by 4:20 PM ET, no weekend holds, whole-day news blocks, hold
   times > 2 min at 1.5R targets. The tick-scalping pattern rule is the
   only one worth re-checking against real fill logs at the paper gate.
