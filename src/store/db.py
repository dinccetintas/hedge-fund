"""Run persistence — SQLite + a git-tracked JSON dump.

The SQLite DB (`store/bear.sqlite`) is the queryable index; the per-run JSON under
`store/runs/<date>/` is the human-readable, git-tracked audit trail (the track-record dataset).
Phase 1 persists the Stage-1 candidate list; later phases extend the schema with ideas/theses.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

from ..schemas import Candidate

STORE_DIR = Path(__file__).resolve().parents[2] / "store"
DB_PATH = STORE_DIR / "bear.sqlite"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id       TEXT PRIMARY KEY,
    run_date     TEXT NOT NULL,
    stage        TEXT NOT NULL,
    n_candidates INTEGER NOT NULL,
    created_at   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS candidates (
    run_id   TEXT NOT NULL,
    ticker   TEXT NOT NULL,
    scout    TEXT NOT NULL,
    theme    TEXT,
    reason   TEXT NOT NULL,
    payload  TEXT NOT NULL,
    PRIMARY KEY (run_id, ticker),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);
"""


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(_SCHEMA)
    return conn


def save_candidates(
    candidates: list[Candidate],
    *,
    run_date: date | None = None,
    stage: str = "stage1",
    db_path: Path = DB_PATH,
    store_dir: Path = STORE_DIR,
) -> str:
    """Persist a candidate list to SQLite + a dated JSON file. Returns the run_id."""
    run_date = run_date or date.today()
    run_id = f"{run_date.isoformat()}-{stage}-{uuid.uuid4().hex[:8]}"
    now = datetime.now(UTC).isoformat()

    conn = connect(db_path)
    try:
        with conn:
            conn.execute(
                "INSERT INTO runs (run_id, run_date, stage, n_candidates, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (run_id, run_date.isoformat(), stage, len(candidates), now),
            )
            conn.executemany(
                "INSERT OR REPLACE INTO candidates "
                "(run_id, ticker, scout, theme, reason, payload) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (run_id, c.ticker, c.scout.value, c.theme, c.one_line_reason,
                     c.model_dump_json())
                    for c in candidates
                ],
            )
    finally:
        conn.close()

    run_dir = store_dir / "runs" / run_date.isoformat()
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "candidates.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "run_date": run_date.isoformat(),
                "stage": stage,
                "candidates": [c.model_dump(mode="json") for c in candidates],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return run_id
