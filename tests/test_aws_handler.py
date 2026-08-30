"""B1.1 — the Lambda dispatch contract.

Two things are worth pinning here, and only two. First, an unknown job
must raise rather than fall through: a mis-scheduled EventBridge rule
should fail visibly in CloudWatch, not quietly run the wrong job or
succeed doing nothing. Second, the deployed engine constants must equal
the sealed ones — B1.4 says the Lambda imports the very modules the
sealed verdicts used, so a drift here is a defect, not a variant.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aws.handler import JOBS, lambda_handler  # noqa: E402

from occams import paper  # noqa: E402


@pytest.mark.parametrize("job", JOBS)
def test_every_declared_job_dispatches(job):
    assert lambda_handler({"job": job}, None)["job"] == job


@pytest.mark.parametrize("event", [
    {}, None, {"job": None}, {"job": "morning "}, {"job": "MORNING"},
    {"job": "backtest"}, {"job": "trade"},
])
def test_unknown_job_raises_rather_than_guessing(event):
    with pytest.raises(ValueError):
        lambda_handler(event, None)


def test_engine_constants_match_the_sealed_cell():
    """PAPER-PREREG §2 sealed k_stop=0.2 and $175 risk. If a deploy ever
    reports different numbers, the Lambda is not running the sealed
    engine and every card it emits is off-protocol."""
    fp = lambda_handler({"job": "morning"}, None)["engine"]
    assert fp["k_stop"] == 0.2 == paper.K_STOP
    assert fp["risk_usd"] == 175.0 == paper.RISK_USD
    assert fp["max_contracts"] == 30 == paper.MAX_CONTRACTS
    assert fp["tick"] == 0.25 == paper.TICK


def test_lambda_path_imports_without_pandas():
    """B0.3. pandas is NOT in the Lambda artifact — `sim`, `harness` and
    `strategy` import it only under TYPE_CHECKING because every use is an
    annotation. A future module-level `import pandas` anywhere on this
    path would not fail locally (pandas is installed for dev) but would
    break every deploy, so the guard has to block the import explicitly.
    """
    import importlib

    mods = ["occams.paper", "occams.sim", "occams.harness", "occams.strategy"]

    class Blocker:
        def find_module(self, name, path=None):
            if name == "pandas":
                raise ImportError("pandas must not be on the Lambda path")

    saved = {m: sys.modules.pop(m, None) for m in mods}
    sys.modules.pop("pandas", None)
    sys.meta_path.insert(0, Blocker())
    try:
        for m in mods:
            importlib.import_module(m)
    finally:
        sys.meta_path.pop(0)
        for m, mod in saved.items():
            if mod is not None:
                sys.modules[m] = mod


def test_delay_parity_default_is_never_fresher_than_the_venue(monkeypatch):
    """B-C1. The default must not be looser than the venue's ~10-minute
    delay even if the environment variable is absent."""
    monkeypatch.delenv("VENUE_DELAY_MINUTES", raising=False)
    out = lambda_handler({"job": "poll"}, None)
    assert out["venue_delay_minutes"] >= 10
