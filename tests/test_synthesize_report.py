"""Stage-7 ranking + briefing assembly + markdown rendering."""

from __future__ import annotations

from datetime import date

from src.orchestrator.synthesize import build_briefing, rank_ideas
from src.report.briefing import render_markdown
from src.schemas import (
    BearCase,
    EdgeVerdict,
    Idea,
    QualityAssessment,
    ScoutType,
    SizingPlan,
    Valuation,
)


def _idea(ticker, conviction, asymmetry, irr, theme=None):
    return Idea(
        ticker=ticker, company_name=f"{ticker} Inc", as_of=date(2026, 6, 1),
        scout=ScoutType.THEMATIC, thesis_one_line=f"{ticker} thesis", why_now="now", theme=theme,
        quality=QualityAssessment(quality_score=8, moat=[], roic=0.2),
        valuation=Valuation(current_price=100, buy_below_price=80, expected_irr_5yr=irr),
        bear_case=BearCase(summary="bear", asymmetry_ratio=asymmetry),
        edge=EdgeVerdict(passes=True),
        sizing=SizingPlan(conviction=conviction, target_weight_pct=10, starter_weight_pct=5),
    )


def test_rank_orders_by_conviction_asymmetry_irr():
    low = _idea("LOW", conviction=4, asymmetry=2, irr=0.05)
    high = _idea("HIGH", conviction=9, asymmetry=4, irr=0.20)
    ranked = rank_ideas([low, high])
    assert [i.ticker for i in ranked] == ["HIGH", "LOW"]
    assert ranked[0].rank_score > ranked[1].rank_score


def test_build_briefing_collects_themes():
    briefing = build_briefing(
        [_idea("AAA", 8, 3, 0.15, theme="AI memory"), _idea("BBB", 7, 2, 0.10, theme="reshoring")],
        run_date=date(2026, 6, 1), run_id="r1",
    )
    assert briefing.run_id == "r1"
    assert briefing.active_themes == ["AI memory", "reshoring"]


def test_markdown_renders_key_fields():
    briefing = build_briefing([_idea("AAA", 8, 3, 0.15, theme="AI memory")],
                              run_date=date(2026, 6, 1), run_id="r1")
    md = render_markdown(briefing)
    assert "# Morning Briefing — 2026-06-01" in md
    assert "## 1. AAA — AAA Inc" in md
    assert "buy-below" in md
    assert "Asymmetry" in md
    assert "not investment advice" in md


def test_markdown_handles_empty_briefing():
    md = render_markdown(build_briefing([], run_date=date(2026, 6, 1)))
    assert "No ideas cleared the funnel" in md
