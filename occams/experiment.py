"""The experiment SOP, as a function rather than a document.

On 2026-08-01 the session's most consequential result -- that no placeable
order reproduces the sealed engine's entry -- was recorded WITHOUT its
script, because one of the three variants had been run inline. The
conclusion was in the register; the means of checking it was not. A written
procedure would not have caught that, because the person skipping the step
is the same person who would have been reading the procedure.

So the procedure is enforced here instead:

1. the hypothesis must already be REGISTERED, with a mechanism
2. the analysis must live in a FILE, never inline
3. the script is archived BEFORE it runs
4. stdout is captured and archived
5. metrics are read from the script's own output, not retyped
6. only then is the experiment recorded, referencing both artifacts

Any step failing aborts the whole thing. There is no flag to skip one.

The script must print exactly one line beginning `METRICS:` followed by
JSON. That line -- not a human's reading of the table above it -- becomes
the record, which removes the transcription step entirely.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from occams import archive, audit

ROOT = Path(__file__).resolve().parent.parent
METRICS_PREFIX = "METRICS:"


def _hypothesis(hid: str) -> dict | None:
    s3 = archive._client()
    try:
        body = s3.get_object(Bucket=archive.bucket(),
                             Key=f"hypotheses/{hid}.json")["Body"].read()
        return json.loads(body)
    except Exception:
        return None


def _check_power(hyp: dict, metrics: dict) -> None:
    """E4. If the hypothesis declared what it needs to see, the run must
    actually have supplied it. An underpowered test is REFUSED rather than
    run, because an ambiguous null costs alpha exactly as a real test does
    and then tempts a second look at a bigger sample -- which is optional
    stopping."""
    plan = hyp.get("power_plan")
    if not plan:
        return
    from occams import power
    need = power.required_n(plan)
    raw = metrics.get("n")
    # E4.2: pooling correlated instruments is not free. If the plan declares
    # a cluster structure, the gate judges the INDEPENDENT-equivalent sample.
    got = None if raw is None else power.effective_n(
        raw, cluster_size=plan.get("cluster_size", 1),
        intra_r=plan.get("intra_cluster_r", 0.0))
    if got is None:
        raise ValueError(
            f"{hyp['id']} declared a power plan, so its script must emit an "
            f"'n' in METRICS. Without it the test cannot be shown adequate.")
    if got < need:
        extra = ("" if got == raw else
                 f" (raw n={raw}, discounted for a cluster of "
                 f"{plan.get('cluster_size')} at r="
                 f"{plan.get('intra_cluster_r')})")
        raise ValueError(
            f"UNDERPOWERED, refused: n={got}{extra} but detecting the declared "
            f"effect needs n>={need} at power {plan.get('power', 0.8)}. "
            f"Running it anyway would spend alpha on a result that cannot "
            f"settle the question. Either widen the sample first, or "
            f"re-register with an effect size this sample CAN detect.")


def _hypothesis_exists(hid: str) -> bool:
    s3 = archive._client()
    try:
        s3.head_object(Bucket=archive.bucket(), Key=f"hypotheses/{hid}.json")
        return True
    except Exception:
        return False


def _extract_metrics(stdout: str) -> dict:
    lines = [ln for ln in stdout.splitlines()
             if ln.strip().startswith(METRICS_PREFIX)]
    if not lines:
        raise ValueError(
            f"the script printed no {METRICS_PREFIX} line. Metrics must come "
            f"from the run itself, not from someone reading the table and "
            f"typing numbers into the record.")
    if len(lines) > 1:
        raise ValueError(f"{len(lines)} {METRICS_PREFIX} lines; expected one")
    return json.loads(lines[0].split(METRICS_PREFIX, 1)[1].strip())


def run(*, hypothesis_id: str, script: str | Path, run_id: str,
        config: dict, note: str, controls_passed: bool,
        spend_usd: float = 0.0) -> dict:
    """Execute one experiment under the SOP. Returns the recorded document."""
    script = Path(script)

    # 1. registered first. Running before registering is how a hypothesis
    #    gets quietly reshaped to fit a number it has already seen.
    if not _hypothesis_exists(hypothesis_id):
        raise LookupError(
            f"{hypothesis_id} is not registered. Register it -- with its "
            f"mechanism -- BEFORE running anything against it.")

    # 2/3. the analysis must be a file, and it is archived before it runs.
    if not script.exists():
        raise FileNotFoundError(f"{script} does not exist. Inline analysis "
                                f"cannot be archived, so it cannot be run.")
    # Scoped by run_id so two runs of an EVOLVING script can coexist. The
    # first design keyed on the filename alone, which meant its own advice
    # -- "use a new run_id" -- did not work. Caught by the guard firing on a
    # real run, which is the only way that flaw was ever going to surface.
    script_key = f"experiments/{hypothesis_id}/{run_id}/{script.name}"
    try:
        archive.put(script, script_key, source="repo",
                    note=f"frozen script for {hypothesis_id}")
    except FileExistsError:
        # Already archived. Confirm the file has not drifted since -- a
        # changed script with an unchanged name is a different experiment.
        rows = [r for r in archive.manifest() if r["key"] == script_key]
        if rows and rows[-1]["sha256"] != archive.sha256(script):
            raise ValueError(
                f"{script.name} has CHANGED since it was archived for "
                f"{hypothesis_id}. Archive it under a new name, or use a new "
                f"run_id -- never silently overwrite frozen evidence.")

    # 4. run it and capture everything it said -- including HOW it computed.
    #    The script runs in a subprocess, so the in-process calculation
    #    ledger cannot be read directly; the child writes it on exit to the
    #    path named here. Scripts do not opt in -- importing the engine is
    #    enough (M3).
    calc_tmp = ROOT / f".{run_id}-calcs.json"
    calc_tmp.unlink(missing_ok=True)
    proc = subprocess.run([sys.executable, str(script)], cwd=ROOT,
                          capture_output=True, text=True,
                          env={**os.environ, audit.ENV_PATH: str(calc_tmp)})
    out_key = f"experiments/{hypothesis_id}/{run_id}/output.txt"
    tmp = ROOT / f".{run_id}-output.txt"
    tmp.write_text(proc.stdout + ("\n--- stderr ---\n" + proc.stderr
                                  if proc.stderr else ""))
    try:
        archive.put(tmp, out_key, source="local",
                    note=f"verbatim stdout, {hypothesis_id} {run_id}")
    finally:
        tmp.unlink(missing_ok=True)

    # 4b. M3: which estimator produced each number, at which source hash.
    #     `engine_sha` pins the commit; this pins the calculation.
    calc_key = ""
    if calc_tmp.exists():
        calc_key = f"experiments/{hypothesis_id}/{run_id}/calcs.json"
        try:
            archive.put(calc_tmp, calc_key, source="local",
                        note=f"calculation ledger, {hypothesis_id} {run_id}")
        except FileExistsError:
            pass
        finally:
            calc_tmp.unlink(missing_ok=True)

    if proc.returncode != 0:
        raise RuntimeError(f"script exited {proc.returncode}; output archived "
                           f"at {out_key} so the failure is on the record too")

    # 5. metrics from the run, never retyped.
    metrics = _extract_metrics(proc.stdout)

    # 5b. E4: was this test big enough to answer its own question?
    hyp = _hypothesis(hypothesis_id)
    if hyp:
        _check_power(hyp, metrics)

    # 6. record, referencing both artifacts.
    rec = archive.record_experiment(
        hid=hypothesis_id, run_id=run_id, config=config, metrics=metrics,
        controls_passed=controls_passed, spend_usd=spend_usd,
        note=f"{note}\n\nSCRIPT: {script_key}\nOUTPUT: {out_key}"
             + (f"\nCALCS: {calc_key}" if calc_key else
                "\nCALCS: none — the script called no audited estimator"))
    print(f"recorded {hypothesis_id}/{run_id}")
    print(f"  script {script_key}")
    print(f"  output {out_key}")
    print(f"  calcs  {calc_key or 'none'}")
    return rec


def emit(metrics: dict) -> None:
    """Call this at the END of an experiment script. The line it prints is
    what lands in the register."""
    print(f"{METRICS_PREFIX} {json.dumps(metrics)}")
