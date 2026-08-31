"""T3 — MGC and MCL are RECORDED, and must not be usable.

The first validity gate on `T3-COST-FILTER-REPLICATION` says the
contract specs must come from the exchange rather than be inferred.
They were unreachable on 2026-08-30, so the specs are written down
and the code refuses to build a `Costs` from them. These tests pin
the refusal, because a recorded spec that quietly becomes usable is
worse than no spec at all.
"""

import pytest



# --- T3: metals and energy, recorded but not usable ---

def test_unverified_specs_are_unreachable_through_the_normal_lookup():
    """Recording a spec must not make it usable. `costs_for` is the single
    lookup every simulation goes through, and MGC/MCL must fail there
    exactly as an unknown instrument does."""
    from occams.instruments import costs_for
    for inst in ("MGC", "MCL"):
        with pytest.raises(ValueError, match="refusing to guess"):
            costs_for(inst)


def test_asking_for_an_unverified_spec_refuses_and_says_what_is_missing():
    """The gate names the unknowns rather than filling them. Commission is
    broker-specific and slippage cannot be known without a trades tape --
    E3 measured the sealed assumption OPTIMISTIC BY 2x on MNQ, so a Costs
    built from plausible placeholders would produce an expectancy
    indistinguishable from a measured one."""
    from occams.instruments import unverified_costs
    with pytest.raises(NotImplementedError) as e:
        unverified_costs("MGC")
    msg = str(e.value)
    assert "RECORDED, NOT VERIFIED" in msg
    assert "slippage_ticks" in msg and "commission_per_side" in msg


def test_every_unverified_spec_is_flagged_unverified():
    """A spec that quietly acquired verified=True would pass straight into
    use. The flag is the thing the gate keys on."""
    from occams.instruments import UNVERIFIED_COSTS
    assert UNVERIFIED_COSTS, "T3 needs MGC/MCL recorded"
    for inst, spec in UNVERIFIED_COSTS.items():
        assert spec["verified"] is False, f"{inst} claims to be verified"
        assert spec["slippage_ticks"] is None, (
            f"{inst} has a slippage number, which cannot be known without a "
            f"trades tape -- if one was measured, move it to MEASURED_COSTS")
