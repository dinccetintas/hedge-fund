"""Persistence writes both the SQLite index and the git-tracked JSON audit trail."""

from __future__ import annotations

import json
import sqlite3
from datetime import date

from src.schemas import Candidate, ScoutType
from src.store import db


def test_save_candidates_writes_sqlite_and_json(tmp_path):
    candidates = [
        Candidate(ticker="AAA", company_name="Alpha", scout=ScoutType.THEMATIC,
                  one_line_reason="second-order AI memory play", theme="AI memory"),
        Candidate(ticker="BBB", company_name="Beta", scout=ScoutType.HIDDEN_GEM,
                  one_line_reason="cheap small-cap leader"),
    ]
    db_path = tmp_path / "bear.sqlite"
    store_dir = tmp_path / "store"

    run_id = db.save_candidates(
        candidates, run_date=date(2026, 6, 1), db_path=db_path, store_dir=store_dir
    )

    # SQLite: run + candidate rows present.
    conn = sqlite3.connect(db_path)
    n_run = conn.execute("SELECT n_candidates FROM runs WHERE run_id=?", (run_id,)).fetchone()[0]
    n_cand = conn.execute(
        "SELECT COUNT(*) FROM candidates WHERE run_id=?", (run_id,)
    ).fetchone()[0]
    conn.close()
    assert n_run == 2
    assert n_cand == 2

    # JSON: dated audit file well-formed.
    payload = json.loads((store_dir / "runs" / "2026-06-01" / "candidates.json").read_text())
    assert payload["run_id"] == run_id
    assert {c["ticker"] for c in payload["candidates"]} == {"AAA", "BBB"}
