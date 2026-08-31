"""R1 — expected value per plan, over a provider's whole menu.

    python3 scripts/plan_menu_ev.py

The previous programme modelled ONE contract and optimised P(pass). This
prices every contract on the menu in dollars, against the SAME synthetic
strategy, so the ranking reflects the contracts rather than the strategy.

Both stages run through the AUDITED rules engine -- `run_from_ledger` for the
evaluation and `PayoutState` for the funded account -- rather than a
reimplementation of the ratcheting drawdown. Retyping that logic is exactly
the transcription error this repo caught earlier today.

The menu itself lives in a git-ignored `profiles/menu.local.json`: the MODEL
is public, the provider's terms are not.
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from occams.harness import DayOutcome, run_from_ledger          # noqa: E402
from occams.payout import PayoutConfig, PayoutState, PayoutStatus  # noqa: E402
from occams.plans import Plan, PlanEconomics, ev                # noqa: E402
from occams.rules import ChallengeConfig, Status                # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MENU = ROOT / "profiles" / "menu.local.json"
SIMS, HORIZON, SEED = 3000, 60, 20260830


def win_rate(edge_r: float, payoff_r: float) -> float:
    """w solving  edge = w*payoff - (1-w)*1."""
    return (edge_r + 1.0) / (payoff_r + 1.0)


def ledgers(rng, *, edge_r, payoff_r, trades_per_day, risk_usd, n, days):
    """n synthetic day-ledgers. Fixed-dollar risk, so R converts linearly."""
    w = win_rate(edge_r, payoff_r)
    t = max(1, int(round(trades_per_day)))
    wins = rng.random((n, days, t)) < w
    r = np.where(wins, payoff_r, -1.0).sum(axis=2) * risk_usd
    d0 = date(2026, 1, 1)
    return [[DayOutcome(d0 + timedelta(days=j), float(r[i, j]), True)
             for j in range(days)] for i in range(n)]


def simulate(plan_row, *, edge_r, payoff_r, trades_per_day, risk_usd,
             payout_frac, rng):
    """P(reach a payout) and expected months, through the audited engines."""
    acct = float(plan_row["account"])
    books = ledgers(rng, edge_r=edge_r, payoff_r=payoff_r,
                    trades_per_day=trades_per_day, risk_usd=risk_usd,
                    n=SIMS, days=HORIZON)

    survivors, days_to_pass = [], []
    if plan_row["eval"] is None:
        survivors, days_to_pass = books, [0] * len(books)      # already funded
    else:
        e = plan_row["eval"]
        cfg = ChallengeConfig(account=acct, target=float(e["target"]),
                              trailing_dd=float(e["dd"]),
                              daily_guard=float(e["guard"]),
                              min_days=int(e["min_days"]),
                              consistency_frac=e["consistency"])
        for book in books:
            run = run_from_ledger(book, cfg)
            if run.status is Status.PASSED:
                survivors.append(book[run.days_used:])
                days_to_pass.append(run.days_used)

    f = plan_row["funded"]
    pcfg = PayoutConfig(account=acct, threshold=float(f["threshold"]),
                        trailing_dd=float(f["dd"]),
                        min_days=int(f["min_days"]),
                        consistency_frac=f["consistency"],
                        payout_frac=payout_frac)
    paid, profits, total_days = 0, [], []
    for book, pre in zip(survivors, days_to_pass):
        st, eq = PayoutState(pcfg), acct
        for k, o in enumerate(book, start=1):
            eq += o.pnl
            if st.record_day(eq, traded=True) is PayoutStatus.PAID:
                paid += 1
                profits.append(eq - acct)
                total_days.append(pre + k)
                break

    p_payout = paid / SIMS
    months = ((np.mean(total_days) if total_days else HORIZON) / 21.0)
    gross = float(np.mean(profits)) if profits else 0.0
    return p_payout, months, gross


def main() -> int:
    if not MENU.exists():
        raise SystemExit(f"{MENU} not found. The model is public; the "
                         f"provider's menu is local and git-ignored.")
    menu = json.loads(MENU.read_text())
    rng = np.random.default_rng(SEED)

    # The measured signal, from nine dead families: gross +0.02 to +0.04R,
    # costs 0.05 to 0.09R. Net is negative, and that is the honest input.
    scenarios = [("measured (net -0.03R)", -0.03), ("break-even (0.00R)", 0.0),
                 ("marginal (+0.05R)", 0.05), ("good (+0.15R)", 0.15)]

    for label, edge in scenarios:
        print(f"\n{'=' * 78}\nEDGE: {label}   payoff 2.0R, 1 trade/day, "
              f"risk 1% of account\n{'=' * 78}")
        print(f"{'plan':16s} {'fee':>10s} {'bar':>4s} {'P(pay)':>8s} "
              f"{'mo':>5s} {'prize':>8s} {'fees':>8s} {'EV $':>9s}")
        rows = []
        for row in menu["plans"]:
            econ = PlanEconomics(fee=float(row["fee"]),
                                 fee_kind=row["fee_kind"],
                                 max_payout=float(row["max_payout"]),
                                 payouts_per_month=menu["payouts_per_month"])
            p, months, gross = simulate(
                row, edge_r=edge, payoff_r=2.0, trades_per_day=1,
                risk_usd=0.01 * float(row["account"]),
                payout_frac=menu["payout_frac"], rng=rng)
            f = row["funded"]
            plan = Plan(row["name"], float(row["account"]),
                        None if row["eval"] is None else ChallengeConfig(
                            account=float(row["account"]),
                            target=float(row["eval"]["target"]),
                            trailing_dd=float(row["eval"]["dd"]),
                            daily_guard=float(row["eval"]["guard"]),
                            min_days=int(row["eval"]["min_days"]),
                            consistency_frac=row["eval"]["consistency"]),
                        PayoutConfig(account=float(row["account"]),
                                     threshold=float(f["threshold"]),
                                     trailing_dd=float(f["dd"]),
                                     min_days=int(f["min_days"]),
                                     consistency_frac=f["consistency"],
                                     payout_frac=menu["payout_frac"]),
                        econ)
            value = ev(plan, p_payout=p, gross_profit=gross, months=months)
            prize = econ.prize(gross, menu["payout_frac"])
            rows.append((value, row["name"], row["fee"], row["fee_kind"],
                         plan.barriers, p, months, prize,
                         econ.fees_for(months)))
        for v, name, fee, kind, bars, p, mo, prize, fees in sorted(
                rows, reverse=True):
            tag = "once" if kind == "once" else "/mo"
            print(f"{name:16s} {f'${fee:.0f}{tag}':>10s} {bars:>4d} "
                  f"{p:>8.4f} {mo:>5.1f} {prize:>8.0f} {fees:>8.0f} "
                  f"{v:>9.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
