"""F1-F4 — the research console, generated from the register.

    python3 scripts/build_report.py            (or: make report)
    python3 scripts/build_report.py --offline  no network; uses the cache
    python3 scripts/build_report.py --archive  upload the rendered page

ONE static HTML file, stamped with `engine_sha`, archived like everything
else. **Generated, not live** — a page that shows whatever the store says at
the moment you load it is not evidence, because it cannot be cited, diffed,
or shown to disagree with itself later.

Every number is READ FROM THE REGISTER or recomputed by the engine, never
typed here. The controls come from `quickstart.controls()`, the same call
`make quickstart` prints from, so the page and the terminal cannot disagree.

WHAT THE PAGE ARGUES, in the order it argues it (F2). The controls run
first: a reader has no reason to trust a finding until the instrument that
produced it has demonstrated it can find a planted edge and report nothing
on a dead world. Philosophy first reads as excuse-making; the control first
makes the philosophy obviously necessary.

Colour encodes TRUST, not profit (F3). There is no equity curve on this
page and that is deliberate: every equity curve this lab drew came from an
entry later proved unobtainable, and the curve looked fine throughout.

No JavaScript, no external assets, no network at view time. An artifact that
needs a CDN to render has a shelf life; this one has to still open in a
decade.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from occams import archive  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
# In `docs/`, not `artifacts/`, because GitHub Pages serves this repo's site
# from that folder -- so the generated page is reachable at a URL instead of
# only readable as source. The register cache stays in `artifacts/`: it is an
# intermediate, and publishing it would put the whole register on the site
# twice.
OUT = ROOT / "docs" / "report.html"
CACHE = ROOT / "artifacts" / "register-cache.json"
PLOTS = ROOT / "artifacts" / "plots"

UNRESOLVED = "registered"

# The conventional single-test allowance. Not a budget anyone declared -- the
# programme's doctrine is that alpha is "a first-class, decrementing
# resource" and "the evidence bar rises as the register grows"
# (docs/RESEARCH-PROGRAM.md), without a numeric tank. So the gauge shows
# consumption against this reference rather than inventing a total.
ALPHA_REFERENCE = 0.05

FIGURES = [
    ("01-feasibility-frontier",
     "What edge the rules actually require",
     "Win rate against payoff ratio, with the pass gate marked. Asymmetry is "
     "the lever, not hit rate: at 2.0R the rules clear at a 45% win rate; at "
     "1.0R they need 60-65%, which is exactly where most retail strategies "
     "live."),
    ("02-p-pass-shape",
     "Why a rising curve is a warning, not a result",
     "P(pass) against risk per trade. A monotonic rise means variance "
     "harvesting -- bigger bets clearing a fixed target more often. Only an "
     "interior peak is consistent with a real edge."),
    ("03-four-orders",
     "Only the assumption is positive",
     "The same signal priced against every order a human could actually "
     "place. The engine's assumed fill makes money; the limit, the market "
     "and the stop all lose it. The edge was in the gap between where the "
     "simulator booked the trade and where a trade could have happened."),
    ("04-reference-price-decomposition",
     "The number that contained its own answer",
     "total = the distance price had already travelled + what happened next. "
     "An exact identity, so it cannot manufacture a better number. 94.8% of "
     "the headline was the reference price."),
]


# ─── reading the register ───

def pull() -> dict:
    """Fetch every hypothesis and experiment record. ~46 GETs."""
    s3 = archive._client()
    bucket = archive.bucket()

    def get(key: str) -> dict:
        return json.loads(s3.get_object(Bucket=bucket, Key=key)["Body"].read())

    manifest = archive.manifest()
    keys = sorted({r.get("key", "") for r in manifest})

    hyps = [get(k) for k in keys if k.startswith("hypotheses/")
            and k.endswith(".json")]
    # Only the top-level record per run. The archived script and stdout sit
    # one level deeper under the same prefix, and `experiments/campaign/`
    # holds live paper-campaign state rather than run records -- it matched
    # the depth test and rendered as a `None / None` row until excluded by
    # name. Depth alone is not a schema.
    exps = [get(k) for k in keys
            if k.startswith("experiments/") and k.endswith(".json")
            and not k.startswith("experiments/campaign/")
            and k.count("/") == 2]
    exps = [e for e in exps if e.get("hypothesis_id")]

    # F4: the frozen script and its stdout are archived beside every run.
    # Carrying their hashes lets the page show that a result is backed by a
    # specific file without embedding the file.
    prov: dict[str, list[dict]] = {}
    for row in manifest:
        k = row.get("key", "")
        if "/" in k and k.startswith("experiments/"):
            parent = k.rsplit("/", 1)[0]
            if parent.count("/") == 2:
                prov.setdefault(parent, []).append(
                    {"key": k, "sha256": row.get("sha256"),
                     "bytes": row.get("bytes"),
                     "archived_at": row.get("archived_at")})

    return {"hypotheses": hyps, "experiments": exps, "provenance": prov,
            "manifest_objects": len(manifest),
            "engine_sha": archive.engine_sha(),
            "pulled_at": datetime.now(timezone.utc).isoformat(
                timespec="seconds")}


def load(*, offline: bool) -> dict:
    if offline:
        if not CACHE.exists():
            # Not `relative_to(ROOT)`: the cache path is overridable, and an
            # unrelated path made the refusal itself raise ValueError -- so
            # the guard crashed instead of explaining.
            raise SystemExit(
                f"--offline needs a cache and {shown(CACHE)} does not "
                f"exist. Run once with credentials first.")
        return json.loads(CACHE.read_text())
    reg = pull()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(reg, indent=1, sort_keys=True))
    return reg


# ─── shaping ───

def alpha_spent(hyps: list[dict]) -> float:
    return sum(float(h.get("alpha_allocated") or 0.0) for h in hyps)


def by_hypothesis(reg: dict) -> list[tuple[dict, list[dict]]]:
    """Each hypothesis with its runs, newest run first. Sorted by id so the
    page is byte-stable apart from its timestamp — an artifact that reshuffles
    itself between runs cannot be diffed, which defeats archiving it."""
    runs: dict[str, list[dict]] = {}
    for e in reg["experiments"]:
        runs.setdefault(e.get("hypothesis_id", "?"), []).append(e)
    for v in runs.values():
        v.sort(key=lambda e: str(e.get("recorded_at", "")), reverse=True)

    hyps = sorted(reg["hypotheses"], key=lambda h: str(h.get("id", "")))
    seen = {h.get("id") for h in hyps}
    # A run whose hypothesis record is missing is a hole in the register, so
    # it is shown as one rather than dropped silently.
    orphans = [(({"id": hid, "status": "MISSING FROM REGISTER"}), v)
               for hid, v in sorted(runs.items()) if hid not in seen]
    return [(h, runs.get(h.get("id", ""), [])) for h in hyps] + orphans


RESULT_KEYS = {"estimate", "verdict"}


def find_audits(exps: list[dict]) -> list[dict]:
    """Blocks carrying a `verdict` but no `estimate`.

    These are AUDIT verdicts, not scored effects -- an entry-obtainability
    sweep returns "clean", not a correlation with an interval. Keeping them
    out of `find_results` is the point (a free-text verdict has no floor to
    be measured against), but leaving them off the page entirely would hide a
    load-bearing result: the obtainability audit is what cleared two sealed
    verdicts of the defect that voided a third.
    """
    out = []
    for e in exps:
        def walk(node, path):
            if not isinstance(node, dict):
                return
            if "verdict" in node and "estimate" not in node:
                out.append({"verdict": node["verdict"], "n": node.get("n"),
                            "_hid": e.get("hypothesis_id"),
                            "_run": e.get("run_id"), "_path": path})
                return
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)
        walk(e.get("metrics", {}), "")
    out.sort(key=lambda r: (str(r.get("_hid")), str(r.get("_path"))))
    return out


def find_results(exps: list[dict]) -> list[dict]:
    """Every `Result.to_metrics()` block in the archive, with its context.

    These are the findings. They were already in the record -- nested inside
    `metrics` -- and the first version of this page flattened them into
    name/value rows where a verdict rendered identically to a bar count. A
    report that owns a `Result` and displays it as a string is throwing away
    the one object built to say what a number is allowed to mean.
    """
    out = []
    for e in exps:
        def walk(node, path):
            if not isinstance(node, dict):
                return
            if RESULT_KEYS <= node.keys():
                out.append({**node, "_hid": e.get("hypothesis_id"),
                            "_run": e.get("run_id"), "_path": path,
                            "_recorded": e.get("recorded_at")})
                return
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)
        walk(e.get("metrics", {}), "")
    out.sort(key=lambda r: (str(r.get("_hid")), str(r.get("_path"))))
    return out


# ─── rendering ───

def shown(p: Path) -> str:
    """Repo-relative when it can be, absolute otherwise. `relative_to` raises
    on an unrelated path, which twice turned a message into a traceback --
    once in the --offline refusal and once in the success line for --out."""
    try:
        return str(Path(p).relative_to(ROOT))
    except ValueError:
        return str(p)


def esc(x) -> str:
    return html.escape("" if x is None else str(x))


def num(x, places: int = 4) -> str:
    if x is None:
        return "&mdash;"
    try:
        return f"{float(x):+.{places}f}"
    except (TypeError, ValueError):
        return esc(x)


def interval(h: dict) -> str:
    lo, hi = h.get("ci_low"), h.get("ci_high")
    if lo is None or hi is None:
        return "&mdash;"
    return f"[{float(lo):+.4f}, {float(hi):+.4f}]"


def metric_rows(metrics, prefix: str = "") -> list[tuple[str, str]]:
    """Flatten nested metrics to name/value pairs. Records nest per
    instrument, and a report that showed only the top level would silently
    drop the per-instrument split that several findings turn on.

    Sorted, and that is not cosmetic: a fresh pull yields S3's key order
    while the cache is written sorted, so the same register rendered two
    different artifacts depending on where the bytes came from. Anything
    archived has to be reproducible from the cache.
    """
    out: list[tuple[str, str]] = []
    if isinstance(metrics, dict):
        for k, v in sorted(metrics.items(), key=lambda kv: str(kv[0])):
            out += metric_rows(v, f"{prefix}{k}.")
    else:
        out.append((prefix.rstrip("."), esc(metrics)))
    return out


VERDICT_CLASS = {"detectable": "v-detect", "null": "v-null",
                 "inconclusive": "v-incon",
                 "precise but immaterial": "v-immat"}


def ci_strip(r: dict, width: int = 340, height: int = 46) -> str:
    """The one novel element, with a familiar anchor: it reads as an error
    bar (F3). What it adds is the FLOOR -- the shaded band inside which an
    effect cannot be told apart from nothing.

    This is the lab's whole argument in one graphic. A confidence interval
    that excludes zero is the usual bar for a claim; an interval that also
    clears its own detectable floor is a much higher one, and the difference
    between 'inconclusive' and 'null' is visible here and nowhere else.
    """
    ci = r.get("ci") or [r.get("ci_low"), r.get("ci_high")]
    try:
        lo, hi = float(ci[0]), float(ci[1])
        est = float(r["estimate"])
        floor = abs(float(r.get("floor") or 0.0))
    except (TypeError, ValueError, IndexError, KeyError):
        return ""

    lim = max(abs(lo), abs(hi), abs(est), floor) * 1.28 or 1.0
    pad = 10
    inner = width - 2 * pad

    def x(v: float) -> float:
        return pad + inner * (v / lim + 1) / 2

    mid = 24
    cls = VERDICT_CLASS.get(str(r.get("verdict")), "v-null")
    band = (f'<rect class="floorband" x="{x(-floor):.1f}" y="8" '
            f'width="{max(x(floor) - x(-floor), 0.8):.1f}" height="32" '
            f'rx="2"/>') if floor else ""

    return f"""<svg class="strip {cls}" viewBox="0 0 {width} {height}"
 width="{width}" height="{height}" role="img"
 aria-label="effect {est:+.4f}, interval {lo:+.4f} to {hi:+.4f}, floor {floor:.3f}">
{band}
<line class="zero" x1="{x(0):.1f}" y1="6" x2="{x(0):.1f}" y2="42"/>
<line class="bar" x1="{x(lo):.1f}" y1="{mid}" x2="{x(hi):.1f}" y2="{mid}"/>
<line class="cap" x1="{x(lo):.1f}" y1="{mid - 6}" x2="{x(lo):.1f}" y2="{mid + 6}"/>
<line class="cap" x1="{x(hi):.1f}" y1="{mid - 6}" x2="{x(hi):.1f}" y2="{mid + 6}"/>
<circle class="est" cx="{x(est):.1f}" cy="{mid}" r="4"/>
</svg>"""


def alpha_gauge(spent: float, n: int) -> str:
    """Alpha as a gauge, reusing the metaphor `report.py::fuel_gauge` already
    uses for equity -- borrowed rather than invented (F3).

    It shows consumption against the conventional single-test allowance,
    because no numeric budget was ever declared; what the programme declared
    was that the bar RISES as the register grows.
    """
    tanks = spent / ALPHA_REFERENCE if ALPHA_REFERENCE else 0.0
    pct = min(tanks / 10.0, 1.0) * 100
    return f"""<div class="gauge">
  <div class="gauge-head">
    <span class="gauge-n">{spent:.2f}</span>
    <span class="gauge-k">alpha allocated across {n} registrations</span>
  </div>
  <div class="gauge-bar"><div class="gauge-fill" style="width:{pct:.1f}%"></div></div>
  <p class="gauge-note"><strong>{tanks:.1f}&times;</strong> the conventional
  {ALPHA_REFERENCE:.2f} single-test allowance. Alpha is a non-renewable
  resource: a finding at attempt {n} must clear a materially higher bar than
  the same finding at attempt 3. The gauge is here so that bar is visible
  rather than remembered.</p>
</div>"""


def inline_svg(name: str) -> str:
    """Embed a figure, namespacing its ids.

    matplotlib emits glyph defs with names like `DejaVuSans-16` and refers to
    them with `xlink:href="#DejaVuSans-16"`. Four figures in one document
    means four sets of colliding ids, and the browser resolves every
    reference to the FIRST match -- so figures 2-4 would silently render with
    figure 1's glyphs. Prefixing every id and every reference is what stops a
    self-contained page from quietly lying about its own charts.
    """
    path = PLOTS / f"{name}.svg"
    if not path.exists():
        return ""
    svg = path.read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>", "", svg, flags=re.I)
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S)

    # Derived from the name, NOT from hash(): string hashing is salted per
    # process, so the prefixes would change between runs and the artifact
    # would stop being diffable -- the one property archiving it depends on.
    tag = re.sub(r"[^a-z0-9]+", "", name.lower())[:12] or "fig"
    svg = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{tag}-{m.group(1)}"', svg)
    svg = re.sub(r'href="#([^"]+)"',
                 lambda m: f'href="#{tag}-{m.group(1)}"', svg)
    svg = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{tag}-{m.group(1)})", svg)
    # Let CSS size it; matplotlib hardcodes pt dimensions.
    svg = re.sub(r'(<svg\b[^>]*?)\s(width|height)="[^"]*"', r"\1", svg,
                 count=2)
    return svg.strip()


# ─── sections ───

def render(reg: dict, controls: dict | None = None) -> str:
    hyps, exps = reg["hypotheses"], reg["experiments"]
    results = find_results(exps)
    audits = find_audits(exps)
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")

    parts = [_HEAD, _header(reg, generated), _contents(controls, results)]
    if controls:
        parts.append(_controls(controls))
    parts.append(_summary(hyps, exps, results, reg))
    if results or audits:
        parts.append(_findings(results, audits))
    parts.append(_figures())
    parts.append(_register(reg, hyps, exps))
    parts.append(_footer(reg, generated))
    parts.append("</main></body></html>")
    return "\n".join(parts)


def _header(reg: dict, generated: str) -> str:
    return f"""<body><main>
<header>
  <h1>occams-trader <span class="thin">research console</span></h1>
  <p class="lede">A falsifiable record: what was asked, what was measured,
     and what the instrument was doing when it measured it. Rendered from
     the register at <code>{esc(reg.get("pulled_at"))}</code>.
     <strong>A dated artifact, not a live view.</strong></p>
  <dl class="stamp">
    <div><dt>engine_sha</dt><dd><code>{esc(reg.get("engine_sha"))}</code></dd></div>
    <div><dt>generated</dt><dd><code>{esc(generated)}</code></dd></div>
    <div><dt>archive objects</dt><dd><code>{reg.get("manifest_objects", 0):,}</code></dd></div>
  </dl>
</header>"""


def _contents(controls, results) -> str:
    items = []
    if controls:
        items.append('<a href="#controls">Controls</a>')
    items.append('<a href="#summary">Position</a>')
    if results:
        items.append(f'<a href="#findings">Findings ({len(results)})</a>')
    items.append('<a href="#figures">Figures</a>')
    items.append('<a href="#register">The register</a>')
    return f'<nav class="toc">{"".join(items)}</nav>'


def _ctl(ok: bool) -> str:
    return ('<span class="badge pass">pass</span>' if ok else
            '<span class="badge fail">FAIL</span>')


def _controls(c: dict) -> str:
    """F2 — above the findings, deliberately."""
    pos, neg = c["positive"], c["negative"]
    hon, art = c["calibration"]["honest"], c["calibration"]["artifact"]
    p = c["profile"]
    banner = ("all four pass &mdash; the instrument is calibrated"
              if c.get("all_pass") else
              "SOMETHING IS WRONG &mdash; do not trust a result on this page")
    bcls = "ok" if c.get("all_pass") else "bad"

    return f"""<section id="controls">
<h2>1 &middot; Controls</h2>
<p class="lede">Run first, and shown first. Nothing below is worth reading
until the instrument has demonstrated it can find an edge that is there and
report nothing where there is none. These recompute on every build; they
touch no market data, no key and no network.</p>

<div class="ctl-grid">
  <div class="ctl">
    <h3>Positive control {_ctl(pos["ok"])}</h3>
    <p class="big">P(pass) = {pos["p_pass"]:.2f}</p>
    <p>A planted edge, in a synthetic world. <strong>A harness that cannot
    find an edge that is there cannot be trusted to report its absence
    either</strong> &mdash; which is the claim this whole lab rests on.</p>
  </div>
  <div class="ctl">
    <h3>Negative control {_ctl(neg["ok"])}</h3>
    <p class="big">P(pass) = {neg["p_pass"]:.2f}
      <span class="thin">&middot; random-entry null {neg["null_baseline"]:.2f}</span></p>
    <p>A dead world, built with the impulse term set to zero. An earlier
    &ldquo;no-edge&rdquo; world still carried a harvestable kick, so it was
    never a negative control at all &mdash; found in 2026-07, and it
    invalidated a gate.</p>
  </div>
  <div class="ctl wide">
    <h3>Calibration gate {_ctl(c["calibration"]["ok"])}</h3>
    <table class="cal">
      <tr><td>measured from <strong>price</strong></td>
          <td class="v">{hon["mean"]:+.4f}</td>
          <td class="v">{hon["sigmas"]:.1f}&sigma;</td>
          <td><span class="badge pass">{esc(hon["verdict"])}</span></td></tr>
      <tr><td>measured from a <strong>level</strong></td>
          <td class="v">{art["mean"]:+.4f}</td>
          <td class="v">{art["sigmas"]:.1f}&sigma;</td>
          <td><span class="badge fail">{esc(art["verdict"])}</span></td></tr>
    </table>
    <p>Same data, same arithmetic, one different reference price. The dead
    world has <em>no forward drift whatsoever</em>, so the second reading is
    the measurement rather than the market: <strong>a market that froze solid
    at the trigger would still print it.</strong> That defect produced a real
    result here at six times its detectable floor, significant on both
    instruments, both sides, both horizons. No significance test asks the
    question this gate asks.</p>
  </div>
  <div class="ctl wide">
    <h3>Rule profile {_ctl(p["ok"])}</h3>
    <p><code>{esc(p["name"])}</code> &middot; effective
       <code>{esc(p["effective"])}</code> &middot;
       account {p["account"]:,.0f} &middot; target {p["target"]:,.0f} &middot;
       trailing DD {p["trailing_dd"]:,.0f} &middot;
       guard {p["daily_guard"]:,.0f} &middot; min {p["min_days"]} day(s)</p>
    <p>The rules are <em>input</em>, and they are dated. <code>assert_fresh</code>
    refuses a snapshot older than your tolerance rather than warning: a
    provider retired a plan tier while its own pages still advertised it, and
    an undated rule set is a silent expiry. <strong>These ship as a worked
    example of a geometry, not as anyone's current terms.</strong></p>
  </div>
</div>
<p class="banner {bcls}">{banner}</p>
</section>"""


def _summary(hyps, exps, results, reg) -> str:
    spend = sum(float(e.get("spend_usd") or 0.0) for e in exps)
    verdicts = [str(r.get("verdict")) for r in results]
    counts = {v: verdicts.count(v) for v in sorted(set(verdicts))}
    chips = "".join(
        f'<span class="chip {VERDICT_CLASS.get(v, "v-null")}">{esc(v)} '
        f'<b>{n}</b></span>' for v, n in counts.items())
    return f"""<section id="summary">
<h2>2 &middot; Position</h2>
<div class="grid">
  <div class="card"><span class="n">{len(hyps)}</span>
    <span class="k">hypotheses registered</span></div>
  <div class="card"><span class="n">{len(exps)}</span>
    <span class="k">archived runs</span></div>
  <div class="card"><span class="n">{len(results)}</span>
    <span class="k">scored results</span></div>
  <div class="card"><span class="n">${spend:,.2f}</span>
    <span class="k">recorded spend</span></div>
</div>
<div class="chips">{chips}</div>
{alpha_gauge(alpha_spent(hyps), len(hyps))}
</section>"""


def _audits(audits: list[dict]) -> str:
    if not audits:
        return ""
    def row(a: dict) -> str:
        n = a.get("n")
        size = f"{int(n):,}" if isinstance(n, (int, float)) else "&mdash;"
        hid = esc(a.get("_hid"))
        return (f'<tr><td><a class="hid" href="#h-{hid}">{hid}</a></td>'
                f'<td class="thin">{esc(a.get("_run"))}</td>'
                f'<td class="v">{size}</td>'
                f'<td>{esc(a.get("verdict"))}</td></tr>')

    rows = "".join(row(a) for a in audits)
    return f"""<h3 class="sub-h">Audit verdicts</h3>
<p class="lede">Not scored effects &mdash; these return a judgement, not a
number with an interval, so they have no floor to be measured against. They
are here because an audit can clear or void a sealed verdict, which makes
them load-bearing in a way their plainness hides.</p>
<table class="metrics audits"><thead><tr><th>hypothesis</th><th>run</th>
<th>n</th><th>verdict</th></tr></thead><tbody>{rows}</tbody></table>"""


def _findings(results: list[dict], audits: list[dict]) -> str:
    body = "".join(_finding(r) for r in results) + _audits(audits)
    return f"""<section id="findings">
<h2>3 &middot; Findings</h2>
<p class="lede">Every scored result in the archive, shown against
<em>its own detectable floor</em>. The shaded band is the region in which an
effect cannot be told apart from nothing; the bar is the 95% interval and the
dot is the estimate. <strong>&ldquo;Not significant&rdquo; is two different
findings</strong> &mdash; an interval that crosses zero but clears the floor
is <em>inconclusive</em> and means get more data, while one inside the floor
is <em>null</em> and means the question is answered.</p>
<div class="legend"><span class="sw floorband"></span> cannot be told apart
from nothing <span class="sw zero"></span> zero</div>
{body}
</section>"""


def _finding(r: dict) -> str:
    v = str(r.get("verdict"))
    cls = VERDICT_CLASS.get(v, "v-null")
    unit = f" {esc(r['unit'])}" if r.get("unit") else ""
    fm = r.get("floor_multiples")
    fmt = (f'<span class="fm">{float(fm):+.2f}&times; floor</span>'
           if isinstance(fm, (int, float)) else "")
    n = r.get("n")
    neff = r.get("n_eff")
    size = f"{int(n):,}" if isinstance(n, (int, float)) else "&mdash;"
    if isinstance(neff, (int, float)) and isinstance(n, (int, float)) \
            and neff != n:
        size += (f' <span class="thin">&rarr; {int(neff):,} '
                 f'independent-equivalent</span>')
    ci = r.get("ci") or [r.get("ci_low"), r.get("ci_high")]
    try:
        cis = f"[{float(ci[0]):+.4f}, {float(ci[1]):+.4f}]"
    except (TypeError, ValueError, IndexError):
        cis = "&mdash;"

    # F4 is a verb: "click a result, get the register entry". The anchor sits
    # on a span INSIDE the <details>, not on the <details> itself, because
    # browsers auto-expand a collapsed <details> only when the fragment
    # target is within it -- targeting the element itself just scrolls to
    # something still shut.
    return f"""<article class="finding {cls}">
  <div class="f-head">
    <div>
      <a class="hid" href="#h-{esc(r.get("_hid"))}">{esc(r.get("_hid"))}</a>
      <span class="thin">&middot; {esc(r.get("_run"))}</span>
      <h3>{esc(r.get("name") or r.get("_path"))}</h3>
    </div>
    <span class="badge {cls}">{esc(v)}</span>
  </div>
  <div class="f-body">
    {ci_strip(r)}
    <dl class="meta">
      <div><dt>estimate</dt><dd class="v">{num(r.get("estimate"), 5)}{unit}</dd></div>
      <div><dt>95% CI</dt><dd class="v">{cis}</dd></div>
      <div><dt>floor</dt><dd class="v">{esc(r.get("floor"))} {fmt}</dd></div>
      <div><dt>n</dt><dd class="v">{size}</dd></div>
    </dl>
  </div>
  {f'<p class="f-note">{esc(r["note"])}</p>' if r.get("note") else ""}
</article>"""


def _figures() -> str:
    out = []
    for name, title, caption in FIGURES:
        svg = inline_svg(name)
        if not svg:
            continue
        out.append(f'<figure><h3>{esc(title)}</h3>{svg}'
                   f'<figcaption>{esc(caption)}</figcaption></figure>')
    if not out:
        return ""
    return f"""<section id="figures">
<h2>4 &middot; Figures</h2>
<p class="lede">Rendered by <code>make plots</code> from the same register.
Embedded rather than linked, so the page stays one file.</p>
{"".join(out)}
</section>"""


def _register(reg, hyps, exps) -> str:
    answered = {e.get("hypothesis_id") for e in exps}
    unwritten = sorted(h.get("id") for h in hyps
                       if str(h.get("status", "")) == UNRESOLVED
                       and h.get("id") in answered)
    gap = _gap(unwritten) if unwritten else ""
    rows = "".join(_hypothesis(h, runs, reg.get("provenance", {}))
                   for h, runs in by_hypothesis(reg))
    return f"""<section id="register">
<h2>5 &middot; The register</h2>
<p class="lede">Every hypothesis, in the state the record actually holds it,
with its mechanism written before the number existed.</p>
{gap}
{rows}
</section>"""


def _gap(ids: list[str]) -> str:
    """A known gap in the instrument, stated on the page that revealed it."""
    lst = ", ".join(f"<code>{esc(i)}</code>" for i in ids)
    return f"""<div class="gap">
<h3>Known gap: the register records questions, not answers</h3>
<p>{len(ids)} hypotheses below have archived runs but still carry
<code>status: registered</code> and a null <code>outcome</code>.
<strong>This is a defect in the register, not a finding about the
market.</strong> <code>register_hypothesis</code> writes those fields once
and nothing ever writes them back, so outcomes live in the run metrics above
and as prose in <code>docs/</code> &mdash; but not in the field built for
them.</p>
<p>The consequence is specific, and it is why this is stated rather than
filed quietly: <strong>the multiplicity ledger cannot be computed from the
register.</strong> Alpha allocated is readable; alpha that actually bought a
resolved answer is not, so the rising evidence bar has to be reconstructed by
hand from documents.</p>
<p class="mono">{lst}</p>
</div>"""


def _hypothesis(h: dict, runs: list[dict], prov: dict) -> str:
    hid = esc(h.get("id"))
    status = str(h.get("status", "") or "")
    open_ = status == UNRESOLVED
    cls = "open" if open_ else "resolved"
    badge = "open" if open_ else esc(status)

    rows = [("axis", esc(h.get("information_axis"))),
            ("search space", esc(h.get("search_space_size"))),
            ("alpha", esc(h.get("alpha_allocated"))),
            ("outcome", esc(h.get("outcome")) or "&mdash;"),
            ("effect", num(h.get("effect_size"))),
            ("interval", interval(h))]
    if h.get("supersedes"):
        rows.append(("supersedes", esc(h["supersedes"])))
    meta = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in rows)

    body = [f'<details class="hyp {cls}"><summary>'
            f'<span class="hid" id="h-{hid}">{hid}</span>'
            f'<span class="badge {cls}">{badge}</span>'
            f'<span class="runs">{len(runs)} run'
            f'{"" if len(runs) == 1 else "s"}</span>'
            f'</summary><dl class="meta">{meta}</dl>']

    if h.get("statement"):
        body.append(f'<h4>Statement</h4><p>{esc(h["statement"])}</p>')
    if h.get("mechanism"):
        # Shown in full rather than truncated: the mechanism is the single
        # best filter against dredging and is worthless if back-filled, so a
        # reader has to be able to check it was written first.
        body.append(f'<h4>Mechanism <span class="thin">written before the '
                    f'number existed</span></h4>'
                    f'<pre>{esc(h["mechanism"])}</pre>')
    if h.get("power_plan"):
        # sort_keys, like the config dump below: without it the page differs
        # between a fresh pull (S3's key order) and a cache round-trip (the
        # cache is written sorted) -- so the same register rendered two
        # different artifacts depending on where the bytes came from.
        body.append(f'<h4>Power plan</h4><pre>'
                    f'{esc(json.dumps(h["power_plan"], indent=1, sort_keys=True))}'
                    f'</pre>')
    for e in runs:
        body.append(_run(e, prov))
    body.append("</details>")
    return "\n".join(body)


def _run(e: dict, prov: dict) -> str:
    ok = bool(e.get("controls_passed"))
    ctl = ('<span class="badge pass">controls passed</span>' if ok else
           '<span class="badge fail">CONTROLS NOT PASSED</span>')
    mrows = "".join(f"<tr><td>{esc(k)}</td><td class='v'>{v}</td></tr>"
                    for k, v in metric_rows(e.get("metrics", {})))
    cfg = esc(json.dumps(e.get("config", {}), indent=1, sort_keys=True))

    key = f"experiments/{e.get('hypothesis_id')}/{e.get('run_id')}"
    files = sorted(prov.get(key, []), key=lambda r: str(r.get("key")))
    frows = "".join(
        f"<tr><td><code>{esc(Path(str(f['key'])).name)}</code></td>"
        f"<td class='v'>{(f.get('bytes') or 0):,} B</td>"
        f"<td class='sha'><code>{esc(str(f.get('sha256'))[:16])}&hellip;</code></td></tr>"
        for f in files)
    prov_block = f"""<h5>Provenance <span class="thin">the frozen script and
    its output, archived before the run</span></h5>
    <table class="metrics"><tbody>{frows}</tbody></table>""" if frows else ""

    return f"""<div class="run">
  <h4>{esc(e.get("run_id"))} {ctl}</h4>
  <dl class="meta">
    <div><dt>recorded</dt><dd><code>{esc(e.get("recorded_at"))}</code></dd></div>
    <div><dt>engine_sha</dt><dd><code>{esc(e.get("engine_sha"))}</code></dd></div>
    <div><dt>spend</dt><dd>${float(e.get("spend_usd") or 0):,.2f}</dd></div>
  </dl>
  <table class="metrics"><thead><tr><th>metric</th><th>value</th></tr></thead>
  <tbody>{mrows}</tbody></table>
  {prov_block}
  <h5>Config</h5><pre>{cfg}</pre>
  <h5>Note</h5><pre>{esc(e.get("note"))}</pre>
</div>"""


def _footer(reg: dict, generated: str) -> str:
    return f"""<footer>
<p><strong>Provenance.</strong> Rendered from
{len(reg["hypotheses"])} hypothesis records and
{len(reg["experiments"])} run records held in the append-only archive
({reg.get("manifest_objects", 0):,} objects). Corrections append with a
<code>supersedes</code> pointer; nothing is edited in place.</p>
<p><strong>What this page is not.</strong> It is not a trading dashboard and
carries no equity curve. Every equity curve this lab drew came from an entry
later proved unobtainable, and the curve looked fine throughout &mdash; so
colour here encodes trust, not profit.</p>
<p class="mono">engine_sha {esc(reg.get("engine_sha"))} &middot;
generated {esc(generated)}</p>
</footer>"""


_HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>occams-trader research console</title>
<style>
:root{--bg:#FBFAF7;--ink:#16211F;--sub:#6D7F82;--line:#D2DAD8;--card:#fff;
      --brass:#96690F;--verdigris:#2F6C63;--rust:#9C4429;--slate:#6D7F82;
      --band:#96690F1F;--shadow:0 1px 2px #16211F0F;}
@media (prefers-color-scheme:dark){:root{--bg:#12191A;--ink:#E6EDEB;
      --sub:#8FA3A5;--line:#2A3839;--card:#182223;--brass:#C79233;
      --verdigris:#4E9C90;--rust:#C9714B;--slate:#8FA3A5;--band:#C7923326;
      --shadow:none;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
     font:15.5px/1.65 ui-serif,Georgia,"Times New Roman",serif;}
main{max-width:66rem;margin:0 auto;padding:2.5rem 1.25rem 5rem;}
h1{font-size:1.9rem;margin:0 0 .35rem;letter-spacing:-.015em}
h1 .thin{font-weight:400;color:var(--sub)}
h2{font-size:1.3rem;margin:3rem 0 .5rem;padding-bottom:.35rem;
   border-bottom:1px solid var(--line);scroll-margin-top:1rem}
h3{font-size:1rem;margin:0 0 .4rem}
h4{font-size:.95rem;margin:1.1rem 0 .3rem}
h5{font-size:.76rem;margin:1rem 0 .25rem;color:var(--sub);
   text-transform:uppercase;letter-spacing:.07em;font-weight:600}
p{margin:.55rem 0}
.lede{color:var(--sub);margin:.25rem 0 1rem;max-width:46rem}
.thin{color:var(--sub);font-weight:400;font-size:.86em}
code,pre,.mono,.v,.big{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
pre{background:var(--bg);border:1px solid var(--line);border-radius:6px;
    padding:.7rem .85rem;overflow-x:auto;font-size:.76rem;line-height:1.55;
    white-space:pre-wrap;word-break:break-word;margin:.3rem 0}
header{border-bottom:2px solid var(--line);padding-bottom:1.3rem}
dl.stamp{display:flex;flex-wrap:wrap;gap:1.6rem;margin:1rem 0 0}
dl.stamp dt,dl.meta dt{font-size:.68rem;text-transform:uppercase;
   letter-spacing:.08em;color:var(--sub);font-weight:600}
dl.stamp dd,dl.meta dd{margin:.12rem 0 0;font-size:.82rem}
nav.toc{display:flex;flex-wrap:wrap;gap:.4rem;margin:1.2rem 0 0;
   position:sticky;top:0;background:var(--bg);padding:.6rem 0;z-index:5;
   border-bottom:1px solid var(--line)}
nav.toc a{font-size:.78rem;text-decoration:none;color:var(--sub);
   border:1px solid var(--line);border-radius:999px;padding:.2rem .7rem}
nav.toc a:hover{color:var(--ink);border-color:var(--sub)}

/* controls */
.ctl-grid{display:grid;gap:.8rem;grid-template-columns:repeat(2,1fr)}
.ctl{background:var(--card);border:1px solid var(--line);border-radius:10px;
     padding:1rem 1.1rem;box-shadow:var(--shadow)}
.ctl.wide{grid-column:1/-1}
.ctl p{font-size:.85rem}
.big{font-size:1.35rem;font-weight:600;color:var(--brass);margin:.2rem 0 .5rem}
table.cal{border-collapse:collapse;width:100%;margin:.3rem 0 .6rem;
   font-size:.85rem}
table.cal td{padding:.3rem .6rem .3rem 0;border-bottom:1px solid var(--line)}
table.cal td.v{font-family:ui-monospace,monospace;text-align:right;
   white-space:nowrap;font-weight:600}
.banner{margin:1rem 0 0;padding:.6rem .9rem;border-radius:8px;
   font-size:.85rem;font-weight:600;letter-spacing:.01em}
.banner.ok{background:#2F6C6314;color:var(--verdigris);
   border:1px solid var(--verdigris)}
.banner.bad{background:#9C442914;color:var(--rust);
   border:1px solid var(--rust)}

/* position */
.grid{display:grid;gap:.75rem;margin:1.2rem 0 .8rem;
      grid-template-columns:repeat(auto-fit,minmax(9rem,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
      padding:.9rem;box-shadow:var(--shadow)}
.card .n{display:block;font-size:1.65rem;font-weight:600;
         font-family:ui-monospace,monospace;color:var(--brass);
         letter-spacing:-.02em}
.card .k{display:block;font-size:.71rem;color:var(--sub);margin-top:.2rem}
.chips{display:flex;flex-wrap:wrap;gap:.4rem;margin:.6rem 0 1.2rem}
.chip{font-size:.75rem;padding:.22rem .6rem;border-radius:999px;
   border:1px solid currentColor}
.chip b{font-family:ui-monospace,monospace}
.gauge{background:var(--card);border:1px solid var(--line);border-radius:10px;
   padding:1rem 1.1rem;box-shadow:var(--shadow)}
.gauge-head{display:flex;align-items:baseline;gap:.6rem}
.gauge-n{font-family:ui-monospace,monospace;font-size:1.5rem;font-weight:600;
   color:var(--brass)}
.gauge-k{font-size:.8rem;color:var(--sub)}
.gauge-bar{height:12px;background:var(--bg);border:1px solid var(--line);
   border-radius:999px;overflow:hidden;margin:.6rem 0 .5rem}
.gauge-fill{height:100%;background:var(--brass)}
.gauge-note{font-size:.82rem;color:var(--sub);margin:0}

/* findings */
.legend{display:flex;align-items:center;gap:.5rem;font-size:.74rem;
   color:var(--sub);margin:.2rem 0 1rem}
.sw{display:inline-block;width:1.5rem;height:.7rem;border-radius:2px;
   vertical-align:middle}
.sw.floorband{background:var(--band);border:1px solid var(--brass)}
.sw.zero{width:0;border-left:1.5px dashed var(--sub);height:.9rem}
.finding{background:var(--card);border:1px solid var(--line);
   border-left:3px solid var(--slate);border-radius:10px;
   padding:.9rem 1.1rem;margin:.6rem 0;box-shadow:var(--shadow)}
.finding.v-detect{border-left-color:var(--verdigris)}
.finding.v-incon{border-left-color:var(--rust)}
.finding.v-null,.finding.v-immat{border-left-color:var(--slate)}
.f-head{display:flex;justify-content:space-between;align-items:flex-start;
   gap:1rem}
.f-head h3{margin:.15rem 0 0;font-size:.98rem;font-weight:600}
.f-body{display:flex;flex-wrap:wrap;gap:1.4rem;align-items:center;
   margin:.7rem 0 0}
.f-note{font-size:.82rem;color:var(--sub);margin:.7rem 0 0;
   border-left:2px solid var(--line);padding-left:.7rem}
.fm{font-size:.72rem;color:var(--sub)}
svg.strip{flex:0 0 auto;max-width:100%;height:auto;overflow:visible}
svg.strip .floorband{fill:var(--band);stroke:var(--brass);stroke-width:.6;
   stroke-dasharray:2 2}
svg.strip .zero{stroke:var(--sub);stroke-width:1.2;stroke-dasharray:3 3}
svg.strip .bar,svg.strip .cap{stroke:var(--slate);stroke-width:2.2}
svg.strip .est{fill:var(--slate)}
svg.strip.v-detect .bar,svg.strip.v-detect .cap{stroke:var(--verdigris)}
svg.strip.v-detect .est{fill:var(--verdigris)}
svg.strip.v-incon .bar,svg.strip.v-incon .cap{stroke:var(--rust)}
svg.strip.v-incon .est{fill:var(--rust)}

/* figures */
figure{margin:1.6rem 0;background:var(--card);border:1px solid var(--line);
   border-radius:10px;padding:1rem 1.1rem;box-shadow:var(--shadow)}
figure svg{width:100%;height:auto;display:block;margin:.5rem 0}
figcaption{font-size:.82rem;color:var(--sub);border-top:1px solid var(--line);
   padding-top:.6rem;margin-top:.4rem}

/* register */
.gap{border:1px solid var(--rust);border-radius:10px;
   padding:.2rem 1.1rem 1rem;margin:1rem 0 1.4rem;background:var(--card)}
.gap h3{color:var(--rust);font-size:1rem;margin:1rem 0 .4rem}
.gap p{font-size:.85rem}
.gap .mono{font-size:.7rem;color:var(--sub);line-height:2}
details.hyp{background:var(--card);border:1px solid var(--line);
   border-radius:10px;margin:.5rem 0;padding:.5rem 1rem;
   box-shadow:var(--shadow);scroll-margin-top:4rem}
details.hyp[open]{padding-bottom:1.1rem}
summary{cursor:pointer;display:flex;align-items:center;gap:.7rem;
   flex-wrap:wrap;padding:.4rem 0;font-size:.92rem}
.hid{font-family:ui-monospace,monospace;font-weight:600;font-size:.86rem}
a.hid{color:inherit;text-decoration:underline;text-decoration-style:dotted;
   text-underline-offset:3px;cursor:pointer}
a.hid:hover{color:var(--brass)}
/* The landed-on entry, for when the browser scrolls to a <details> it did
   not auto-expand -- otherwise the jump looks like nothing happened. */
.hid:target{background:var(--band);outline:2px solid var(--brass);
   outline-offset:2px;border-radius:3px}
.runs{color:var(--sub);font-size:.75rem;margin-left:auto}
.badge{font-size:.65rem;text-transform:uppercase;letter-spacing:.07em;
   padding:.16rem .5rem;border-radius:4px;border:1px solid currentColor;
   font-family:ui-monospace,monospace;white-space:nowrap}
.badge.open,.badge.v-incon{color:var(--brass)}
.badge.pass,.badge.resolved,.badge.v-detect{color:var(--verdigris)}
.badge.fail{color:var(--rust);font-weight:700}
.badge.v-null,.badge.v-immat{color:var(--slate)}
dl.meta{display:flex;flex-wrap:wrap;gap:1.2rem;margin:.5rem 0 0}
dl.meta dd.v{font-family:ui-monospace,monospace;font-weight:600}
.run{border-top:1px solid var(--line);margin-top:1.1rem;padding-top:.7rem}
table.metrics{border-collapse:collapse;width:100%;font-size:.76rem;
   margin:.4rem 0;display:block;overflow-x:auto}
table.metrics th{text-align:left;font-size:.66rem;text-transform:uppercase;
   letter-spacing:.07em;color:var(--sub);border-bottom:1px solid var(--line);
   padding:.25rem .5rem .25rem 0}
table.metrics td{padding:.2rem .5rem .2rem 0;
   border-bottom:1px solid var(--line);vertical-align:top}
table.metrics td.v{font-weight:600;text-align:right;white-space:nowrap;
   font-family:ui-monospace,monospace}
table.metrics td.sha{color:var(--sub)}
footer{margin-top:3.5rem;padding-top:1.3rem;border-top:2px solid var(--line);
   font-size:.85rem;color:var(--sub)}
footer .mono{font-size:.7rem}
@media (max-width:44rem){.ctl-grid{grid-template-columns:1fr}
  .f-head{flex-direction:column;gap:.4rem}}
</style></head>"""


# ─── entry point ───

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--offline", action="store_true",
                    help="render from artifacts/register-cache.json")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--archive", action="store_true",
                    help="upload the rendered page to the archive")
    ap.add_argument("--no-controls", action="store_true",
                    help="skip the control run (~2s)")
    args = ap.parse_args()

    reg = load(offline=args.offline)

    controls = None
    if not args.no_controls:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_quickstart", ROOT / "scripts" / "quickstart.py")
        qs = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = qs
        spec.loader.exec_module(qs)
        controls = qs.controls()

    page = render(reg, controls)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8")

    results = find_results(reg["experiments"])
    n_open = sum(1 for h in reg["hypotheses"]
                 if str(h.get("status", "")) == UNRESOLVED)
    print(f"{shown(args.out)}  {len(page):,} bytes")
    print(f"  {len(reg['hypotheses'])} hypotheses ({n_open} open) - "
          f"{len(reg['experiments'])} runs - {len(results)} scored results - "
          f"alpha {alpha_spent(reg['hypotheses']):.2f}")
    if controls:
        print(f"  controls: "
              f"{'ALL FOUR PASS' if controls['all_pass'] else 'FAILED'}")
    print(f"  engine_sha {reg.get('engine_sha')}")

    if args.archive:
        sha = reg.get("engine_sha", "unknown")
        key = f"reports/{datetime.now(timezone.utc):%Y-%m-%d}-{sha[:12]}.html"
        archive.put(args.out, key, source="report",
                    note="research console, generated from the register")
        print(f"  archived -> {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
