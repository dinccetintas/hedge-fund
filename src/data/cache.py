"""Disk cache for data-provider responses.

Two jobs:
  1. Keep us under the FMP free-tier daily call cap during development (repeated runs hit cache).
  2. Make loaders **point-in-time-ready** — the cache key includes the as-of date, so a given
     (endpoint, params, as_of) always resolves to the same payload.

Deliberately simple: JSON files under a cache dir, one per key hash. Not for the git-tracked
`store/` (that's the audit trail); this is a throwaway speed/cost cache and is gitignored.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache" / "data"


def _key(endpoint: str, params: dict[str, Any], as_of: str | None) -> str:
    blob = json.dumps(
        {"endpoint": endpoint, "params": params, "as_of": as_of},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(blob.encode()).hexdigest()[:24]


def get(
    endpoint: str,
    params: dict[str, Any],
    as_of: str | None = None,
    *,
    max_age_seconds: float | None = None,
) -> Any | None:
    """Return a cached payload, or None on miss / expiry."""
    path = CACHE_DIR / f"{_key(endpoint, params, as_of)}.json"
    if not path.exists():
        return None
    if max_age_seconds is not None and (time.time() - path.stat().st_mtime) > max_age_seconds:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))["payload"]
    except (json.JSONDecodeError, KeyError):
        return None


def put(endpoint: str, params: dict[str, Any], as_of: str | None, payload: Any) -> None:
    """Persist a payload for (endpoint, params, as_of)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{_key(endpoint, params, as_of)}.json"
    record = {"endpoint": endpoint, "params": params, "as_of": as_of, "payload": payload}
    path.write_text(json.dumps(record, default=str), encoding="utf-8")
