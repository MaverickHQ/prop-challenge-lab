"""Re-score every archived result under the MEASURED intra-cluster
correlation.

`rho = 0.9` was asserted when the design effect was introduced (E4.2) and
never checked. Measured on 1,637 paired trading days it is **0.3818**, CI
[0.3396, 0.4224]. `effective_n = n / (1 + (m-1)*rho)`, so the register has
been crediting itself with LESS effective sample than it had, and every
detectable floor derived from it is too high.

WHY THIS RUNS OVER EVERYTHING. The correction moves floors DOWN, which turns
some nulls into findings -- the direction that needs most scrutiny. Applying
it only where it flatters is the defect; applying it everywhere and
reporting what moved is the fix. A result that changes verdict here is a
FINDING ABOUT THE OLD POWER MODEL, not a new discovery about the market.

The estimate and the interval are UNTOUCHED. Intervals come from the cluster
bootstrap, which resamples dates and never uses `intra_r`. Only the floor
moves -- so `crosses_zero` cannot change, and any verdict shift is strictly
between "immaterial/null" and "detectable/inconclusive".
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from occams import archive, power                     # noqa: E402
from occams.result import Result, blocks              # noqa: E402

ASSUMED, MEASURED = 0.90, 0.3818
CLUSTER_SIZE = 2


def rescore(b: dict) -> dict | None:
    """Floor under measured rho. None when the block cannot be re-scored."""
    n, floor, est = b.get("n"), b.get("floor"), b.get("estimate")
    if not all(isinstance(x, (int, float)) for x in (n, floor, est)):
        return None
    ne_old = power.effective_n(int(n), cluster_size=CLUSTER_SIZE,
                               intra_r=ASSUMED)
    dms_old = power.detectable_mean_shift(ne_old)
    if dms_old <= 0:
        return None
    sd = floor / dms_old                       # recovered, not re-simulated
    ne_new = power.effective_n(int(n), cluster_size=CLUSTER_SIZE,
                               intra_r=MEASURED)
    new_floor = power.detectable_mean_shift(ne_new) * sd
    ci = b.get("ci") or [b.get("ci_low"), b.get("ci_high")]
    try:
        lo, hi = float(ci[0]), float(ci[1])
    except (TypeError, ValueError, IndexError):
        return None
    old = Result(name="", estimate=est, ci=(lo, hi), n=int(n),
                 floor=floor, d=est)
    new = Result(name="", estimate=est, ci=(lo, hi), n=int(n),
                 floor=new_floor, d=est)
    return {"n": int(n), "n_eff_old": ne_old, "n_eff_new": ne_new,
            "floor_old": floor, "floor_new": new_floor,
            "verdict_old": old.verdict, "verdict_new": new.verdict,
            "moved": old.verdict != new.verdict}


def main() -> int:
    s3 = archive._client()
    bucket = archive.bucket()
    keys = sorted({r.get("key", "") for r in archive.manifest()})
    exps = [k for k in keys if k.startswith("experiments/")
            and k.endswith(".json") and k.count("/") == 2
            and not k.startswith("experiments/campaign/")]

    print(f"rho: assumed {ASSUMED} -> measured {MEASURED}  "
          f"(1,637 paired days, CI [0.340, 0.422])")
    print(f"scanning {len(exps)} archived run records\n")
    print(f"{'hypothesis / block':44s} {'n':>6s} {'floor':>16s} {'verdict':>26s}")
    print("-" * 96)

    scanned = moved = 0
    for key in exps:
        rec = json.loads(s3.get_object(Bucket=bucket, Key=key)["Body"].read())
        for path, b in sorted(blocks(rec.get("metrics", {})).items()):
            out = rescore(b)
            if out is None:
                continue
            scanned += 1
            label = f"{rec.get('hypothesis_id')}.{path or '.'}"
            flag = "  <-- MOVED" if out["moved"] else ""
            if out["moved"]:
                moved += 1
            print(f"{label[:44]:44s} {out['n']:>6,} "
                  f"{out['floor_old']:>7.4f}->{out['floor_new']:<7.4f} "
                  f"{out['verdict_old'][:12]:>12s} -> "
                  f"{out['verdict_new'][:12]:<12s}{flag}")

    print(f"\n  {scanned} scored blocks re-scored, {moved} changed verdict")
    if moved == 0:
        print("  Nothing moved. The correction is real and its consequences "
              "for the register are nil -- which is worth knowing, and is "
              "the outcome that could not have been assumed.")
    else:
        print("  A verdict that moved is a finding about the OLD POWER "
              "MODEL, not a new discovery about the market. Each needs an "
              "appended resolution naming this backfill as its cause.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
