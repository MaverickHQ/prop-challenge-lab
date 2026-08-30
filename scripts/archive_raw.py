"""B3 — put the purchased data somewhere it will outlive this machine.

Unblocked by A1: the user confirmed our licensed copy may live in our own
private bucket -- internal use, not redistribution.

Right now 1.5 GB of order-flow tape and 400 MB of bars exist ONLY on one
laptop, which is precisely the situation the archive was built to end. Every
file goes in with a sha256 and a provenance row, so a wiped machine can be
rebuilt and any restored byte can be proved identical to what was bought.

`raw/` is write-once, so re-running skips what is already there rather than
re-uploading or failing.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from occams import archive  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def targets() -> list[tuple[Path, str, str]]:
    out: list[tuple[Path, str, str]] = []
    for name in ("MES.csv", "MNQ.csv", "MES.definition.csv",
                 "MNQ.definition.csv", "MES.dbn", "MNQ.dbn",
                 "MES.definition.dbn", "MNQ.definition.dbn"):
        p = DATA / name
        if p.exists():
            out.append((p, f"raw/databento/{name}",
                        "GLBX.MDP3 ohlcv-1m 2019-2026, purchased 2026-07-05"))
    for inst in ("MES_v_0", "MNQ_v_0"):
        d = DATA / "orderflow" / inst
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.ndjson.gz")):
            out.append((f, f"raw/orderflow/{inst}/{f.name}",
                        "GLBX.MDP3 trades 09:45-10:15 ET, purchased 2026-08-01"))
    return out


def main() -> int:
    t = targets()
    done = skipped = 0
    total = sum(p.stat().st_size for p, _, _ in t)
    print(f"{len(t)} files, {total/1e9:.2f} GB")
    for i, (p, key, note) in enumerate(t, 1):
        try:
            archive.put(p, key, source="databento", note=note)
            done += 1
        except FileExistsError:
            skipped += 1
        if i % 100 == 0 or i == len(t):
            print(f"  {i}/{len(t)}  uploaded {done}, already present {skipped}")
    print(f"\nuploaded {done}, skipped {skipped}. "
          f"provenance rows now {len(archive.manifest())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
