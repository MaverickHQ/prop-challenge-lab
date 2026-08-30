"""The charset guard must fire on the real slips and stay silent otherwise.

A guard that has never been shown to fail is not evidence of anything —
this file exists so `make check`'s "clean" line means something. Both
cases below are the ones that actually happened in this repo.
"""

from __future__ import annotations

from pathlib import Path

from occams.charset import check_text, script_of


def test_the_actual_slip_is_caught():
    """2026-07-31: the Chinese word for 'condition' appeared mid-sentence
    in docs/TASKS.md."""
    # The offending word is built from escapes, not written literally:
    # this file must itself pass the guard, and an exemption list would be
    # a hole in it. \u6761\u4ef6 is Chinese for "condition".
    bad = check_text("the Pine fill-watcher's\n\u6761\u4ef6 was written")
    assert len(bad) == 2                       # two characters
    line_no, _, reason = bad[0]
    assert line_no == 2                        # reported where it is
    assert "CJK" in reason


def test_pine_files_must_be_pure_ascii():
    """Commit 3490f68: TradingView mangles any non-ASCII, and an em-dash
    is legitimate everywhere else in the repo — so .pine is stricter."""
    text = "// range high — the boundary"
    assert check_text(text) == []              # fine in a .md
    assert len(check_text(text, ascii_only=True)) == 1   # not in a .pine


def test_legitimate_typography_is_not_flagged():
    """The repo really does contain ~30 non-ASCII characters. A guard that
    fires on em-dashes gets switched off within a week."""
    assert check_text("MES — 09:30→09:45 · §4 · 3 × $175 · ≥ 40 trades "
                      "· ±2 ticks · ≈0.1R · ✅") == []


def test_other_wrong_language_slips_are_caught():
    for sample, script in (("\u043f\u0440\u0438\u0432\u0435\u0442", "Cyrillic"),
                           ("\u3053\u3093\u306b\u3061\u306f", "Hiragana"),
                           ("\uc548\ub155\ud558\uc138\uc694", "Hangul"),
                           ("\u0645\u0631\u062d\u0628\u0627", "Arabic")):
        assert check_text(sample), f"{script} not caught"


def test_script_of_names_the_system():
    assert script_of("\u6761") == "CJK"
    assert script_of("—") is None
    assert script_of("a") is None


def test_the_scan_sees_a_file_that_is_not_yet_TRACKED():
    """The gap that let a Greek character reach a commit on 2026-08-03.

    `git ls-files` lists tracked files only, so a brand-new file is
    invisible to the scan until AFTER it has been committed -- one commit
    too late. `make check` running before `git add` is the normal order, so
    this was not an unlikely path.
    """
    from occams import charset
    probe = Path("__scan_probe__.md")
    probe.write_text("probe\n")
    try:
        assert probe in charset.scannable_files()
    finally:
        probe.unlink(missing_ok=True)


def test_the_scan_still_excludes_git_ignored_paths():
    """`data/` holds licensed vendor bars and must stay out of the scan --
    widening to untracked files must not widen to ignored ones."""
    from occams import charset
    assert not [f for f in charset.scannable_files()
                if str(f).startswith("data/")]
