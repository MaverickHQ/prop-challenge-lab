"""Fail the build if a deployable artifact contains anything it must not.

`occams.privacy` scans **tracked** files, so by construction it cannot see
the things git deliberately ignores — `.env`, `venue.local.md`, `data/`.
Those are exactly the files a packager sweeps in anyway: SAM does not read
`.gitignore`, and a `.samignore` is silently ignored by the Python
builder. A first build proved it, producing a 533 MB artifact carrying
purchased bars, the API key, the Telegram token and the venue name.

So this scans the built tree itself, and the build target runs it before
the artifact can ever reach `sam deploy`.

Usage:  python3 scripts/check_artifact.py <artifact-dir>
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from occams.privacy import load_terms, scan_files  # noqa: E402

# Lambda's own ceiling. Exceeding it fails the deploy anyway, but a size
# blow-up is usually the symptom of having swept in something unwanted.
MAX_UNZIPPED_MB = 250

# The one data file that SHOULD ship: our own derived, sealed calendar
# (259 rows) that the morning card reads. Vendor bars never ship.
ALLOWED_DATA = {"occams/data/economic_calendar.csv"}

FORBIDDEN_NAMES = (".env", ".privacy-terms")
FORBIDDEN_SUFFIXES = (".dbn", ".ndjson", ".local.md")


def offences(root: Path) -> list[str]:
    bad: list[str] = []
    for f in sorted(root.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(root).as_posix()
        if rel in ALLOWED_DATA:
            continue
        name = f.name
        if name.startswith(FORBIDDEN_NAMES) or name in FORBIDDEN_NAMES:
            bad.append(f"secret/config file shipped: {rel}")
        elif rel.startswith("data/"):
            bad.append(f"licensed vendor data shipped: {rel}")
        elif rel.endswith(FORBIDDEN_SUFFIXES):
            bad.append(f"forbidden file type shipped: {rel}")
    return bad


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit("usage: check_artifact.py <artifact-dir>")
    root = Path(sys.argv[1])
    if not root.is_dir():
        sys.exit(f"no such artifact dir: {root}")

    bad = offences(root)

    # Venue name (B-C5) and any other forbidden term, in the artifact
    # rather than in git. Skip the vendored dependency tree — third-party
    # packages are not ours and produce only noise.
    ours = [f for f in root.rglob("*.py")
            if f.is_file() and not any(
                p in ("numpy", "numpy.libs") or p.endswith(".dist-info")
                for p in f.relative_to(root).parts)]
    ours += [f for f in root.rglob("*.md") if f.is_file()]
    ours += [f for f in root.rglob("*.txt") if f.is_file()]
    for f, _ in scan_files(ours, load_terms(".privacy-terms")):
        bad.append(f"forbidden term (B-C5) in: {f.relative_to(root)}")

    size_mb = sum(f.stat().st_size for f in root.rglob("*")
                  if f.is_file()) / 1e6
    if size_mb > MAX_UNZIPPED_MB:
        bad.append(f"artifact is {size_mb:.0f} MB, over Lambda's "
                   f"{MAX_UNZIPPED_MB} MB unzipped limit")

    if bad:
        print(f"ARTIFACT CHECK FAILED ({len(bad)} problems):")
        for b in bad:
            print(f"  - {b}")
        return 1
    print(f"artifact check: clean, {size_mb:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
