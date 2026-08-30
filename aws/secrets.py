"""SSM SecureString access for the Lambda (B1.2, B-C4).

Secrets never live in the repo, in plaintext env vars, or in logs. They are
read from `/occams/*` at runtime and cached for the life of the execution
environment, so a warm invocation makes no extra API call.

`available()` deliberately returns only names and lengths. Anything that
returns a value must be called by code that will not log it — which is why
the health check the handler reports uses this and not `get()`.
"""

from __future__ import annotations

import functools
import os

PREFIX = os.environ.get("SSM_PREFIX", "/occams")

TELEGRAM_TOKEN = "telegram/token"
TELEGRAM_CHAT = "telegram/chat"


@functools.cache
def _client():
    import boto3                      # provided by the Lambda runtime
    return boto3.client("ssm")


@functools.cache
def get(name: str) -> str:
    """Decrypted value for `<PREFIX>/<name>`. Cached per container."""
    r = _client().get_parameter(Name=f"{PREFIX}/{name}", WithDecryption=True)
    return r["Parameter"]["Value"]


def available(*names: str) -> dict[str, int | None]:
    """{name: length} — length, never the value, so this is safe to log.
    None means the parameter is missing or unreadable, which is the
    failure the dead-man's switch (B4.1) needs to surface loudly rather
    than discover at send time."""
    out: dict[str, int | None] = {}
    for n in names:
        try:
            out[n] = len(get(n))
        except Exception:
            out[n] = None
    return out
