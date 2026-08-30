# FROZEN EVIDENCE - archived under experiments/Z-ENTRY-IMPLEMENTABLE/.
"""Z0 — which REAL order reproduces the sealed engine's entry? (None.)

The engine books a fill AT the range boundary at the failure close. This
runs all three orders a human could actually place, on the same days with
the same geometry, and compares them to that assumption.

This script exists because option (b) was first run inline and left no
frozen artifact -- the most important result of the day was, for a few
hours, not reproducible.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
from occams.loader import read_vendor_csv, to_trading_days
from occams.fade import FadeParams, simulate_fade_day
from occams.instruments import COSTS_BY_INSTRUMENT

RISK = 175.0
P = FadeParams(k_stop=0.2, width_max=None, risk_usd=RISK)


def setup(day):
    rb, sb = day.range_bars, day.session_bars
    if rb is None or rb.empty or sb.empty: return None
    hi, lo = float(rb["high"].max()), float(rb["low"].min()); h = hi - lo
    if h <= 0: return None
    H, L, C = (sb["high"].to_numpy(float), sb["low"].to_numpy(float),
               sb["close"].to_numpy(float))
    bi = next((i for i in range(len(sb)) if H[i] > hi or L[i] < lo), None)
    if bi is None: return None
    up = H[bi] > hi
    fc = next((i for i in range(bi, len(sb))
               if (C[i] < hi if up else C[i] > lo)), None)
    return dict(H=H, L=L, C=C, hi=hi, lo=lo, h=h, bi=bi, up=up, fc=fc)


def settle(s, costs, entry_i, entry_px, ext_end):
    up, hi, lo, h = s["up"], s["hi"], s["lo"], s["h"]
    H, L, C = s["H"], s["L"], s["C"]
    b = hi if up else lo; sg = -1.0 if up else 1.0
    ext = H[s["bi"]:ext_end + 1].max() if up else L[s["bi"]:ext_end + 1].min()
    stop = b - sg * ((ext - hi if up else lo - ext) + 0.2 * h)
    tgt = b + sg * h
    lp = abs(stop - entry_px) + costs.slippage
    n = min(int(RISK // (lp * costs.multiplier
                         + 2 * costs.commission_per_side)), 30)
    if n < 1: return None
    ex = C[-1]
    for i in range(entry_i + 1, len(C)):
        if (L[i] <= stop if sg > 0 else H[i] >= stop): ex = stop; break
        if (H[i] >= tgt if sg > 0 else L[i] <= tgt): ex = tgt; break
    return n * ((ex - entry_px) * sg * costs.multiplier
                - 2 * costs.commission_per_side)


def variants(day, costs):
    s = setup(day)
    if s is None: return {}
    up, hi, lo = s["up"], s["hi"], s["lo"]
    b = hi if up else lo; sg = -1.0 if up else 1.0
    slip = costs.slippage
    out = {}
    # (a) LIMIT resting at the boundary, placed AFTER the failure close
    if s["fc"] is not None:
        e = next((i for i in range(s["fc"] + 1, len(s["C"]))
                  if (s["H"][i] >= b if up else s["L"][i] <= b)), None)
        if e is not None:
            out["a_limit_after_close"] = settle(s, costs, e, b, s["fc"])
    # (b) MARKET at the failure close -- you get the CLOSE, not the boundary
    if s["fc"] is not None:
        out["b_market_at_close"] = settle(s, costs, s["fc"],
                                          s["C"][s["fc"]] + sg * slip, s["fc"])
    # (c) STOP armed at the breakout, resting at the boundary
    e = next((i for i in range(s["bi"], len(s["C"]))
              if (s["L"][i] <= b if up else s["H"][i] >= b)), None)
    if e is not None:
        out["c_stop_armed_at_breakout"] = settle(s, costs, e, b + sg * slip, e)
    return out


if __name__ == "__main__":
    print(f"{'':<34}{'MES':>10}{'MNQ':>10}")
    acc = {}
    for inst in ("MES", "MNQ"):
        costs = COSTS_BY_INSTRUMENT[inst]
        days = to_trading_days(read_vendor_csv(f"data/{inst}.csv"),
                               range_minutes=15, instrument=f"{inst}.v.0")
        sealed = [t.pnl_usd for d in days
                  for t in simulate_fade_day(d, P, costs).trades]
        acc.setdefault("sealed engine (ASSUMED fill)", {})[inst] = \
            float(np.mean(sealed)) / RISK
        for d in days:
            for k, v in variants(d, costs).items():
                if v is not None:
                    acc.setdefault(k, {}).setdefault(inst, []).append(v)
    for k in ("sealed engine (ASSUMED fill)", "a_limit_after_close",
              "b_market_at_close", "c_stop_armed_at_breakout"):
        row = acc.get(k, {})
        vals = []
        for inst in ("MES", "MNQ"):
            v = row.get(inst)
            vals.append(v if isinstance(v, float) else float(np.mean(v)) / RISK)
        print(f"{k:<34}{vals[0]:>+10.3f}{vals[1]:>+10.3f}")
    print("\nOnly the assumption is positive. No placeable order reproduces it.")
    # The SOP reads THIS line into the register -- nothing is retyped.
    from occams import experiment
    experiment.emit({k: {i: (v if isinstance(v, float)
                             else float(np.mean(v)) / RISK)
                         for i, v in row.items()}
                     for k, row in acc.items()})
