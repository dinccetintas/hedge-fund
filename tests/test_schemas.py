"""Phase-0 sanity checks: the structured-output contracts import and instantiate.

These guard the data shapes the whole funnel depends on. Real funnel tests arrive in Phase 2.
"""

from datetime import date

from src.schemas import (
    BearCase,
    Briefing,
    Candidate,
    EdgeVerdict,
    Evidence,
    Idea,
    MoatDimension,
    QualityAssessment,
    ScoutType,
    SizingPlan,
    SourceType,
    Valuation,
)


def _evidence() -> Evidence:
    return Evidence(
        claim="ROIC of 22% in FY2025.",
        source_type=SourceType.FILING,
        source_name="10-K FY2025",
        source_date=date(2025, 2, 1),
    )


def test_candidate_roundtrips():
    c = Candidate(
        ticker="MU",
        company_name="Micron Technology",
        scout=ScoutType.THEMATIC,
        one_line_reason="Second-order beneficiary of an accelerating memory-shortage cycle.",
        theme="AI datacenter memory demand",
        evidence=[_evidence()],
    )
    assert c.scout is ScoutType.THEMATIC
    assert c.model_dump()["ticker"] == "MU"


def test_full_idea_assembles():
    idea = Idea(
        ticker="MU",
        company_name="Micron Technology",
        as_of=date(2025, 6, 1),
        scout=ScoutType.THEMATIC,
        thesis_one_line="Memory shortage drives a multi-year earnings inflection.",
        why_now="Datacenter memory demand inflecting ahead of consensus.",
        quality=QualityAssessment(
            quality_score=7.5,
            moat=[
                MoatDimension(name="scale", score=7, direction="widening", rationale="cost leader")
            ],
        ),
        valuation=Valuation(current_price=100.0, buy_below_price=85.0),
        bear_case=BearCase(
            summary="Commodity cyclicality could compress margins.", asymmetry_ratio=3.0
        ),
        edge=EdgeVerdict(
            passes=True, time_arbitrage_rationale="Crowd underweights the cycle turn."
        ),
        sizing=SizingPlan(conviction=8, target_weight_pct=12.0, starter_weight_pct=6.0),
    )
    assert 0 <= idea.quality.quality_score <= 10
    assert idea.bear_case.asymmetry_ratio == 3.0


def test_briefing_holds_ideas():
    b = Briefing(run_date=date(2025, 6, 1), ideas=[], active_themes=["AI memory"])
    assert b.ideas == []
    assert "AI memory" in b.active_themes
