# prop-challenge-lab

**A backtesting harness designed to be hard to fool.**

Most backtest frameworks optimise for expressiveness: how quickly can you
describe a strategy and see a curve. This one optimises for **refusal** —
how many distinct ways it can stop you believing something that isn't true.

It is a Python package, a CLI, and an append-only experiment register. It
runs on futures bars and tick data, and nothing in it is specific to any
market or venue.

```bash
make quickstart     # ten seconds, no data, no API key, no network
```

**Status: the research programme that built this is closed.** 24 registered
hypotheses, 24 resolved, three sealed verdicts, no edge found — and no fee
ever paid to a funded-account provider, because the instrument said not to.
The harness stands on its own; see **[docs/RESULTS.md](docs/RESULTS.md)** for
what it was pointed at and what came back.

---

## The problem it exists to solve

A backtest is a measurement instrument, and measurement instruments have a
specific failure mode: **they can produce confident, well-formatted,
statistically significant output while measuring nothing at all.**

Three examples, all of which pass every check a normal framework applies:

- A strategy books its entry at a price level the moment a condition becomes
  true — but at that moment price is on the far side of the level, so no
  order a human could place would have filled there. The equity curve is
  fiction, and looks identical to one that isn't.
- A forward return is measured from a level price has already passed. The
  number now contains the distance already travelled, so a market that froze
  solid at the signal still prints a large positive result.
- A position sizer returns zero contracts for every parameter combination.
  Every statistic is a structural zero, and the report says "no edge found"
  in exactly the format it would use if it had actually looked.

None of these is a statistical error. The arithmetic is correct in all
three. They are errors in the relationship between the numbers and the
world — and no p-value inspects that relationship.

This repository is a set of gates that do.

---

## Quickstart

```bash
git clone https://github.com/MaverickHQ/prop-challenge-lab
cd prop-challenge-lab && pip install -e ".[dev]"
make quickstart
```

No market data, no credentials, no network. It runs the four checks that
should precede reading any backtest number:

```
1. POSITIVE CONTROL   planted-edge world  P(pass) = 1.00
2. NEGATIVE CONTROL   dead world          P(pass) = 0.00  random-entry null = 0.00
3. CALIBRATION GATE   from PRICE   +0.0735 = 0.5 sigma  -> calibrated
                      from a LEVEL +0.7040 = 5.0 sigma  -> fails the dead world
4. RULE PROFILE       example-50k   effective 2026-07-02

ALL FOUR PASS — the instrument is calibrated.
Nothing above touched market data, an API key, or the network.
```

**A harness that cannot find a planted edge cannot be trusted to report its
absence either.** That gate runs first, and it is the one most backtests
skip.

Then: `make check` (tests, lint, privacy and charset scans) and
`make reproduce` (re-score archived results end to end).

---

## The research console

`make report` renders the whole register as **one self-contained HTML page**:
the four controls, every scored result against its own detectable floor, the
figures, and each hypothesis with the mechanism written before its number
existed.

**[View it here](https://maverickhq.github.io/prop-challenge-lab/report.html)** —
published from [`docs/report.html`](docs/report.html), so it is readable
without credentials or a checkout. To regenerate your own:

```bash
make report          # needs archive credentials on first run
make report-offline  # renders from the cached register, no network
```

Two properties it is built for. It is **generated, not live** — a page
showing whatever the store says at load time cannot be cited or diffed, so
this writes a dated artifact stamped with `engine_sha` that you can put
beside a claim. And it is **reproducible**: the same register renders the
same bytes whether it came from the archive or the cache.

The controls render *above* the findings, deliberately. Nothing on the page
is worth reading until the instrument has shown it can find a planted edge
and report nothing on a dead world. Colour encodes trust, not profit; there
is no equity curve anywhere on it.

---

## The five refusals

Each gate refuses a specific class of false result. They are independent —
none of them would have caught what the others catch.

### 1. A hypothesis without a mechanism is rejected unrun

`occams/experiment.py`

Register the claim before you measure it, including **why it should work,
written before the number exists**, and an interpretation for *both*
directions. A test that can only be read one way was never a test.

Alpha is a depleting budget rather than a warning: each registration raises
the evidence bar for the next survivor, and the register makes the count
visible instead of leaving it to memory.

The procedure is code, not documentation — the run refuses to proceed unless
the hypothesis is registered, refuses inline analysis because an inline
script cannot be archived, archives the script *before* executing it, and
reads recorded values from the run's own output rather than from anyone
retyping them. There is no flag to skip a step, and a test asserts no such
flag exists.

### 2. A fill is derived, never asserted

`occams/execution.py`

A strategy declares an **Order** — kind, side, level, the bar it was placed
on. The fill comes from what the market subsequently did.

This is stronger than a fill model. A fill model answers *"what price would
I get?"*; this answers *"could this order have existed at that moment?"* A
limit on the marketable side is refused. A stop on the wrong side triggers
instantly. A gapped stop fills at the open, never at its level. Slippage is
adverse by construction, because a simulator that lets it help is measuring
optimism.

**Default-deny:** a strategy family with no entry auditor cannot be tested
at all. The failure mode is a loud refusal, not a plausible number.

### 3. Estimators must be calibrated in both directions

`occams/calibration.py`

Every estimator is run against two synthetic worlds: one with no forward
drift, where it must return approximately zero, and one with a known planted
effect, which it must recover.

**Both halves are required.** An estimator that returns zero for everything
passes the first and is useless; one that reports an effect from noise
passes the second and is dangerous.

This is what catches the reference-price class. The same measurement, taken
from where price actually is versus from a level price has already passed,
reads 0.5 sigma and 5.0 sigma respectively — on a world where nothing is
happening.

### 4. Pooling correlated data is not free

`occams/power.py`

Sample-size gates apply a design effect: `n_eff = n / (1 + (m-1) * rho)`. Two
highly correlated instruments do not give you twice the evidence, and
treating them as though they do roughly halves your true sample while
doubling your apparent one.

**Underpowered runs are refused, not run-and-caveated** — an ambiguous null
costs the same alpha as a real test and then tempts a second look at a
bigger sample, which is optional stopping.

### 5. The register is append-only, and records how

`occams/archive.py`, `occams/audit.py`

Every experiment writes its hypothesis, config, metrics, controls, the
script that produced it, its stdout, and a `calcs.json` naming **which
estimator computed each number, at which source hash**. Corrections append
with `supersedes`; nothing is edited.

`engine_sha` pins the commit. `calcs.json` pins the function — which matters
once shared estimators replace per-script copies, because the commit no
longer tells you which code path ran.

---

## Testing your own strategy

Full walkthrough: **[docs/USAGE.md](docs/USAGE.md)**. In outline:

```python
from occams import profiles, archive, experiment

# 1. Rules are input, and dated.
p = profiles.load("profiles/example-50k.json")
profiles.assert_fresh(p, max_age_days=90)      # refuses a stale snapshot

# 2. Register before measuring — mechanism first, both directions named.
archive.register_hypothesis(
    hid="MY-HYPOTHESIS", statement="...", mechanism="why this should work",
    information_axis="price", search_space_size=1, alpha_allocated=0.05,
    power_plan={"test": "correlation", "effect": 0.07,
                "cluster_size": 2, "intra_cluster_r": 0.9})

# 3. Run the analysis as a FILE, through the harness.
experiment.run(hypothesis_id="MY-HYPOTHESIS", script="scripts/exp_mine.py",
               run_id="r1", config={...}, note="...", controls_passed=True)
```

Your strategy supplies an entry auditor (`occams/execution.py::AUDITORS`) so
the obtainability gate can check it, and your estimators must pass
`calibration.assert_calibrated` before their numbers mean anything.

---

## Rules as configuration

```python
p = profiles.load("profiles/example-50k.json")
p.config          # ChallengeConfig: target, trailing drawdown, guard, min days
```

Evaluation geometry lives in dated JSON with a source reference, not in code.
`assert_fresh` **refuses** a snapshot older than your tolerance rather than
warning — providers change terms, and an undated rule set is a silent
expiry. The shipped profiles are worked examples describing a *geometry*,
not any provider's current terms. Replace them.

---

## Architecture

Detail: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**

```
occams/
  loader · sessions · calendar     vendor bars -> trading days, no lookahead
  strategy · fade · search         a strategy is: one day -> one plan
  execution · sim                  a plan -> fills, or a refusal
  rules · payout                   the rule arithmetic: evaluation, then funded
  harness                          every viable start day, simulated once
  estimators · stats · result      the number, and what it is allowed to mean
  calibration · power              the gates
  archive · audit · backfill       the register and the calculation ledger
```

Runtime dependencies are `pandas` and `numpy`. scipy is test-only, used as
an oracle so the package's own implementations are pinned rather than
delegated.

**Why the package is `occams` and the repository is not.** Occam's razor is
the project's governing principle, and the package kept the name when the
repository took one that says what it is *for*. It also cannot be renamed
without destroying what the repository is for: **17 frozen experiment
scripts import it**, each archived byte-for-byte as the artifact that
produced a registered result, referenced by **64 distinct `engine_sha`
commits**. Renaming would either edit frozen evidence or break
`make reproduce` — so the mild inconsistency is the cheaper of two prices.

---

## What this is not

Not a trading system and not a signal service. It emits no orders and places
none; there is no live-execution path and never was.

Not a claim about discretionary trading. What it tests is the part that can
be written down as a rule, which is a weaker claim than the one usually
argued about.

Not a source of market data. `data/` is git-ignored; licensed vendor data is
never redistributed.

---

## The programme this was built for

The lab ran for a year against two index futures, testing whether a
mechanical strategy could clear a funded-account evaluation. **It closed
without entering one.**

**24 registered hypotheses, 24 resolved, three sealed verdicts, $128 of
market data, and no provider fee ever paid.** Nine distinct rearrangements
of seven years of 1-minute bars produced a gross signal of +0.02 to +0.04R
per trade against costs of 0.05–0.09R.

Two findings are worth the click even if you never trade:

- **Three results looked real and were not** — an unobtainable entry price,
  a measurement containing 94.8% of its own answer, and a broken estimator
  that met forgiving data. Each was caught by a different gate above, and
  none by a significance test.
- **The constraint was the adversary, not the market.** Trade *geometry*
  moved results more than any signal the programme measured, and roughly
  half of modelled failures breach the trailing drawdown rather than run out
  of edge.

**[docs/RESULTS.md](docs/RESULTS.md)** is the checkable record — every number
resolves to an entry in
[the register](https://maverickhq.github.io/prop-challenge-lab/report.html).
The narrative versions are [essays](https://harveygill.substack.com/).

**You do not need any of it to use the harness.** Nothing in `occams/` is
specific to that programme, that venue, or those instruments.

---

## Licence

Apache-2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
