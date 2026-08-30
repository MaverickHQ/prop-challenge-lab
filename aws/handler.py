"""Lambda entrypoint — one function, four jobs, dispatched by name (B1.1).

One package and one deploy for every job, per the razor in the backlog.
The event carries `{"job": "morning"|"poll"|"evening"|"command"}`.

This is the B1.1 skeleton: it validates dispatch, proves the package
imports the *unforked* engine, and exits. The jobs themselves land in
B3. Deliberately no order routing, here or anywhere downstream (B-C2) —
this stack emits cards and a human places every order.
"""

from __future__ import annotations

import json
import logging
import os

log = logging.getLogger()
log.setLevel(logging.INFO)

JOBS = ("morning", "poll", "evening", "command")


def _engine_fingerprint() -> dict:
    """Prove the Lambda imports the same modules the sealed verdicts and
    the local runs used (B1.4). Any divergence between them is a defect,
    not a variant — so the deployed constants are logged, not assumed."""
    from occams import paper

    return {"k_stop": paper.K_STOP, "risk_usd": paper.RISK_USD,
            "max_contracts": paper.MAX_CONTRACTS, "tick": paper.TICK}


def _secret_health() -> dict:
    """Can the execution role actually read /occams/*? Locally there is no
    role and no boto3 session, so report `unavailable` rather than failing
    the unit tests — the check exists for the deployed path."""
    try:
        from aws import secrets
    except ImportError as e:
        # The module is genuinely absent — a packaging fault, not an
        # environment one. Say so; the first version of this reported
        # "not running in Lambda" and hid exactly that bug.
        return {"error": f"secrets module not packaged: {e}"}
    try:
        return secrets.available(secrets.TELEGRAM_TOKEN, secrets.TELEGRAM_CHAT)
    except Exception as e:                      # noqa: BLE001 — reported
        return {"error": f"{type(e).__name__}: {e}"}


def lambda_handler(event, context):
    job = (event or {}).get("job")
    if job not in JOBS:
        # Loud, never guessed — a mis-scheduled rule must fail visibly
        # rather than silently run the wrong job.
        raise ValueError(f"unknown job {job!r}; expected one of {JOBS}")

    payload = {
        "job": job,
        "engine": _engine_fingerprint(),
        "venue_delay_minutes": int(os.environ.get("VENUE_DELAY_MINUTES", 10)),
        "state_bucket": os.environ.get("STATE_BUCKET"),
        # Lengths only, never values — this line is logged (B-C4). A None
        # here means the Lambda cannot reach a secret it will need at send
        # time, which is exactly what should be visible before B3 relies
        # on it rather than at 09:45 ET on a trading day.
        "secrets": _secret_health(),
        "status": "ok",
    }
    # The standard payload is emitted for EVERY job, poll included, so the
    # engine fingerprint and the delay setting are in the log of every
    # invocation — that is what the dead-man's switch (B4.1) reads.
    if job == "poll":
        from aws import jobs
        payload["result"] = jobs.run_poll()
    elif job == "morning":
        from aws import jobs
        payload["result"] = jobs.run_morning()
    elif job == "evening":
        from aws import jobs
        payload["result"] = jobs.run_evening()
    elif job == "command":
        from aws import commands
        payload["result"] = commands.run_commands()
    log.info(json.dumps(payload))
    return payload
