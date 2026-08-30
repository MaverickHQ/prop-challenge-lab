# FROZEN EVIDENCE - archived under experiments/X1/.
"""X1 — why does the comparator read -0.046R where the sealed verdict read +0.1R?

Decomposes the gap one factor at a time, using the REAL loader and the REAL
engine rather than a re-implementation. Each row adds exactly one sealed
behaviour, so the row where the number moves is the explanation.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from occams.loader import read_vendor_csv, to_trading_days
from occams.fade import FadeParams, simulate_fade_day
from occams.calendar import blocked_reason, load_events
from occams.instruments import COSTS_BY_INSTRUMENT

RISK = 175.0
EVENTS = load_events(Path("occams/data/economic_calendar.csv"))
PARAMS = FadeParams(k_stop=0.2, width_max=None, risk_usd=RISK)

def pnls(days, costs, blocked=False):
    out = []
    for d in days:
        if blocked and blocked_reason(d.date, EVENTS):
            continue
        r = simulate_fade_day(d, PARAMS, costs)
        for t in r.trades:
            out.append((d.date, t.pnl_usd))
    return out

def show(label, rows):
    if not rows:
        print(f"  {label:<44}{'no trades':>12}"); return
    a = np.array([p for _, p in rows])
    print(f"  {label:<44}{len(a):>7}{a.mean()/RISK:>+11.3f}R")

for inst in ("MES", "MNQ"):
    costs = COSTS_BY_INSTRUMENT[inst]
    df = read_vendor_csv(f"data/{inst}.csv")
    days = to_trading_days(df, range_minutes=15, instrument=f"{inst}.v.0")
    print(f"\n=== {inst} — sealed loader gives {len(days)} clean trading days ===")
    print(f"  {'variant':<44}{'trades':>7}{'R/trade':>12}")
    all_rows = pnls(days, costs)
    show("sealed engine + sealed loader, pooled", all_rows)
    cal_rows = pnls(days, costs, blocked=True)
    show("  + FOMC/CPI/NFP calendar filter", cal_rows)
    # sealed 60/20/20 walk-forward on the CALENDAR-FILTERED universe
    n = len(days)
    lock0, oos0 = int(n * 0.8), int(n * 0.6)
    spans = {"dev  (first 60%)": days[:oos0],
             "OOS  (next 20%)":  days[oos0:lock0],
             "lockbox (last 20%)": days[lock0:]}
    for name, sub in spans.items():
        show(f"  + fold: {name}", pnls(sub, costs, blocked=True))
