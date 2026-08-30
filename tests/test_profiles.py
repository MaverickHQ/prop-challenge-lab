"""D2.4 / Q3 — rules are input, and an undated rule set is a silent expiry.

`ChallengeConfig` was already parameterised; the values just lived in code,
so publishing the lab would have published one provider's geometry as if it
were the lab's definition of a challenge. And nothing carried a DATE: a
provider retired a plan tier on 2026-05-01 while its own public pages still
advertised it, and no code here would have known.
"""

from __future__ import annotations

from datetime import date

import pytest

from occams import profiles


def _p(name="example-50k"):
    return profiles.load(profiles.PROFILE_DIR / f"{name}.json")


def test_the_shipped_example_loads_into_a_usable_config():
    p = _p()
    assert p.config.account == 50000.0
    assert p.config.target == 3000.0
    assert p.config.trailing_dd == 2000.0
    assert p.config.consistency_frac is None
    assert p.effective_date == date(2026, 7, 2)


def test_the_consistency_variant_exercises_that_path():
    p = _p("example-50k-with-consistency")
    assert p.config.consistency_frac == 0.40
    assert p.config.min_days == 2


def test_a_stale_snapshot_is_REFUSED_not_warned_about():
    p = _p()
    far = date(2027, 1, 1)
    assert p.is_stale(90, today=far)
    with pytest.raises(profiles.StaleProfile, match="days old"):
        profiles.assert_fresh(p, 90, today=far)


def test_a_fresh_snapshot_passes_and_returns_itself():
    p = _p()
    near = date(2026, 7, 20)
    assert not p.is_stale(90, today=near)
    assert profiles.assert_fresh(p, 90, today=near) is p


def test_the_refusal_shows_the_rules_it_is_refusing():
    p = _p()
    with pytest.raises(profiles.StaleProfile) as e:
        profiles.assert_fresh(p, 30, today=date(2027, 1, 1))
    msg = str(e.value)
    assert "trailing DD" in msg
    assert "2,000" in msg
    assert p.source in msg


def test_a_missing_rule_is_refused_rather_than_defaulted(tmp_path):
    """A rule that silently becomes zero is a rule that never binds."""
    bad = tmp_path / "bad.json"
    bad.write_text('{"name":"x","description":"d","effective_date":'
                   '"2026-01-01","source":"s","rules":{"account":50000}}')
    with pytest.raises(ValueError, match="Refusing to default"):
        profiles.load(bad)


def test_a_profile_without_a_date_or_source_is_refused(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"name":"x","description":"d","rules":{}}')
    with pytest.raises(ValueError, match="effective_date"):
        profiles.load(bad)


def test_no_shipped_profile_names_a_provider():
    """Section 0 of CLAUDE.md, enforced rather than remembered. The privacy
    scan covers this too; this fails closer to the change."""
    from occams.privacy import load_terms, scan_files
    terms = load_terms(".privacy-terms")
    files = sorted(profiles.PROFILE_DIR.glob("*.json"))
    assert files
    assert not scan_files(files, terms)
