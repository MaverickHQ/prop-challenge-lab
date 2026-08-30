"""Session/timezone contract — review fix #5.

Everything downstream (opening range, session close, EOD marks) is defined
in US/Eastern. Vendor data ships tz-aware (usually UTC). The contract:
naive timestamps are a LOUD error at the boundary, never a silent shift.
The Phase 1.2 data loader must pass every frame through `to_eastern` before
anything else touches it.
"""

from __future__ import annotations

import pandas as pd

EASTERN = "America/New_York"
RTH_OPEN = "09:30"
RTH_CLOSE = "16:00"


def to_eastern(df: pd.DataFrame) -> pd.DataFrame:
    """Convert a tz-aware frame to US/Eastern. Naive input raises."""
    if df.index.tz is None:
        raise ValueError(
            "naive timestamps: vendor bars must arrive tz-aware (UTC); "
            "refusing to guess — a wrong assumption here silently shifts "
            "every session boundary")
    return df.tz_convert(EASTERN)


def rth_only(df_eastern: pd.DataFrame) -> pd.DataFrame:
    """Regular-trading-hours bars only (09:30 ≤ t < 16:00 ET)."""
    return df_eastern.between_time(RTH_OPEN, RTH_CLOSE, inclusive="left")


def split_opening_range(df_eastern: pd.DataFrame, range_minutes: int
                        ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(range_bars, session_bars) split at 09:30 + range_minutes ET."""
    rth = rth_only(df_eastern)
    cutoff = pd.Timestamp(rth.index[0].date(), tz=EASTERN) + pd.Timedelta(
        hours=9, minutes=30 + range_minutes)
    return rth[rth.index < cutoff], rth[rth.index >= cutoff]
