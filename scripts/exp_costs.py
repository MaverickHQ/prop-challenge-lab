# FROZEN EVIDENCE - archived under experiments/E3-COSTS/.
"""E3 — measure the cost model instead of assuming it.

Commission is 0.05-0.09R per trade against an edge of ~0.03R gross, so
slippage sits in the same arithmetic and is currently a guess: 1 tick. If
it is really 2, every net number in the register moves by about the size of
the edge.

Measured off the trades tape bought for R2.1 -- aggressor side and size on
every print, 09:45-10:15 ET, the exact window our entries fall in.

Readouts fixed at registration:
  * distribution of print sizes -- is 6 contracts material?
  * effective spread from consecutive OPPOSITE-aggressor prints
  * share of prints at or above our typical order size
  * implied slippage in ticks at 1, 3 and 6 contracts
"""
import gzip
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np

TICK = 0.25
SIZES = (1, 3, 6)


def load(inst_dir: Path, limit: int = 60):
    """A sample of sessions; every print in each."""
    out = []
    for f in sorted(inst_dir.glob("*.ndjson.gz"))[-limit:]:
        px, sz, sd = [], [], []
        with gzip.open(f, "rt") as fh:
            for ln in fh:
                if not ln.strip():
                    continue
                r = json.loads(ln)
                if r.get("action") != "T":       # trades only
                    continue
                px.append(int(r["price"]) / 1e9)
                sz.append(int(r["size"]))
                sd.append(r.get("side", "N"))
        if px:
            out.append((np.array(px), np.array(sz), np.array(sd)))
    return out


def analyse(sessions, label):
    all_sz = np.concatenate([s for _, s, _ in sessions])
    spreads, walks = [], {n: [] for n in SIZES}
    for px, sz, sd in sessions:
        # effective spread: consecutive prints on OPPOSITE aggressor sides
        for i in range(1, len(px)):
            if sd[i] != sd[i - 1] and sd[i] in "AB" and sd[i - 1] in "AB":
                d = abs(px[i] - px[i - 1])
                if d <= 4 * TICK:            # ignore genuine moves
                    spreads.append(d)
        # implied slippage: to fill N contracts starting at print i, how far
        # does price travel across consecutive same-side prints?
        for n in SIZES:
            for i in range(0, len(px) - 20, 97):     # sparse, unbiased sample
                need, j, start = n, i, px[i]
                while need > 0 and j < len(px):
                    need -= sz[j]
                    j += 1
                if need <= 0 and j > i:
                    walks[n].append(abs(px[j - 1] - start))
    sp = np.array(spreads)
    print(f"\n=== {label} ===")
    print(f"  prints sampled            {len(all_sz):,}")
    print(f"  print size  median {int(np.median(all_sz))}  "
          f"mean {all_sz.mean():.1f}  p90 {int(np.percentile(all_sz,90))}  "
          f"max {int(all_sz.max())}")
    for n in SIZES:
        print(f"  prints >= {n:>2} contracts     "
              f"{(all_sz >= n).mean():>6.1%}")
    print(f"  effective spread (median) {np.median(sp)/TICK:.2f} ticks  "
          f"(mean {sp.mean()/TICK:.2f})")
    res = {"print_size_median": int(np.median(all_sz)),
           "print_size_p90": int(np.percentile(all_sz, 90)),
           "spread_ticks_median": round(float(np.median(sp)) / TICK, 3),
           "spread_ticks_mean": round(float(sp.mean()) / TICK, 3)}
    for n in SIZES:
        w = np.array(walks[n])
        med = float(np.median(w)) / TICK if len(w) else 0.0
        p90 = float(np.percentile(w, 90)) / TICK if len(w) else 0.0
        print(f"  fill {n:>2} contracts: travel  median {med:.2f} ticks, "
              f"p90 {p90:.2f}")
        res[f"walk_ticks_median_{n}"] = round(med, 3)
        res[f"walk_ticks_p90_{n}"] = round(p90, 3)
        res[f"share_prints_ge_{n}"] = round(float((all_sz >= n).mean()), 4)
    return res


if __name__ == "__main__":
    base = Path("data/orderflow")
    out = {}
    for inst, d in (("MES", base / "MES_v_0"), ("MNQ", base / "MNQ_v_0")):
        if not d.is_dir():
            continue
        out[inst] = analyse(load(d), inst)
    print("\nsealed model assumes 1 tick of slippage and $1.25/side")
    from occams import experiment
    experiment.emit(out)
