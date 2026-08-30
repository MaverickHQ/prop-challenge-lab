"""T3.1 — can this repository be published without leaking anything?

`occams.privacy` scans TRACKED FILES AT HEAD. Publication exposes something
much larger: every commit message, every file in every historical tree, and
every blob that was ever added and later deleted. A term removed in a later
commit is still in the history and still public.

This is the gate on Track 3. The sibling repo already learned it the
expensive way -- crucible-autoresearcher needed an orphan-branch rebuild
because its history carried the venue name, which is why only its
`public-release` branch may ever be pushed.

Read-only. Reports; never rewrites history.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from occams.charset import check_text  # noqa: E402
from occams.privacy import load_terms  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _git(*args) -> str:
    """Git output as text, tolerating BINARY blobs.

    The first version decoded strictly and CRASHED on the first PNG ever
    committed (byte 0x89 — the PNG magic). A leak scanner that dies on a
    binary file is one a careless commit takes offline, and the failure
    looks like a tooling error rather than a security one.

    `errors="replace"` keeps the scan running AND keeps it useful: any
    recoverable ASCII inside a binary -- PNG tEXt chunks, EXIF, an embedded
    path, a comment in a compiled artifact -- is still searched for
    forbidden terms. Skipping binaries entirely would have been the easier
    fix and the wrong one.
    """
    out = subprocess.run(["git", *args], cwd=ROOT,
                         capture_output=True).stdout
    return out.decode("utf-8", errors="replace")


def scan_commit_messages(terms) -> list[str]:
    hits = []
    log = _git("log", "--format=%H%x00%s%x00%b%x00%an%x00%ae", "--all")
    for entry in log.split("\n"):
        if not entry.strip():
            continue
        parts = entry.split("\x00")
        sha, text = parts[0], " ".join(parts[1:]).lower()
        for t in terms:
            if t in text:
                hits.append(f"commit message {sha[:10]} contains a term")
    return hits


def scan_history_blobs(terms) -> list[str]:
    """Every path that has ever existed, at every revision it existed in."""
    hits, seen = [], set()
    paths = {p for p in _git("log", "--all", "--name-only", "--format=")
             .splitlines() if p.strip()}
    for path in sorted(paths):
        revs = _git("rev-list", "--all", "--", path).split()
        for rev in revs[:40]:                 # bounded: recent history first
            key = (rev, path)
            if key in seen:
                continue
            seen.add(key)
            blob = _git("show", f"{rev}:{path}")
            if not blob:
                continue
            low = blob.lower()
            for t in terms:
                if t in low:
                    hits.append(f"{path} @ {rev[:10]} contains a term")
                    break
    return hits


INFRA_PATTERNS = {
    "aws account id": r"(?<![\d.eE-])\d{12}(?![\d.eE-])",
    "aws access key": r"\bAKIA[0-9A-Z]{16}\b",
    "aws secret key": r"\baws_secret_access_key\s*=\s*\S+",
    "explicit arn": r"arn:aws:[a-z0-9-]+:[a-z0-9-]*:\d{12}:",
    "telegram bot token": r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b",
    "private key block": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
}
# occams/stats.py carries AS241 polynomial coefficients -- 12-digit runs that
# are mathematics, not identifiers. Excluded by name so the check keeps
# meaning something rather than being switched off wholesale.
INFRA_EXEMPT = {"occams/stats.py", "scripts/prepublish_audit.py"}


def scan_infrastructure(paths=None) -> list[str]:
    """Identifiers that are not secrets but should not be published.

    The venue scan and the charset scan between them missed an entire class:
    an AWS account id sat in six files and three commits, an IAM principal
    name shipped as a CloudFormation default, and the research bucket was
    hardcoded to one account. None of those is a credential, so none of them
    tripped a secret scanner -- and together they are a considerably better
    starting point for an attacker than any one of them alone.

    Same gap shape as the scan that could not see untracked files: the check
    was real, and it was looking in the wrong place.
    """
    import re
    hits = []
    files = paths if paths is not None else [
        Path(f) for f in _git("ls-files", "--cached", "--others",
                              "--exclude-standard").splitlines() if f.strip()]
    for f in files:
        f = Path(f)
        if str(f) in INFRA_EXEMPT or f.suffix in {".png", ".svg", ".dbn"}:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except (OSError, IsADirectoryError):
            continue
        for label, pat in INFRA_PATTERNS.items():
            if re.search(pat, text):
                hits.append(f"{f}: {label}")
    return hits


def scan_authors() -> list[str]:
    out = set()
    for line in _git("log", "--all", "--format=%an <%ae>").splitlines():
        if line.strip():
            out.add(line.strip())
    return sorted(out)


def main() -> int:
    terms = load_terms(ROOT / ".privacy-terms")
    if not terms:
        print("no .privacy-terms file — cannot audit, refusing to say clean")
        return 1
    print(f"auditing FULL history against {len(terms)} forbidden terms\n")

    msg = scan_commit_messages(terms)
    print(f"  commit messages : {len(msg)} hits")
    for h in msg[:10]:
        print(f"      {h}")

    blob = scan_history_blobs(terms)
    print(f"  historical blobs: {len(blob)} hits")
    for h in blob[:10]:
        print(f"      {h}")

    # non-ASCII in any *current* text file is a separate publication hazard
    bad_charset = 0
    for p in _git("ls-files").splitlines():
        f = ROOT / p
        if f.suffix not in {".py", ".md", ".pine", ".toml", ".json", ".txt"}:
            continue
        try:
            if check_text(f.read_text(errors="ignore"),
                          ascii_only=f.suffix == ".pine"):
                bad_charset += 1
        except OSError:
            pass
    print(f"  charset hazards : {bad_charset} files")

    infra = scan_infrastructure()
    print(f"  infrastructure  : {len(infra)} hits")
    for h in infra[:10]:
        print(f"      {h}")

    print(f"\n  commit authors  : {', '.join(scan_authors())}")
    total = len(msg) + len(blob) + len(infra)
    print(f"\n{'PUBLISHABLE — history is clean' if total == 0 else f'BLOCKED — {total} leaks in history'}")
    print("A term removed at HEAD is still public if it is anywhere in the "
          "history. Fixing that means rewriting history or an orphan branch, "
          "never a follow-up commit.")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
