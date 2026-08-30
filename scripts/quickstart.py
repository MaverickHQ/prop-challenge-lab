"""D2.3 — the $0 quickstart. No data, no credentials, no network.

The whole argument of this repository is that a backtest is worthless until
you have shown the harness can (a) find an edge that is definitely there and
(b) find nothing where there is nothing. Anyone can claim that. This runs it,
in about ten seconds, on synthetic worlds built here rather than bought.

Four demonstrations, in the order they matter:

  1. POSITIVE CONTROL   a planted edge, and the harness finds it
  2. NEGATIVE CONTROL   a dead world, and the harness reports nothing
  3. CALIBRATION GATE   the same measurement from two reference prices --
                        one correct, one that manufactures a large effect
                        from a market with no drift at all
  4. RULE PROFILE       the challenge rules as dated, replaceable input

Steps 1 and 2 are the ones every backtest should have to pass. Step 3 is the
one this programme had to learn: a result can survive every robustness check
and still be measuring the measurement.

    python3 scripts/quickstart.py        (or: make quickstart)
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from occams import calibration as cal
from occams import profiles
from occams.harness import monte_carlo, null_baseline
from occams.sim import Costs
from occams.strategy import OrbParams, make_orb_strategy
from occams.synth import make_days

COSTS = Costs(multiplier=5.0, tick_size=0.25, commission_per_side=1.25,
              slippage_ticks=1)
PARAMS = OrbParams(stop_range=1.0, target_r=1.5, risk_usd=200.0, max_trades=1)
HORIZON = 40
RULE = "-" * 72


def head(n, title):
    print(f"\n{RULE}\n{n}. {title}\n{RULE}")


def main() -> int:
    profile = profiles.load(profiles.PROFILE_DIR / "example-50k.json")
    cfg = profile.config

    head(1, "POSITIVE CONTROL — can the harness find an edge that IS there?")
    edge = make_days(120, seed=7, edge_follow=0.75, drift_pts=15.0)
    e = monte_carlo(edge, make_orb_strategy(PARAMS, COSTS), cfg, COSTS,
                    horizon_days=HORIZON)
    print(f"  planted-edge world   P(pass) = {e.p_pass:.2f}")
    print("  A harness that cannot find a planted edge cannot be trusted to")
    print("  report its absence either. This is the gate that runs FIRST.")

    head(2, "NEGATIVE CONTROL — does it report nothing where there is nothing?")
    dead = make_days(120, seed=7, edge_follow=0.50, drift_pts=0.0,
                     kick_scale=0.0)
    d = monte_carlo(dead, make_orb_strategy(PARAMS, COSTS), cfg, COSTS,
                    horizon_days=HORIZON)
    nb = null_baseline(dead, PARAMS, cfg, COSTS, horizon_days=HORIZON)
    print(f"  dead world           P(pass) = {d.p_pass:.2f}"
          f"   random-entry null = {nb:.2f}")
    print("  kick_scale=0 matters: an earlier 'no-edge' world still carried")
    print("  a harvestable impulse, so it was never a negative control at")
    print("  all. Found in 2026-07 and it invalidated a gate.")

    head(3, "CALIBRATION GATE — is the estimator measuring the market, or itself?")
    honest = cal.calibrate(cal.at_price, expected=2.0, seed=11)
    artifact = cal.calibrate(cal.at_level, expected=2.0, seed=11)
    print("  Same data. Same arithmetic. One different reference price.\n")
    print(f"  measured from PRICE        dead world {honest.dead_mean:+.4f} "
          f"= {honest.dead_sigmas:.1f} sigma  -> {honest.verdict}")
    print(f"  measured from a LEVEL      dead world {artifact.dead_mean:+.4f} "
          f"= {artifact.dead_sigmas:.1f} sigma  -> {artifact.verdict}")
    print("\n  The dead world has NO forward drift whatsoever, so the second")
    print("  reading is the measurement rather than the market: a market that")
    print("  froze solid at the trigger would still print it. That defect")
    print("  produced a real result here at six times its detectable floor,")
    print("  significant on both instruments, both sides, both horizons.")
    print("  No significance test asks the question this gate asks.")

    head(4, "RULE PROFILE — the challenge rules are input, and they are DATED")
    print(profile.render(today=date(2026, 8, 3)))
    print("\n  Swap in your own provider's published rules. `assert_fresh`")
    print("  REFUSES a snapshot older than your tolerance: a provider")
    print("  retired a plan tier while its own pages still advertised it,")
    print("  and an undated rule set is a silent expiry.")

    print(f"\n{RULE}")
    ok = e.p_pass >= 0.90 and d.p_pass <= 0.10 and \
        honest.verdict == "calibrated" and \
        artifact.verdict == "fails the dead world"
    print("ALL FOUR PASS — the instrument is calibrated." if ok else
          "SOMETHING IS WRONG — do not trust a result from this build.")
    print("Nothing above touched market data, an API key, or the network.")
    print(f"{RULE}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
