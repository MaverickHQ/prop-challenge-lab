"""F5-BACKFILL — recompute archived experiments through the audited engine.

    python3 scripts/backfill_f5.py --list
    python3 scripts/backfill_f5.py --hid H-RECLAIM

WHY THIS EXISTS. Eighteen of the register's twenty-two runs predate M1-M7.
They carry raw metric dictionaries -- a printed mean, no interval, no floor,
no effective n -- so nothing in them can be resolved as a measured result.
`docs/M5-BACKFILL.md` already named the remaining work and the order to do
it in; this is that list, executed.

It also replaces a shortcut. Fourteen hypotheses were resolved as
`documented`: an outcome copied out of a writeup, with the numeric fields
left null and the source hashed. That is honest bookkeeping and it is not a
measurement, and a lab whose register is mostly transcription is a reading
list. Every hypothesis this script recomputes gets a resolution that
SUPERSEDES its documented one, so the register keeps both -- the shortcut
and its correction -- which is what append-only is for.

THE ORIGINAL SCRIPTS ARE FROZEN EVIDENCE and are not touched. Each says so
in its own header: the archived copy must stay byte-identical to the script
that produced the registered result. So the recompute lives here, beside
them, and `backfill.compare` checks the archived number reproduces -- a
difference under a reproduction is a defect, a difference under an estimator
swap is a finding about the old function.

WHAT THE UPGRADE ACTUALLY IS. The old scripts computed point estimates and
printed them. The recompute states an estimand, resamples CLUSTERS rather
than rows (MES and MNQ on one date are close to one draw), applies the
design effect, and reports the effect against the smallest one the sample
could have seen. A mean with no floor beside it cannot be called null and
cannot be called a finding.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from occams import power, stats  # noqa: E402
from occams.result import Result  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ET = ZoneInfo("America/New_York")

# Read from the frozen originals rather than restated, so a recompute cannot
# quietly change the setup it claims to be reproducing.
K, RISK, CAP = 0.2, 175.0, 30
SPEC = {"MES": (5.0, 0.25, 1.25), "MNQ": (2.0, 0.25, 1.25)}
SEED = 20260830

# Two instruments per date, near-identical draws (E4.2).
CLUSTER_SIZE, INTRA_R = 2, 0.9

# What each recompute must reproduce before any statistic it produces means
# anything. Read from the archived run records, not restated from a writeup.
ARCHIVED = {
    "H-RECLAIM": {
        "MES": {"setups": 1706, "v0_trades": 1623, "v0_r_per_trade": -0.046,
                "v5_trades": 1018, "v5_r_per_trade": -0.262},
        "MNQ": {"setups": 1622, "v0_trades": 1538, "v0_r_per_trade": -0.025,
                "v5_trades": 946, "v5_r_per_trade": -0.215}},
}


def load(inst: str) -> pd.DataFrame:
    df = pd.read_csv(ROOT / f"data/{inst}.csv",
                     usecols=["ts_event", "open", "high", "low", "close"])
    df["ts"] = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(ET)
    df = df.drop(columns=["ts_event"])
    hm = df["ts"].dt.hour * 60 + df["ts"].dt.minute
    df = df[(hm >= 570) & (hm < 960)]
    df["d"] = df["ts"].dt.date
    return df


def size(pts: float, mult: float, comm: float, tick: float) -> int:
    """Transcribed exactly, INCLUDING the two ticks of slippage. Dropping
    them is not a rounding difference -- it changes contract count, which
    changes every P&L downstream."""
    per = (pts + 2 * tick) * mult + 2 * comm
    return min(int(RISK // per), CAP)


def reproduces(hid: str, archived: dict, recomputed: dict, *,
               places: int = 3) -> None:
    """THE GATE. Refuse to report anything until the recompute reproduces
    the archived run.

    Added after the first attempt at H-RECLAIM silently became a different
    strategy -- the breakout bar conflated with the failure close, the
    excursion term dropped from the stop, slippage dropped from sizing --
    and returned a clean `detectable` result at 2.33x its floor for a setup
    nobody had ever tested. Correct arithmetic about a world that did not
    exist, which is the exact failure this lab was built to catch.

    A recompute is only evidence about the archived result if it is
    demonstrably the same computation. Reproduction first, statistics after.
    """
    from occams import backfill
    checks = backfill.compare(archived, recomputed, decimals_override=places)
    print(backfill.render(checks))
    if not backfill.all_ok(checks):
        raise SystemExit(
            f"\nREFUSED: the recompute does not reproduce {hid}'s archived "
            f"run.\nEvery number below it would be a measurement of "
            f"something else. Fix the transcription against the frozen "
            f"script before reading anything into the statistics.")


def scored(name: str, values, clusters, *, unit: str, note: str = "") -> Result:
    """A mean with the uncertainty it was always missing.

    The floor is `detectable_mean_shift` at the EFFECTIVE n, scaled by the
    sample's own SD. Using raw n here would flatter the result exactly the
    way pooling two correlated instruments flattered H5.
    """
    a = np.asarray(values, dtype=float)
    n = int(a.size)
    n_eff = power.effective_n(n, cluster_size=CLUSTER_SIZE, intra_r=INTRA_R)
    lo, hi = stats.cluster_bootstrap_ci(a, clusters, seed=SEED)
    floor = power.detectable_mean_shift(n_eff) * float(a.std(ddof=1))
    return Result(name=name, estimate=float(a.mean()), ci=(lo, hi), n=n,
                  n_eff=n_eff, d=float(a.mean()), floor=floor, unit=unit,
                  note=note)


# ─── H-RECLAIM ───

def _reclaim_rows(inst: str) -> list[tuple]:
    """(date, sealed_R, reclaim_R) for every setup, either possibly None.

    Logic transcribed from the frozen `scripts/exp_reclaim.py` without
    change; only the statistics that follow are new.
    """
    mult, tick, comm = SPEC[inst]
    df = load(inst)
    out = []
    for d, g in df.groupby("d", sort=True):
        hm = g["ts"].dt.hour * 60 + g["ts"].dt.minute
        rb = g[(hm >= 570) & (hm < 585)]
        if len(rb) < 15:
            continue
        hi, lo = rb["high"].max(), rb["low"].min()
        h = hi - lo
        if h <= 0:
            continue
        s = g[hm >= 585]
        if s.empty:
            continue
        H = s["high"].to_numpy()
        L = s["low"].to_numpy()
        C = s["close"].to_numpy()
        # BREAKOUT, then the FAILURE CLOSE back inside. Two distinct bars --
        # collapsing them into one is what made the first attempt a
        # different strategy.
        bi = next((i for i in range(len(s)) if H[i] > hi or L[i] < lo), None)
        if bi is None:
            continue
        up = H[bi] > hi
        fi = next((i for i in range(bi, len(s))
                   if (C[i] < hi if up else C[i] > lo)), None)
        if fi is None:
            continue
        ext = H[bi:fi + 1].max() if up else L[bi:fi + 1].min()
        b = hi if up else lo
        sg = -1.0 if up else 1.0
        stop = b - sg * ((ext - hi if up else lo - ext) + K * h)
        tgt = b + sg * h
        n = size(abs(stop - b), mult, comm, tick)
        if n < 1:
            continue

        def settle(i0, entry, stop_, n_):
            for i in range(i0, len(s)):
                hs = L[i] <= stop_ if sg > 0 else H[i] >= stop_
                ht = H[i] >= tgt if sg > 0 else L[i] <= tgt
                if hs:
                    return n_ * ((stop_ - entry) * sg * mult - 2 * comm)
                if ht:
                    return n_ * ((tgt - entry) * sg * mult - 2 * comm)
            return n_ * ((C[-1] - entry) * sg * mult - 2 * comm)

        e0 = next((i for i in range(fi + 1, len(s))
                   if (L[i] <= b if sg > 0 else H[i] >= b)), None)
        v0 = settle(e0 + 1, b, stop, n) if e0 is not None else None

        v5 = None
        p = next((i for i in range(fi + 1, len(s))
                  if (L[i] <= stop if sg > 0 else H[i] >= stop)), None)
        if p is not None:
            q = next((i for i in range(p, len(s))
                      if (H[i] > stop if sg > 0 else L[i] < stop)), None)
            if q is not None:
                r = next((i for i in range(q, len(s))
                          if (H[i] > b if sg > 0 else L[i] < b)), None)
                if r is not None:
                    v5 = settle(r + 1, b, stop, n)
        out.append((d, v0, v5))
    return out


def h_reclaim() -> dict:
    """Does waiting for a reclaim improve the entry?

    The estimand is a PAIRED difference, which the original never computed:
    on days where both entries exist, reclaim minus sealed. Comparing the two
    unpaired means would confound the filter's effect with the fact that it
    trades a different, smaller set of days.
    """
    paired_v, paired_c, sealed, reclaim = [], [], [], []
    sealed_clusters, reclaim_clusters = [], []
    archived, recomputed = ARCHIVED["H-RECLAIM"], {}
    for inst in ("MES", "MNQ"):
        rows = _reclaim_rows(inst)
        v0s = [v0 / RISK for _, v0, _ in rows if v0 is not None]
        v5s = [v5 / RISK for _, _, v5 in rows if v5 is not None]
        sealed_clusters += [(str(d), inst) for d, v0, _ in rows
                            if v0 is not None]
        reclaim_clusters += [(str(d), inst) for d, _, v5 in rows
                             if v5 is not None]
        recomputed[inst] = {
            "setups": len(rows), "v0_trades": len(v0s),
            "v0_r_per_trade": float(np.mean(v0s)),
            "v5_trades": len(v5s),
            "v5_r_per_trade": float(np.mean(v5s))}
        sealed += v0s
        reclaim += v5s
        for d, v0, v5 in rows:
            if v0 is not None and v5 is not None:
                paired_v.append((v5 - v0) / RISK)
                paired_c.append(str(d))

    reproduces("H-RECLAIM", archived, recomputed)

    # STRATEGY level, not trade level. The filter changes WHICH DAYS get
    # traded, so the two arms are different strategies and the comparison is
    # between their expectancies. The first version of this paired the arms
    # on shared days and reported +0.243R -- the filter looking BETTER -- for
    # a real but different reason: a reclaim only happens on days where price
    # went through the stop first, which are days the sealed entry was
    # already losing. Pairing conditioned on the subset where the comparator
    # does worst.
    primary = scored(
        "H-RECLAIM PRIMARY - reclaim-filtered expectancy, per trade",
        reclaim, [c for c, _ in reclaim_clusters], unit="R",
        note="the filtered strategy's own expectancy. Compare with the "
             "sealed arm below: the intervals do not overlap.")
    comparator = scored(
        "H-RECLAIM COMPARATOR - sealed (unfiltered) expectancy, per trade",
        sealed, [c for c, _ in sealed_clusters], unit="R",
        note="the arm the filter was supposed to improve on.")
    secondary = scored(
        "H-RECLAIM SECONDARY - paired reclaim minus sealed, shared days only",
        paired_v, paired_c, unit="R",
        note="POSITIVE and it does NOT rescue the filter. This conditions on "
             "days a reclaim occurred, which are days price first went "
             "through the stop -- exactly where the sealed entry does worst. "
             "It answers 'given a reclaim happened, was the later entry "
             "better', not 'is the filter worth applying'.")
    return {"primary": primary.to_metrics(),
            "comparator": comparator.to_metrics(),
            "secondary_paired": secondary.to_metrics(),
            "n_sealed": len(sealed), "n_reclaim": len(reclaim),
            "n_paired": len(paired_v)}


def render(hid: str, out: dict) -> str:
    """One rendering, used by the CLI and by the archived entry points, so a
    run's stdout and an interactive run cannot describe it differently."""
    lines = [f"\n{'=' * 72}",
             f"{hid}  recomputed through the audited engine",
             "=" * 72]
    for k, v in out.items():
        if isinstance(v, dict) and "verdict" in v:
            fields = {x: y for x, y in v.items()
                      if x in Result.__dataclass_fields__}
            if isinstance(fields.get("ci"), list):
                fields["ci"] = tuple(fields["ci"])
            lines.append(Result(**fields).render())
        else:
            lines.append(f"  {k:<20} {v}")
    return "\n".join(lines)


TARGETS = {"H-RECLAIM": (h_reclaim, "2026-08-01-full-history")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hid")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list or not a.hid:
        print("recomputable through the audited engine:")
        for k in sorted(TARGETS):
            print(f"  {k}")
        return 0

    if a.hid not in TARGETS:
        raise SystemExit(f"{a.hid} has no recompute yet. Have: "
                         f"{sorted(TARGETS)}")
    fn, archived_run = TARGETS[a.hid]
    out = fn()

    print(render(a.hid, out))
    print(f"\n  archived run for comparison: {archived_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
