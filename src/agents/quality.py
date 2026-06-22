"""Stage 2 — Business Quality Analysis → QualityAssessment (Quality Score /10).

Encodes Oguz's 5-step moat analysis (scored on strength AND direction), Slegers' Quality Score,
MBI's moderate-growth preference, App Economy's unit economics, and Giuliano's reinvestment moat.
"""

from __future__ import annotations

from ..schemas import Candidate, QualityAssessment
from .base import Agent
from .data import CompanyData
from .prompts import HOUSE_VIEW


class QualityAgent(Agent[QualityAssessment]):
    model_tier = "analysis"
    methodology_files = [
        "oguz_erkan.md", "compounding_quality_slegers.md", "mbi.md",
        "app_economy.md", "from_0_to_1_giuliano.md",
    ]
    output_schema = QualityAssessment

    async def run(self, candidate: Candidate, data: CompanyData) -> QualityAssessment:
        system = (
            "You are the Moat / Quality analyst. Produce a Quality Score out of 10 and a 5-step "
            "moat analysis (network_effects, switching_costs, cost_advantage, intangibles_brand, "
            "scale), each scored 0–10 on strength with a direction (widening | stable | eroding). "
            "Assess ROIC and its sustainability, the reinvestment runway (returns on INCREMENTAL "
            "capital), growth quality (prefer moderate-durable), unit economics (Rule of 40, NRR "
            "for software, SBC/dilution), and management/capital allocation. Attach dated evidence."
            f"\n\n{HOUSE_VIEW}\n\nMethodology:\n{self.load_methodology()}"
        )
        user = (
            f"Candidate (found by {candidate.scout.value}): {candidate.one_line_reason}\n\n"
            f"{data.to_prompt()}\n\nScore this business's quality."
        )
        return await self._complete(system, user)
