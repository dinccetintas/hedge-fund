"""Stage 4 — Red Team / Downside → BearCase (bear case + invalidation markers).

The Red Team's job is to KILL the idea. Encodes the forensic short-seller red-flag scan, Morris's
pre-set invalidation markers (anti-thesis-drift), and Walker's downside-first skepticism.
"""

from __future__ import annotations

from ..config import RECEIVABLES_TO_SALES_MAX
from ..schemas import BearCase, Candidate, QualityAssessment, Valuation
from .base import Agent
from .data import CompanyData
from .prompts import HOUSE_VIEW


class RedTeamAgent(Agent[BearCase]):
    model_tier = "analysis"
    methodology_files = ["forensic_short_flags.md", "tsoh_morris.md", "yet_another_value_walker.md"]
    output_schema = BearCase
    max_tokens = 2500

    async def run(
        self,
        candidate: Candidate,
        data: CompanyData,
        quality: QualityAssessment,
        valuation: Valuation,
    ) -> BearCase:
        system = (
            "You are the Red Team. Try to KILL this idea. Run the forensic red-flag scan "
            f"(receivables >{RECEIVABLES_TO_SALES_MAX:.0%} of sales, inventory growing faster than "
            "sales, peer-anomalous margins, SBC/dilution, leverage/refinancing risk, cash flow "
            "diverging from earnings, governance flags) — return each as a RedFlag with tripped + "
            "detail. State the bear case, the explicit thesis_killers, a downside_floor_price, and "
            "pre-set invalidation_markers (future data points that would prove the thesis wrong). "
            "Compute the asymmetry_ratio (upside vs downside) from buy-below and downside floor. "
            "Attach dated evidence."
            f"\n\n{HOUSE_VIEW}\n\nMethodology:\n{self.load_methodology()}"
        )
        user = (
            f"Candidate: {candidate.one_line_reason}\n"
            f"Quality: {quality.quality_score}/10  |  Buy-below: {valuation.buy_below_price}  |  "
            f"Current price: {valuation.current_price}\n\n"
            f"{data.to_prompt()}\n\nDismantle this thesis."
        )
        return await self._complete(system, user)
