"""M3 — one object carrying the whole picture, rendering itself both ways.

Every experiment script currently prints its own table AND builds its own
METRICS dict. Those are two independent renderings of the same result, and
nothing checks that they agree. The `METRICS:` line exists so a human never
retypes a number; this exists so a human never formats one twice.

The interpretive part is the verdict, and it is deliberately a 2x2 rather
than a yes/no:

                     |  CI excludes zero   |  CI spans zero
    ---------------- | ------------------- | -----------------
    |d| >= floor     |  detectable         |  inconclusive
    |d| <  floor     |  precise but        |  null
                     |  immaterial         |

Collapsing that to "significant / not significant" is how a signal
explaining 1.7% of variance gets written up as a finding — C2 sat in the
bottom-left corner and it took a paragraph of prose to say so. And ICT-P2's
raw reading was squarely `detectable`, which is exactly why a significance
test could not save us and a control had to.

`floor_multiples` is the transformation that makes results comparable: a
correlation, a Cohen's d and an ATR-scaled return all become "how many
multiples of the effect this test could actually see".
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Result"]


@dataclass(frozen=True)
class Result:
    name: str
    estimate: float
    ci: tuple[float, float] | None
    n: int
    d: float | None = None
    floor: float | None = None
    n_eff: int | None = None
    unit: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if self.n <= 0:
            raise ValueError(f"n must be positive, got {self.n}")
        if self.n_eff is not None:
            if self.n_eff <= 0 or self.n_eff > self.n:
                raise ValueError(
                    f"n_eff={self.n_eff} must be in (0, n={self.n}] — an "
                    f"independent-equivalent sample cannot exceed the raw one")
        if self.floor is not None and self.floor <= 0:
            raise ValueError(f"floor must be positive, got {self.floor}")
        if self.ci is not None:
            lo, hi = self.ci
            if lo > hi:
                raise ValueError(f"ci is inverted: ({lo}, {hi})")

    # ---- derived readings -------------------------------------------------

    @property
    def crosses_zero(self) -> bool:
        if self.ci is None:
            return True
        return self.ci[0] <= 0.0 <= self.ci[1]

    @property
    def inside_floor(self) -> bool:
        """Smaller than the smallest effect this test declared worth acting
        on. Not the same question as statistical significance."""
        if self.d is None or self.floor is None:
            return False
        return abs(self.d) < self.floor

    @property
    def floor_multiples(self) -> float | None:
        """Effect in multiples of its own detectable floor."""
        if self.d is None or self.floor is None:
            return None
        return self.d / self.floor

    @property
    def verdict(self) -> str:
        if self.crosses_zero:
            return "null" if self.inside_floor else "inconclusive"
        return "precise but immaterial" if self.inside_floor else "detectable"

    # ---- the two renderings, from one place -------------------------------

    def render(self) -> str:
        u = f" {self.unit}" if self.unit else ""
        lines = [f"{self.name}"]
        lines.append(f"  estimate    {self.estimate:+.5f}{u}")
        if self.ci is not None:
            lines.append(f"  95% CI      [{self.ci[0]:+.5f}, "
                         f"{self.ci[1]:+.5f}]{u}")
        size = f"  n           {self.n:,}"
        if self.n_eff is not None:
            size += f"   (independent-equivalent {self.n_eff:,})"
        lines.append(size)
        if self.d is not None:
            row = f"  effect      d {self.d:+.4f}"
            if self.floor is not None:
                row += (f"   floor {self.floor:.3f}"
                        f"   = {self.floor_multiples:+.2f}x floor")
            lines.append(row)
        lines.append(f"  VERDICT     {self.verdict}")
        if self.note:
            lines.append(f"  note        {self.note}")
        return "\n".join(lines)

    def to_metrics(self) -> dict:
        """The dict that goes into the `METRICS:` line. Same numbers as
        `render`, from the same fields — they cannot disagree."""
        m: dict = {"name": self.name, "estimate": self.estimate,
                   "n": self.n, "verdict": self.verdict,
                   "crosses_zero": self.crosses_zero}
        if self.ci is not None:
            m["ci"] = [self.ci[0], self.ci[1]]
        if self.n_eff is not None:
            m["n_eff"] = self.n_eff
        if self.d is not None:
            m["d"] = self.d
        if self.floor is not None:
            m["floor"] = self.floor
            m["floor_multiples"] = self.floor_multiples
        if self.unit:
            m["unit"] = self.unit
        if self.note:
            m["note"] = self.note
        return m
