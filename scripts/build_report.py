"""F1 — the research console, generated from the register.

    python3 scripts/build_report.py            (or: make report)
    python3 scripts/build_report.py --offline  no network; uses the cache
    python3 scripts/build_report.py --archive  upload the rendered page

ONE static HTML file, stamped with `engine_sha`, archived like everything
else. **Generated, not live** — a page that shows whatever the store says at
the moment you load it is not evidence, because it cannot be cited, diffed,
or shown to disagree with itself later. This writes a dated artifact you can
put beside a claim.

Every number is READ FROM THE REGISTER, never typed here. `make_plots.py`
already works this way and the reason is the same: a figure or a page that
restates a result from memory can drift from the record it claims to show,
and nothing catches it.

The register lives in S3, so the first run needs credentials. It then caches
to `artifacts/register-cache.json`, and `--offline` renders from that — the
same cache-not-evidence rule `archive_pull.py` sets out: deleting the cache
should cost time, never evidence.

F2-F4 extend the page (controls-first layout, CI-vs-floor strips and the
alpha fuel gauge, one drill-down layer). This is the generator and the
provenance stamp they hang off.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from occams import archive  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "artifacts" / "report" / "index.html"
CACHE = ROOT / "artifacts" / "register-cache.json"

# Rendered as "not yet resolved" rather than left blank. A blank cell reads
# as "nothing to report"; these are hypotheses that are registered and still
# open, which is a different and more interesting state.
UNRESOLVED = "registered"


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

    return {"hypotheses": hyps, "experiments": exps,
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
    drop the per-instrument split that several findings turn on."""
    out: list[tuple[str, str]] = []
    if isinstance(metrics, dict):
        for k, v in metrics.items():
            out += metric_rows(v, f"{prefix}{k}." if not prefix
                               else f"{prefix}{k}.")
    else:
        out.append((prefix.rstrip("."), esc(metrics)))
    return out


def render(reg: dict) -> str:
    hyps = reg["hypotheses"]
    exps = reg["experiments"]
    grouped = by_hypothesis(reg)
    resolved = [h for h in hyps if str(h.get("status", "")) != UNRESOLVED]
    spend = sum(float(e.get("spend_usd") or 0.0) for e in exps)
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")

    parts: list[str] = [_HEAD, _header(reg, generated),
                        _summary(hyps, exps, resolved, spend, reg)]

    # Surfaced the first time the register was rendered whole (F1). Left
    # visible rather than smoothed over: a page that quietly showed 20 open
    # questions would read as "this programme answered nothing", which is
    # false, and hiding it would make the report agree with a register that
    # is wrong rather than with the world.
    answered = {e.get("hypothesis_id") for e in exps}
    unwritten = sorted(h.get("id") for h in hyps
                       if str(h.get("status", "")) == UNRESOLVED
                       and h.get("id") in answered)
    if unwritten:
        parts.append(_gap(unwritten))

    parts.append('<section><h2>The register</h2>'
                 '<p class="lede">Every hypothesis, in the state the record '
                 'actually holds it. A hypothesis with no outcome is '
                 '<em>open</em>, not <em>negative</em> &mdash; the two have '
                 'opposite next actions and collapsing them is how dead '
                 'strategies get retested until one passes.</p>')
    for h, runs in grouped:
        parts.append(_hypothesis(h, runs))
    parts.append("</section>")

    parts.append(_footer(reg, generated))
    parts.append("</main></body></html>")
    return "\n".join(parts)


def _header(reg: dict, generated: str) -> str:
    return f"""<body><main>
<header>
  <h1>occams-trader &mdash; research console</h1>
  <p class="lede">Generated from the register at
     <code>{esc(reg.get("pulled_at"))}</code>.
     This page is a dated artifact, not a live view.</p>
  <dl class="stamp">
    <div><dt>engine_sha</dt><dd><code>{esc(reg.get("engine_sha"))}</code></dd></div>
    <div><dt>generated</dt><dd><code>{esc(generated)}</code></dd></div>
    <div><dt>archive objects</dt><dd><code>{reg.get("manifest_objects", 0):,}</code></dd></div>
  </dl>
</header>"""


def _summary(hyps, exps, resolved, spend, reg) -> str:
    a = alpha_spent(hyps)
    return f"""<section class="grid">
  <div class="card"><span class="n">{len(hyps)}</span>
    <span class="k">hypotheses registered</span></div>
  <div class="card"><span class="n">{len(resolved)}</span>
    <span class="k">resolved &middot; {len(hyps) - len(resolved)} still open</span></div>
  <div class="card"><span class="n">{len(exps)}</span>
    <span class="k">archived runs</span></div>
  <div class="card"><span class="n">{a:.2f}</span>
    <span class="k">alpha allocated</span></div>
  <div class="card"><span class="n">${spend:,.2f}</span>
    <span class="k">recorded spend</span></div>
</section>
<p class="note"><strong>Alpha is a depleting budget, not a warning.</strong>
Each registration raises the evidence bar for the next survivor. The figure
above is the sum of what was allocated in advance, which is the only version
of it that means anything &mdash; counted after the fact it is a description
of how much looking got done.</p>"""


def _gap(ids: list[str]) -> str:
    """A known gap in the instrument, stated on the page that revealed it."""
    lst = ", ".join(f"<code>{esc(i)}</code>" for i in ids)
    return f"""<section class="gap">
<h3>Known gap: the register records questions, not answers</h3>
<p>{len(ids)} hypotheses below have archived runs but still carry
<code>status: registered</code> and a null <code>outcome</code>.
<strong>This is a defect in the register, not a finding about the
market.</strong> <code>register_hypothesis</code> writes those fields once
and nothing ever writes them back, so the outcomes live only as prose in
<code>docs/*-WRITEUP.md</code> and the sealed verdicts.</p>
<p>The consequence is specific and it is the reason this is stated here
rather than filed quietly: <strong>the multiplicity ledger cannot be
computed from the register.</strong> Alpha allocated is readable; alpha that
actually bought a resolved answer is not, so the evidence bar for the next
hypothesis has to be reconstructed by hand from documents.</p>
<p class="mono">{lst}</p>
</section>"""


def _hypothesis(h: dict, runs: list[dict]) -> str:
    hid = esc(h.get("id"))
    status = str(h.get("status", "") or "")
    open_ = status == UNRESOLVED
    cls = "open" if open_ else "resolved"
    badge = "open" if open_ else esc(status)

    rows = [
        ("axis", esc(h.get("information_axis"))),
        ("search space", esc(h.get("search_space_size"))),
        ("alpha", esc(h.get("alpha_allocated"))),
        ("outcome", esc(h.get("outcome")) or "&mdash;"),
        ("effect", num(h.get("effect_size"))),
        ("interval", interval(h)),
    ]
    if h.get("supersedes"):
        rows.append(("supersedes", esc(h["supersedes"])))

    meta = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in rows)
    body = [f'<details class="hyp {cls}"><summary>'
            f'<span class="hid">{hid}</span>'
            f'<span class="badge {cls}">{badge}</span>'
            f'<span class="runs">{len(runs)} run{"" if len(runs) == 1 else "s"}</span>'
            f'</summary><dl class="meta">{meta}</dl>']

    if h.get("statement"):
        body.append(f'<h4>Statement</h4><p>{esc(h["statement"])}</p>')
    if h.get("mechanism"):
        # The mechanism is the single best filter against dredging and is
        # worthless if back-filled, so it is shown in full rather than
        # truncated -- a reader has to be able to check it was written first.
        body.append(f'<h4>Mechanism <span class="sub">written before the '
                    f'number existed</span></h4><pre>{esc(h["mechanism"])}</pre>')
    if h.get("power_plan"):
        body.append(f'<h4>Power plan</h4><pre>'
                    f'{esc(json.dumps(h["power_plan"], indent=1))}</pre>')

    for e in runs:
        body.append(_run(e))
    body.append("</details>")
    return "\n".join(body)


def _run(e: dict) -> str:
    ok = bool(e.get("controls_passed"))
    ctl = ('<span class="badge resolved">controls passed</span>' if ok else
           '<span class="badge fail">CONTROLS NOT PASSED</span>')
    mrows = "".join(f"<tr><td>{esc(k)}</td><td class='v'>{v}</td></tr>"
                    for k, v in metric_rows(e.get("metrics", {})))
    cfg = esc(json.dumps(e.get("config", {}), indent=1, sort_keys=True))
    return f"""<div class="run">
  <h4>{esc(e.get("run_id"))} {ctl}</h4>
  <dl class="meta">
    <div><dt>recorded</dt><dd><code>{esc(e.get("recorded_at"))}</code></dd></div>
    <div><dt>engine_sha</dt><dd><code>{esc(e.get("engine_sha"))}</code></dd></div>
    <div><dt>spend</dt><dd>${float(e.get("spend_usd") or 0):,.2f}</dd></div>
  </dl>
  <table class="metrics"><thead><tr><th>metric</th><th>value</th></tr></thead>
  <tbody>{mrows}</tbody></table>
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
      --brass:#96690F;--verdigris:#2F6C63;--rust:#9C4429;}
@media (prefers-color-scheme:dark){:root{--bg:#12191A;--ink:#E6EDEB;
      --sub:#8FA3A5;--line:#26343550;--card:#182223;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
     font:15px/1.6 ui-serif,Georgia,"Times New Roman",serif;}
main{max-width:64rem;margin:0 auto;padding:2.5rem 1.25rem 5rem;}
h1{font-size:1.75rem;margin:0 0 .3rem;letter-spacing:-.01em}
h2{font-size:1.25rem;margin:2.5rem 0 .4rem;padding-bottom:.3rem;
   border-bottom:1px solid var(--line)}
h4{font-size:.95rem;margin:1.1rem 0 .3rem}
h5{font-size:.8rem;margin:.9rem 0 .25rem;color:var(--sub);
   text-transform:uppercase;letter-spacing:.06em}
.lede{color:var(--sub);margin:.2rem 0 1rem}
.sub{color:var(--sub);font-weight:400;font-size:.8rem}
code,pre,.mono,.v{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
pre{background:var(--card);border:1px solid var(--line);border-radius:6px;
    padding:.7rem .85rem;overflow-x:auto;font-size:.78rem;line-height:1.5;
    white-space:pre-wrap;word-break:break-word}
header{border-bottom:2px solid var(--line);padding-bottom:1.2rem}
dl.stamp{display:flex;flex-wrap:wrap;gap:1.5rem;margin:.8rem 0 0}
dl.stamp dt,dl.meta dt{font-size:.7rem;text-transform:uppercase;
   letter-spacing:.07em;color:var(--sub)}
dl.stamp dd,dl.meta dd{margin:.1rem 0 0;font-size:.82rem}
.grid{display:grid;gap:.75rem;margin:1.5rem 0 .5rem;
      grid-template-columns:repeat(auto-fit,minmax(9rem,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;
      padding:.85rem}
.card .n{display:block;font-size:1.6rem;font-weight:600;
         font-family:ui-monospace,monospace;color:var(--brass)}
.card .k{display:block;font-size:.72rem;color:var(--sub);margin-top:.15rem}
.note{font-size:.85rem;color:var(--sub);border-left:3px solid var(--line);
      padding-left:.9rem;margin:1rem 0 0}
details.hyp{background:var(--card);border:1px solid var(--line);
     border-radius:8px;margin:.6rem 0;padding:.5rem .95rem}
details.hyp[open]{padding-bottom:1.1rem}
summary{cursor:pointer;display:flex;align-items:center;gap:.7rem;
        flex-wrap:wrap;padding:.35rem 0;font-size:.9rem}
.hid{font-family:ui-monospace,monospace;font-weight:600}
.runs{color:var(--sub);font-size:.76rem;margin-left:auto}
.badge{font-size:.66rem;text-transform:uppercase;letter-spacing:.06em;
       padding:.14rem .45rem;border-radius:4px;border:1px solid currentColor}
.badge.open{color:var(--brass)}
.badge.resolved{color:var(--verdigris)}
.badge.fail{color:var(--rust);font-weight:700}
dl.meta{display:flex;flex-wrap:wrap;gap:1.1rem;margin:.5rem 0 0}
.run{border-top:1px solid var(--line);margin-top:1.1rem;padding-top:.6rem}
table.metrics{border-collapse:collapse;width:100%;font-size:.78rem;
              margin:.4rem 0;display:block;overflow-x:auto}
table.metrics th{text-align:left;font-size:.68rem;text-transform:uppercase;
   letter-spacing:.06em;color:var(--sub);border-bottom:1px solid var(--line);
   padding:.25rem .5rem .25rem 0}
table.metrics td{padding:.18rem .5rem .18rem 0;
   border-bottom:1px solid var(--line)}
table.metrics td.v{font-weight:600;text-align:right;white-space:nowrap}
.gap{border:1px solid var(--rust);border-radius:8px;padding:.2rem 1rem 1rem;
     margin:1.6rem 0 0;background:var(--card)}
.gap h3{color:var(--rust);font-size:1rem;margin:.9rem 0 .4rem}
.gap p{font-size:.85rem;margin:.5rem 0}
.gap .mono{font-size:.7rem;color:var(--sub);line-height:2}
footer{margin-top:3rem;padding-top:1.2rem;border-top:2px solid var(--line);
       font-size:.85rem;color:var(--sub)}
footer .mono{font-size:.7rem}
</style></head>"""


# ─── entry point ───

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--offline", action="store_true",
                    help="render from artifacts/register-cache.json")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--archive", action="store_true",
                    help="upload the rendered page to the archive")
    args = ap.parse_args()

    reg = load(offline=args.offline)
    page = render(reg)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8")

    n_open = sum(1 for h in reg["hypotheses"]
                 if str(h.get("status", "")) == UNRESOLVED)
    print(f"{shown(args.out)}  {len(page):,} bytes")
    print(f"  {len(reg['hypotheses'])} hypotheses "
          f"({n_open} open) - {len(reg['experiments'])} runs - "
          f"alpha {alpha_spent(reg['hypotheses']):.2f}")
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
