# Testing your own strategy

End to end, with the gates in the order they will stop you.

Expect to be refused at least once. That is the product working — each
refusal below corresponds to a way a backtest can produce a confident number
that means nothing.

---

## 0. Install and prove the harness works

```bash
pip install -e ".[dev]"
make quickstart
```

`make quickstart` runs a positive control (planted edge, must be found), a
negative control (dead world, must return nothing), the calibration gate, and
a rule-profile freshness check. **If those four do not pass, no result you
produce afterwards is interpretable.**

---

## 1. Rules are input

```python
from occams import profiles

p = profiles.load("profiles/example-50k.json")
profiles.assert_fresh(p, max_age_days=90)     # raises StaleProfile if not
cfg = p.config                                # ChallengeConfig
```

The shipped profiles are worked examples describing a *geometry* — a profit
target, a trailing drawdown that ratchets and never comes back down, a daily
guard, a minimum number of days. They are not any provider's current terms.
Copy one, edit it, date it, cite your source.

`assert_fresh` raises rather than warns. An undated rule set is a silent
expiry, and every number computed under stale rules is wrong in a way nothing
else will catch.

---

## 2. Write the strategy

A strategy is a pure function from one day to one plan.

```python
from occams.strategy import NoTrade
from occams.sim import DayPlan

def make_plan(day):
    if day.range_bars is None or day.atr <= 0:
        return NoTrade(reason="no opening range")

    hi = float(day.range_bars["high"].max())
    lo = float(day.range_bars["low"].min())
    stop_dist = 0.75 * day.atr

    if stop_dist < costs.tick_size:
        return NoTrade(reason="stop below one tick — unexecutable")
    contracts = int(risk_budget // (stop_dist * costs.multiplier))
    if contracts < 1:
        return NoTrade(reason="risk per contract exceeds budget")  # say why

    return DayPlan(buy_stop=hi, sell_stop=lo,
                   stop_dist=stop_dist, target_dist=2.0 * stop_dist,
                   contracts=contracts, max_trades=1,
                   daily_stop_usd=500.0)
```

Three things matter here.

**A plan is a bracket, not a fill.** You declare where the orders rest
(`buy_stop` / `sell_stop`) and how far the exits sit (`stop_dist`,
`target_dist`). You never state an entry price — that is derived from what the
market did. Setting a side to `None` disarms it.

**Return `NoTrade(reason=...)`, never `None`.** A strategy that returns zero
contracts for every parameter combination produces a report of structural
zeros that reads exactly like "no edge found". The reason string is what
distinguishes the two.

**Only touch `day.range_bars` when deciding.** `session_bars` is what the
simulator trades. Conditioning on it is lookahead, and the separation exists
so you cannot do it by accident.

---

## 3. Register the entry auditor — or be refused

```python
from occams import execution

def audit_mine(day, plan, costs) -> list[str]:
    """Return a list of failures; empty means every entry was obtainable."""
    bad = []
    for i, bar in enumerate(day.session_bars.itertuples()):
        ok, why = execution.obtainable(
            assumed_entry=plan.entry, side="long", decision_bar=i,
            market_at_decision=bar.close,
            highs=day.session_bars["high"], lows=day.session_bars["low"],
            opens=day.session_bars["open"])
        if not ok:
            bad.append(f"{day.date}: {why}")
    return bad

execution.AUDITORS["mine"] = audit_mine
```

Without this, `assert_entries_obtainable("mine", ...)` raises
`UnobtainableEntry`. **Default-deny is deliberate** — an unaudited family is
refused rather than quietly trusted.

`obtainable` tries a limit, a stop, and a market order in turn, and tells you
what each did:

```
False, "limit: would fill immediately at 5231.50, not 5228.00;
        stop: placeable, but never filled;
        market: fills at 5231.75, not 5228.00"
```

That is the failure to take seriously. It says the price your backtest booked
was not reachable by any order a human could have placed.

---

## 4. Calibrate every estimator

```python
from occams import calibration, estimators

def measure(world, i):
    return estimators.forward_return(
        world.closes, at=i, horizon=20, direction=+1,
        reference=estimators.AT_PRICE)

calibration.assert_calibrated(measure, expected=0.07, seed=1)
```

The estimator is run on a world with no forward drift (must return ~0) and a
world with a planted effect (must recover it). Both halves are required: one
that always returns zero passes the first and is useless; one that finds an
effect in noise passes the second and is dangerous.

If you measure from a **level** rather than the current price, decomposition
is mandatory:

```python
d = estimators.forward_return(closes, at=i, horizon=20, direction=+1,
                              reference=estimators.AT_LEVEL,
                              level=swept_low, decompose=True)
d.total        # what you would have reported
d.positional   # the distance price had ALREADY travelled
d.drift        # the only part that is a claim about the future
```

`total = positional + drift`, asserted on every call. Without `decompose=True`
this raises `AmbiguousReference` — because a headline that silently contains
its own starting point is the single easiest way to manufacture a large,
significant, meaningless result.

---

## 5. Check power before you spend alpha

```python
from occams import power

n_needed = power.n_for_correlation(r=0.07)
n_eff    = power.effective_n(n_observed, cluster_size=2, intra_r=0.9)
```

Two correlated instruments are not two independent samples. At `rho = 0.9`,
2,000 pooled observations are worth about 1,053.

Run this **before** the experiment. An underpowered run produces an ambiguous
null, costs the same alpha as a real test, and then tempts you into a second
look at a bigger sample — which is optional stopping, and invalidates both.

---

## 6. Register the hypothesis

```python
from occams import archive

archive.register_hypothesis(
    hid="MY-H1",
    statement="Opening-range breakouts on <instrument> carry positive "
              "forward expectancy at a 2R target.",
    mechanism="Overnight inventory imbalance resolves in the first hour; "
              "the range boundary is where resting size is cleared.",
    information_axis="price",
    search_space_size=1,
    alpha_allocated=0.05,
    power_plan={"test": "correlation", "effect": 0.07,
                "cluster_size": 2, "intra_cluster_r": 0.9},
    note="Both directions: a null closes the ORB family on this instrument.")
```

`mechanism` is required and cannot be empty — a hypothesis without one is
rejected unrun. It has to be written before the number exists, because a
mechanism that can be back-filled is worthless: any result can be explained
after the fact.

State what **both** outcomes mean, in `note`, before you look. A test that
can only be read one way was never a test.

`search_space_size` is honest bookkeeping. If you tried eight parameter
combinations, it is 8, and your evidence bar moves accordingly.

---

## 7. Run it through the harness

The analysis must be a file. Put it in `scripts/`:

```python
# scripts/exp_my_h1.py
from occams import experiment, harness, calibration
...
stats = harness.monte_carlo(days, make_plan, cfg, costs, horizon_days=60)
experiment.emit({"p_pass": stats.p_pass, "p_breach": stats.p_breach,
                 "n_runs": stats.n_runs, "traded_days": stats.traded_days})
```

Then:

```python
experiment.run(hypothesis_id="MY-H1", script="scripts/exp_my_h1.py",
               run_id="r1", config={"horizon": 60, "risk": 200},
               note="first look", controls_passed=True)
```

What this enforces, in order:

1. The hypothesis is registered. Running first is how a hypothesis gets
   quietly reshaped to fit a number it has already seen.
2. The script exists as a file. Inline analysis cannot be archived.
3. The script is copied to the archive **before** it runs.
4. Metrics come from the script's own stdout, via `emit` — not from anyone
   retyping them into a document.
5. Power is checked against the registered plan.

There is no flag to skip any of it, and a test asserts no such flag exists.

---

## 8. Read the verdict honestly

```python
from occams.result import Result

r = Result(name="MY-H1 forward return", estimate=-0.0004,
           ci=(-0.011, 0.010), n=3260, n_eff=1053, floor=0.07)
print(r.verdict)      # -> "null"
print(r.render())
```

Four outcomes, not two:

| | interval excludes 0 | interval includes 0 |
|---|---|---|
| **\|effect\| ≥ floor** | `detectable` | `inconclusive` |
| **\|effect\| < floor** | `precise but immaterial` | `null` |

`inconclusive` means *get more data*. `null` means *this is answered, stop*.
Collapsing both into "not significant" is how dead strategies get retested
until one of them passes.

Effects are reported in multiples of the detectable floor, so results from
different sample sizes can be compared without re-deriving each one's power.

---

## 9. If you change a shared component

Re-run every archived result that depended on it and compare, field by field,
against what was recorded:

```python
from occams import backfill

checks = backfill.compare(archived_doc, recompute(),
                          decimals_override=4, superseded=("old_metric",))
print(backfill.render(checks))
assert backfill.all_ok(checks)
```

`compare` infers each field's tolerance from the precision actually stored —
a value archived as `0.0735` is checked to four places, not to float equality.
Mark genuinely random fields `stochastic=` and retired ones `superseded=`.

[`scripts/backfill_m5.py`](../scripts/backfill_m5.py) is the worked example:
a target table of `(kind, key, recompute_fn, places, superseded)` driven from
the command line. Note what it does when a check fails on an estimator swap —
it reports the difference as **a finding about the old function**, not a
defect in the new one. Corrections then **append** to the register with a
`supersedes` pointer; nothing is edited in place.

Do this even when you are confident the change is cosmetic. A defect that
leaves one result untouched and moves another by 28% is not exotic — it just
means the two datasets had different shapes, and the only way to know which
you have is to re-run.

---

## Reference

| | |
|---|---|
| `make quickstart` | four controls, no data or network needed |
| `make test` | test suite |
| `make check` | tests, lint, privacy and charset scans |
| `make reproduce` | re-score archived results end to end |
| `make plots` | render figures |

Design rationale: [ARCHITECTURE.md](ARCHITECTURE.md).
Worked examples: [`scripts/`](../scripts/) and the `VERDICT-*` records in
this directory.
