"""F5 — resolve registered hypotheses from the runs that answered them.

    python3 scripts/resolve.py                  propose, write nothing
    python3 scripts/resolve.py --hid X1-COMPRESSION --path primary \\
        --decision "..."                        propose ONE, still dry
    python3 scripts/resolve.py --hid ... --path ... --decision "..." --commit

**Dry by default, and deliberately so.** The register is append-only: a
resolution written in error cannot be deleted, only superseded, and the
supersession is permanent too. So writing is opt-in per hypothesis rather
than a batch that runs over twenty records at once.

WHAT THIS TOOL WILL AND WILL NOT DO. It reads the outcome -- verdict,
estimate, interval, floor, n -- from the archived run, because a number
retyped is a number free to disagree with its source. It will NOT invent
the `decision`: what the programme does about a result is a judgement, it
is the whole reason a human is in this loop, and a tool that guessed it
would be manufacturing the most important field in the record.

So the listing below shows what CAN be resolved and with what numbers. The
sentence that goes with each is yours.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from occams import archive  # noqa: E402
from occams.result import blocks  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def survey() -> dict:
    """What is registered, what has been run, and what could resolve what."""
    s3 = archive._client()
    bucket = archive.bucket()
    keys = sorted({r.get("key", "") for r in archive.manifest()})

    def get(key):
        return __import__("json").loads(
            s3.get_object(Bucket=bucket, Key=key)["Body"].read())

    hyps = {}
    for k in keys:
        if k.startswith("hypotheses/") and k.endswith(".json"):
            h = get(k)
            hyps[h.get("id")] = h

    runs = []
    for k in keys:
        if (k.startswith("experiments/") and k.endswith(".json")
                and not k.startswith("experiments/campaign/")
                and k.count("/") == 2):
            e = get(k)
            if e.get("hypothesis_id"):
                runs.append(e)

    resolved = {r.get("hypothesis_id") for r in archive.resolutions()}

    candidates = []
    for e in sorted(runs, key=lambda x: (str(x.get("hypothesis_id")),
                                         str(x.get("run_id")))):
        for path, r in sorted(blocks(e.get("metrics", {})).items()):
            candidates.append({"hid": e.get("hypothesis_id"),
                               "run_id": e.get("run_id"), "path": path,
                               "result": r})
    return {"hypotheses": hyps, "runs": runs, "resolved": resolved,
            "candidates": candidates}


def render(s: dict) -> str:
    lines = []
    hyps, cands, resolved = s["hypotheses"], s["candidates"], s["resolved"]
    ran = {c["hid"] for c in cands}

    lines.append("=" * 74)
    lines.append("RESOLVABLE — a registered hypothesis with a scored result")
    lines.append("=" * 74)
    for c in cands:
        r = c["result"]
        mark = "already resolved" if c["hid"] in resolved else ""
        lines.append(f"\n  {c['hid']}  ({c['run_id']}, path={c['path'] or '.'})"
                     f"  {mark}")
        lines.append(f"    {str(r.get('name', ''))[:66]}")
        ci = r.get("ci") or [r.get("ci_low"), r.get("ci_high")]
        try:
            cis = f"[{float(ci[0]):+.4f}, {float(ci[1]):+.4f}]"
        except (TypeError, ValueError, IndexError):
            cis = "--"
        lines.append(f"    verdict {str(r.get('verdict')):<22} "
                     f"estimate {r.get('estimate')}")
        lines.append(f"    CI {cis:<26} floor {r.get('floor')}"
                     f"   n {r.get('n')}")

    unrun = sorted(set(hyps) - ran)
    lines.append("\n" + "=" * 74)
    lines.append(f"NOT RESOLVABLE FROM THE ARCHIVE — {len(unrun)} registered "
                 f"hypotheses")
    lines.append("=" * 74)
    lines.append("  No scored result is archived against these, so there is")
    lines.append("  nothing to read an outcome from. Some were answered in")
    lines.append("  prose and never written back; some were never run. The")
    lines.append("  register cannot tell those apart, which is exactly the")
    lines.append("  gap F5 exists to close going forward.\n")
    for hid in unrun:
        lines.append(f"    {hid}")

    lines.append("\n" + "=" * 74)
    lines.append(f"{len(cands)} resolvable - {len(resolved)} already resolved "
                 f"- {len(unrun)} with no scored result")
    lines.append("Nothing was written. To resolve one:")
    lines.append("  python3 scripts/resolve.py --hid HID --run RUN "
                 "--path PATH \\")
    lines.append("      --decision \"what the programme does about it\" "
                 "--commit")
    lines.append("=" * 74)
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hid")
    ap.add_argument("--run")
    ap.add_argument("--path", default="")
    ap.add_argument("--decision", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--supersedes", default="")
    ap.add_argument("--commit", action="store_true",
                    help="actually write. Without it, nothing is written.")
    a = ap.parse_args()

    if not a.hid:
        print(render(survey()))
        return 0

    if not a.commit:
        print(f"DRY RUN. Would resolve {a.hid} from run {a.run} "
              f"at path {a.path or '.'}\n"
              f"  decision: {a.decision or '(none given — will be REFUSED)'}\n"
              f"Add --commit to write. The register is append-only, so this "
              f"cannot be undone, only superseded.")
        return 0

    rec = archive.resolve_hypothesis(
        hid=a.hid, run_id=a.run, metric_path=a.path, decision=a.decision,
        note=a.note, supersedes=a.supersedes)
    print(f"resolved {rec['hypothesis_id']} -> {rec['outcome']} "
          f"(effect {rec['effect_size']}, from run {rec['run_id']})")
    print(f"  written to resolutions/{rec['hypothesis_id']}/"
          f"{rec['run_id']}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
