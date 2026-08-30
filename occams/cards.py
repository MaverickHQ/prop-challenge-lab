"""B2.4 — one source of truth for the text the human acts on.

Three things emit cards: the AWS poller, the local scripts, and the Pine
chart aid. If their wording drifts, the human reads one instruction on the
chart and a different one on the phone — and the STOP/LIMIT episode
(AMENDMENT-4a) is exactly what that costs: two of the campaign's first
three setups, lost to a card naming an order no venue accepts.

Python callers import these functions. Pine cannot import Python, so the
shared vocabulary is pinned as constants here and
`tests/test_cards.py::test_the_pine_aid_uses_the_same_wording` asserts the
`.pine` file still contains every one of them. Change a phrase here without
changing the chart and the suite fails.
"""

from __future__ import annotations

# --- the shared vocabulary. Pine must contain each of these literally. ---
BUY_VERB = "BUY LIMIT"        # protocol #4a: a limit, never a stop
SELL_VERB = "SELL LIMIT"
QTY_JOIN = "x @ "
STOP_JOIN = " | stop "
TARGET_JOIN = " | target "
STAND_ASIDE = "STAND ASIDE"
FILL_PLACEHOLDER = "<YOUR FILL>"

PINE_REQUIRED = (BUY_VERB, SELL_VERB, QTY_JOIN, STOP_JOIN, TARGET_JOIN,
                 STAND_ASIDE, FILL_PLACEHOLDER)


def _n(x: float) -> str:
    """Trim a trailing .0 so 7480.25 and 28415 both read naturally, and
    the string matches what the chart prints."""
    return f"{x:g}"


def verb(side: str) -> str:
    return SELL_VERB if side == "short" else BUY_VERB


def order_line(side: str, contracts: int, entry: float, stop: float,
               target: float) -> str:
    """The instruction itself. This exact shape appears on the chart."""
    return (f"{verb(side)} {contracts}{QTY_JOIN}{_n(entry)}"
            f"{STOP_JOIN}{_n(stop)}{TARGET_JOIN}{_n(target)}")


def range_card(instrument: str, high: float, low: float) -> str:
    return (f"{instrument} opening range {_n(high)} / {_n(low)}\n"
            f"/range {instrument} {_n(high)} {_n(low)}")


def stand_aside_card(instrument: str, risk_usd: float) -> str:
    return (f"{instrument} {STAND_ASIDE} - risk per contract exceeds "
            f"${risk_usd:.0f}. Send: /skip {instrument} stand-aside risk")


def setup_card(instrument: str, side: str, contracts: int, entry: float,
               stop: float, target: float, extreme: float) -> str:
    return (f"{instrument} "
            f"{order_line(side, contracts, entry, stop, target)}\n"
            f"/setup {instrument} {side} {_n(extreme)}\n"
            f"Reply /ack {instrument} placed|missed <reason>")


def fill_prompt(instrument: str, event: str, level: float, when: str,
                contracts: int) -> str:
    """Never states a price. The system saw a LEVEL trade; the fill is
    read off the Trading Panel, because a computed price would drive drift
    to zero by construction."""
    label = "entry level" if event == "entry" else f"{event.upper()} level"
    return (f"{instrument} {label} {_n(level)} traded at {when} ET.\n"
            f"Check your Trading Panel and send:\n"
            f"/fills {instrument} {event} {FILL_PLACEHOLDER} {contracts}")
