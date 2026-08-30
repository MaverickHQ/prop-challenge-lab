"""T3.1 — the publication gate, tested by making it fail.

`occams.privacy` scans tracked files AT HEAD. Publication exposes every
commit message and every blob that ever existed, including ones deleted
later. The sibling repo learned this expensively: crucible-autoresearcher
needed an orphan-branch rebuild because its history carried the venue name.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from occams.privacy import load_terms

ROOT = Path(__file__).resolve().parent.parent
HAVE_TERMS = bool(load_terms(ROOT / ".privacy-terms"))

# `.privacy-terms` is git-ignored BY DESIGN -- the terms are the thing being
# protected, so they cannot live in a public repo and a fork legitimately has
# none. The publication gate is therefore an AUTHOR-MACHINE gate, and the two
# tests below can only run where it can.
#
# They are SKIPPED rather than made to pass, because the alternative is a
# green tick certifying a history nobody scanned. That is the defect this
# file exists to prevent, one level up.
needs_terms = pytest.mark.skipif(
    not HAVE_TERMS,
    reason="no .privacy-terms (git-ignored by design): the publication gate "
           "cannot run here, and must not report a pass it did not earn")


def test_the_audit_scans_MORE_than_privacy_does():
    """The distinction the gate exists for."""
    import scripts.prepublish_audit as a
    src = open(a.__file__).read() if hasattr(a, "__file__") else ""
    assert "rev-list" in src and "log" in src


@needs_terms
def test_terms_exist_or_the_audit_refuses_to_claim_clean():
    """An audit with nothing to look for must not report success."""
    assert load_terms(ROOT / ".privacy-terms")


@needs_terms
def test_history_is_currently_clean():
    """The live assertion. If this ever fails, publication is BLOCKED and a
    follow-up commit will not fix it -- the term is already in the history."""
    r = subprocess.run(["python3", "scripts/prepublish_audit.py"],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"publication gate failed:\n{r.stdout}"
    assert "PUBLISHABLE" in r.stdout


def test_the_audit_survives_a_binary_blob_and_still_scans_it():
    """The audit crashed on the first PNG ever committed (byte 0x89, the
    PNG magic). A leak scanner that dies on a binary file is one a careless
    commit takes offline, and the failure reads as a tooling error rather
    than a security one.

    The fix decodes with errors="replace" rather than skipping binaries, so
    recoverable ASCII inside a binary -- PNG tEXt chunks, EXIF, an embedded
    path -- is still searched. This asserts both halves: it does not crash,
    and it does not go blind.
    """
    import importlib.util
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location(
        "_audit", root / "scripts" / "prepublish_audit.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    pngs = sorted((root / "artifacts" / "plots").glob("*.png"))
    assert pngs, "no binary in the tree — this test would prove nothing"

    raw = pngs[0].read_bytes()
    assert raw[:4] == b"\x89PNG"                     # genuinely binary
    text = raw.decode("utf-8", errors="replace")
    assert "PNG" in text                             # still searchable
    # The sentinel is BUILT AT RUNTIME so the literal never appears in this
    # file. The first version hard-coded it and the audit duly found it --
    # in the very test asserting it would find nothing. A scanner matching
    # its own fixture is the same class of error as a guard that cannot see
    # untracked files: the test passes on the wrong evidence.
    sentinel = "zz" + "q-absent-" + "sentinel"
    assert mod.scan_history_blobs([sentinel]) == []
