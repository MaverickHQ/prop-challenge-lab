"""Privacy scanner — forbidden terms must never enter tracked files.

The terms themselves are git-ignored (.privacy-terms), so even the scanner
config can't leak them. Fixture-tested; `make check` runs the live scan.
"""

from __future__ import annotations

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


def main() -> int:
    terms = load_terms(".privacy-terms")
    if not terms:
        print("privacy: no .privacy-terms file — nothing to scan")
        return 0
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
