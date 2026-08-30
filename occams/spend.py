"""One cumulative spend guard, shared by every path that can buy data.

Audited 2026-08-01 after R2.1 went $33 over an approval. The cause was
assumed to be a per-run cap that reset between invocations. The audit found
worse: `fetch_data.py` and `validate_feed.py` had **no cost guard at all** —
they quoted, then bought on `--submit` with nothing stopping them — and
`aws_recon.py`'s cap was per-request, so it never accumulated either.

Three scripts, three different answers to "how much may this spend", and
one of those answers was "anything". So the guard lives here now and they
all call it.

Two properties the previous attempts lacked:

- **cumulative across runs and across scripts.** A budget that forgets what
  it already spent is not a budget. Every purchase appends to a ledger on
  disk and every check reads the whole ledger.
- **refuses rather than warns.** `check()` raises. There is no flag to
  proceed anyway, because the one time a cap was advisory it was exceeded.

The free-credit era ended at $128.09 of $125, so every further byte is real
money and this stopped being bookkeeping.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "data" / "spend_ledger.jsonl"

# The programme cap from docs/SPEND.md. A change here is meaningless on its
# own — the cap is the USER's, and moving it is a ledger entry they make,
# not an edit an agent slips in.
PROGRAMME_CAP_USD = 150.00

# Vendor actuals to 2026-08-01, reconciled against the Databento portal.
# Recorded as a baseline because the ledger below starts empty and the money
# was already spent.
BASELINE_USD = 128.09


class BudgetExceeded(RuntimeError):
    """This purchase would take the programme past its cap."""


def _rows() -> list[dict]:
    if not LEDGER.exists():
        return []
    return [json.loads(x) for x in LEDGER.read_text().splitlines() if x.strip()]


def spent() -> float:
    """Everything spent to date, baseline included."""
    return BASELINE_USD + sum(r.get("usd", 0.0) for r in _rows())


def remaining() -> float:
    return max(PROGRAMME_CAP_USD - spent(), 0.0)


def check(amount_usd: float, *, what: str = "") -> None:
    """Call BEFORE buying. Raises if the purchase would breach the cap.

    Deliberately takes the QUOTE and compares it to the cap, so the refusal
    happens before any request is made — a guard that fires after the money
    has gone is a receipt, not a guard."""
    if amount_usd <= 0:
        return
    if spent() + amount_usd > PROGRAMME_CAP_USD:
        raise BudgetExceeded(
            f"REFUSED{': ' + what if what else ''}. ${amount_usd:,.2f} would "
            f"take the programme to ${spent() + amount_usd:,.2f} against a "
            f"${PROGRAMME_CAP_USD:,.2f} cap (${spent():,.2f} already spent, "
            f"${remaining():,.2f} left). The cap is the user's to raise, in "
            f"docs/SPEND.md, and raising it is their decision to record — "
            f"not a number to edit here.")


def record(amount_usd: float, *, what: str, actual: bool = False) -> dict:
    """Append a purchase. `actual=False` means this is a QUOTE.

    The distinction is load-bearing: SPEND.md spent a day overstated by 22%
    because quotes were recorded as charges, and that error made a $6
    overrun look like $34."""
    row = {"usd": round(float(amount_usd), 4), "what": what,
           "actual": bool(actual),
           "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    LEDGER.parent.mkdir(exist_ok=True)
    with LEDGER.open("a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def status() -> str:
    return (f"spend ${spent():,.2f} of ${PROGRAMME_CAP_USD:,.2f} "
            f"(${remaining():,.2f} left; free credit exhausted, every byte "
            f"from here is real money)")
