"""M3 — a ledger of how each number was actually computed.

`engine_sha` pins the COMMIT that produced a result. It does not say which
function did the arithmetic, nor with what input. Those were the same thing
while every script carried its own copy of the maths; they stopped being the
same thing the moment M1 replaced three divergent bootstraps with one.

So every public estimator is wrapped in `@audited`, which records:

- the fully-qualified function name
- the sha256 of its own SOURCE, so a later edit is visible even if the
  function name and the commit are unchanged
- a summary of each argument — arrays by shape and content hash, never by
  value, because a ledger that inlined the inputs would be larger than the
  data and would still not prove more

The ledger is process-local and written on exit to whatever path
`OCCAMS_CALC_LEDGER` names. `experiment.run` sets that variable for the
subprocess and archives the file as `calcs.json`, beside the `script.py` and
`output.txt` it already keeps. Scripts do not opt in: importing the engine is
enough.
"""

from __future__ import annotations

import atexit
import functools
import hashlib
import inspect
import json
import os
from typing import Any

MAX_SAMPLES = 8          # distinct call signatures kept per function
_LEDGER: dict[str, dict[str, Any]] = {}
_SOURCE_CACHE: dict[str, str] = {}

ENV_PATH = "OCCAMS_CALC_LEDGER"


def _source_sha(fn) -> str:
    key = f"{fn.__module__}.{fn.__qualname__}"
    if key not in _SOURCE_CACHE:
        try:
            src = inspect.getsource(fn)
        except (OSError, TypeError):          # pragma: no cover - built-ins
            src = key
        _SOURCE_CACHE[key] = hashlib.sha256(src.encode()).hexdigest()
    return _SOURCE_CACHE[key]


def _describe(value: Any) -> dict[str, Any]:
    """Arrays by shape and hash; scalars by value. Never the whole array."""
    if hasattr(value, "shape") and hasattr(value, "dtype"):
        try:
            import numpy as np
            arr = np.ascontiguousarray(value)
            return {"shape": list(arr.shape), "dtype": str(arr.dtype),
                    "sha256": hashlib.sha256(arr.tobytes()).hexdigest()[:16]}
        except Exception:                     # pragma: no cover
            return {"repr": type(value).__name__}
    if isinstance(value, (list, tuple)):
        try:
            import numpy as np
            arr = np.ascontiguousarray(np.asarray(value, dtype=float))
            return {"shape": list(arr.shape), "dtype": str(arr.dtype),
                    "sha256": hashlib.sha256(arr.tobytes()).hexdigest()[:16]}
        except Exception:
            return {"len": len(value)}
    if isinstance(value, (int, float, bool, str)) or value is None:
        return {"value": value}
    return {"repr": type(value).__name__}


def audited(fn):
    """Record every call to `fn` in the process ledger."""
    name = f"{fn.__module__}.{fn.__qualname__}"

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        row = _LEDGER.setdefault(name, {"function": name,
                                        "source_sha256": _source_sha(fn),
                                        "calls": 0, "arg_samples": []})
        row["calls"] += 1
        if len(row["arg_samples"]) < MAX_SAMPLES:
            sample = [_describe(a) for a in args]
            sample += [{"kw": k, **_describe(v)} for k, v in kwargs.items()]
            if sample not in row["arg_samples"]:
                row["arg_samples"].append(sample)
        return fn(*args, **kwargs)

    wrapper.__wrapped__ = fn
    return wrapper


def ledger() -> list[dict[str, Any]]:
    """Every distinct estimator called in this process, with a first
    argument sample under `args` for convenience."""
    out = []
    for row in _LEDGER.values():
        entry = dict(row)
        entry["args"] = row["arg_samples"][0] if row["arg_samples"] else []
        out.append(entry)
    return out


def reset() -> None:
    _LEDGER.clear()


def dumps() -> str:
    from occams.archive import engine_sha
    return json.dumps({"engine_sha": engine_sha(),
                       "calculations": ledger()}, indent=1, sort_keys=True)


def dump(path) -> None:
    from pathlib import Path
    Path(path).write_text(dumps())


@atexit.register
def _dump_on_exit() -> None:                  # pragma: no cover - exit hook
    target = os.environ.get(ENV_PATH)
    if target and _LEDGER:
        try:
            dump(target)
        except Exception:
            pass                              # never break a run over a log
