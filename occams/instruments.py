"""Instrument registry — identity and per-instrument costs (Codex 1.1).

The sweep and harness must never apply MES economics to MNQ. `costs_for`
is the single lookup; unknown instruments fail loudly BEFORE any simulation.
"SYN" is the synthetic-market instrument used by tests and controls.
"""

from __future__ import annotations

from collections.abc import Mapping

from occams.sim import Costs

COSTS_BY_INSTRUMENT: dict[str, Costs] = {
    # tick 0.25 on both; multipliers differ: MES $5/pt, MNQ $2/pt.
    "MES": Costs(multiplier=5.0, tick_size=0.25, commission_per_side=1.25,
                 slippage_ticks=1),
    "MNQ": Costs(multiplier=2.0, tick_size=0.25, commission_per_side=1.25,
                 slippage_ticks=1),
}

# E3, 2026-08-01: the sealed model above ASSUMES 1 tick of slippage. Measured
# off the trades tape (60 sessions per instrument, 09:45-10:15 ET) the
# effective spread is 1.00 ticks on MES -- the assumption is right -- but
# 2.00 ticks median on MNQ, double it. A 6-lot is ordinary on MES (p90 of
# print size, 0 ticks of travel) and large on MNQ (only 3.6% of prints are
# that size; travel 1 tick median, 4 at p90).
#
# The sealed dict is deliberately NOT changed. X1 established that the engine
# reproduces verdict v3 to three decimals, and that reproducibility is worth
# more than the correction: one extra tick per side on MNQ is ~0.006R at one
# contract, an order of magnitude below the gap that matters. NEW work uses
# MEASURED_COSTS; the sealed record stays reproducible against the old model,
# and any result quoting one should say which.
MEASURED_COSTS: dict[str, Costs] = {
    "MES": Costs(multiplier=5.0, tick_size=0.25, commission_per_side=1.25,
                 slippage_ticks=1),      # measured: 1.00 ticks, confirmed
    "MNQ": Costs(multiplier=2.0, tick_size=0.25, commission_per_side=1.25,
                 slippage_ticks=2),      # measured: 2.00 ticks median
}


def costs_for(instrument: str,
              table: Mapping[str, Costs] | None = None) -> Costs:
    table = COSTS_BY_INSTRUMENT if table is None else table
    try:
        return table[instrument]
    except KeyError:
        raise ValueError(
            f"no costs registered for instrument {instrument!r} — refusing "
            f"to guess a multiplier (Codex 1.1)") from None


def resolve_costs(costs: "Costs | Mapping[str, Costs]",
                  instrument: str) -> Costs:
    """A single Costs applies to everything (synthetic paths); a mapping is
    resolved per instrument, loudly."""
    if isinstance(costs, Costs):
        return costs
    return costs_for(instrument, costs)
