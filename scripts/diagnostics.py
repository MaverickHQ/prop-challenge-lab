"""Phase B — dev-fold diagnostics: the anatomy of opening-range failure.

STRICT SCOPE: dev folds only (first 60% of each instrument's tradable
days — the same split arithmetic as the sealed verdict). OOS and lockbox
are never touched here.

The question Phase A sharpened: after a breakout FAILS (price re-enters
the range), does the reversal travel to the far side often enough to pay
the fade at 2R (stop 0.5x height beyond the extreme) or 3R (0.33x)?
Those (WR, R) pairs place directly on the FEASIBILITY.md frontier.

Trade template measured (short side shown; long mirrored):
  breakout: a bar HIGH strictly above the range high
  failure:  a later bar CLOSE back below the range high
  entry:    at the range high (limit as price returns)
  extreme:  max high from breakout to failure
  stop:     extreme + k x height touched (bar high)
  target:   far side = range low touched (bar low)
  same-bar stop+target: counted as LOSS (conservative)
  neither by session end: EOD exit, counted separately (flat-ish scratch)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from occams.calendar import load_events  # noqa: E402
from occams.harness import TradingDay  # noqa: E402

K_STOPS = (0.25, 0.33, 0.5)


def fade_anatomy(day: TradingDay, k_stops=K_STOPS) -> dict | None:
    """Scan one day for the first breakout-failure fade. Returns None when
    no breakout happens; else a dict with the setup's geometry + outcome
    per stop multiple."""
    rb, sb = day.range_bars, day.session_bars
    hi = float(rb["high"].max())
    lo = float(rb["low"].min())
    height = hi - lo
    if height <= 0:
        return None
    highs = sb["high"].to_numpy(float)
    lows = sb["low"].to_numpy(float)
    closes = sb["close"].to_numpy(float)

    up_break = np.argmax(highs > hi) if (highs > hi).any() else None
    dn_break = np.argmax(lows < lo) if (lows < lo).any() else None
    if up_break is None and dn_break is None:
        return {"setup": "none", "height": height, "atr": day.atr}
    if dn_break is None or (up_break is not None and up_break <= dn_break):
        side, b = "up", int(up_break)
    else:
        side, b = "down", int(dn_break)

    if side == "up":
        fails = closes[b:] < hi
        if not fails.any():
            return {"setup": "held", "side": side, "height": height,
                    "atr": day.atr}
        f = b + int(np.argmax(fails))
        extreme = float(highs[b:f + 1].max())
        out = {"setup": "failed", "side": side, "height": height,
               "atr": day.atr, "break_bar": b, "fail_bar": f,
               "extreme_ext": (extreme - hi) / height}
        for k in k_stops:
            stop = extreme + k * height
            won = lost = False
            for i in range(f + 1, len(highs)):
                hit_stop = highs[i] >= stop
                hit_tgt = lows[i] <= lo
                if hit_stop:          # conservative: stop first on ties
                    lost = True
                    break
                if hit_tgt:
                    won = True
                    break
            out[f"k{k}"] = "win" if won else ("loss" if lost else "eod")
        return out

    fails = closes[b:] > lo
    if not fails.any():
        return {"setup": "held", "side": side, "height": height,
                "atr": day.atr}
    f = b + int(np.argmax(fails))
    extreme = float(lows[b:f + 1].min())
    out = {"setup": "failed", "side": side, "height": height,
           "atr": day.atr, "break_bar": b, "fail_bar": f,
           "extreme_ext": (lo - extreme) / height}
    for k in k_stops:
        stop = extreme - k * height
        won = lost = False
        for i in range(f + 1, len(lows)):
            if lows[i] <= stop:
                lost = True
                break
            if highs[i] >= hi:
                won = True
                break
        out[f"k{k}"] = "win" if won else ("loss" if lost else "eod")
    return out


def main() -> int:
    from occams.verdict_cli import load_instrument, project_root
    root = project_root()
    events = load_events(root / "occams" / "data" / "economic_calendar.csv")

    lines = ["# DIAGNOSTICS — failed-breakout anatomy (Phase B, dev folds ONLY)",
             "",
             "Universe: dev fold = first 60% of tradable days per instrument"
             " (verdict split), event days excluded — the same day-universe"
             " the sealed pipeline trades. Conservative outcomes: same-bar"
             " stop+target = loss; 'eod' = neither hit by close.", ""]
    for rm in (15, 30):
        for inst in ("MES", "MNQ"):
            days = load_instrument(root / "data", inst, range_minutes=rm)
            dev = days[:int(len(days) * 0.6)]
            dev = [d for d in dev if d.date not in events]
            n = len(dev)
            res = [fade_anatomy(d) for d in dev]
            res = [r for r in res if r is not None]
            failed = [r for r in res if r["setup"] == "failed"]
            held = sum(1 for r in res if r["setup"] == "held")
            none = sum(1 for r in res if r["setup"] == "none")
            lines += [f"## {inst} · {rm}-min range · dev {dev[0].date} → "
                      f"{dev[-1].date} ({n} days)",
                      "",
                      f"- breakout: {len(failed) + held}/{n} days "
                      f"({(len(failed) + held) / n:.0%}) · "
                      f"**failure rate: {len(failed)}/{len(failed) + held} "
                      f"({len(failed) / max(1, len(failed) + held):.0%})** · "
                      f"no-breakout {none}",
                      f"- setups/day (fade frequency): "
                      f"{len(failed) / n:.2f}", ""]
            hdr = "| stop k | naive R | win | loss | eod | WR | " \
                  "mean ext | **true mean R** | **E[R]/trade** | E[R] eod=loss |"
            lines += [hdr, "|---|---|---|---|---|---|---|---|---|---|"]
            for k in K_STOPS:
                w = sum(1 for r in failed if r[f"k{k}"] == "win")
                ls = sum(1 for r in failed if r[f"k{k}"] == "loss")
                e = sum(1 for r in failed if r[f"k{k}"] == "eod")
                wr = w / max(1, w + ls)
                # TRUE risk = (extreme extension + k) x height: entry at the
                # boundary, stop k x height BEYOND the extreme. Reward =
                # height. Per-setup R_i = 1 / (ext_i + k).
                exts = [r["extreme_ext"] for r in failed]
                mean_ext = float(np.mean(exts))
                rs = {id(r): 1.0 / (r["extreme_ext"] + k) for r in failed}
                wins_r = sum(rs[id(r)] for r in failed if r[f"k{k}"] == "win")
                er = (wins_r - ls) / max(1, w + ls)          # eod excluded
                er_all = (wins_r - ls - e) / max(1, w + ls + e)  # eod = loss
                true_r = float(np.mean([1.0 / (x + k) for x in exts]))
                lines.append(
                    f"| {k} | {1 / k:.1f}R | {w} | {ls} | {e} | {wr:.1%} "
                    f"| {mean_ext:.2f} | **{true_r:.2f}R** "
                    f"| **{er:+.3f}** | {er_all:+.3f} |")
            # conditioning: OR width/ATR terciles, WR + E[R] (eod = loss)
            ratios = np.array([r["height"] / r["atr"] for r in failed])
            if len(ratios) > 30:
                t1, t2 = np.quantile(ratios, [1 / 3, 2 / 3])
                for k in (0.25, 0.5):
                    lines += ["", f"Width/ATR conditioning (k={k}):"]
                    for name, m in (("narrow", ratios <= t1),
                                    ("mid", (ratios > t1) & (ratios <= t2)),
                                    ("wide", ratios > t2)):
                        sub = [r for r, keep in zip(failed, m) if keep]
                        w = sum(1 for r in sub if r[f"k{k}"] == "win")
                        ls = sum(1 for r in sub if r[f"k{k}"] == "loss")
                        e = sum(1 for r in sub if r[f"k{k}"] == "eod")
                        wins_r = sum(1.0 / (r["extreme_ext"] + k)
                                     for r in sub if r[f"k{k}"] == "win")
                        er = (wins_r - ls - e) / max(1, w + ls + e)
                        lines.append(
                            f"- {name} (n={len(sub)}): WR "
                            f"{w / max(1, w + ls):.1%} · E[R]={er:+.3f}")
            lines.append("")
    out = "\n".join(lines) + "\n"
    (root / "docs" / "DIAGNOSTICS.md").write_text(out)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
