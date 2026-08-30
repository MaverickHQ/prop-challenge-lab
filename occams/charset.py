"""Catch stray foreign-script characters before they reach a file.

This has now happened twice. Commit 3490f68 purged a stray non-ASCII char
from the Pine aid, where TradingView mangles them and it broke the display.
On 2026-07-31 the Chinese word for "condition" appeared mid-sentence in
docs/TASKS.md, written by an LLM whose internal representation of a
concept is not tied to one language — so the wrong language's surface
token surfaces occasionally, usually at a line break.

The rule is a DENYLIST of writing systems, not an allowlist of symbols.
The repo legitimately contains 30-odd non-ASCII characters — em-dashes,
arrows, §, ×, ≥, box drawing, a few emoji — so banning non-ASCII outright
would produce constant false positives and be switched off within a week.
Banning scripts that cannot appear in an English codebase costs nothing
and catches the real failure exactly.

`.pine` is stricter: TradingView mangles ANY non-ASCII, so those files
must be pure ASCII. That rule is what the earlier incident needed.
"""

from __future__ import annotations

import subprocess
import sys
import unicodedata
from pathlib import Path

# Writing systems that cannot legitimately appear here. Named rather than
# enumerated so the failure message can say what it found.
DENIED_RANGES: list[tuple[int, int, str]] = [
    (0x0370, 0x03FF, "Greek"),
    (0x0400, 0x04FF, "Cyrillic"),
    (0x0530, 0x058F, "Armenian"),
    (0x0590, 0x05FF, "Hebrew"),
    (0x0600, 0x06FF, "Arabic"),
    (0x0900, 0x097F, "Devanagari"),
    (0x0E00, 0x0E7F, "Thai"),
    (0x3040, 0x309F, "Hiragana"),
    (0x30A0, 0x30FF, "Katakana"),
    (0x3400, 0x4DBF, "CJK ext A"),
    (0x4E00, 0x9FFF, "CJK"),
    (0xAC00, 0xD7AF, "Hangul"),
    (0xF900, 0xFAFF, "CJK compat"),
]

TEXT_SUFFIXES = {".py", ".md", ".pine", ".toml", ".json", ".yaml", ".yml",
                 ".txt", ".cfg", ".sh", ".csv"}


def script_of(ch: str) -> str | None:
    """Name of the denied writing system `ch` belongs to, else None."""
    cp = ord(ch)
    for lo, hi, name in DENIED_RANGES:
        if lo <= cp <= hi:
            return name
    return None


def check_text(text: str, *, ascii_only: bool = False
               ) -> list[tuple[int, str, str]]:
    """[(line_no, char, reason)] for every offending character."""
    bad: list[tuple[int, str, str]] = []
    for n, line in enumerate(text.splitlines(), 1):
        for ch in line:
            if ord(ch) < 128:
                continue
            if ascii_only:
                bad.append((n, ch, "non-ASCII in a .pine file "
                                   "(TradingView mangles these)"))
                continue
            script = script_of(ch)
            if script:
                name = unicodedata.name(ch, "?")
                bad.append((n, ch, f"{script} character ({name})"))
    return bad


def scannable_files() -> list[Path]:
    """Everything the next commit would contain: tracked files PLUS
    untracked ones that are not git-ignored.

    `git ls-files` alone lists only TRACKED files, which means a brand-new
    file is invisible to this scan until after it has been committed --
    exactly one commit too late. That gap was not hypothetical: on
    2026-08-03 a Greek character reached a commit in a new write-up because
    `make check` ran before `git add`, the file was still untracked, and the
    scan therefore had nothing to look at. The archive guard caught it on
    upload, which was luck of ordering rather than design.

    `--others --exclude-standard` adds the untracked-but-not-ignored set, so
    `data/` and other ignored paths stay out.
    """
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        capture_output=True, text=True, check=True).stdout.splitlines()
    seen, files = set(), []
    for f in out:
        if f in seen or Path(f).suffix not in TEXT_SUFFIXES:
            continue
        seen.add(f)
        files.append(Path(f))
    return files


def tracked_files() -> list[Path]:
    """Deprecated alias. Kept so any caller still asking for the narrower
    set gets the wider one rather than a silent miss."""
    return scannable_files()


def main() -> int:
    problems = 0
    files = scannable_files()
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_no, ch, reason in check_text(
                text, ascii_only=f.suffix == ".pine"):
            print(f"CHARSET: {f}:{line_no} contains {ch!r} — {reason}")
            problems += 1
    if problems:
        print(f"\n{problems} stray character(s). These are almost always a "
              f"slip, not intent — replace with the English/ASCII equivalent.")
        return 1
    print(f"charset: {len(files)} text files clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
