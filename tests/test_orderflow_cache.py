"""The one function that protects the data budget.

Metered market data has been re-billed twice in this repo -- the $9.21 lost
stream and a $0.0625 top-up -- both because a cache check did not recognise
data we had already paid for. This is the third form of that mistake, caught
before it cost anything: an earlier batch was written uncompressed and later
gzipped, so a check that only knew `.ndjson.gz` would have re-bought all 356
instrument-days.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch_orderflow as fo  # noqa: E402

D = date(2026, 6, 15)
SYM = "MES.v.0"


@pytest.fixture
def out(tmp_path, monkeypatch):
    monkeypatch.setattr(fo, "OUT", tmp_path)
    (tmp_path / "MES_v_0").mkdir()
    return tmp_path / "MES_v_0"


def test_gzipped_data_counts_as_cached(out):
    (out / "2026-06-15.ndjson.gz").write_bytes(b"x")
    assert fo.cached(SYM, D)


def test_LEGACY_UNCOMPRESSED_data_also_counts_as_cached(out):
    """The actual near-miss: 356 instrument-days were fetched uncompressed
    and gzipped afterwards. Missing this branch re-buys all of them."""
    (out / "2026-06-15.ndjson").write_text("x")
    assert fo.cached(SYM, D)


def test_absent_data_is_not_cached(out):
    assert not fo.cached(SYM, D)


def test_a_different_day_is_not_cached(out):
    (out / "2026-06-15.ndjson.gz").write_bytes(b"x")
    assert not fo.cached(SYM, date(2026, 6, 16))


def test_new_fetches_are_written_gzipped(out):
    assert fo.cache_path(SYM, D).name.endswith(".ndjson.gz")
