# Architecture

How the pieces fit, and why the seams are where they are.

The organising idea: **every layer can only hand the next one something it
could actually have known at the time.** Most of the design falls out of
enforcing that mechanically rather than by care.

---

## The pipeline

```
vendor bars
   │  loader.py · sessions.py · calendar.py · instruments.py
   ▼
TradingDay          date · session_bars · atr · range_bars · instrument
   │  strategy.py · fade.py · search.py        (a strategy is: day -> plan)
   ▼
DayPlan             entry · stop · target · size          — or NoTrade
   │  execution.py · sim.py                    (a plan -> fills, or refused)
   ▼
DayOutcome          pnl · traded · marks
   │  rules.py · payout.py                     (the literal rule arithmetic)
   ▼
ChallengeRun        status · final_equity · days_used
   │  harness.py                               (every viable start day)
   ▼
MCStats / PayoutStats
   │  estimators.py · stats.py · result.py     (the number and its meaning)
   ▼
Verdict → archive.py + audit.py               (append-only, with provenance)
```

Each arrow is a place a false result can enter. The gates sit on the arrows,
not at the end.

---

## Layers

### 1. Data — `loader.py`, `sessions.py`, `calendar.py`, `instruments.py`

Vendor bars become `TradingDay` objects. Session boundaries and the trading
calendar are applied here so nothing downstream has to know about holidays,
half-days or contract roll.

`TradingDay` carries `instrument` because **identity has to survive the
seam** — pooled analysis that has lost track of which instrument a row came
from cannot compute a design effect, and will silently double its own sample.

`range_bars` (the opening range, or whatever the strategy conditions on) is
separated from `session_bars` (what the simulator may trade). A strategy
physically cannot see bars it should not have: the lookahead defence is a
type boundary, not a convention.

### 2. Strategy — `strategy.py`, `fade.py`, `search.py`

```python
MakePlan = Callable[[TradingDay], DayPlan | NoTrade]
```

That is the entire contract. A strategy is a pure function from one day to
one plan. It returns `NoTrade` rather than `None`, so "decided not to trade"
is distinguishable from "crashed and returned nothing" — the distinction that
lets a structural zero be caught instead of reported as a null.

Strategies do not compute their own fills, costs, or statistics. They cannot
reach the register.

### 3. Execution — `execution.py`, `sim.py`

The layer that refuses.

```python
Order(kind, side, level)     # kind: LIMIT | STOP | MARKET
```

`validate(order, market)` rejects orders that could not exist at that moment
— a limit on the marketable side, a stop on the wrong side of price.
`fill(order, highs, lows, opens, placed_at)` derives what actually happened,
returning `None` if it never filled. A gapped stop fills at the open, never
at its level.

`obtainable(...)` is the gate: it enumerates **every** order kind and asks
whether *any* of them could have produced the assumed entry price. It returns
`(ok, explanation)`, and the explanation names what each order kind did
instead — which is what turns a refusal into a diagnosis.

`AUDITORS` maps a strategy family to its entry auditor.
`assert_entries_obtainable(family, ...)` raises `UnobtainableEntry` for an
unregistered family. **Default-deny:** an untested family is refused, not
waved through.

`Costs(multiplier, tick_size, commission_per_side, slippage_ticks)` — slippage
is adverse by construction. A simulator in which slippage can help is
measuring optimism.

### 4. Rules — `rules.py`, `payout.py`

The literal arithmetic of an evaluation programme, kept apart from every
strategy: `ChallengeConfig(account, target, trailing_dd, daily_guard,
min_days, consistency_frac)`.

`payout.py` models what happens *after* qualification — a stricter rule on an
account whose drawdown floor has already ratcheted up. Kept separate because
passing and getting paid are different events with different failure modes,
and collapsing them into one probability flatters weak strategies.

`payout.record_day` takes **cumulative** equity, not daily P&L. It is the
sharpest edge in the API and the one to check first if payout numbers look
wrong.

### 5. Evaluation — `harness.py`

`monte_carlo(days, make_plan, cfg, costs, horizon_days)` runs one attempt from
every start day that has a full horizon ahead of it.

Each day is simulated **once**; overlapping windows replay the cheap rules
engine over ledger slices. Identical results, roughly `horizon×` faster. This
is why `daily_ledger` and `run_from_ledger` are separate — the expensive part
(simulation) and the cheap part (rule arithmetic) run at different
frequencies.

`edge_shape` reads the P(pass)-versus-risk curve as a diagnostic: monotonic
means variance harvesting, and only an interior peak is consistent with a
real edge.

### 6. Measurement — `estimators.py`, `stats.py`, `result.py`

`stats.py` implements its own `rankdata`, `ppf` (Wichura AS241), Fisher-z
correlation intervals, Wilson proportion intervals, cluster and block
bootstraps. **scipy is a test-only dependency**, used as an oracle: the
package's own implementations are pinned against it rather than delegating to
it at runtime.

`estimators.py` requires `reference=` on every measurement — where does this
number start from?

- `AT_PRICE` — from the close. The only reference with no positional term,
  and the only one returnable as a bare number.
- `AT_LEVEL` / `AT_FILL` — from a named price or a derived fill. These
  **require `decompose=True`** and return `total = positional + drift`.

A measurement taken from a level price has already passed contains the
distance already travelled. Forcing decomposition makes that term visible
instead of letting it hide inside a headline.

`result.py` renders a 2×2 verdict against the detectable floor — `detectable`
/ `inconclusive` / `precise but immaterial` / `null`. "Not significant" is two
different findings and they have opposite next actions.

### 7. Gates — `calibration.py`, `power.py`

`calibration.py` builds two synthetic worlds — `dead_world` (no forward
drift) and `planted_world` (known effect) — and `assert_calibrated` **raises**
unless the estimator returns ~0 on the first and recovers the second. There
is no override parameter, and a test asserts none exists.

`power.py` computes required and detectable effect sizes, and applies the
design effect: `effective_n(n, cluster_size=, intra_r=)` implements
`n_eff = n / (1 + (m-1) * rho)`.

### 8. Register — `archive.py`, `audit.py`, `backfill.py`, `experiment.py`

`experiment.run` is the SOP as code. In order: the hypothesis must already be
registered; the analysis must be a **file** (inline analysis cannot be
archived); the script is archived **before** it executes; metrics are read
from the run's own stdout via `experiment.emit`, never retyped.

`@audited` in `audit.py` wraps every primitive so a run emits `calcs.json` —
which function computed which number, at which source hash. `engine_sha` pins
the commit; `calcs.json` pins the function, which is what you need once
shared estimators replace per-script copies.

`backfill.py` re-runs archived results when a shared component changes,
classifying each as `DETERMINISTIC`, `STOCHASTIC` or `SUPERSEDED`, with the
rounding tolerance inferred from the precision actually stored.

---

## Cross-cutting

**Configuration, not code.** `profiles.py` loads dated JSON rule snapshots
with a source reference. `assert_fresh` raises `StaleProfile` past your
tolerance — an undated rule set is a silent expiry.

**Reporting.** `report.py`, `cards.py`, `obsidian.py`, `plots` — rendering
only, downstream of everything. No analysis lives here.

**Operations.** `paper.py`, `poller.py`, `feed.py`, `telegram.py`, `state.py`,
`dayflow.py` support a paper-only observation loop. `parity.py` checks that
the live path and the backtest path agree on the same day. **There is no
live-execution path.**

**Hygiene.** `privacy.py` and `charset.py` run in `make check`.

---

## Dependencies

Runtime: `pandas`, `numpy`. Test-only: `scipy`, `pytest`, linters.

`harness.py` imports pandas only under `TYPE_CHECKING` — with
`from __future__ import annotations` the hints never evaluate, so the
serverless artifact does not carry pandas for the sake of a type name.

---

## Extension points

| To add | Implement | Registered at |
|---|---|---|
| a strategy | `MakePlan` — `TradingDay -> DayPlan \| NoTrade` | passed to the harness |
| a strategy *family* | an entry auditor | `execution.AUDITORS` |
| an estimator | a function taking `reference=` | must pass `assert_calibrated` |
| a rule set | dated JSON | `profiles/` |
| an instrument | `Costs` + session definition | `instruments.py` |

The first two are the ones with teeth. A new family without an auditor is
refused by default, and a new estimator without calibration cannot produce a
number anyone should read.
