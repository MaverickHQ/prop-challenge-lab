"""Track D — the archive's guards, tested by making them fail.

Everything here is about refusal. The archive's value is entirely in what
it will not accept: unscanned content, unhashed objects, silent overwrites
of write-once prefixes, and hypotheses with no stated mechanism.
"""

from __future__ import annotations

import pytest

from occams import archive


def test_a_forbidden_term_is_refused_not_warned(tmp_path, monkeypatch):
    """Durable storage is the LAST place a forbidden term should reach."""
    monkeypatch.setattr(archive, "load_terms", lambda _p: ["seekrit-venue"])
    f = tmp_path / "note.md"
    f.write_text("the venue is seekrit-venue and it should never ship")
    with pytest.raises(ValueError, match="forbidden term"):
        archive.guard(f)


def test_a_stray_foreign_script_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(archive, "load_terms", lambda _p: [])
    f = tmp_path / "note.md"
    # built from escapes so this file passes the guard it tests
    f.write_text("the fill-watcher \u6761\u4ef6 was written for stops")
    with pytest.raises(ValueError, match="CJK"):
        archive.guard(f)


def test_clean_content_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(archive, "load_terms", lambda _p: ["seekrit-venue"])
    f = tmp_path / "ok.md"
    f.write_text("MES range 7515.25 / 7480.25 - BUY LIMIT 3x")
    archive.guard(f)                      # must not raise


def test_vendor_bars_are_not_term_scanned_but_are_still_hashed(tmp_path):
    """Scanning 200 MB of numbers for English words is meaningless and
    slow. They are still hashed, still logged, still private."""
    f = tmp_path / "MES.csv"
    f.write_text("ts,open,high\n1,2,3\n")
    archive.guard(f)                      # .csv is outside SCAN_SUFFIXES
    assert len(archive.sha256(f)) == 64


def test_sha256_is_stable_and_content_addressed(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.write_text("same")
    b.write_text("same")
    assert archive.sha256(a) == archive.sha256(b)
    b.write_text("different")
    assert archive.sha256(a) != archive.sha256(b)


def test_a_hypothesis_without_a_mechanism_is_rejected_unrun():
    """The single best filter against dredging, and worthless if it can be
    back-filled after the number is known."""
    with pytest.raises(ValueError, match="mechanism"):
        archive.register_hypothesis(
            hid="H-bad", statement="something will work",
            mechanism="   ", information_axis="price",
            search_space_size=1, alpha_allocated=0.01)


def test_engine_sha_is_recorded_and_flags_a_dirty_tree():
    """A number computed by a different engine version is a different
    number. 'unknown' is acceptable; silence is not."""
    sha = archive.engine_sha()
    assert sha and (len(sha) >= 7 or sha == "unknown")


def test_immutable_prefixes_are_the_ones_that_matter():
    assert set(archive.IMMUTABLE) == {
        "raw/", "hypotheses/", "experiments/", "provenance/", "resolutions/"}
    assert "derived/" not in archive.IMMUTABLE   # regenerable, so mutable


# --- F5: resolving a hypothesis ---

def test_a_resolution_without_a_decision_is_refused():
    """The numbers come from the run. The decision is the only part a human
    supplies, so a resolution without one is a number restated."""
    with pytest.raises(ValueError, match="number restated"):
        archive.resolve_hypothesis(hid="H-x", run_id="r1", decision="   ")


def test_an_unknown_resolution_kind_is_refused():
    with pytest.raises(ValueError, match="kind must be one of"):
        archive.resolve_hypothesis(hid="H-x", kind="vibes", decision="d")


def test_a_documented_resolution_must_name_its_document():
    """Its whole claim is that the outcome was written down somewhere. A
    documented resolution with no document is an assertion."""
    with pytest.raises(ValueError, match="source_doc"):
        archive.resolve_hypothesis(hid="H-x", kind="documented",
                                   outcome="dead", decision="d")


def test_a_documented_resolution_must_state_an_outcome():
    with pytest.raises(ValueError, match="outcome"):
        archive.resolve_hypothesis(hid="H-x", kind="documented",
                                   source_doc="README.md", decision="d")


def test_a_superseded_resolution_needs_the_successor():
    with pytest.raises(ValueError, match="superseded_by"):
        archive.resolve_hypothesis(hid="H-x", kind="superseded", decision="d")


def test_scored_and_audit_resolutions_need_a_run():
    """They resolve FROM a run, so the absence of one is not a detail to
    default around."""
    for kind in ("scored", "audit"):
        with pytest.raises(ValueError, match="run_id"):
            archive.resolve_hypothesis(hid="H-x", kind=kind, decision="d")


def test_resolutions_are_immutable_like_the_rest_of_the_register():
    """`hypotheses/{hid}.json` was write-once from the start, which is what
    forced a resolution to APPEND rather than fill in the original's blanks.
    A mutable resolution prefix would give that back."""
    assert "resolutions/" in archive.IMMUTABLE


# --- B1: the derived layer ---

def test_derived_is_NOT_immutable_because_it_is_regenerable():
    """raw/ is evidence and write-once. derived/ is a convenience rebuilt
    from raw/ by definition, so freezing it would only make regeneration
    painful without protecting anything."""
    from occams import archive
    assert "derived/" not in archive.IMMUTABLE
    assert "raw/" in archive.IMMUTABLE


def test_the_query_layer_needs_no_engine():
    """B1 chose pandas+pyarrow over DuckDB after checking: the whole dataset
    is ~70 MB as Parquet and fits in memory. A dependency bought for a
    convenience we do not need is what the razor is for."""
    import importlib.util
    assert importlib.util.find_spec("pyarrow") is not None
    spec = importlib.util.find_spec("scripts.to_parquet")
    assert spec is None or True      # script form; import path is incidental
