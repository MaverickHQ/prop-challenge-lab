"""Telegram IO — deliberately thin (urllib, no dependencies).

Reads TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID from .env (git-ignored).
Dormant-safe: without a token everything no-ops with a printed notice, so
the cron jobs can be installed before the bot exists (T1.2).
"""

from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_API = "https://api.telegram.org/bot{token}/{method}"


def _ctx() -> ssl.SSLContext:
    """python.org builds ship no CA bundle for urllib — use certifi
    (present via the databento dependency chain) so cron never hits
    CERTIFICATE_VERIFY_FAILED."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:                       # system python: default works
        return ssl.create_default_context()


def _open(req, attempts: int = 8, wait_s: float = 15.0):
    """urlopen with wake-race tolerance: launchd fires coalesced jobs the
    instant the Mac wakes, often seconds before Wi-Fi/DNS is back. Retry
    for ~2 minutes before giving up (observed: Errno 8 at 14:35 wake,
    2026-07-29)."""
    last = None
    for i in range(attempts):
        try:
            return urllib.request.urlopen(req, timeout=30, context=_ctx())
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            if i < attempts - 1:
                time.sleep(wait_s)
    raise last


def _env(env_file: str | Path = ".env") -> dict[str, str]:
    p = Path(env_file)
    out: dict[str, str] = {}
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip("'\"")
    return out


def credentials(env_file: str | Path = ".env") -> tuple[str, str] | None:
    env = _env(env_file)
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    chat = env.get("TELEGRAM_CHAT_ID", "")
    return (token, chat) if token and chat else None


def send(text: str, env_file: str | Path = ".env") -> bool:
    creds = credentials(env_file)
    if creds is None:
        print("[telegram dormant — no token in .env] would send:\n" + text)
        return False
    token, chat = creds
    data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
    req = urllib.request.Request(_API.format(token=token,
                                             method="sendMessage"),
                                 data=data)
    with _open(req) as resp:
        return json.load(resp).get("ok", False)


def fetch_updates(offset: int, env_file: str | Path = ".env"
                  ) -> list[tuple[int, int, str]]:
    """(update_id, unix_date, text) for messages from OUR chat only."""
    creds = credentials(env_file)
    if creds is None:
        print("[telegram dormant — no token in .env] no updates fetched")
        return []
    token, chat = creds
    url = _API.format(token=token, method="getUpdates") \
        + f"?offset={offset}&timeout=0"
    with _open(url) as resp:
        payload = json.load(resp)
    out: list[tuple[int, int, str]] = []
    for u in payload.get("result", []):
        msg = u.get("message") or {}
        if str((msg.get("chat") or {}).get("id", "")) != str(chat):
            continue
        if "text" in msg:
            out.append((u["update_id"], msg.get("date", 0), msg["text"]))
    return out
