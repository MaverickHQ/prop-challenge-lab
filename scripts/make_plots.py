"""D2.5 — the three figures worth publishing.

Every number is READ FROM THE REGISTER, not typed here, so a figure cannot
drift from the record it claims to show. The one exception is the
feasibility frontier, which is recomputed through the real rules engine
because it is a property of the rules rather than of a past run.

    1. FRONTIER    what edge the rules actually require
    2. P(PASS) SHAPE   why a rising curve is a warning, not a result
    3. FOUR ORDERS     the most publishable single figure this lab produced

matplotlib is a DEV dependency only. `occams/` is imported by the Lambda and
its dependency weight already broke a build once (B0.3), so nothing in the
package imports it.

    python3 scripts/make_plots.py        (or: make plots)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from occams import archive, profiles

OUT = Path(__file__).resolve().parent.parent / "artifacts" / "plots"
INK, GRID = "#16211F", "#D2DAD8"
BRASS, VERDIGRIS, RUST, SLATE = "#96690F", "#2F6C63", "#9C4429", "#6D7F82"


def _style(ax, title, sub=""):
    ax.set_title(title, fontsize=12, fontweight="600", color=INK, loc="left",
                 pad=26 if sub else 8)
    if sub:
        ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=8.5,
                color=SLATE, va="bottom")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=SLATE, labelsize=9)
    ax.grid(axis="y", color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def _metrics(key: str) -> dict:
    s3 = archive._client()
    body = s3.get_object(Bucket=archive.bucket(), Key=key)["Body"].read()
    return json.loads(body)["metrics"]


# --------------------------------------------------------------------------

def fig_frontier():
    """What the rules REQUIRE, computed before any edge was hunted."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_feas", Path(__file__).resolve().parent / "feasibility.py")
    feas = importlib.util.module_from_spec(spec)
    # must be in sys.modules BEFORE exec: a @dataclass in the loaded module
    # resolves its annotations through sys.modules[cls.__module__]
    sys.modules[spec.name] = feas
    spec.loader.exec_module(feas)

    cfg = profiles.load(profiles.PROFILE_DIR / "example-50k.json").config
    wrs = np.arange(0.35, 0.71, 0.025)
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for r_net, colour in ((1.0, SLATE), (1.5, BRASS), (2.0, VERDIGRIS)):
        ys = [feas.simulate(cfg, float(w), r_net, 0.5, 175.0, 90,
                            runs=300, seed=11).p_pass for w in wrs]
        ax.plot(wrs * 100, ys, color=colour, lw=2,
                label=f"net {r_net:.1f}R per win")
    ax.axhline(0.55, color=RUST, lw=1.2, ls="--")
    ax.text(35.4, 0.575, "0.55 — the gate", color=RUST, fontsize=9)
    _style(ax, "Asymmetry is the lever, not hit rate",
           "P(pass) in 90 days · 0.5 trades/day · $175 risk · "
           "computed through the real rules engine")
    ax.set_xlabel("win rate (%)", fontsize=9.5, color=SLATE)
    ax.set_ylabel("P(pass)", fontsize=9.5, color=SLATE)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    return fig, "01-feasibility-frontier"


def fig_pass_shape():
    """E2. The prediction was wrong, and being wrong produced the diagnostic."""
    m = _metrics("experiments/E2-OBJECTIVE/2026-08-01-zero-tier.json")
    ladder = m["risk_ladder"]
    risks = sorted(int(k) for k in ladder)
    p_pass = [ladder[str(r)]["p_pass"] for r in risks]
    p_breach = [ladder[str(r)]["p_breach"] for r in risks]

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.plot(risks, p_pass, color=BRASS, lw=2, marker="o", ms=5,
            label="P(pass)")
    ax.plot(risks, p_breach, color=RUST, lw=2, marker="o", ms=5, ls="--",
            label="P(breach)")
    ax.axhline(0.55, color=SLATE, lw=1, ls=":")
    ax.text(80, 0.575, "0.55 — the gate", color=SLATE, fontsize=9)
    _style(ax, "A rising P(pass) curve is a warning, not a result",
           "Monotonic means variance harvesting. An interior peak REQUIRES a "
           "positive edge — so the shape is an edge diagnostic")
    ax.set_xlabel("risk per trade ($)", fontsize=9.5, color=SLATE)
    ax.set_ylabel("probability", fontsize=9.5, color=SLATE)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.annotate("more size only buys\nmore variance",
                xy=(350, p_pass[-1]), xytext=(250, 0.45), fontsize=9,
                color=INK, arrowprops=dict(arrowstyle="->", color=SLATE,
                                           lw=1))
    fig.tight_layout()
    return fig, "02-p-pass-shape"


def fig_four_orders():
    """Z0. The most publishable single figure this lab produced."""
    m = _metrics("experiments/Z-ENTRY-IMPLEMENTABLE/"
                 "2026-08-01-sop-verified.json")
    rows = [("sealed engine\n(ASSUMED fill)", "sealed engine (ASSUMED fill)"),
            ("limit after\nthe failure close", "a_limit_after_close"),
            ("market at\nthe failure close", "b_market_at_close"),
            ("stop armed\nat the breakout", "c_stop_armed_at_breakout")]
    labels = [r[0] for r in rows]
    mes = [m[r[1]]["MES"] for r in rows]
    mnq = [m[r[1]]["MNQ"] for r in rows]

    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.barh(y - 0.19, mes, height=0.36,
            color=[VERDIGRIS if v > 0 else RUST for v in mes], label="MES")
    ax.barh(y + 0.19, mnq, height=0.36, alpha=0.55,
            color=[VERDIGRIS if v > 0 else RUST for v in mnq], label="MNQ")
    ax.axvline(0, color=INK, lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    for yy, v in list(zip(y - 0.19, mes)) + list(zip(y + 0.19, mnq)):
        ax.text(v + (0.006 if v > 0 else -0.006), yy, f"{v:+.3f}",
                va="center", ha="left" if v > 0 else "right", fontsize=8.5,
                color=INK)
    _style(ax, "Only the assumption is positive",
           "R per trade. The strategy passed a sealed verdict at +0.1R — "
           "then no placeable order reproduced its fill")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, lw=0.6, alpha=0.7)
    ax.set_xlabel("R per trade", fontsize=9.5, color=SLATE)
    # proxy handles in NEUTRAL grey: in this figure colour encodes SIGN,
    # not instrument, and a colour-coded legend would say the opposite
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=SLATE, label="MES"),
                       Patch(facecolor=SLATE, alpha=0.55, label="MNQ")],
              frameon=False, fontsize=9, loc="lower right")
    ax.text(0.99, 0.02, "green = positive · red = negative",
            transform=ax.transAxes, ha="right", fontsize=8, color=SLATE)
    fig.tight_layout()
    return fig, "03-four-orders"


def fig_decomposition():
    """ICT-P2-CONTROL. The headline, split into the part that had already
    happened and the part that was the claim."""
    m = _metrics("experiments/ICT-P2-CONTROL/r1.json")
    total, pen, drift = m["total_mean"], m["penetration_mean"], m["drift_mean"]
    lo, hi = m["drift_ci"]
    share = m["penetration_share"]

    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    rows = ["the headline",
            "already travelled\nbefore the signal",
            "what happened next\n(the actual claim)"]
    y = np.arange(3)
    for yy, v, c, a in zip(y, (total, pen, drift),
                           (RUST, RUST, SLATE), (0.92, 0.5, 0.92)):
        ax.barh(yy, v, height=0.52, color=c, alpha=a)

    # values INSIDE the two large bars; the small one is labelled outside
    ax.text(total / 2, 0, f"{total:+.3f}", va="center", ha="center",
            fontsize=11, color="white", fontweight="700")
    ax.text(pen / 2, 1, f"{pen:+.3f}\n{share:.1%} of the headline",
            va="center", ha="center", fontsize=9.5, color=INK,
            fontweight="600", linespacing=1.5)

    ax.errorbar(drift, 2, xerr=[[drift - lo], [hi - drift]], fmt="none",
                ecolor=INK, elinewidth=1.5, capsize=5, capthick=1.5)
    ax.text(lo - 0.004, 2, f"{drift:+.3f}", va="center", ha="right",
            fontsize=10, color=INK, fontweight="700")
    ax.text(hi + 0.004, 2, "interval crosses zero", va="center", ha="left",
            fontsize=9, color=SLATE, style="italic")

    ax.axvline(0, color=INK, lw=1.1)
    ax.set_yticks(y)
    ax.set_yticklabels(rows, fontsize=9.5)
    ax.invert_yaxis()
    _style(ax, "95% ruler, 5% world",
           "A measurement taken from a level price had already passed — a "
           "market that froze at the signal prints the same headline")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, lw=0.6, alpha=0.7)
    ax.set_xlabel("ATR units, reversal-signed", fontsize=9.5, color=SLATE)
    ax.set_xlim(-0.20, 0.075)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.text(0.5, 0.035,
             "headline  =  already travelled  +  what happened next     "
             "\u2014 an exact identity, so the split cannot flatter itself",
             ha="center", fontsize=8.5, color=SLATE)
    return fig, "04-reference-price-decomposition"


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for builder in (fig_frontier, fig_pass_shape, fig_four_orders,
                    fig_decomposition):
        fig, name = builder()
        for ext in ("png", "svg"):
            path = OUT / f"{name}.{ext}"
            fig.savefig(path, dpi=200, bbox_inches="tight",
                        facecolor="white")
        plt.close(fig)
        print(f"  wrote {name}.png / .svg")
    print(f"\n{len(list(OUT.glob('*.png')))} figures in {OUT}")
