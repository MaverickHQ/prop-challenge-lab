# FROZEN EVIDENCE - archived under experiments/H5-FLOW-PREDICTS/.
"""H5 — does the tape carry directional information at the breakout at all?

Prior to any strategy. H4 asked whether imbalance improves the FADE; the
fade's entry cannot be obtained, so that question is moot. This asks the
question underneath it.

The outcome is deliberately NOT a P&L. It is a strategy-free forward
return, because the fade's defect entered through the outcome variable --
an entry assumption smuggled in as a number. A signed return from the
failure close to the session close cannot carry one.
"""
import gzip
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
from occams.loader import read_vendor_csv, to_trading_days

ET = ZoneInfo("America/New_York")
FLOW = Path("data/orderflow")


def flow_for(inst_dir: Path, d: date):
    """(ts, price, size, side) for one session, or None."""
    f = inst_dir / f"{d.isoformat()}.ndjson.gz"
    if not f.exists():
        return None
    ts, sz, sd = [], [], []
    with gzip.open(f, "rt") as fh:
        for ln in fh:
            if not ln.strip():
                continue
            r = json.loads(ln)
            if r.get("action") != "T" or r.get("side") not in ("A", "B"):
                continue
            hd = r.get("hd") or {}
            ts.append(int(hd.get("ts_event", 0)))
            sz.append(int(r["size"]))
            sd.append(r["side"])
    if not ts:
        return None
    return np.array(ts), np.array(sz), np.array(sd)


def setups(inst, flow_dir):
    days = to_trading_days(read_vendor_csv(f"data/{inst}.csv"),
                           range_minutes=15, instrument=f"{inst}.v.0")
    rows = []
    for d in days:
        fl = flow_for(flow_dir, d.date)
        if fl is None:
            continue
        rb, sb = d.range_bars, d.session_bars
        if rb is None or rb.empty or sb.empty:
            continue
        hi, lo = float(rb["high"].max()), float(rb["low"].min())
        h = hi - lo
        if h <= 0:
            continue
        H = sb["high"].to_numpy(float); L = sb["low"].to_numpy(float)
        C = sb["close"].to_numpy(float)
        bi = next((i for i in range(len(sb)) if H[i] > hi or L[i] < lo), None)
        if bi is None:
            continue
        up = H[bi] > hi
        fi = next((i for i in range(bi, len(sb))
                   if (C[i] < hi if up else C[i] > lo)), None)
        if fi is None:
            continue
        t0 = sb.index[bi].to_pydatetime().astimezone(timezone.utc)
        t1 = sb.index[fi].to_pydatetime().astimezone(timezone.utc)
        n0 = int(t0.timestamp() * 1e9)
        n1 = int(t1.timestamp() * 1e9) + 60 * 10**9      # inclusive of the bar
        ts, sz, sd = fl
        m = (ts >= n0) & (ts < n1)
        if m.sum() < 20:                    # window outside what we bought
            continue
        s, side = sz[m], sd[m]
        # aggressor side A = lifting the offer (buying), B = hitting the bid
        buy = s[side == "A"].sum()
        sell = s[side == "B"].sum()
        tot = buy + sell
        if tot == 0:
            continue
        sign = 1.0 if up else -1.0
        imbalance = float((buy - sell) / tot) * sign      # WITH the breakout
        fwd = float((C[-1] - C[fi]) / h) * sign           # strategy-free
        rows.append((imbalance, fwd))
    return rows


def spearman(x, y):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean(); ry -= ry.mean()
    den = np.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / den) if den else 0.0


if __name__ == "__main__":
    out, pooled = {}, []
    for inst in ("MES", "MNQ"):
        d = FLOW / f"{inst}_v_0"
        rows = setups(inst, d) if d.is_dir() else []
        if not rows:
            print(f"{inst}: no overlapping sessions"); continue
        x = np.array([r[0] for r in rows]); y = np.array([r[1] for r in rows])
        r = spearman(x, y)
        out[inst] = {"n": len(rows), "spearman": round(r, 4),
                     "imbalance_mean": round(float(x.mean()), 4),
                     "fwd_mean": round(float(y.mean()), 4)}
        pooled += rows
        print(f"  {inst}: n={len(rows):>4}  spearman r = {r:+.4f}")
    if pooled:
        x = np.array([r[0] for r in pooled]); y = np.array([r[1] for r in pooled])
        r = spearman(x, y)
        print(f"\n  POOLED: n={len(pooled)}  spearman r = {r:+.4f}")
        # pre-specified secondary: mean forward move by imbalance tercile
        q = np.quantile(x, [1/3, 2/3])
        for lbl, m in (("low  imbalance", x <= q[0]),
                       ("mid  imbalance", (x > q[0]) & (x < q[1])),
                       ("high imbalance", x >= q[1])):
            print(f"    {lbl}: n={m.sum():>4}  mean fwd move "
                  f"{y[m].mean():+.4f} range-heights")
        out["pooled"] = {"spearman": round(r, 4)}
        out["n"] = len(pooled)
    from occams import experiment
    experiment.emit(out)
