"""S3-backed day state (B1.3) — single-writer by construction.

The schedules never overlap, so there is one writer at a time by design.
The ETag precondition on top of that is the backstop for the case design
does not cover: a manual invoke racing a scheduled one.

Shape is deliberately a plain JSON document, not a database (B7.3). A few
hundred days of a handful of fields is an in-memory filter, and DynamoDB
would add IAM surface, schema decisions and ops for no benefit at this
scale. The ledger shape does not change if that ever stops being true.

    {"2026-08-03": {"MES": {"phase": "carded",
                            "card": {...},
                            "sent": ["range", "card"],
                            "filled_at": "..."}}}
"""

from __future__ import annotations

import json
import os
from typing import Any

KEY = "state/paper_state.json"


def _s3():
    import boto3
    return boto3.client("s3")


def load() -> tuple[dict, str | None]:
    """(document, etag). A missing object is an empty day-book, not an
    error — the first run of a new deployment must not need seeding."""
    bucket = os.environ["STATE_BUCKET"]
    try:
        r = _s3().get_object(Bucket=bucket, Key=KEY)
    except Exception:
        return {}, None
    return json.loads(r["Body"].read()), r.get("ETag")


def save(doc: dict, etag: str | None) -> bool:
    """Conditional write. False means someone else wrote first — the
    caller re-reads and retries rather than clobbering."""
    kw: dict[str, Any] = {}
    if etag:
        kw["IfMatch"] = etag
    else:
        kw["IfNoneMatch"] = "*"
    try:
        _s3().put_object(Bucket=os.environ["STATE_BUCKET"], Key=KEY,
                         Body=json.dumps(doc, indent=1).encode(),
                         ContentType="application/json", **kw)
        return True
    except Exception as e:
        if "PreconditionFailed" in str(e) or "412" in str(e):
            return False
        raise


def day(doc: dict, date_str: str, instrument: str) -> dict:
    return doc.setdefault(date_str, {}).setdefault(
        instrument, {"phase": "idle", "sent": []})


def append_log(record: dict) -> None:
    """Append-only event log. Separate object per day so a write can never
    rewrite history — the log is evidence, and evidence that can be
    rewritten by a retry is not evidence."""
    import boto3
    from datetime import datetime, timezone
    s3 = boto3.client("s3")
    bucket = os.environ["STATE_BUCKET"]
    key = f"logs/{record['date']}.jsonl"
    try:
        prev = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode()
    except Exception:
        prev = ""
    record = {**record,
              "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    s3.put_object(Bucket=bucket, Key=key,
                  Body=(prev + json.dumps(record) + "\n").encode(),
                  ContentType="application/x-ndjson")
