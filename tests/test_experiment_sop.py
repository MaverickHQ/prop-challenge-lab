"""The SOP's guards, tested by making each one fire.

Every guard here exists because the corresponding step was actually skipped
on 2026-08-01: an experiment was recorded whose script had been run inline
and therefore could not be archived, so the conclusion outlived the means of
checking it. A written procedure would not have caught that. These do.
"""

from __future__ import annotations


import pytest

from occams import experiment


def test_metrics_must_come_from_the_run_not_from_retyping():
    """The register should hold what the script computed, not what someone
    read off a table and typed in."""
    with pytest.raises(ValueError, match="no METRICS"):
        experiment._extract_metrics("MES +0.080\nMNQ +0.186\n")


def test_metrics_line_is_parsed_into_the_record():
    out = "some table\nMETRICS: {\"mes\": 0.08, \"mnq\": 0.186}\n"
    assert experiment._extract_metrics(out) == {"mes": 0.08, "mnq": 0.186}


def test_two_metrics_lines_are_ambiguous_and_rejected():
    with pytest.raises(ValueError, match="expected one"):
        experiment._extract_metrics('METRICS: {"a":1}\nMETRICS: {"a":2}\n')


def test_emit_prints_a_parseable_line():
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        experiment.emit({"r": -0.049})
    assert experiment._extract_metrics(buf.getvalue()) == {"r": -0.049}


def test_an_unregistered_hypothesis_cannot_be_run(monkeypatch, tmp_path):
    """Running before registering is how a hypothesis gets quietly reshaped
    to fit a number it has already seen."""
    monkeypatch.setattr(experiment, "_hypothesis_exists", lambda h: False)
    s = tmp_path / "exp.py"
    s.write_text("print('hi')")
    with pytest.raises(LookupError, match="not registered"):
        experiment.run(hypothesis_id="H-NOPE", script=s, run_id="r1",
                       config={}, note="", controls_passed=True)


def test_inline_analysis_cannot_be_run(monkeypatch):
    """The exact 2026-08-01 failure: option (b) was a heredoc, so there was
    nothing to archive and the result could not be reproduced."""
    monkeypatch.setattr(experiment, "_hypothesis_exists", lambda h: True)
    with pytest.raises(FileNotFoundError, match="Inline analysis"):
        experiment.run(hypothesis_id="H-YES", script="does/not/exist.py",
                       run_id="r1", config={}, note="", controls_passed=True)


def test_the_sop_has_no_skip_flag():
    """A procedure with an override is a suggestion."""
    import inspect
    sig = inspect.signature(experiment.run)
    for bad in ("force", "skip", "allow_inline", "no_archive", "dry_run"):
        assert bad not in sig.parameters, f"{bad} would make the SOP optional"
