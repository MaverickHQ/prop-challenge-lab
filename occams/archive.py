"""Track D — the durable research archive: put, get, and the register.

A result you cannot reproduce in three years is not evidence. Everything
here exists to make that sentence true.

Four rules, all enforced rather than documented:

- **Nothing is uploaded without passing the privacy and charset scans.**
  Durable storage gets the same guard the Lambda artifact gets. Refuses,
  never warns, no override flag.
- **Nothing is uploaded without provenance**: sha256, source, cost, and the
  git commit that produced it. Without the commit pinned you cannot later
  tell which engine produced a number, which is the X1 lesson.
- **`raw/` and the register are write-once.** Enforced by bucket policy;
  this module refuses to overwrite them anyway, so the failure is a clear
  message rather than a 403.
- **A download that does not verify its hash is not a restore.**
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from occams.charset import check_text
from occams.privacy import load_terms, scan_files

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = "provenance/manifest.jsonl"

# The bucket and the AWS profile are DERIVED, never hardcoded.
#
# `aws/research-template.yaml` names the bucket
# `occams-research-${AWS::AccountId}`, so it belongs to whoever deployed it.
# This module used to hardcode one account's name, which meant a reader
# could deploy the infrastructure correctly and still have the code point at
# somebody else's bucket -- and it published an account id in the process.
# The profile name was hardcoded too, and a new user has no profile called
# "occams".
#
# Both now follow the same rule: an explicit environment variable wins,
# otherwise derive from whatever credentials are actually in use.
BUCKET_ENV = "OCCAMS_RESEARCH_BUCKET"
PROFILE_ENV = "OCCAMS_AWS_PROFILE"
BUCKET_PREFIX = "occams-research"

_bucket_cache: str | None = None

IMMUTABLE = ("raw/", "hypotheses/", "experiments/", "provenance/",
             "resolutions/")
# Vendor bars are numeric and enormous; scanning them for English terms is
# meaningless and slow. They are still hashed, still logged, still private.
SCAN_SUFFIXES = {".py", ".md", ".json", ".jsonl", ".yaml", ".yml", ".toml",
                 ".txt", ".pine", ".sh"}


def _session():
    """A boto3 session. Honours OCCAMS_AWS_PROFILE, otherwise falls back to
    the default credential chain -- which is what a new user will have."""
    import boto3
    profile = os.environ.get(PROFILE_ENV)
    return boto3.Session(profile_name=profile) if profile else boto3.Session()


def bucket() -> str:
    """The research bucket name, derived from the account actually in use.

    Cached: the STS call happens at most once per process, so importing this
    module costs nothing and a Lambda cold start is unaffected.
    """
    global _bucket_cache
    if _bucket_cache is not None:
        return _bucket_cache
    override = os.environ.get(BUCKET_ENV)
    if override:
        _bucket_cache = override
        return _bucket_cache
    account = _session().client("sts").get_caller_identity()["Account"]
    _bucket_cache = f"{BUCKET_PREFIX}-{account}"
    return _bucket_cache


def _reset_bucket_cache() -> None:
    """Tests only."""
    global _bucket_cache
    _bucket_cache = None


def _client():
    return _session().client("s3")


def engine_sha() -> str:
    """The commit that produced whatever is being archived."""
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip()
        return out.stdout.strip() + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def guard(path: Path) -> None:
    """Refuse anything carrying a forbidden term or a stray script. Raises
    rather than returning a flag, so a caller cannot ignore it."""
    if path.suffix not in SCAN_SUFFIXES:
        return
    hits = scan_files([path], load_terms(ROOT / ".privacy-terms"))
    if hits:
        raise ValueError(f"REFUSED: {path.name} contains a forbidden term. "
                         f"Durable storage is the last place it should reach.")
    bad = check_text(path.read_text(encoding="utf-8", errors="ignore"),
                     ascii_only=path.suffix == ".pine")
    if bad:
        raise ValueError(f"REFUSED: {path.name} line {bad[0][0]} — {bad[0][2]}")


def put(path: Path, key: str, *, source: str = "local",
        cost_usd: float = 0.0, note: str = "") -> dict:
    """Scan, hash, upload, then append provenance. In that order: a manifest
    row for an object that failed to upload would be a lie."""
    path = Path(path)
    guard(path)
    digest = sha256(path)
    s3 = _client()

    if key.startswith(IMMUTABLE):
        try:
            s3.head_object(Bucket=bucket(), Key=key)
            raise FileExistsError(
                f"REFUSED: {key} already exists under a write-once prefix. "
                f"Corrections append a new record; they never overwrite.")
        except s3.exceptions.ClientError as e:
            if e.response["Error"]["Code"] not in ("404", "NoSuchKey"):
                raise

    s3.upload_file(str(path), bucket(), key)
    row = {"key": key, "sha256": digest, "bytes": path.stat().st_size,
           "source": source, "cost_usd": cost_usd, "note": note,
           "engine_sha": engine_sha(),
           "archived_at": datetime.now(timezone.utc).isoformat(
               timespec="seconds")}
    _append_manifest(s3, row)
    return row


def _append_manifest(s3, row: dict) -> None:
    try:
        prev = s3.get_object(Bucket=bucket(), Key=MANIFEST)["Body"].read().decode()
    except Exception:
        prev = ""
    s3.put_object(Bucket=bucket(), Key=MANIFEST,
                  Body=(prev + json.dumps(row) + "\n").encode(),
                  ContentType="application/x-ndjson")


def manifest() -> list[dict]:
    s3 = _client()
    try:
        body = s3.get_object(Bucket=bucket(), Key=MANIFEST)["Body"].read().decode()
    except Exception:
        return []
    return [json.loads(x) for x in body.splitlines() if x.strip()]


def get(key: str, dest: Path) -> dict:
    """Fetch and VERIFY. A download whose hash does not match the manifest
    is not a restore — it is a silent corruption, so this raises."""
    dest = Path(dest)
    _client().download_file(bucket(), key, str(dest))
    rows = [r for r in manifest() if r["key"] == key]
    if not rows:
        raise LookupError(f"{key} has no provenance row — cannot verify it")
    want = rows[-1]["sha256"]
    got = sha256(dest)
    if got != want:
        raise ValueError(f"HASH MISMATCH for {key}\n  manifest {want}\n"
                         f"  fetched  {got}\nThe archived copy is not what "
                         f"the manifest says it is.")
    return {**rows[-1], "verified": True, "path": str(dest)}


# ─── the hypothesis register (R0.2) ───

def register_hypothesis(*, hid: str, statement: str, mechanism: str,
                        information_axis: str, search_space_size: int,
                        alpha_allocated: float, supersedes: str = "",
                        note: str = "", power_plan: dict | None = None
                        ) -> dict:
    """Registered BEFORE evaluation. `mechanism` is why it should work,
    written before the number is known — the single best filter against
    dredging, and worthless if it can be back-filled."""
    if not mechanism.strip():
        raise ValueError("a hypothesis without a stated mechanism is "
                         "rejected unrun (RESEARCH-PROGRAM §5)")
    rec = {"id": hid, "stated_at": datetime.now(timezone.utc).isoformat(
               timespec="seconds"),
           "statement": statement, "mechanism": mechanism,
           "information_axis": information_axis,
           "search_space_size": search_space_size,
           "alpha_allocated": alpha_allocated,
           "status": "registered", "outcome": None,
           "effect_size": None, "ci_low": None, "ci_high": None,
           "decision": None, "supersedes": supersedes, "note": note,
           # E4: declare the smallest effect worth acting on, and the run is
           # REFUSED if the sample cannot detect it.
           "power_plan": power_plan,
           "engine_sha": engine_sha()}
    _put_json(f"hypotheses/{hid}.json", rec)
    return rec


def resolve_hypothesis(*, hid: str, run_id: str, decision: str,
                       metric_path: str = "", note: str = "",
                       supersedes: str = "") -> dict:
    """Record what a hypothesis turned out to be. F5.

    The register was write-once from the start, so `hypotheses/{hid}.json`
    can never be edited -- `_put_json` refuses. That is the right constraint
    and it decides the design: **a resolution APPENDS**, it does not fill in
    the original's blanks. What it appends is a separate immutable record
    pointing at the hypothesis and at the run that answered it.

    **The numbers are READ FROM THE ARCHIVED RUN, never passed in.** Letting
    a caller supply the effect size would recreate the exact defect the
    `METRICS:` line exists to prevent: two independent renderings of one
    result, free to disagree, with nothing checking. What the caller
    supplies is the `decision` -- what the programme does about it -- which
    is a judgement and cannot be read from anywhere.

    Resolving a hypothesis a second time from a different run is allowed,
    because a later run legitimately supersedes an earlier one. It is not
    allowed SILENTLY: `supersedes` must name the prior resolution. Running
    again until the answer is agreeable is optional stopping, and the
    register's job is to make it visible rather than to prevent it.
    """
    if not decision.strip():
        raise ValueError(
            "a resolution without a stated decision is a number restated. "
            "Say what the programme does about it -- that is the part no "
            "run can produce.")

    s3 = _client()

    def _get(key: str, what: str) -> dict:
        try:
            return json.loads(
                s3.get_object(Bucket=bucket(), Key=key)["Body"].read())
        except Exception as e:
            raise LookupError(f"{what} not in the archive ({key}): {e}") from e

    _get(f"hypotheses/{hid}.json", f"{hid}")
    run = _get(f"experiments/{hid}/{run_id}.json", f"run {run_id} of {hid}")

    from occams.result import blocks
    found = blocks(run.get("metrics", {}))
    if not found:
        raise ValueError(
            f"{hid}/{run_id} carries no scored result, so there is nothing "
            f"to resolve it with. An audit verdict has no estimate and no "
            f"floor; record its outcome as a note on the run instead.")
    if metric_path not in found:
        raise KeyError(
            f"{metric_path!r} is not a result in {hid}/{run_id}. "
            f"Available: {sorted(found)}")
    r = found[metric_path]

    prior = [k for k in _keys_under(s3, f"resolutions/{hid}/")]
    if prior and not supersedes:
        raise FileExistsError(
            f"{hid} is already resolved by {prior}. A second resolution must "
            f"name the one it supersedes -- resolving twice without saying so "
            f"is how running again until the answer is agreeable stops being "
            f"visible.")

    ci = r.get("ci") or [r.get("ci_low"), r.get("ci_high")]
    rec = {"hypothesis_id": hid, "run_id": run_id, "metric_path": metric_path,
           "resolved_at": datetime.now(timezone.utc).isoformat(
               timespec="seconds"),
           # read, not retyped
           "outcome": r.get("verdict"), "effect_size": r.get("estimate"),
           "ci_low": ci[0] if ci else None,
           "ci_high": ci[1] if len(ci or []) > 1 else None,
           "floor": r.get("floor"), "floor_multiples": r.get("floor_multiples"),
           "n": r.get("n"), "n_eff": r.get("n_eff"), "unit": r.get("unit", ""),
           "result_name": r.get("name", ""),
           # supplied, because no run can produce it
           "decision": decision, "note": note, "supersedes": supersedes,
           "source_run_sha256": hashlib.sha256(
               json.dumps(run, sort_keys=True).encode()).hexdigest(),
           "engine_sha": engine_sha()}
    _put_json(f"resolutions/{hid}/{run_id}.json", rec)
    return rec


def _keys_under(s3, prefix: str) -> list[str]:
    try:
        page = s3.list_objects_v2(Bucket=bucket(), Prefix=prefix)
    except Exception:
        return []
    return [o["Key"] for o in page.get("Contents", [])]


def resolutions() -> list[dict]:
    """Every resolution record, newest first."""
    s3 = _client()
    out = []
    for key in _keys_under(s3, "resolutions/"):
        if key.endswith(".json"):
            out.append(json.loads(
                s3.get_object(Bucket=bucket(), Key=key)["Body"].read()))
    out.sort(key=lambda r: str(r.get("resolved_at")), reverse=True)
    return out


def record_experiment(*, hid: str, run_id: str, config: dict, metrics: dict,
                      controls_passed: bool, spend_usd: float = 0.0,
                      note: str = "") -> dict:
    rec = {"hypothesis_id": hid, "run_id": run_id, "config": config,
           "metrics": metrics, "controls_passed": controls_passed,
           "spend_usd": spend_usd, "note": note,
           "engine_sha": engine_sha(),
           "recorded_at": datetime.now(timezone.utc).isoformat(
               timespec="seconds")}
    _put_json(f"experiments/{hid}/{run_id}.json", rec)
    return rec


def _put_json(key: str, obj: dict) -> None:
    s3 = _client()
    try:
        s3.head_object(Bucket=bucket(), Key=key)
        raise FileExistsError(f"REFUSED: {key} exists. The register is "
                              f"append-only; corrections use `supersedes`.")
    except s3.exceptions.ClientError as e:
        if e.response["Error"]["Code"] not in ("404", "NoSuchKey"):
            raise
    body = json.dumps(obj, indent=1).encode()
    s3.put_object(Bucket=bucket(), Key=key, Body=body,
                  ContentType="application/json")
    _append_manifest(s3, {"key": key,
                          "sha256": hashlib.sha256(body).hexdigest(),
                          "bytes": len(body), "source": "register",
                          "cost_usd": 0.0, "note": obj.get("statement", ""),
                          "engine_sha": obj.get("engine_sha", ""),
                          "archived_at": obj.get("stated_at")
                          or obj.get("recorded_at")})
