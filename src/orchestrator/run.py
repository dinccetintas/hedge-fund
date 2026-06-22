"""The daily run — wires the funnel end to end.

Phase 0 ships the skeleton: the control flow and stage boundaries are defined so Phases 1–3 can
fill each stage in without re-architecting. Calling it today raises NotImplementedError at the
first unimplemented stage (loud failure > silent stub).
"""

from __future__ import annotations

from datetime import date

from ..schemas import Briefing


async def run_daily(run_date: date | None = None) -> Briefing:
    """Execute one full research pass and return the morning Briefing.

    Pipeline (see METHODOLOGY §3):
        candidates = await source_all_scouts(as_of)        # Stage 1
        for c in candidates:                               # Stages 2–6
            quality   = await QualityAgent().run(c, as_of)
            if quality.quality_score < MIN_QUALITY_SCORE: continue
            valuation = await ValuationAgent().run(c, quality, as_of)
            bear      = await RedTeamAgent().run(c, quality, valuation, as_of)
            edge      = await EdgeGateAgent().run(c, bear, as_of)
            if not edge.passes: continue
            sizing    = await RiskPMAgent().run(c, quality, valuation, bear, as_of)
            ideas.append(Idea(...))
        briefing = rank_and_synthesize(ideas)              # Stage 7
        store.save_run(briefing); report.write_markdown(briefing)
        watchlist.update(briefing)
        return briefing
    """
    run_date = run_date or date.today()
    raise NotImplementedError(
        "The funnel is scaffolded but not yet wired — see Phases 1–3 in docs/METHODOLOGY.md."
    )
