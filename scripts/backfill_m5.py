"""M5 — re-score archived results through the audited engine.

NOT an experiment. No hypothesis is registered and no alpha is spent: a
re-run with the SAME estimand is a reproduction, not a second look. That is
why this lives in `scripts/` under its own name rather than as an `exp_*`
frozen artifact.

Each target imports the ORIGINAL frozen script and calls its own setup
functions, so the data and the setup logic are held constant and the only
thing that changes is the estimator. Re-implementing the setups here would
risk introducing a different bug and then blaming the engine for it.

Two kinds of target, and the distinction is the point:

  reproduction    same estimator, run again — a difference is a DEFECT
  estimator swap  M1 replaced the function — a difference is a FINDING

Usage:  python3 scripts/backfill_m5.py [target ...]
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np

from occams import archive, backfill, stats

SWAP, REPRO = "estimator swap", "reproduction"


def frozen(name: str):
    """Import a frozen experiment script without running its __main__."""
    path = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_frozen_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    # must be registered BEFORE exec: a @dataclass in the loaded module
    # resolves its annotations through sys.modules[cls.__module__], and
    # without this it raises on a script that happens to define one
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def archived(key: str) -> dict:
    s3 = archive._client()
    body = s3.get_object(Bucket=archive.bucket(), Key=key)["Body"].read()
    return json.loads(body)["metrics"]


# --------------------------------------------------------------------------
# 1. H5 — our only live positive signal, and it rested on the tie bug
# --------------------------------------------------------------------------

def h5():
    m = frozen("exp_flow_predicts")
    out, pooled = {}, []
    for inst in ("MES", "MNQ"):
        d = m.FLOW / f"{inst}_v_0"
        rows = m.setups(inst, d) if d.is_dir() else []
        if not rows:
            continue
        x = np.array([r[0] for r in rows])
        y = np.array([r[1] for r in rows])
        out[inst] = {"n": len(rows), "spearman": round(stats.spearman(x, y), 4)}
        pooled += rows
    if pooled:
        x = np.array([r[0] for r in pooled])
        y = np.array([r[1] for r in pooled])
        out["pooled"] = {"spearman": round(stats.spearman(x, y), 4)}
        out["n"] = len(pooled)
    return out


# --------------------------------------------------------------------------
# 2. C2 — same replaced function, and the estimand was already questioned
# --------------------------------------------------------------------------

def c2():
    m = frozen("exp_mae_predictable")
    res, pooled = {}, []
    for inst in ("MES", "MNQ"):
        rows = m.rows_for(inst)
        pooled += rows
        a = np.array([x for x in rows if not any(np.isnan(v) for v in x)])
        y = np.log(a[:, 4])
        res[inst] = {"n": len(a)}
        for j, nm in enumerate(m.NAMES):
            res[inst][nm] = round(stats.spearman(a[:, j], y), 4)
    a = np.array([x for x in pooled if not any(np.isnan(v) for v in x)])
    y = np.log(a[:, 4])
    res["pooled"] = {nm: round(stats.spearman(a[:, j], y), 4)
                     for j, nm in enumerate(m.NAMES)}
    res["n"] = len(a)
    return res


# --------------------------------------------------------------------------
# 3. Z0 — the flagship. Re-verified BECAUSE we rely on it, not because it
#    is suspect: it is the result the whole NO-GO now rests on.
# --------------------------------------------------------------------------

def z0():
    m = frozen("exp_entry_obtainable")
    acc: dict = {}
    for inst in ("MES", "MNQ"):
        costs = m.COSTS_BY_INSTRUMENT[inst]
        days = m.to_trading_days(m.read_vendor_csv(f"data/{inst}.csv"),
                                 range_minutes=15, instrument=f"{inst}.v.0")
        sealed = [t.pnl_usd for d in days
                  for t in m.simulate_fade_day(d, m.P, costs).trades]
        acc.setdefault("sealed engine (ASSUMED fill)", {})[inst] = \
            float(np.mean(sealed)) / m.RISK
        for d in days:
            for k, v in m.variants(d, costs).items():
                if v is not None:
                    acc.setdefault(k, {}).setdefault(inst, []).append(v)
    return {k: {i: (v if isinstance(v, float) else float(np.mean(v)) / m.RISK)
                for i, v in row.items()}
            for k, row in acc.items()}


# (kind, archived key, recompute fn, recorded decimals, superseded metrics)
TARGETS = {
    "H5": (SWAP, "experiments/H5-FLOW-PREDICTS/2026-08-01-first-look.json",
           h5, 4, ()),
    # Two metrics were CORRECTED by the M5 reproduction record: `mins to
    # breakout` (97.1% tied, moved 28% on MNQ) and `5d mean range/ATR`
    # (0.1% tied, moved 1e-4). The register is append-only, so the original
    # values stay in place forever; naming them here is what stops a
    # permanent, meaningless failure -- and stops someone "fixing" that by
    # loosening a tolerance until it passes.
    #
    # The test for whether this is legitimate rather than silencing: BOTH
    # appear in the appended correction record, and both were reported in
    # docs/M5-BACKFILL.md before this list existed.
    "C2": (SWAP,
           "experiments/C2-MAE-PREDICTABLE/2026-08-01-four-predictors.json",
           c2, 4, ("mins to breakout", "5d mean range/ATR")),
    # The CANONICAL run, not the earlier `2026-08-01-three-orders`. That
    # record predates the SOP harness and its own note says so; diffing
    # against it reported a phantom mismatch on `a_limit_after_close`
    # (-0.049 vs -0.0559) which is simply the superseded value. An
    # experiment with several runs has a canonical one, and a backfill that
    # picks the wrong record blames the engine for the register's history.
    "Z0": (REPRO,
           "experiments/Z-ENTRY-IMPLEMENTABLE/2026-08-01-sop-verified.json",
           z0, 12, ()),
}


if __name__ == "__main__":
    wanted = sys.argv[1:] or list(TARGETS)
    failures = []
    for name in wanted:
        kind, key, fn, places, sup = TARGETS[name]
        print(f"\n{'=' * 72}\n{name}  [{kind}]\n{'=' * 72}")
        checks = backfill.compare(archived(key), fn(),
                                  decimals_override=places, superseded=sup)
        print(backfill.render(checks))
        if not backfill.all_ok(checks):
            failures.append(name)
            if kind == SWAP:
                print(f"  NOTE: {name} is an estimator swap. A difference "
                      f"here is a FINDING about the old function, not a "
                      f"defect in the new one — report it, do not silence it.")
    print(f"\n{'=' * 72}")
    if failures:
        print(f"M5: {', '.join(failures)} did NOT reproduce within tolerance.")
        sys.exit(1)
    print(f"M5: all {len(wanted)} target(s) reproduce through the engine.")
