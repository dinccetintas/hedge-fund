"""Stage 6 — Portfolio Construction & Sizing → SizingPlan (size + entry plan).

Encodes Morris's 4-variable sizing rubric (5-yr expected return × moat durability × profitability
predictability × management quality) and Oguz's start-small + two pre-armed sell rules.
"""

from __future__ import annotations

from ..config import (
    MAX_SINGLE_NAME_PCT,
    MIN_ASYMMETRY_RATIO,
    STARTER_POSITION_PCT,
)
from ..schemas import BearCase, Candidate, EdgeVerdict, QualityAssessment, SizingPlan, Valuation
from .base import Agent
from .data import CompanyData
from .prompts import HOUSE_VIEW


class RiskPMAgent(Agent[SizingPlan]):
    model_tier = "analysis"
    methodology_files = ["tsoh_morris.md", "oguz_erkan.md"]
    output_schema = SizingPlan

    async def run(
        self,
        candidate: Candidate,
        data: CompanyData,
        quality: QualityAssessment,
        valuation: Valuation,
        bear: BearCase,
        edge: EdgeVerdict,
    ) -> SizingPlan:
        system = (
            "You are the Risk & Portfolio Manager. Apply Morris's 4-variable rubric — 5-yr "
            "expected return × moat_durability × profitability_predictability × management_quality "
            "(each 0–10) — to set a conviction (0–10) and a conviction-weighted target_weight_pct "
            f"of a $10k book (cap any single name at {MAX_SINGLE_NAME_PCT:.0%}). Start small: "
            f"starter_weight_pct ≈ {STARTER_POSITION_PCT:.0%} of target. Define an entry_zone "
            "(low/high) around the buy-below price, pre-plan add_on_levels (validated + price "
            "still lagging), and pre-arm two sell_rules: (a) upside capped vs position → trim & "
            "reallocate; (b) thesis cracks → exit. Only size meaningfully if asymmetry ≥ "
            f"{MIN_ASYMMETRY_RATIO:g}× and the edge passed."
            f"\n\n{HOUSE_VIEW}\n\nMethodology:\n{self.load_methodology()}"
        )
        user = (
            f"Candidate: {candidate.one_line_reason}\n"
            f"Quality: {quality.quality_score}/10  |  Expected IRR: {valuation.expected_irr_5yr}\n"
            f"Buy-below: {valuation.buy_below_price}  |  Current: {valuation.current_price}\n"
            f"Asymmetry: {bear.asymmetry_ratio}  |  Edge passed: {edge.passes}\n\n"
            f"Size this position and define the entry/exit plan."
        )
        return await self._complete(system, user)
