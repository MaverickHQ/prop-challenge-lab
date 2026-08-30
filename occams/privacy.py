"""Privacy scanner — forbidden terms must never enter tracked files.

The terms themselves are git-ignored (.privacy-terms), so even the scanner
config can't leak them. Fixture-tested; `make check` runs the live scan.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def load_terms(path: str | Path) -> list[str]:
    p = Path(path)
    if not p.exists():
        return []
    return [line.strip().lower() for line in p.read_text().splitlines()
            if line.strip() and not line.startswith("#")]


def scan_files(files: list[Path], terms: list[str]) -> list[tuple[Path, str]]:
    hits: list[tuple[Path, str]] = []
    for f in files:
        try:
            text = f.read_text(errors="ignore").lower()
        except (OSError, IsADirectoryError):
            continue
        for term in terms:
            if term in text:
                hits.append((f, term))
    return hits


ALLOW_EMPTY_ENV = "OCCAMS_PRIVACY_ALLOW_EMPTY"


def main() -> int:
    terms = load_terms(".privacy-terms")
    if not terms:
        # A scanner with no terms finds nothing and used to exit 0, printing
        # a line that read like a pass. That is the same defect as the test
        # that asserted a forbidden term was absent while containing it, and
        # the scanner that reported clean on files it had never opened: the
        # check was real and pointed nowhere.
        #
        # `.privacy-terms` is git-ignored by design, so a fresh clone HAS no
        # terms and that is legitimate -- a new user has no venue to protect.
        # So the disarmed state is allowed, but only when asked for, and it
        # never renders as a pass.
        if os.environ.get(ALLOW_EMPTY_ENV):
            print("privacy: DISARMED — no .privacy-terms, 0 terms checked. "
                  "This is not a pass; nothing was looked for.")
            return 0
        print("privacy: REFUSED — no .privacy-terms file, so this scan would "
              f"check nothing and report clean.\n  Set {ALLOW_EMPTY_ENV}=1 to "
              f"run it disarmed on purpose (a fresh clone has no terms).")
        return 1
    # tracked PLUS untracked-but-not-ignored: a brand-new file is invisible
    # to `git ls-files` until it has been committed, which is one commit too
    # late for a leak scan. See occams.charset.scannable_files.
    tracked = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        capture_output=True, text=True, check=True).stdout.splitlines()
    tracked = sorted(set(tracked))
    hits = scan_files([Path(t) for t in tracked], terms)
    if hits:
        for f, term in hits:
            print(f"PRIVACY LEAK: {f} contains a forbidden term")
        return 1
    print(f"privacy: {len(tracked)} files clean "
          f"(tracked + untracked, ignored paths excluded)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
