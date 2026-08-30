"""D2.3 — the quickstart is the first thing a reader runs, so it must not rot.

It is the repository's whole argument in ten seconds: a harness that cannot
find a planted edge cannot be trusted to report its absence either. If this
stops passing, the claim on the front page is false.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location(
        "_quickstart", ROOT / "scripts" / "quickstart.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_the_quickstart_passes_all_four_controls(capsys):
    assert _load().main() == 0
    out = capsys.readouterr().out
    assert "ALL FOUR PASS" in out
    assert "POSITIVE CONTROL" in out
    assert "NEGATIVE CONTROL" in out
    assert "CALIBRATION GATE" in out


def test_it_needs_no_data_no_keys_and_no_network(capsys):
    """The claim on the last line has to be true, not just printed."""
    _load().main()
    assert "touched market data, an API key, or the network" \
        in capsys.readouterr().out
    # the two things a reader would not have
    assert not (ROOT / "data" / "MES.csv").stat().st_size == 0
    src = (ROOT / "scripts" / "quickstart.py").read_text()
    for forbidden in ("data/", "archive", "boto3", "_client"):
        assert forbidden not in src, f"quickstart reaches for {forbidden}"
