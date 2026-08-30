"""A2 — the cumulative spend guard, tested by making it refuse.

Audited after R2.1 went over an approval. The assumed cause was a per-run
cap; the audit found two scripts with no cap at all and a third whose cap
was per-request. All three now call this.
"""

from __future__ import annotations

import pytest

from occams import spend


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(spend, "LEDGER", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(spend, "BASELINE_USD", 100.0)
    monkeypatch.setattr(spend, "PROGRAMME_CAP_USD", 150.0)


def test_the_baseline_counts_as_spent(ledger):
    """The ledger starts empty but the money was already gone."""
    assert spend.spent() == 100.0
    assert spend.remaining() == 50.0


def test_a_purchase_inside_the_cap_is_allowed(ledger):
    spend.check(40.0, what="fine")            # must not raise


def test_a_purchase_that_would_BREACH_the_cap_is_refused(ledger):
    with pytest.raises(spend.BudgetExceeded, match="REFUSED"):
        spend.check(60.0, what="too much")


def test_the_guard_is_CUMULATIVE_across_calls(ledger):
    """The R2.1 defect: two purchases each passing a check that together
    they should have failed."""
    spend.check(30.0)
    spend.record(30.0, what="run 1", actual=True)
    spend.check(15.0)
    spend.record(15.0, what="run 2", actual=True)
    assert spend.spent() == 145.0
    with pytest.raises(spend.BudgetExceeded):
        spend.check(10.0, what="run 3")       # each was small; together, no


def test_the_refusal_says_where_the_cap_is_raised(ledger):
    """A guard that blocks without saying who can unblock it is an obstacle."""
    try:
        spend.check(60.0)
    except spend.BudgetExceeded as e:
        assert "docs/SPEND.md" in str(e) and "user's to raise" in str(e)


def test_quotes_and_actuals_are_distinguished(ledger):
    """SPEND.md was overstated 22% by recording quotes as charges, which
    made a $6 overrun look like $34."""
    q = spend.record(10.0, what="quote", actual=False)
    a = spend.record(10.0, what="charge", actual=True)
    assert q["actual"] is False and a["actual"] is True


def test_there_is_no_override_on_check():
    import inspect
    sig = inspect.signature(spend.check)
    for bad in ("force", "override", "allow", "skip"):
        assert bad not in sig.parameters
