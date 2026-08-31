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


# ─── T3: metals and energy, RECORDED BUT NOT USABLE ───
#
# `T3-COST-FILTER-REPLICATION` needs MGC and MCL, and its first validity gate
# says the specs must come from the exchange's published contract
# specifications rather than be inferred. On 2026-08-30 both sources were
# unreachable (CME timed out, the broker page returned 403), so these are
# RECORDED FROM MEMORY AND NOT VERIFIED.
#
# They are deliberately NOT in `COSTS_BY_INSTRUMENT` or `MEASURED_COSTS`, so
# `costs_for` cannot reach them and no simulation can quietly consume them.
# `unverified_costs()` raises instead of returning, and a test pins that.
#
# Slippage is the field that matters and the one nobody can look up. E3
# measured 1.00 ticks on MES -- the sealed assumption was right -- and 2.00
# ticks on MNQ, DOUBLE the assumption, off 60 sessions of trades tape. Metals
# and energy have their own microstructure and no tape has been bought, so
# `slippage_ticks` below is a placeholder, not an estimate.
UNVERIFIED_COSTS: dict[str, dict] = {
    "MGC": {"contract": "Micro Gold, 10 troy oz",
            "multiplier": 10.0, "tick_size": 0.10,
            "commission_per_side": None,   # broker-specific, not published
            "slippage_ticks": None,        # UNMEASURED -- needs tape
            "verified": False},
    "MCL": {"contract": "Micro WTI Crude Oil, 100 barrels",
            "multiplier": 100.0, "tick_size": 0.01,
            "commission_per_side": None,
            "slippage_ticks": None,
            "verified": False},
}


def unverified_costs(instrument: str) -> Costs:
    """Refuse. Recorded specs are not verified specs.

    This exists so the MGC/MCL numbers can be written down without becoming
    usable. Every field marked None is a real unknown -- commission is
    broker-specific and slippage cannot be known without a trades tape --
    and a `Costs` built by filling them with plausible values would produce
    an expectancy indistinguishable from a measured one.
    """
    spec = UNVERIFIED_COSTS.get(instrument)
    if spec is None:
        raise ValueError(f"no unverified spec recorded for {instrument!r}")
    missing = [k for k, v in spec.items() if v is None]
    raise NotImplementedError(
        f"{instrument} ({spec['contract']}) is RECORDED, NOT VERIFIED. "
        f"multiplier={spec['multiplier']}, tick={spec['tick_size']} were "
        f"written from memory on 2026-08-30 because the exchange's published "
        f"specifications were unreachable, and {missing} are genuine "
        f"unknowns. Verify against the contract specs and measure slippage "
        f"off a trades tape before registering a result -- E3 found the "
        f"sealed slippage assumption optimistic by 2x on MNQ."
    )


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
