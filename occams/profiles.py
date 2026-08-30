"""D2.4 / Q3 — rule sets as versioned, dated, external profiles.

Two problems, one module.

**Hard-coded rules.** `ChallengeConfig` is already parameterised, but the
values live in code, so publishing the lab publishes one funding provider's
geometry as if it were the lab's definition of a challenge. A reader with
different rules has to edit the engine. That is backwards: **the rules are
input, not implementation.**

**Undated rules.** A provider retired a plan tier on 2026-05-01 while its
own public pages still advertised it. A rule snapshot with no date on it is
a silent expiry waiting to happen, and nothing in the code would have known.
So a profile carries an `effective_date` and a `source`, and
`assert_fresh` **refuses** a snapshot older than the caller's tolerance
rather than warning about it.

JSON rather than YAML deliberately: `occams/` is imported by the Lambda and
its dependency weight already broke a build once (B0.3). The standard
library reads JSON.

No provider is named in any shipped profile. `profiles/example-50k.json`
describes a GEOMETRY -- account size, target, trailing drawdown, guard --
because that is what the engine consumes and what a reader needs to replace.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from occams.rules import ChallengeConfig

__all__ = ["RuleProfile", "StaleProfile", "load", "assert_fresh",
           "PROFILE_DIR"]

PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles"
DEFAULT_MAX_AGE_DAYS = 90

_REQUIRED = ("name", "description", "effective_date", "source", "rules")
_RULE_KEYS = ("account", "target", "trailing_dd", "daily_guard", "min_days")


class StaleProfile(RuntimeError):
    """The rule snapshot is older than the caller is willing to trust."""


@dataclass(frozen=True)
class RuleProfile:
    name: str
    description: str
    effective_date: date
    source: str
    config: ChallengeConfig
    path: Path | None = None

    def age_days(self, today: date | None = None) -> int:
        return ((today or date.today()) - self.effective_date).days

    def is_stale(self, max_age_days: int = DEFAULT_MAX_AGE_DAYS,
                 today: date | None = None) -> bool:
        return self.age_days(today) > max_age_days

    def render(self, today: date | None = None) -> str:
        """Shown for confirmation before a run is treated as current."""
        age = self.age_days(today)
        c = self.config
        return "\n".join([
            f"  profile        {self.name}",
            f"  description    {self.description}",
            f"  effective      {self.effective_date.isoformat()}  "
            f"({age} days old)",
            f"  source         {self.source}",
            f"  account        {c.account:,.0f}",
            f"  target         {c.target:,.0f}",
            f"  trailing DD    {c.trailing_dd:,.0f}",
            f"  daily guard    {c.daily_guard:,.0f}",
            f"  min days       {c.min_days}",
            "  consistency    "
            + (f"{c.consistency_frac:.0%}" if c.consistency_frac
               else "none"),
        ])


def load(path: str | Path) -> RuleProfile:
    """Read a profile. Refuses anything incomplete rather than defaulting —
    a missing rule silently defaulting to zero is a rule that never binds."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"no profile at {p}")
    blob = json.loads(p.read_text())
    missing = [k for k in _REQUIRED if k not in blob]
    if missing:
        raise ValueError(f"{p.name} is missing {missing}. A profile without "
                         f"an effective_date and a source is a rule snapshot "
                         f"nobody can date or check.")
    rules = blob["rules"]
    absent = [k for k in _RULE_KEYS if k not in rules]
    if absent:
        raise ValueError(
            f"{p.name} is missing rules {absent}. Refusing to default them: "
            f"a rule that silently becomes zero is a rule that never binds.")
    cfg = ChallengeConfig(
        account=float(rules["account"]), target=float(rules["target"]),
        trailing_dd=float(rules["trailing_dd"]),
        daily_guard=float(rules["daily_guard"]),
        min_days=int(rules["min_days"]),
        consistency_frac=(None if rules.get("consistency_frac") is None
                          else float(rules["consistency_frac"])))
    return RuleProfile(name=blob["name"], description=blob["description"],
                       effective_date=date.fromisoformat(
                           blob["effective_date"]),
                       source=blob["source"], config=cfg, path=p)


def assert_fresh(profile: RuleProfile,
                 max_age_days: int = DEFAULT_MAX_AGE_DAYS,
                 today: date | None = None) -> RuleProfile:
    """Refuse a stale snapshot. Raises rather than warns, because a warning
    about rules is one nobody reads twice."""
    if profile.is_stale(max_age_days, today):
        raise StaleProfile(
            f"{profile.name} is {profile.age_days(today)} days old "
            f"(effective {profile.effective_date.isoformat()}, tolerance "
            f"{max_age_days}). Re-verify it against {profile.source} before "
            f"treating any result as current. A provider retired a plan tier "
            f"on 2026-05-01 while its own public pages still advertised it, "
            f"which is exactly what this refusal is for.\n\n"
            f"{profile.render(today)}")
    return profile
