"""The daily run — wires the funnel end to end.

Phase 1 implements the Stage-1 path: build the universe, run the scout swarm, persist the
candidate list. Stages 2–7 (quality → … → synthesis) arrive in Phase 2; calling `run_daily`
raises NotImplementedError after sourcing until they land.
"""

from __future__ import annotations

import logging
from datetime import date

from ..data.bigdata_client import BigdataClient
from ..data.fmp_client import FMPClient
from ..schemas import Briefing, Candidate
from ..scouts.aggregate import source_candidates
from ..scouts.base import ScoutContext
from ..store import db
from ..universe.build import build_universe

log = logging.getLogger(__name__)


async def source_stage1(
    run_date: date | None = None, *, enrich_cap: int = 50, per_scout_limit: int = 25
) -> tuple[str, list[Candidate]]:
    """Stage 1 only: universe → scout swarm → persisted candidates. Returns (run_id, candidates)."""
    run_date = run_date or date.today()
    async with FMPClient() as fmp:
        universe = await build_universe(fmp, as_of=run_date)
        ctx = ScoutContext(
            fmp=fmp,
            universe=universe,
            as_of=run_date,
            bigdata=BigdataClient(),
            enrich_cap=enrich_cap,
        )
        candidates = await source_candidates(ctx, per_scout_limit=per_scout_limit)

    run_id = db.save_candidates(candidates, run_date=run_date, stage="stage1")
    log.info("Stage 1 complete: %d candidates (run_id=%s)", len(candidates), run_id)
    return run_id, candidates


async def run_daily(run_date: date | None = None) -> Briefing:
    """Execute the full funnel. Stages 2–7 are wired in Phase 2."""
    run_date = run_date or date.today()
    await source_stage1(run_date)
    raise NotImplementedError(
        "Stages 2–7 (quality → … → synthesis) are wired in Phase 2 — see docs/METHODOLOGY.md."
    )
