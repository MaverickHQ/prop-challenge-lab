"""File-backed live state — review fix #2 (persistence + idempotency).

The live path is two separate daily processes (morning/evening cron), so
everything the day mutates must round-trip through one JSON file, and
re-running a day must REPLACE its records (the grill decision: late /fills
→ recompute + resend), never double-append. Writes are atomic (tmp +
os.replace); a corrupt file is a loud error, never silently reset — losing
the trailing-DD floor mid-challenge is a money bug.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from occams.parity import ParityLog
from occams.rules import ChallengeConfig, ChallengeState


@dataclass
class LiveState:
    challenge: ChallengeState | None = None
    day_drifts: dict[str, list[float]] = field(default_factory=dict)
    processed_days: dict[str, dict] = field(default_factory=dict)

    def set_day_drifts(self, day: str, drifts: list[float]) -> None:
        """Idempotent by construction: keyed by day, last write wins."""
        self.day_drifts[day] = list(drifts)

    def record_processed(self, day: str, **record) -> None:
        self.processed_days[day] = record

    def parity_log(self, *, kill_threshold_usd: float,
                   min_trades_before_kill: int = 10,
                   abs_kill_threshold_usd: float | None = None) -> ParityLog:
        log = ParityLog(kill_threshold_usd=kill_threshold_usd,
                        min_trades_before_kill=min_trades_before_kill,
                        abs_kill_threshold_usd=abs_kill_threshold_usd)
        for day in sorted(self.day_drifts):
            for d in self.day_drifts[day]:
                log.record_drift(d)
        return log


class StateStore:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self, cfg: ChallengeConfig | None = None) -> LiveState:
        if not self._path.exists():
            return LiveState()
        try:
            raw = json.loads(self._path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"corrupt state file {self._path}: {exc}. NOT resetting — "
                f"the trailing-DD floor lives here; restore from backup or "
                f"reconstruct from Debrief history.") from exc
        state = LiveState(
            day_drifts={k: list(v) for k, v in raw.get("day_drifts", {}).items()},
            processed_days=dict(raw.get("processed_days", {})),
        )
        snap = raw.get("challenge")
        if snap is not None:
            if cfg is None:
                raise ValueError("state file holds challenge state; pass cfg "
                                 "to restore it")
            state.challenge = ChallengeState.restore(cfg, snap)
        return state

    def save(self, state: LiveState) -> None:
        payload = {
            "challenge": (state.challenge.snapshot()
                          if state.challenge is not None else None),
            "day_drifts": state.day_drifts,
            "processed_days": state.processed_days,
        }
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True))
        os.replace(tmp, self._path)      # atomic on POSIX
