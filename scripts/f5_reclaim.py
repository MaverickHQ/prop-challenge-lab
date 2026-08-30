"""F5 recompute: H-RECLAIM, through the audited engine.

Deliberately a thin entry point. `experiment.run` executes an archived
script with NO ARGUMENTS, so that a frozen script is a faithful record you
can re-run and get the same thing -- a parameterised script archived without
its parameter is not. One entry point per hypothesis is what that buys.

The computation lives in `scripts/backfill_f5.py`, pinned by `engine_sha`,
with every audited primitive it called recorded in `calcs.json`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from occams import experiment  # noqa: E402
from scripts.backfill_f5 import h_reclaim, render  # noqa: E402

if __name__ == "__main__":
    out = h_reclaim()
    print(render("H-RECLAIM", out))
    experiment.emit(out)
