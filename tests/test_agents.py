"""Agents return their schema and route to the right model tier (cost-aware)."""

from __future__ import annotations

from datetime import date

import pytest

import src.llm as llm
from src.agents.data import CompanyData
from src.agents.edge_gate import EdgeGateAgent
from src.agents.quality import QualityAgent
from src.agents.valuation import ValuationAgent
from src.schemas import (
    BearCase,
    Candidate,
    EdgeVerdict,
    MoatDimension,
    QualityAssessment,
    ScoutType,
    Valuation,
)
from src.settings import settings


@pytest.fixture
def capture_model(monkeypatch):
    seen = {}

    def _install(return_value):
        async def fake_structured(*, model, system, user, schema, max_tokens=2000):
            seen["model"] = model
            seen["schema"] = schema
            return return_value
        monkeypatch.setattr(llm, "structured", fake_structured)
        return seen

    return _install


def _cand():
    return Candidate(ticker="AAA", company_name="Alpha", scout=ScoutType.QUALITY_COMPOUNDER,
                     one_line_reason="high-ROIC compounder")


def _data():
    return CompanyData(ticker="AAA", as_of=date(2026, 6, 1))


async def test_quality_agent_uses_analysis_tier(capture_model):
    qa = QualityAssessment(
        quality_score=7.5,
        moat=[MoatDimension(name="scale", score=7, direction="stable", rationale="x")],
    )
    seen = capture_model(qa)
    out = await QualityAgent().run(_cand(), _data())
    assert out is qa
    assert seen["model"] == settings.model_analysis    # Sonnet — mid-depth
    assert seen["schema"] is QualityAssessment


async def test_valuation_agent_uses_synthesis_tier(capture_model):
    val = Valuation(current_price=100, buy_below_price=80)
    seen = capture_model(val)
    quality = QualityAssessment(quality_score=8, moat=[], roic=0.2)
    out = await ValuationAgent().run(_cand(), _data(), quality)
    assert out is val
    assert seen["model"] == settings.model_synthesis   # Opus — depth


async def test_edge_gate_uses_synthesis_tier(capture_model):
    verdict = EdgeVerdict(passes=True)
    seen = capture_model(verdict)
    out = await EdgeGateAgent().run(_cand(), _data(), BearCase(summary="bear"))
    assert out is verdict
    assert seen["model"] == settings.model_synthesis