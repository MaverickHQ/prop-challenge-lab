"""B1.2 — copy local secrets into SSM SecureString, without exposing them.

Secrets live in `.env` for Workstream A (local) and under `/occams/` in SSM
for Workstream B (Lambda). Neither reads the other's; this is the one-way
bridge that syncs them.

Values go through **boto3**, never argv and never a temp file: a
`--value <secret>` argument is visible in the process table to every other
user on the machine and lands in shell history, and a file on disk is one
crash away from being left behind. Nothing here prints a value, so it is
safe to run with output captured.

Re-runnable: `--overwrite` means rotating a token is just a re-run.

Usage:
    python3 scripts/push_secrets.py --profile occams
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# local .env name -> SSM parameter path (B-C4: everything under /occams/)
MAPPING = {
    "TELEGRAM_BOT_TOKEN": "/occams/telegram/token",
    "TELEGRAM_CHAT_ID": "/occams/telegram/chat",
}


def read_env() -> dict[str, str]:
    env = ROOT / ".env"
    if not env.exists():
        sys.exit(".env not found — nothing to push")
    out = {}
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip("'\"")
    return out


def client(profile: str):
    import boto3
    return boto3.Session(profile_name=profile).client("ssm")


def put(ssm, name: str, value: str) -> None:
    ssm.put_parameter(Name=name, Value=value, Type="SecureString",
                      Overwrite=True,
                      Description="occams campaign (Workstream B)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="occams")
    a = ap.parse_args()

    env = read_env()
    missing = [k for k in MAPPING if k not in env or not env[k]]
    if missing:
        sys.exit(f"missing in .env: {', '.join(missing)}")

    ssm = client(a.profile)
    for local, path in MAPPING.items():
        put(ssm, path, env[local])
        # length only — never the value
        print(f"  {path:<26} written ({len(env[local])} chars)")
    print(f"\n{len(MAPPING)} parameters in SSM under /occams/. "
          f"Re-run after rotating a token.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
