"""Stage 3 — Valuation → Valuation (expected 5-yr IRR + buy-below price).

Opus-tier depth. Encodes MBI's reverse-DCF "what must be true" + bond-yield-anchored IRR hurdle,
Oguz/Graham margin of safety, App Economy stage-based multiple selection, and Wolf's inverse-DCF.
"""

from __future__ import annotations

from ..config import IRR_HURDLE_FLOOR, MIN_MARGIN_OF_SAFETY
from ..schemas import Candidate, QualityAssessment, Valuation
from .base import Agent
from .data import CompanyData
from .prompts import HOUSE_VIEW


class ValuationAgent(Agent[Valuation]):
    model_tier = "synthesis"  # Opus — valuation is depth work
    methodology_files = [
        "mbi.md", "app_economy.md", "wolf_of_harcourt.md", "best_anchor_leandro.md",
    ]
    output_schema = Valuation

    async def run(
        self, candidate: Candidate, data: CompanyData, quality: QualityAssessment
    ) -> Valuation:
        system = (
            "You are the Valuation analyst. Run a REVERSE DCF: back out the growth/returns the "
            "current price implies (reverse_dcf_implied_growth), estimate what the business can "
            "realistically deliver (achievable_growth_estimate), and judge feasibility. Report an "
            f"expected 5-yr IRR (hurdle floor ~{IRR_HURDLE_FLOOR:.0%}; equity must beat its debt), "
            "a margin of safety, a stage-appropriate multiple_basis (EV/Revenue or "
            "EV/Gross-Profit for scalers; EV/FCF or EV/EBITDA for profitable compounders), and a "
            f"concrete buy_below_price delivering ≥{MIN_MARGIN_OF_SAFETY:.0%} margin of safety. "
            "Attach dated evidence."
            f"\n\n{HOUSE_VIEW}\n\nMethodology:\n{self.load_methodology()}"
        )
        user = (
            f"Candidate: {candidate.one_line_reason}\n"
            f"Quality Score: {quality.quality_score}/10; ROIC: {quality.roic}\n\n"
            f"{data.to_prompt()}\n\nValue this business and give a buy-below price."
        )
        result = await self._complete(system, user)
        # current_price is known data — trust the price feed over the model's echo of it.
        if data.current_price is not None:
            result.current_price = data.current_price
        return result
