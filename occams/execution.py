"""E1 — can this fill actually be obtained? Orders, not assumed prices.

On 2026-08-01 a sealed verdict was found to rest on an entry price no order
could produce. `fade.py` books a fill AT the range boundary at the failure
close, but at that moment price is INSIDE the range: the boundary is behind
the market, and nothing was resting there. Every placeable order returned a
negative number while only the assumption was positive.

Nothing in the lab caught it. The planted-edge positive control could not:
a planted edge is detectable whether or not its entry price is reachable,
so the control passed and the flaw went through underneath.

This module is the fix. A strategy declares an ORDER — type, side, level,
and the bar it is placed on — and the fill is derived from what the market
then did. An entry price is never an input.

The rules are the venue's, not ours:

- **limit** buys at or below its level, sells at or above. It must be
  placed on the passive side of the market or it is a marketable order.
- **stop** buys at or above its level, sells at or below. It must be
  placed on the aggressive side or it triggers instantly.
- **market** takes the next price. It cannot name a level, which is exactly
  the guarantee the fade's entry assumption was quietly borrowing.

A limit fills only if price REACHES it; a fill is never assumed because a
level was touched at some other time.
"""

from __future__ import annotations

from dataclasses import dataclass

LIMIT, STOP, MARKET = "limit", "stop", "market"
BUY, SELL = "buy", "sell"


@dataclass(frozen=True)
class Order:
    kind: str            # limit | stop | market
    side: str            # buy | sell
    level: float | None  # None for market


class Unplaceable(ValueError):
    """The order could not have been entered at the stated moment."""


def validate(order: Order, market: float) -> None:
    """Would a venue accept this order, given where price is right now?"""
    if order.kind == MARKET:
        if order.level is not None:
            raise Unplaceable("a market order cannot name a level — that is "
                              "the assumption this module exists to refuse")
        return
    if order.level is None:
        raise Unplaceable(f"a {order.kind} order needs a level")
    if order.kind == LIMIT:
        # passive side: buy below, sell above
        if order.side == BUY and order.level > market:
            raise Unplaceable(
                f"buy limit {order.level} is ABOVE market {market} — it would "
                f"fill immediately at market, not at the level")
        if order.side == SELL and order.level < market:
            raise Unplaceable(
                f"sell limit {order.level} is BELOW market {market} — it would "
                f"fill immediately at market, not at the level")
    elif order.kind == STOP:
        # aggressive side: buy above, sell below
        if order.side == BUY and order.level < market:
            raise Unplaceable(
                f"buy stop {order.level} is BELOW market {market} — a stop on "
                f"the wrong side triggers instantly")
        if order.side == SELL and order.level > market:
            raise Unplaceable(
                f"sell stop {order.level} is ABOVE market {market} — a stop on "
                f"the wrong side triggers instantly")
    else:
        raise Unplaceable(f"unknown order kind {order.kind!r}")


def fill(order: Order, highs, lows, opens, placed_at: int,
         slippage: float = 0.0) -> tuple[int, float] | None:
    """(bar index, fill price) or None if it never filled.

    Slippage is adverse by construction: it can only ever make the fill
    worse, because a simulator that lets it help is measuring optimism."""
    n = len(highs)
    if placed_at >= n:
        return None
    if order.kind == MARKET:
        i = min(placed_at + 1, n - 1)
        adverse = slippage if order.side == BUY else -slippage
        return i, opens[i] + adverse
    lvl = order.level
    for i in range(placed_at + 1, n):
        if order.kind == LIMIT:
            hit = lows[i] <= lvl if order.side == BUY else highs[i] >= lvl
            if hit:
                # a limit does not slip in your favour, and cannot slip
                # against you past its own level
                return i, lvl
        else:                                     # STOP
            hit = highs[i] >= lvl if order.side == BUY else lows[i] <= lvl
            if hit:
                gapped = (opens[i] >= lvl if order.side == BUY
                          else opens[i] <= lvl)
                px = opens[i] if gapped else lvl
                adverse = slippage if order.side == BUY else -slippage
                return i, px + adverse
    return None


def obtainable(*, assumed_entry: float, side: str, decision_bar: int,
               market_at_decision: float, highs, lows, opens,
               tolerance: float = 1e-9) -> tuple[bool, str]:
    """THE GATE. Could ANY order placed at `decision_bar` have produced a
    fill at `assumed_entry`? Returns (ok, explanation).

    This is what would have caught the fade: at the failure close the
    boundary sits behind the market, so the only order that can name it is
    a limit, and a limit only fills on a retest — at a different time, on
    different information."""
    reasons = []
    for kind in (LIMIT, STOP, MARKET):
        o = Order(kind, side, None if kind == MARKET else assumed_entry)
        try:
            validate(o, market_at_decision)
        except Unplaceable as e:
            reasons.append(f"{kind}: {e}")
            continue
        got = fill(o, highs, lows, opens, decision_bar)
        if got is None:
            reasons.append(f"{kind}: placeable, but never filled")
            continue
        _, px = got
        if abs(px - assumed_entry) <= tolerance:
            return True, f"{kind} order fills at {assumed_entry}"
        reasons.append(f"{kind}: fills at {px}, not {assumed_entry}")
    return False, "; ".join(reasons)


# ─── the gate as a verdict precondition (E1) ───

class UnobtainableEntry(ValueError):
    """A protocol tried to seal on a fill no order could produce."""


def audit_orb(day, plan, costs) -> list[str]:
    """ORB arms stops OUTSIDE the range while price is inside it. Verified
    clean over 6,774 orders (Z04-ORB-OBTAINABLE)."""
    problems = []
    market = float(day.range_bars["close"].iloc[-1])
    for side, lvl in ((BUY, getattr(plan, "buy_stop", None)),
                      (SELL, getattr(plan, "sell_stop", None))):
        if lvl is None:
            continue
        try:
            validate(Order(STOP, side, lvl), market)
        except Unplaceable as e:
            problems.append(f"{day.date} {side}: {e}")
    return problems


def audit_fade(day, plan, costs) -> list[str]:
    """The fade books a fill AT the boundary at the failure close, when the
    boundary is already behind the market. This is the defect the gate was
    built for, so it reports rather than pretends."""
    return [f"{day.date}: the fade books its entry at the range boundary at "
            f"the failure close, a price already behind the market. See "
            f"docs/VERDICT-2026-07-06-v3-ADDENDUM.md"]


AUDITORS = {"orb": audit_orb, "fade": audit_fade}


def assert_entries_obtainable(family: str, days, plans, costs, *,
                              sample: int = 200) -> None:
    """Called before any sweep. Raises rather than warns.

    DEFAULT-DENY: a family with no auditor FAILS. A new strategy must supply
    one, because the alternative -- unknown families passing silently -- is
    exactly how the fade was sealed on an impossible fill while the
    planted-edge control looked fine. A control detects a planted edge
    whether or not its entry is reachable, so it could never have caught it."""
    auditor = AUDITORS.get(family)
    if auditor is None:
        raise UnobtainableEntry(
            f"family {family!r} has no entry auditor. Add one to "
            f"occams.execution.AUDITORS. An unaudited family cannot be "
            f"sealed -- default-deny is the point of this gate.")
    problems: list[str] = []
    for day, plan in list(zip(days, plans))[:sample]:
        if plan is None:
            continue
        problems.extend(auditor(day, plan, costs))
        if len(problems) >= 5:
            break
    if problems:
        raise UnobtainableEntry(
            f"{family}: entries are not obtainable. First problems:\n  "
            + "\n  ".join(problems[:5]))
