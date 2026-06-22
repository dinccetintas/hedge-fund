"""Stages 2–6 orchestration: kill-gates and a clean pass, with the LLM mocked.

`src.llm.structured` is patched to return canned schema objects keyed by the requested schema, so
the agents and `analyze_candidate` run deterministically with no network.
"""

from __future__ import annotations

from datetime import date

import pytest

import src.llm as llm
from src.orchestrator.run import analyze_candidate
from src.schemas import (
    BearCase,
    Candidate,
    EdgeVerdict,
    MoatDimension,
    QualityAssessment,
    ScoutType,
    SizingPlan,
    Valuation,
)
from tests.conftest import FakeFMP


def _responses(quality_score=8.0, edge_passes=True):
    return {
        QualityAssessment: QualityAssessment(
            quality_score=quality_score,
            moat=[MoatDimension(name="scale", score=8, direction="widening", rationale="x")],
            roic=0.22,
        ),
        Valuation: Valuation(current_price=100.0, buy_below_price=80.0, expected_irr_5yr=0.15),
        BearCase: BearCase(summary="cyclical risk", asymmetry_ratio=3.0, downside_floor_price=70.0),
        EdgeVerdict: EdgeVerdict(passes=edge_passes, time_arbitrage_rationale="crowd waits"),
        SizingPlan: SizingPlan(conviction=8.0, target_weight_pct=12.0, starter_weight_pct=6.0),
    }


@pytest.fixture
def patch_llm(monkeypatch):
    def _install(responses):
        async def fake_structured(*, model, system, user, schema, max_tokens=2000):
            return responses[schema]
        monkeypatch.setattr(llm, "structured", fake_structured)
    return _install


def _candidate():
    return Candidate(
        ticker="AAA", company_name="Alpha", scout=ScoutType.THEMATIC,
        one_line_reason="second-order AI memory play", theme="AI memory",
    )


async def test_full_pass_produces_idea(patch_llm):
    patch_llm(_responses(quality_score=8.0, edge_passes=True))
    idea = await analyze_candidate(FakeFMP(), _candidate(), date(2026, 6, 1))
    assert idea is not None
    assert idea.ticker == "AAA"
    assert idea.theme == "AI memory"
    assert idea.quality.quality_score == 8.0
    assert idea.sizing.conviction == 8.0


async def test_quality_gate_kills_low_score(patch_llm):
    patch_llm(_responses(quality_score=2.0))  # below MIN_QUALITY_SCORE
    idea = await analyze_candidate(FakeFMP(), _candidate(), date(2026, 6, 1))
    assert idea is None


async def test_edge_gate_kills_no_edge(patch_llm):
    patch_llm(_responses(quality_score=8.0, edge_passes=False))
    idea = await analyze_candidate(FakeFMP(), _candidate(), date(2026, 6, 1))
    assert idea is None
