"""The daily run — wires the funnel end to end.

Stage 1 sources candidates (Phase 1). Stages 2–6 deep-dive the top-N candidates through the
analysis agents with two kill-gates (quality floor, edge gate). Stage 7 ranks the survivors,
builds the Briefing, persists it, and writes the dated markdown report.
"""

from __future__ import annotations

import logging
from datetime import date

from ..agents.data import gather_company_data
from ..agents.edge_gate import EdgeGateAgent
from ..agents.quality import QualityAgent
from ..agents.red_team import RedTeamAgent
from ..agents.risk_pm import RiskPMAgent
from ..agents.valuation import ValuationAgent
from ..config import DEPTH_LIMIT, MIN_QUALITY_SCORE
from ..data.bigdata_client import BigdataClient
from ..data.finviz_client import FinvizScreener
from ..data.fmp_client import FMPClient
from ..report.briefing import write_briefing
from ..schemas import Briefing, Candidate, Idea
from ..scouts.aggregate import source_candidates
from ..scouts.base import ScoutContext
from ..scouts.enrich import fundamentals_from_finviz, profiles_from_finviz
from ..store import db
from ..universe.build import build_universe_finviz
from .synthesize import build_briefing

log = logging.getLogger(__name__)


async def source_stage1(
    run_date: date | None = None,
    *,
    enrich_cap: int = 50,
    per_scout_limit: int = 25,
    universe_size: int = 1000,
) -> tuple[str, list[Candidate]]:
    """Stage 1 only: universe → scout swarm → persisted candidates. Returns (run_id, candidates).

    The universe (and the quant fundamentals the scouts need) is sourced from the Finviz screener,
    since FMP's legacy screener is deprecated and the new one is gated behind a paid plan. FMP is
    still opened for any per-symbol calls a scout may attempt (best-effort, degrades gracefully).
    """
    run_date = run_date or date.today()
    async with FinvizScreener() as fv:
        universe, rows = await build_universe_finviz(
            fv, as_of=run_date, max_rows=universe_size
        )
    fundamentals = fundamentals_from_finviz(rows)
    profiles = profiles_from_finviz(rows)

    async with FMPClient() as fmp:
        ctx = ScoutContext(
            fmp=fmp, universe=universe, as_of=run_date,
            bigdata=BigdataClient(), enrich_cap=enrich_cap,
            fundamentals=fundamentals, profiles=profiles,
        )
        candidates = await source_candidates(ctx, per_scout_limit=per_scout_limit)

    run_id = db.save_candidates(candidates, run_date=run_date, stage="stage1")
    log.info("Stage 1 complete: %d candidates (run_id=%s)", len(candidates), run_id)
    return run_id, candidates


async def analyze_candidate(
    fmp: FMPClient, candidate: Candidate, run_date: date
) -> Idea | None:
    """Run Stages 2–6 on one candidate. Returns an Idea, or None if a kill-gate trips."""
    data = await gather_company_data(fmp, candidate.ticker, run_date)

    quality = await QualityAgent().run(candidate, data)
    if quality.quality_score < MIN_QUALITY_SCORE:
        log.info("%s killed at quality gate (%.1f)", candidate.ticker, quality.quality_score)
        return None

    valuation = await ValuationAgent().run(candidate, data, quality)
    bear = await RedTeamAgent().run(candidate, data, quality, valuation)
    edge = await EdgeGateAgent().run(candidate, data, bear)
    if not edge.passes:
        log.info("%s killed at edge gate", candidate.ticker)
        return None

    sizing = await RiskPMAgent().run(candidate, data, quality, valuation, bear, edge)
    return Idea(
        ticker=candidate.ticker,
        company_name=candidate.company_name,
        as_of=run_date,
        scout=candidate.scout,
        thesis_one_line=candidate.one_line_reason,
        why_now=candidate.theme or candidate.one_line_reason,
        theme=candidate.theme,
        quality=quality,
        valuation=valuation,
        bear_case=bear,
        edge=edge,
        sizing=sizing,
    )


async def run_daily(run_date: date | None = None, *, depth_limit: int = DEPTH_LIMIT) -> Briefing:
    """Execute the full funnel and return the morning Briefing."""
    run_date = run_date or date.today()
    run_id, candidates = await source_stage1(run_date)

    ideas: list[Idea] = []
    async with FMPClient() as fmp:
        for candidate in candidates[:depth_limit]:
            try:
                idea = await analyze_candidate(fmp, candidate, run_date)
            except Exception:  # noqa: BLE001 — one bad candidate must not sink the run
                log.exception("Analysis failed for %s", candidate.ticker)
                continue
            if idea is not None:
                ideas.append(idea)

    briefing = build_briefing(ideas, run_date=run_date, run_id=run_id)
    db.save_briefing(briefing)
    path = write_briefing(briefing)
    log.info("Funnel complete: %d ideas → %s", len(briefing.ideas), path)
    return briefing
