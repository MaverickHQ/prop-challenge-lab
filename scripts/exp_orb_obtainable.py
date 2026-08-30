# FROZEN EVIDENCE - archived under experiments/Z04-ORB-OBTAINABLE/.
"""Z0.4 — do the ORB verdicts share the fade's defect?

The fade booked a fill at a price no order could obtain. ORB arms stops
OUTSIDE the opening range while price is inside it, which is the correct
side for a stop, so it should be clean. This checks rather than assumes,
and checks BOTH halves:

  1. was the order PLACEABLE at the moment it was armed?
  2. does the engine's fill price equal what that order would really have
     produced, gaps included?

(2) is the half that reading the code cannot settle.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
from occams.loader import read_vendor_csv, to_trading_days
from occams.strategy import build_plan, OrbParams, NoTrade
from occams.execution import Order, STOP, BUY, SELL, validate, fill, Unplaceable
from occams.instruments import COSTS_BY_INSTRUMENT

PARAMS = OrbParams(stop_range=0.5, target_r=2.0, risk_usd=175.0)


def audit(inst):
    costs = COSTS_BY_INSTRUMENT[inst]
    days = to_trading_days(read_vendor_csv(f"data/{inst}.csv"),
                           range_minutes=15, instrument=f"{inst}.v.0")
    placeable = unplaceable = 0
    fill_match = fill_mismatch = 0
    examples = []
    for d in days:
        plan = build_plan(d.range_bars, PARAMS, costs)
        if isinstance(plan, NoTrade):
            continue
        market = float(d.range_bars["close"].iloc[-1])   # price when armed
        sb = d.session_bars
        H, L, O = (sb["high"].to_numpy(float), sb["low"].to_numpy(float),
                   sb["open"].to_numpy(float))
        for side, lvl in ((BUY, plan.buy_stop), (SELL, plan.sell_stop)):
            if lvl is None:
                continue
            o = Order(STOP, side, lvl)
            try:
                validate(o, market)
                placeable += 1
            except Unplaceable as e:
                unplaceable += 1
                if len(examples) < 3:
                    examples.append(f"{d.date} {side} {lvl}: {e}")
                continue
            got = fill(o, H, L, O, placed_at=-1, slippage=costs.slippage)
            if got is None:
                continue
            i, px = got
            # what the sealed engine books for the same trigger
            engine = (max(lvl, O[i]) + costs.slippage if side == BUY
                      else min(lvl, O[i]) - costs.slippage)
            if abs(px - engine) < 1e-9:
                fill_match += 1
            else:
                fill_mismatch += 1
                if len(examples) < 3:
                    examples.append(f"{d.date} {side}: gate {px} vs engine "
                                    f"{engine}")
    return dict(days=len(days), placeable=placeable, unplaceable=unplaceable,
                fill_match=fill_match, fill_mismatch=fill_mismatch,
                examples=examples)


if __name__ == "__main__":
    out = {}
    for inst in ("MES", "MNQ"):
        r = audit(inst)
        out[inst] = r
        print(f"\n=== {inst} — {r['days']} trading days ===")
        print(f"  orders PLACEABLE when armed   {r['placeable']:>6}")
        print(f"  orders UNPLACEABLE            {r['unplaceable']:>6}")
        print(f"  fills matching the engine     {r['fill_match']:>6}")
        print(f"  fills DISAGREEING             {r['fill_mismatch']:>6}")
        for e in r["examples"]:
            print(f"    ! {e}")
    total_bad = sum(r["unplaceable"] + r["fill_mismatch"] for r in out.values())
    out["n"] = sum(r["placeable"] for r in out.values())
    out["verdict"] = ("CLEAN - ORB does not share the fade's defect"
                      if total_bad == 0 else
                      f"DEFECT FOUND - {total_bad} problems")
    print(f"\n{out['verdict']}")
    from occams import experiment
    experiment.emit(out)
