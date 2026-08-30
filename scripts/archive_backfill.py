"""D5/D6 — put everything produced so far into the durable archive.

Idempotent: the write-once prefixes refuse a second upload, so re-running
reports what is already there rather than failing or duplicating.

`raw/` vendor data is NOT included here — it is gated on D0.6, the licence
confirmation, which is a user decision and not mine to assume.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from occams import archive  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VAULT_FIGS = Path.home() / "Documents/maverick-hq/autoresearch/figures"

# D6.1 sealed governance — the documents a result is judged against
GOVERNANCE = ["PREREG.md", "PREREG.sealed", "PAPER-PREREG.md",
              "AMENDMENT-4a.md", "PROTOCOLS.md", "SPEND.md", "RULES.md",
              "VERDICT-2026-07-06.md", "VERDICT-2026-07-06-v2.md",
              "VERDICT-2026-07-06-v3.md", "EVIDENCE.md", "CONTEXT.md",
              "FEASIBILITY.md", "DIAGNOSTICS.md", "RESEARCH-PROGRAM.md",
              "AWS-RECON.md", "aws-recon-latency.md",
              "aws-recon-samples.jsonl", "day-state-machine.md"]


def send(local: Path, key: str, note: str, source: str = "repo") -> None:
    if not local.exists():
        print(f"  -- missing, skipped: {local.name}")
        return
    try:
        row = archive.put(local, key, source=source, note=note)
        print(f"  ok  {key:<58} {row['bytes']:>9,} B")
    except FileExistsError:
        print(f"  ={''} already archived: {key}")
    except ValueError as e:
        print(f"  !! {e}")


def main() -> int:
    print("D6.1 sealed governance ->  artifacts/governance/")
    for name in GOVERNANCE:
        send(ROOT / "docs" / name, f"artifacts/governance/{name}",
             "sealed governance / verdict record")

    print("\nD6.4 figures ->  artifacts/figures/")
    if VAULT_FIGS.is_dir():
        for f in sorted(VAULT_FIGS.glob("*.png")):
            send(f, f"artifacts/figures/{f.name}",
                 "autoresearch essay figure", source="vault")
    else:
        print(f"  -- no figures directory at {VAULT_FIGS}")

    print("\nD6.5 live campaign record ->  experiments/campaign/")
    for name in ("paper_logs.jsonl", "paper_state.json", "paper_offset.txt"):
        send(ROOT / "data" / name, f"experiments/campaign/local-{name}",
             "local campaign record to date", source="local-campaign")

    print("\nD6.3 test fixtures ->  derived/fixtures/")
    fx = ROOT / "tests" / "fixtures"
    for f in sorted(fx.glob("*.json")) if fx.is_dir() else []:
        send(f, f"derived/fixtures/{f.name}",
             "recorded bars backing the poller tests")

    print("\nprovenance rows:", len(archive.manifest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
