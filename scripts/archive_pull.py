"""B2/D8.3 — rebuild the local working set from the archive.

The goal was never "data never touches this machine" -- analysis has to read
bytes from somewhere and streaming a gigabyte per run is pointless. The goal
is that the local copy is a CACHE: `rm -rf data/` should cost time, never
evidence.

That is only true if the restore path works, so this exists BEFORE anything
local is deleted. Every file is verified against its manifest sha256 on the
way down; a mismatch raises rather than warns, because a silently corrupted
restore is worse than a failed one.

    python3 scripts/archive_pull.py --list
    python3 scripts/archive_pull.py --prefix raw/databento
    python3 scripts/archive_pull.py --prefix raw/ --dest /tmp/restore
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from occams import archive  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
# archive key prefix -> where it belongs locally
LAYOUT = {"raw/databento/": ROOT / "data",
          "raw/orderflow/": ROOT / "data" / "orderflow",
          "derived/": ROOT / "data" / "derived"}


def local_path(key: str, dest: Path | None) -> Path:
    for pre, root in LAYOUT.items():
        if key.startswith(pre):
            rel = key[len(pre):]
            return (dest / rel) if dest else (root / rel)
    return (dest or ROOT / "data" / "_restored") / Path(key).name


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="raw/")
    ap.add_argument("--dest", type=Path, default=None,
                    help="restore elsewhere; default is the real layout")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    rows = [r for r in archive.manifest() if r["key"].startswith(a.prefix)]
    if not rows:
        sys.exit(f"nothing in the archive under {a.prefix!r}")
    size = sum(r["bytes"] for r in rows)
    print(f"{len(rows)} objects, {size/1e9:.2f} GB under {a.prefix!r}")
    if a.list:
        for r in rows[:20]:
            print(f"  {r['key']:<58} {r['bytes']:>12,} B")
        if len(rows) > 20:
            print(f"  ... and {len(rows)-20} more")
        return 0

    done = skipped = 0
    for i, r in enumerate(rows, 1):
        p = local_path(r["key"], a.dest)
        if p.exists() and archive.sha256(p) == r["sha256"]:
            skipped += 1                      # already here and identical
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        archive.get(r["key"], p)              # verifies, raises on mismatch
        done += 1
        if i % 100 == 0 or i == len(rows):
            print(f"  {i}/{len(rows)}  restored {done}, already correct "
                  f"{skipped}")
    print(f"\nrestored {done}, already correct {skipped}. "
          f"Every byte verified against its manifest hash.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
