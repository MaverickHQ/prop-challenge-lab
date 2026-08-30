"""F1-F4 — the research console must not be able to flatter the register.

A generated report is a rendering, so every defect it can have is a defect
of agreement: it says something the record does not.

**It must not invent resolution.** The register records questions and never
writes answers back, so a report showing a tidy outcome column would be
reporting on a register that does not exist.

**It must not silently drop rows.** The first run rendered a `None / None`
row because `experiments/campaign/` holds live paper state at the same key
depth as a run record. The fix was to exclude it by name -- and the failure
mode of the fix is over-filtering, which loses real runs without saying so.

**It must not flatten a `Result` into a string.** A verdict rendered as one
more name/value row throws away the only object built to say what a number
is allowed to mean. Nor may it promote a free-text audit verdict into a
scored effect: an audit has no floor, so there is nothing to measure it
against and any precision shown would be invented.

**It must be reproducible.** A fresh pull yields S3's key order while the
cache is written sorted -- twice, that produced two different artifacts from
one register. Anything archived beside a claim has to render the same from
either source, and has to be diffable against the next one.

**It must fetch nothing at view time.** Including when four matplotlib
figures are inlined, whose colliding glyph ids would otherwise make figures
2-4 silently render with figure 1's letterforms.
"""

from __future__ import annotations

import importlib.util
import itertools
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location(
        "_build_report", ROOT / "scripts" / "build_report.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture
def register():
    """Two hypotheses -- one with a run, one untouched -- and a run whose
    hypothesis record is missing entirely."""
    return {
        "hypotheses": [
            {"id": "H-BETA", "status": "registered", "outcome": None,
             "alpha_allocated": 0.05, "information_axis": "price",
             "search_space_size": 2, "statement": "beta statement",
             "mechanism": "why beta should work",
             "power_plan": {"test": "correlation", "effect": 0.07}},
            {"id": "H-ALPHA", "status": "registered", "outcome": None,
             "alpha_allocated": 0.02, "information_axis": "flow",
             "search_space_size": 1, "statement": "alpha statement",
             "mechanism": "why alpha should work"},
        ],
        "experiments": [
            {"hypothesis_id": "H-BETA", "run_id": "r1",
             "metrics": {"MES": {"effect": -0.0004}, "n": 3260},
             "config": {"horizon": 20}, "controls_passed": True,
             "spend_usd": 1.5, "note": "a null",
             "recorded_at": "2026-08-01T00:00:00+00:00",
             "engine_sha": "abc123"},
            {"hypothesis_id": "H-GHOST", "run_id": "r1", "metrics": {},
             "config": {}, "controls_passed": False, "spend_usd": 0.0,
             "note": "", "recorded_at": "2026-08-02T00:00:00+00:00",
             "engine_sha": "def456"},
        ],
        "manifest_objects": 1259,
        "engine_sha": "0f134eb",
        "pulled_at": "2026-08-30T00:00:00+00:00",
    }


def test_it_reports_the_register_gap_instead_of_inventing_outcomes(
        mod, register):
    """The gap is the point. H-BETA has a run and no outcome, so the page
    must say so in the words of a defect, not leave a blank cell that reads
    as 'nothing to report'."""
    page = mod.render(register)
    # Collapsed: the sentence wraps in the source, and a test that depends
    # on where the line breaks tests the formatter, not the claim.
    flat = " ".join(page.split())
    assert "with an archived run and no resolution" in flat
    assert "multiplicity ledger cannot be computed" in flat
    # The distinction the absence cannot express, stated rather than implied.
    assert "Unresolved is not the same as unanswered" in flat
    assert "H-BETA" in page
    # The gap names only hypotheses that HAVE a run and no outcome. H-ALPHA
    # has no run, so it is merely open -- not evidence of the gap. Read from
    # the id list the block ends with rather than by slicing on tags, which
    # broke silently when the block moved inside the register section.
    listed = re.search(r'<p class="mono">(.*?)</p>', page, re.S).group(1)
    assert "H-BETA" in listed and "H-ALPHA" not in listed


def test_a_run_with_no_hypothesis_record_is_shown_not_dropped(mod, register):
    """A hole in the register is evidence about the register. Dropping it
    would make the page tidier and the record less true."""
    page = mod.render(register)
    assert "H-GHOST" in page
    assert "MISSING FROM REGISTER" in page


def test_failed_controls_are_loud(mod, register):
    """H-GHOST's run did not pass its controls. A report that rendered that
    the same way as a passing run would be worse than no report."""
    page = mod.render(register)
    assert "CONTROLS NOT PASSED" in page


def test_nested_metrics_survive_flattening(mod, register):
    """Records nest per instrument, and several findings turn entirely on
    the per-instrument split."""
    page = mod.render(register)
    assert "MES.effect" in page
    assert "-0.0004" in page


def test_alpha_is_summed_from_the_records(mod, register):
    assert mod.alpha_spent(register["hypotheses"]) == pytest.approx(0.07)


def test_hypotheses_are_ordered_so_the_artifact_is_diffable(mod, register):
    """Sorted by id, not by whatever order the archive listed them in. An
    artifact that reshuffles cannot be diffed against the next one."""
    order = [h.get("id") for h, _ in mod.by_hypothesis(register)]
    assert order == ["H-ALPHA", "H-BETA", "H-GHOST"]


def test_the_page_fetches_nothing_at_view_time(mod, register):
    """It has to render from a file:// URL years from now with no network.

    The check is on things the browser would FETCH, not on the substring
    'http'. Inlined matplotlib figures carry XML namespace declarations like
    `xmlns="http://www.w3.org/2000/svg"`, which are identifiers and are never
    requested -- an earlier version of this test banned the substring and so
    forbade embedding a figure at all.
    """
    page = mod.render(register)
    assert not re.search(r"<(script|iframe|object|embed)\b", page)
    assert "@import" not in page
    for attr, val in re.findall(r'\b(?:xlink:)?(href|src)="([^"]*)"', page):
        assert val.startswith("#"), f"{attr}={val!r} would be fetched"


def test_the_page_is_well_formed(mod, register):
    """An unclosed <html> shipped in the first run of this generator."""
    from html.parser import HTMLParser

    void = {"meta", "br", "hr", "img", "input", "link", "source"}

    class P(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack, self.bad = [], []

        def handle_starttag(self, tag, attrs):
            if tag not in void:
                self.stack.append(tag)

        def handle_endtag(self, tag):
            if not self.stack:
                self.bad.append(f"stray </{tag}>")
            elif self.stack[-1] == tag:
                self.stack.pop()
            else:
                self.bad.append(f"</{tag}> inside <{self.stack[-1]}>")

    p = P()
    p.feed(mod.render(register))
    assert p.bad == []
    assert p.stack == []


def test_values_from_the_register_are_escaped(mod):
    """Notes and statements are free text written by a human. They are data,
    not markup."""
    reg = {"hypotheses": [{"id": "H-X", "status": "registered",
                           "statement": "<script>alert(1)</script>",
                           "mechanism": "m", "alpha_allocated": 0.01}],
           "experiments": [], "manifest_objects": 0,
           "engine_sha": "x", "pulled_at": "t"}
    page = mod.render(reg)
    assert "<script>" not in page
    assert "&lt;script&gt;" in page


SCORED = {
    "hypothesis_id": "H-BETA", "run_id": "r2", "controls_passed": True,
    "spend_usd": 0.0, "note": "", "recorded_at": "2026-08-03T00:00:00+00:00",
    "engine_sha": "abc123", "config": {},
    "metrics": {
        "primary": {"name": "the claim", "estimate": -0.089,
                    "ci": [-0.134, -0.043], "d": -0.089, "floor": 0.07,
                    "floor_multiples": -1.27, "n": 3442, "n_eff": 1811,
                    "unit": "Spearman r", "verdict": "detectable",
                    "note": "positive = the mechanism holds"},
        "audit_only": {"verdict": "CLEAN - no defect", "n": 6774},
        "bars": 120,
    },
}


def test_result_blocks_are_found_and_audits_are_not(mod):
    """`Result.to_metrics()` blocks are findings. A free-text audit verdict
    is not -- it has no estimate and no floor, so there is nothing to measure
    it against, and rendering it as a scored effect would invent precision."""
    results = mod.find_results([SCORED])
    audits = mod.find_audits([SCORED])
    assert [r["_path"] for r in results] == ["primary"]
    assert [a["_path"] for a in audits] == ["audit_only"]
    assert results[0]["_hid"] == "H-BETA" and results[0]["_run"] == "r2"


def test_a_finding_renders_its_verdict_and_floor_not_just_a_number(mod):
    """The first version of this page flattened a Result into name/value rows
    where `verdict` looked like any other metric."""
    page = mod.render({"hypotheses": [], "experiments": [SCORED],
                       "manifest_objects": 0, "engine_sha": "x",
                       "pulled_at": "t"})
    assert "detectable" in page
    assert "-1.27&times; floor" in page or "-1.27" in page
    assert "1,811" in page          # independent-equivalent n is shown
    assert "CLEAN - no defect" in page   # the audit survives, separately


def test_every_finding_drills_through_to_its_register_entry(mod):
    """F4 is a verb -- "click a result, get the register entry". The first
    build defined 20 anchors and linked to none of them, so the content was
    reachable only by scrolling and the feature was claimed but absent.

    The anchor must sit INSIDE the <details>, not on it: browsers auto-expand
    a collapsed <details> only when the fragment target is within it.
    """
    reg = {"hypotheses": [{"id": "H-BETA", "status": "registered",
                           "mechanism": "m", "alpha_allocated": 0.05}],
           "experiments": [SCORED], "manifest_objects": 0,
           "engine_sha": "x", "pulled_at": "t"}
    page = mod.render(reg)

    targets = set(re.findall(r'href="#(h-[^"]+)"', page))
    assert targets, "no finding links to a register entry"
    for t in targets:
        assert f'id="{t}"' in page, f"link to #{t} with no such anchor"

    # The anchor is on a span inside the <details>, not on the element.
    assert 'class="hid" id="h-H-BETA"' in page
    assert '<details class="hyp' in page
    assert 'id="h-H-BETA"><summary' not in page


def test_the_ci_strip_places_zero_and_the_floor_band(mod):
    """The strip is the lab's argument in one graphic, so its geometry is
    worth asserting: an interval entirely below zero must draw entirely to
    the left of the zero line, and the floor band must straddle it."""
    r = {"estimate": -0.089, "ci": [-0.134, -0.043], "floor": 0.07,
         "verdict": "detectable"}
    svg = mod.ci_strip(r, width=340)
    zero = float(re.search(r'class="zero" x1="([\d.]+)"', svg).group(1))
    hi = float(re.search(r'class="bar"[^/]*x2="([\d.]+)"', svg).group(1))
    band_x = float(re.search(r'class="floorband" x="([\d.]+)"', svg).group(1))
    band_w = float(re.search(r'class="floorband"[^/]*width="([\d.]+)"',
                             svg).group(1))
    assert hi < zero, "an interval below zero must not cross the zero line"
    assert band_x < zero < band_x + band_w, "the floor band must straddle zero"


def test_a_strip_without_an_interval_is_omitted_not_faked(mod):
    assert mod.ci_strip({"estimate": 0.1, "verdict": "null"}) == ""


def test_metric_rows_are_sorted_so_the_cache_renders_the_same_page(mod):
    """A fresh pull yields S3's key order; the cache is written sorted. Until
    these were sorted, the same register produced two different artifacts
    depending on where the bytes came from."""
    a = mod.metric_rows({"b": 1, "a": {"z": 2, "y": 3}})
    b = mod.metric_rows({"a": {"y": 3, "z": 2}, "b": 1})
    assert a == b == [("a.y", "3"), ("a.z", "2"), ("b", "1")]


def test_figure_ids_are_namespaced_per_figure(mod):
    """matplotlib names glyph defs `DejaVuSans-NN` and refers to them by id.
    Four figures in one document means four colliding sets, and the browser
    resolves every reference to the FIRST match -- so figures 2-4 would
    silently render with figure 1's glyphs."""
    names = [n for n, _, _ in mod.FIGURES]
    svgs = {n: mod.inline_svg(n) for n in names}
    svgs = {n: s for n, s in svgs.items() if s}
    if len(svgs) < 2:
        pytest.skip("figures not rendered; run `make plots`")

    ids = {n: set(re.findall(r'\bid="([^"]+)"', s)) for n, s in svgs.items()}
    for a, b in itertools.combinations(ids, 2):
        assert not (ids[a] & ids[b]), f"{a} and {b} share ids"
    # And every internal reference still resolves inside its own figure.
    for n, s in svgs.items():
        refs = set(re.findall(r'href="#([^"]+)"', s))
        assert refs <= ids[n], f"{n} references ids it does not define"


def test_the_controls_band_reports_a_failure_loudly(mod):
    """A page whose controls failed must not look like one whose controls
    passed -- that is the entire reason the band renders first."""
    bad = {"positive": {"p_pass": 0.10, "ok": False},
           "negative": {"p_pass": 0.90, "null_baseline": 0.5, "ok": False},
           "calibration": {"honest": {"mean": 0.9, "sigmas": 6.0,
                                      "verdict": "fails the dead world"},
                           "artifact": {"mean": 0.9, "sigmas": 6.0,
                                        "verdict": "fails the dead world"},
                           "ok": False},
           "profile": {"name": "p", "effective": "2026-01-01", "account": 1,
                       "target": 1, "trailing_dd": 1, "daily_guard": 1,
                       "min_days": 1, "source": "", "ok": True},
           "all_pass": False}
    page = mod.render({"hypotheses": [], "experiments": [],
                       "manifest_objects": 0, "engine_sha": "x",
                       "pulled_at": "t"}, bad)
    assert "do not trust a result on this page" in page
    assert "FAIL" in page


def test_controls_render_before_findings(mod):
    """F2: philosophy first reads as excuse-making; the control first makes
    the philosophy obviously necessary."""
    good = {"positive": {"p_pass": 1.0, "ok": True},
            "negative": {"p_pass": 0.0, "null_baseline": 0.0, "ok": True},
            "calibration": {"honest": {"mean": 0.07, "sigmas": 0.5,
                                       "verdict": "calibrated"},
                            "artifact": {"mean": 0.70, "sigmas": 5.0,
                                         "verdict": "fails the dead world"},
                            "ok": True},
            "profile": {"name": "p", "effective": "2026-01-01", "account": 1,
                        "target": 1, "trailing_dd": 1, "daily_guard": 1,
                        "min_days": 1, "source": "", "ok": True},
            "all_pass": True}
    page = mod.render({"hypotheses": [], "experiments": [SCORED],
                       "manifest_objects": 0, "engine_sha": "x",
                       "pulled_at": "t"}, good)
    assert page.index('id="controls"') < page.index('id="findings"')
    assert page.index('id="findings"') < page.index('id="register"')


RESOLUTION = {
    "hypothesis_id": "H-BETA", "run_id": "r2", "metric_path": "primary",
    "resolved_at": "2026-08-30T12:00:00+00:00", "outcome": "detectable",
    "effect_size": -0.089, "ci_low": -0.134, "ci_high": -0.043,
    "floor": 0.07, "n": 3442, "n_eff": 1811, "decision": "close the family",
    "supersedes": "", "source_run_sha256": "0" * 64, "engine_sha": "x",
}


def test_a_resolved_hypothesis_reports_its_outcome(mod):
    """Before F5 every hypothesis read `open` forever, because the field was
    written once as null and nothing wrote it back."""
    reg = {"hypotheses": [{"id": "H-BETA", "status": "registered",
                           "mechanism": "m", "alpha_allocated": 0.05}],
           "experiments": [SCORED], "resolutions": [RESOLUTION],
           "manifest_objects": 0, "engine_sha": "x", "pulled_at": "t"}
    page = mod.render(reg)
    assert "close the family" in page          # the decision is shown
    assert "Resolved" in page
    assert "Known gap" not in page             # nothing left unresolved


def test_the_gap_shrinks_to_what_is_actually_unresolved(mod):
    """A resolved hypothesis must leave the gap list, or the page keeps
    reporting a defect that has been fixed -- the same stale-status failure
    the gap notice exists to prevent."""
    reg = {"hypotheses": [
               {"id": "H-BETA", "status": "registered", "mechanism": "m",
                "alpha_allocated": 0.05},
               {"id": "H-GAMMA", "status": "registered", "mechanism": "m",
                "alpha_allocated": 0.05}],
           "experiments": [SCORED, {**SCORED, "hypothesis_id": "H-GAMMA"}],
           "resolutions": [RESOLUTION],
           "manifest_objects": 0, "engine_sha": "x", "pulled_at": "t"}
    page = mod.render(reg)
    listed = re.search(r'<p class="mono">(.*?)</p>', page, re.S).group(1)
    assert "H-GAMMA" in listed
    assert "H-BETA" not in listed


def test_a_documented_resolution_never_shows_numbers_it_does_not_have(mod):
    """The one that matters. A `documented` outcome was written up in prose
    and never computed into the register, so it has no effect size, interval
    or floor -- and a page that rendered it in the same shape as a measured
    one would let a sentence copied out of a writeup pass for a measurement.
    """
    doc = {"hypothesis_id": "H-BETA", "kind": "documented",
           "outcome": "dead - costs ate the signal", "run_id": "",
           "effect_size": None, "ci_low": None, "ci_high": None, "floor": None,
           "decision": "closed", "source_doc": "docs/PROGRAMME-CONCLUSION.md",
           "source_sha256": "a" * 64, "resolved_at": "2026-08-30T00:00:00Z",
           "supersedes": ""}
    reg = {"hypotheses": [{"id": "H-BETA", "status": "registered",
                           "mechanism": "m", "alpha_allocated": 0.05}],
           "experiments": [], "resolutions": [doc],
           "manifest_objects": 0, "engine_sha": "x", "pulled_at": "t"}
    page = mod.render(reg)

    assert "documented" in page
    assert "docs/PROGRAMME-CONCLUSION.md" in page
    assert "never computed into the register" in page
    # No numeric row may appear for it.
    block = page.split('class="resolution')[1].split("</div>")[0]
    for label in (">effect<", ">95% CI<", ">floor<"):
        assert label not in block, f"{label} rendered for a documented outcome"


def test_the_page_says_how_many_rest_on_a_document(mod):
    """19 resolved reads as 19 measured unless the page says otherwise, and
    the weaker kind would borrow the authority of the stronger."""
    res = [{"hypothesis_id": f"H-{i}", "kind": k, "outcome": "o",
            "decision": "d", "run_id": "", "resolved_at": "t",
            "supersedes": ""}
           for i, k in enumerate(["scored", "documented", "documented",
                                  "superseded", "audit"])]
    reg = {"hypotheses": [], "experiments": [], "resolutions": res,
           "manifest_objects": 0, "engine_sha": "x", "pulled_at": "t"}
    page = mod.render(reg)
    assert "How each was resolved" in page
    assert "2 of 5 rest on a document rather than a computation" in page


def test_a_register_with_no_resolutions_key_still_renders(mod, register):
    """The cache predates F5, so `resolutions` can be absent entirely."""
    assert "resolutions" not in register
    mod.render(register)                    # must not raise


def test_offline_without_a_cache_fails_loudly(mod, tmp_path, monkeypatch):
    """Rendering a stale or empty page would be worse than refusing."""
    monkeypatch.setattr(mod, "CACHE", tmp_path / "nope.json")
    with pytest.raises(SystemExit, match="offline"):
        mod.load(offline=True)
