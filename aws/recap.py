"""B7.4-B7.6 — recaps, with the honesty guard built in rather than bolted on.

Every recap states its sample size FIRST and refuses to present an
expectancy below ~20 trades without the caveat alongside. That is not
politeness: the live five-day sample read +1.2R after 3 trades, +0.69R
after 4 and +0.35R after 5, converging on a measured +0.1R from above.
Early samples lie, and they lie optimistically, so the guard has to be
part of the number rather than a footnote someone can drop.

Missed cards and no-fills are counted in the denominator. A process defect
that happens to dodge a loser is exactly as much a defect as one that
dodges a winner (PAPER-PREREG §8, AMENDMENT-4a).
"""

from __future__ import annotations

from datetime import date, timedelta

MIN_TRADES_FOR_EXPECTANCY = 20
EVIDENCE_BAR_TRADES = 40
EVIDENCE_BAR_DAYS = 60
MEASURED_BASELINE_R = 0.1


def _money(x: float) -> str:
    return f"{'+' if x >= 0 else '-'}${abs(x):,.2f}"


def completed_trades(doc: dict, days: list[str]) -> list[dict]:
    out = []
    for d in days:
        for inst, st in (doc.get(d) or {}).items():
            if st.get("entry_price") is not None and st.get("exit_price"):
                out.append({**st, "date": d, "instrument": inst})
    return out


def counts(doc: dict, days: list[str]) -> dict:
    """Denominator first. A recap that reports only completed trades makes
    a campaign look healthier than it is."""
    c = {"cards": 0, "placed": 0, "defects": 0, "no_fills": 0,
         "stand_asides": 0, "completed": 0}
    for d in days:
        for _inst, st in (doc.get(d) or {}).items():
            if st.get("card"):
                c["cards"] += 1
                if (st["card"] or {}).get("contracts", 0) < 1:
                    c["stand_asides"] += 1
            if st.get("defect"):
                c["defects"] += 1
            if st.get("skip_reason", "").startswith("no fill"):
                c["no_fills"] += 1
            if st.get("entry_price") is not None:
                c["placed"] += 1
            if st.get("exit_price"):
                c["completed"] += 1
    return c


def drift_stats(trades: list[dict]) -> dict:
    drifts = [t["drift"] for t in trades if t.get("drift") is not None]
    if not drifts:
        return {"n": 0}
    n = len(drifts)
    mean = sum(drifts) / n
    mean_abs = sum(abs(d) for d in drifts) / n
    return {"n": n, "mean": mean, "mean_abs": mean_abs}


def kill_status(stats: dict) -> str:
    """PAPER-PREREG §5, armed from trade 10."""
    if stats["n"] < 10:
        return f"kill thresholds arm at trade 10 ({stats['n']}/10)"
    if stats["mean"] <= -5.0:
        return "KILL: mean drift <= -$5/trade. Campaign over."
    if stats["mean_abs"] > 10.0:
        return "KILL: mean |drift| > $10/trade. The model is wrong."
    return (f"kill check OK (mean {_money(stats['mean'])}, "
            f"mean abs {_money(stats['mean_abs'])})")


def honesty_line(n: int) -> str:
    if n < MIN_TRADES_FOR_EXPECTANCY:
        return (f"n={n}. Below {MIN_TRADES_FOR_EXPECTANCY} trades no "
                f"expectancy here means anything - early samples lie, "
                f"optimistically. Measured baseline is "
                f"+{MEASURED_BASELINE_R}R.")
    return f"n={n}."


def daily(doc: dict, day_str: str, health: dict | None = None) -> str:
    c = counts(doc, [day_str])
    lines = [f"DAILY RECAP {day_str}", ""]
    for inst, st in sorted((doc.get(day_str) or {}).items()):
        card = st.get("card")
        bits = [f"  {inst}: {st.get('phase', 'idle')}"]
        if card:
            bits.append(f"    card {card['side']} {card['contracts']}x "
                        f"@{card['entry']} stop {card['stop']} "
                        f"target {card['target']}")
        if st.get("entry_price") is not None:
            bits.append(f"    you  {st['entry_price']} -> "
                        f"{st.get('exit_price', 'open')} "
                        f"({st.get('exit_event', '-')})")
        if st.get("drift") is not None:
            bits.append(f"    drift {_money(st['drift'])}")
        if st.get("defect"):
            bits.append(f"    DEFECT: {st['defect']} (not a trade avoided)")
        if st.get("skip_reason"):
            bits.append(f"    skipped: {st['skip_reason']}")
        lines.extend(bits)
    if len(lines) == 2:
        lines.append("  no cards today")

    lines += ["", f"cards {c['cards']} | placed {c['placed']} | "
                  f"completed {c['completed']} | defects {c['defects']} | "
                  f"no-fills {c['no_fills']} | stand-asides "
                  f"{c['stand_asides']}"]
    if health:
        lines.append(_health_line(health))
    return "\n".join(lines)


def _health_line(health: dict) -> str:
    """B4.1 — the dead-man's switch. The top risk is a SILENT poller: no
    cards looks identical to no setups. Saying the poll count out loud is
    what makes the difference visible without opening a console."""
    polls = health.get("polls", 0)
    if polls == 0:
        return ("!! THE POLLER DID NOT RUN TODAY. No card could have been "
                "sent. Treat every missing card as a system failure, not a "
                "quiet day.")
    warn = "" if polls >= 40 else "  (low - expected ~75)"
    return (f"health: {polls} polls{warn}, last bar "
            f"{health.get('last_bar_age_min', '?')} min old")


def period(doc: dict, days: list[str], label: str) -> str:
    trades = completed_trades(doc, days)
    c = counts(doc, days)
    stats = drift_stats(trades)
    n = len(trades)

    lines = [f"{label.upper()} RECAP", honesty_line(n), ""]
    if trades:
        pnls = [t.get("pnl", 0.0) for t in trades]
        wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
        lines += [f"  trades {n} | wins {wins} ({wins / n:.0%})",
                  f"  total {_money(sum(pnls))} | "
                  f"per trade {_money(sum(pnls) / n)}"]
        if stats["n"]:
            lines.append(f"  drift mean {_money(stats['mean'])} | "
                         f"mean abs {_money(stats['mean_abs'])}")
            lines.append(f"  {kill_status(stats)}")
    else:
        lines.append("  no completed trades yet")

    lines += ["",
              f"  cards {c['cards']} | defects {c['defects']} | "
              f"no-fills {c['no_fills']} | stand-asides {c['stand_asides']}",
              f"  operational drag: {c['defects'] + c['no_fills']} of "
              f"{c['cards']} cards did not become trades", ""]
    traded_days = len([d for d in days if doc.get(d)])
    lines.append(f"  progress: {n}/{EVIDENCE_BAR_TRADES} trades, "
                 f"{traded_days}/{EVIDENCE_BAR_DAYS} days")
    return "\n".join(lines)


def days_back(today: date, n: int) -> list[str]:
    return [(today - timedelta(days=i)).isoformat() for i in range(n)]
