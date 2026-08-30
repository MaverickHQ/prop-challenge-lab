"""Telegram out, from the Lambda. Stdlib only.

Credentials come from SSM SecureString at call time (B-C4) — never from
the repo, never from a plaintext env var, never logged. `secrets.get` is
cached per execution environment, so a warm invocation makes no extra call.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

_API = "https://api.telegram.org/bot{token}/{method}"


def send(text: str) -> bool:
    from aws import secrets
    try:
        token = secrets.get(secrets.TELEGRAM_TOKEN)
        chat = secrets.get(secrets.TELEGRAM_CHAT)
    except Exception:
        # A missing secret must not take the whole poll down: the other
        # instrument still needs processing and the dead-man's switch
        # (B4.1) is what surfaces the silence.
        return False
    body = urllib.parse.urlencode(
        {"chat_id": chat, "text": text,
         "disable_web_page_preview": "true"}).encode()
    req = urllib.request.Request(_API.format(token=token,
                                             method="sendMessage"),
                                 data=body)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r).get("ok", False)
    except Exception:
        return False


def fetch_updates(offset: int) -> list[tuple[int, int, str]]:
    """(update_id, unix_date, text) from OUR chat only — same contract as
    occams.telegram, so the local and Lambda paths cannot drift."""
    from aws import secrets
    token = secrets.get(secrets.TELEGRAM_TOKEN)
    chat = secrets.get(secrets.TELEGRAM_CHAT)
    url = (_API.format(token=token, method="getUpdates")
           + f"?offset={offset}&timeout=0")
    with urllib.request.urlopen(url, timeout=30) as r:
        payload = json.load(r)
    out = []
    for u in payload.get("result", []):
        msg = u.get("message") or {}
        if str((msg.get("chat") or {}).get("id", "")) != str(chat):
            continue
        if "text" in msg:
            out.append((u["update_id"], msg.get("date", 0), msg["text"]))
    return out
