# AWS-RECON — B0 gating spikes: findings and decisions

**Run 2026-07-31.** Total metered spend **$0.1877** — $0.000146 of
latency probes plus a $0.0625 validation top-up that was billed three
times through a caching defect (logged in SPEND.md against ~$0.10
approved; fixed). Method and raw samples: `scripts/aws_recon.py`,
`scripts/validate_feed.py`, `docs/aws-recon-samples.jsonl`,
`docs/aws-recon-latency.md` (regenerable).

B0.1 and B0.2 were run together because one script answers both.

---

## B0.1 — intraday availability: **GATE FIRED**

**Finding: the historical entitlement is a rolling 8-hour wall.**

`metadata.get_dataset_range().end` tracked `now − 8h00m` to the second
across six samples spanning 16 minutes — a delay tier, not batch
publication. A metered fetch anchored exactly on that boundary returned
30 real 1-minute bars with a **true lag of 480.2 minutes**. Asking for
anything fresher is refused *at the quote stage*, before spend:

```
422 dataset_unavailable_range — "Part or all of your request for dataset
'GLBX.MDP3' requires a subscription and/or license to access."
```

Bisecting the boundary confirmed it is exactly 8h: `end = now − 8h`
quotes fine at $0.000146; `now − 7h55m` is refused.

**Consequence.** The 09:30–09:45 ET opening range would not become
retrievable until **≈17:45 ET** — after the close, hours after the trade.
The session poller as specified (B2.3, B3.2) **cannot be built on the
current entitlement.** This is the outcome the gate anticipated.

**What it does *not* block.** The signal path is the only casualty. The
morning card needs the sealed local calendar, not market data; the
evening debrief computes parity from the **human fill stream only**
(B-C3). So B1, B3.1, B3.3, B3.4, B4 and all of B7 are untouched — the
majority of the workstream, and the parts carrying most of the value.

## B0.2 — client vs REST: **DECIDED — REST + stdlib**

The whole spike ran on `urllib` + `json` with HTTP Basic auth. A
`timeseries.get_range` POST with `encoding=json&compression=none`
returned 30 parsed bars in 6,048 bytes.

**Decision: the Lambda ships no `databento` client**, and therefore no
zstandard and none of the client's own dependency tree. Smaller artifact,
faster cold start, far less supply-chain surface.

**Correction (same day).** This spike initially also claimed B0.3 was
retired — that the Lambda needed no numpy or pandas. That was wrong, and
checking the import graph rather than assuming it is what caught it:

- **numpy is genuinely required.** `occams/fade.py` uses `np.argmax` and
  `np.random.default_rng` at runtime. It must ship. At ~15 MB on arm64
  that is comfortable inside the 250 MB unzipped limit and needs no layer.
- **pandas is on the path but only through annotations.** `occams/sim.py`,
  `occams/harness.py` and `occams/strategy.py` each `import pandas as pd`
  at module level, yet **every single use is a type annotation** and all
  three carry `from __future__ import annotations`, so nothing is ever
  evaluated. The import is dead weight at runtime — but a module-level
  import still loads it.

**B0.3 is therefore re-opened**, with three options and a recommendation:

| | Cost | Note |
|---|---|---|
| (a) Bundle pandas + numpy | ~60–80 MB artifact | Works; slowest cold start |
| (b) `AWSSDKPandas-Python312` layer | managed | The original B0.3 plan |
| (c) Move the three imports under `if TYPE_CHECKING:` | free | **Recommended** |

(c) removes pandas from the runtime path entirely and changes no
behaviour — the annotations are already strings. It is not a fork in
B1.4's sense: same modules, same logic, same arithmetic, one deferred
import. The 160-test suite is the check that it stays identical.

**RESOLVED same day, by (c) — and it was not optional.** The first real
`sam build` proved the point: with pandas absent from the artifact,
`from occams import paper` raises `ModuleNotFoundError` at
`occams/sim.py:19`. The Lambda could not import its own engine. The three
imports now sit under `if TYPE_CHECKING:`; **173 tests pass** and the
engine imports cleanly with pandas *actively blocked* via `sys.meta_path`.
A regression test pins it, because a stray module-level `import pandas`
would never fail locally (pandas is a dev dependency) yet would break
every deploy.

Cost per boundary probe: **$0.000146**. Round trip 1.5 s (metadata),
4.7 s (30-bar fetch).

---

## B0.4 — account, region, auth: **read-only portion DONE**

`aws` and `sam` are both installed and credentials resolve. Account
`<account-id>`, IAM user `Tromso-Aura-Hunter-dev` (a legacy identity from
an unrelated project). **Configured region is `eu-north-1`**, not the
`eu-west-2` the backlog assumed — worth a deliberate choice rather than
inheriting one.

**Cost baseline (Cost Explorer, unblended, by service):**

| Month | Total | Largest components |
|---|---|---|
| 2026-05 | $11.71 | Lambda 3.26 · EC2-Other 2.02 · Secrets Mgr 1.23 · KMS 1.00 |
| 2026-06 | $10.81 | Lambda 3.15 · EC2-Other 2.02 · Secrets Mgr 1.60 · KMS 1.00 |
| 2026-07 | $10.51 | Lambda 3.15 · EC2-Other 1.93 · Secrets Mgr 1.54 · KMS 0.97 |

**This confirms the tagging requirement is load-bearing, not tidiness.**
A raw $5 budget alarm (B4.4) would fire immediately against the existing
~$10.51/month and be permanently useless. Every resource this stack
creates must carry `project=occams` and its budget must filter on that
tag.

None of this spend is ours — it belongs to the two retired projects
awaiting teardown. Roughly **$8.60/month ex-tax (~$103/yr)** looks
recoverable, which is a useful number for that **separate** brief
(`~/Documents/maverick-hq/10 - Projects/aws-account-cleanup.md`).
Destructive work stays out of this workstream.

**Still needs a decision:** region (inherit `eu-north-1` or move to
`eu-west-2`), and whether to keep using this legacy IAM identity or
create a scoped deploy user.

## The decision this forces

The poller needs bars in a narrow band: **~10 minutes old**. Not fresher
— PAPER-PREREG §3 rule 1 forbids peeking at any price the venue's own
delayed tape has not yet shown, and B-C1 makes that executable. Not much
older — the signal window would have passed.

| Option | Freshness | Cost | Verdict |
|---|---|---|---|
| Current entitlement | 480 min | $0 | **Unusable for the poller** |
| Databento CME live, non-professional | real-time | ~$36.50/mo ≈ **$438/yr** | **Rejected** |
| Yahoo delayed futures (`MES=F`,`MNQ=F`) | **10.0 min** | $0 | **Candidate — validate first** |
| Schedule-only fallback | n/a | $0 | **Baseline; ship regardless** |

**Databento live is rejected on proportionality, not affordability.**
Usage-based CME live was discontinued in April 2025; the Standard plan is
now $199/mo, with non-professional live starting ~$36.50/mo. That is ~3×
the *entire* $150 lab cap in year one, spent to automate a ~15-minute
daily task, on a campaign measuring a **+0.1R** edge that its own kill
thresholds may end at trade 10. If the campaign survives to a live
decision, revisit — real-time data is a live-trading cost, not a
paper-campaign cost.

**Yahoo measured at exactly 10.0 minutes** on MES=F, MNQ=F and ES=F
(476 one-minute bars, same probe). That is the TradingView free-tier
delay, so **delay parity holds by construction** rather than by an
artificial delay in code — a better fit for B-C1 than buying real-time
and throttling it. It is also free.

The known blocker "yfinance can't reach Yahoo behind the LAN DNS blocker"
is **stale**: the endpoint answered from this machine on the first try.

### Why Yahoo is a candidate and not yet a decision

Three risks, none yet measured:

1. **Bar fidelity.** Yahoo's 1-minute bars must agree with CME's for the
   09:30–09:45 range. A one-tick disagreement moves the range, the stop,
   the size and therefore the drift measurement.
2. **Roll convention.** `MES=F` is front-month; our sealed history is
   volume-rolled `MES.v.0`. Roll days are the hazard.
3. **Fragility.** An unofficial endpoint can rate-limit or break without
   notice. Mitigated by the dead-man's switch (B4.1) and by the fact that
   the human retains the TradingView chart as the authority — the poller
   assists, it never becomes the source of truth.

Risk 1 was decisively testable, so it became B0.5 — **run the same day,
result below.**

---

## B0.5 — Yahoo vs CME ground truth: **GATE PASSED**

Bought a $0.0625 top-up of the last 7 sessions (MES + MNQ, `ohlcv-1m`)
and compared the **09:30–09:45 ET range high and low, to the tick** —
the one number everything downstream is derived from.

**12 of 12 sessions matched exactly.** Both instruments, 6 trading days,
15 bars on each side of every comparison, zero disagreement:

| | MES (CME = Yahoo) | MNQ (CME = Yahoo) |
|---|---|---|
| 2026-07-23 | 7486.50 / 7444.75 | 28883.75 / 28656.00 |
| 2026-07-24 | 7455.25 / 7442.25 | 28622.25 / 28458.00 |
| 2026-07-27 | 7514.25 / 7492.75 | 28617.00 / 28427.50 |
| 2026-07-28 | 7452.50 / 7423.25 | 27993.00 / 27728.25 |
| 2026-07-29 | 7461.00 / 7444.25 | 27997.00 / 27836.50 |
| 2026-07-30 | 7421.50 / 7399.75 | 27996.25 / 27813.25 |

**Independent corroboration:** MES 2026-07-30 reads 7421.50 / 7399.75 —
exactly the range the human transcribed off TradingView into Telegram
that morning. Three sources agree to the tick: CME, Yahoo, and the
chart. That also retro-validates day 1's transcription.

**Decision: the poller is rebuilt against Yahoo.** B2.1–B2.3 and B3.2
are unblocked. Delay parity (B-C1) now holds *because the source is
10.0 minutes delayed*, not because code throttles a fresher feed —
which is a stronger guarantee than the original design had, since there
is no fresh data available to leak through a bug.

**Not yet tested:** roll-boundary behaviour (no roll fell inside the
7-session window) and long-run reliability of an unofficial endpoint.
Both are handled by the shadow week (B5.1) and the dead-man's switch
(B4.1) rather than by more spiking now. `MES=F` is front-month while our
sealed history is volume-rolled `MES.v.0`; over these 6 sessions that
distinction did not bite, but a roll week is the place to watch.

**Process defect, logged in SPEND.md.** The top-up was billed three
times ($0.1875 against ~$0.10 approved) because the script had no cache
and each re-run re-downloaded. `fetch_data.py` already carried this
lesson from the $9.21 lost stream and it was not carried across.
`validate_feed.py` now persists to git-ignored `data/`; re-runs cost $0.

---

---

## Revised sequencing

**Unblocked, build now:** B1 (foundations) → B3.1 morning card →
B3.3 evening debrief → B3.4 idempotency → B4 observability → B7
interaction model and recaps. None of these touch intraday market data.

**Blocked pending B0.5:** B2.1–B2.3 (signal path) and B3.2 (poller).

**Retired:** B0.3 — answered by B0.2; no pandas layer needed.

### New task — B0.5: validate Yahoo bars against CME ground truth

We own Databento MES/MNQ 1-minute history, but it ends 2026-07-05 and
Yahoo's 1-minute window only reaches back ~7 days, so they do not
currently overlap. Buy a **~$0.10** top-up of the last 7 sessions
(quoted first; inside PAPER-PREREG §7's allowance for an EOD drift
audit) and compare, per session:

- the 09:30–09:45 ET range high and low, to the tick — **the only number
  that must match**;
- bar count and any gaps inside the RTH session;
- timestamp convention (bar-open vs bar-close labelling);
- behaviour across a roll boundary if one falls in the window.

**Pass:** ranges agree to the tick on every session → Yahoo is fit for
the poller, and the poller is rebuilt against it with delay parity free.
**Fail:** any range disagreement → the poller is abandoned, Workstream B
ships schedule-only, and intraday signals stay manual on the TradingView
chart with its 3 free price alerts (which is what PAPER-PREREG §4 step 2
already assumes).

Either way the campaign is unaffected: it has never depended on the
poller existing.

---

## Incident — `.env` corruption (found and fixed during this spike)

The first probe returned 401. The stored `DATABENTO_API_KEY` was **125
characters** where a valid key is 32: the Telegram bot-token line had
been appended to the key line without a newline, almost certainly during
the 2026-07-29 "Plan B file drop" that delivered the token. A stray
93-character fragment sat on its own line too.

The official `databento` client failed identically, which is what
established that the key — not the new stdlib code — was at fault.

Fixed: `.env` rewritten to four well-formed lines, original preserved as
`.env.broken-backup` (git-ignored via `.env.*`). Verified: the key
authenticates and all four variables load.

**This had been silently broken since 2026-07-29.** Nothing depended on
Databento in the interim, so it surfaced only here — the next data
purchase would have hit it instead. Follow-up: `scripts/fetch_data.py`
and this script should fail loudly on a malformed key shape rather than
sending it and reading a 401.
