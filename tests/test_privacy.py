"""Codex 6.2 — the privacy scanner (fixture-tested; the real forbidden terms
live in git-ignored .privacy-terms, never in the repo — including here)."""

from __future__ import annotations

from occams.privacy import load_terms, scan_files


def test_scanner_finds_forbidden_term_in_tracked_text(tmp_path) -> None:
    good = tmp_path / "ok.md"
    good.write_text("the venue is never named")
    bad = tmp_path / "leak.md"
    bad.write_text("we trade at ForbiddenCo!")
    hits = scan_files([good, bad], terms=["forbiddenco"])
    assert hits == [(bad, "forbiddenco")]


def test_scanner_is_case_insensitive_and_multi_term(tmp_path) -> None:
    f = tmp_path / "x.md"
    f.write_text("FORBIDDENCO and SecretPlan")
    hits = scan_files([f], terms=["forbiddenco", "secretplan"])
    assert len(hits) == 2


def test_terms_loader_skips_missing_file(tmp_path) -> None:
    assert load_terms(tmp_path / "absent") == []
    p = tmp_path / ".privacy-terms"
    p.write_text("# comment\nForbiddenCo\n\n")
    assert load_terms(p) == ["forbiddenco"]
