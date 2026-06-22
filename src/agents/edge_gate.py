"""Stage 5 — Edge Gate → EdgeVerdict (pass/fail: is this really mispriced?).

Opus-tier. Encodes Oguz's analytical × behavioral edge and time-arbitrage, plus the contrarian
"is the market unduly discounting the future?" check. A pass requires a real, articulable edge.
"""

from __future__ import annotations

from ..schemas import BearCase, Candidate, EdgeVerdict
from .base import Agent
from .data import CompanyData
from .prompts import HOUSE_VIEW


class EdgeGateAgent(Agent[EdgeVerdict]):
    model_tier = "synthesis"  # Opus — the go/no-go judgment
    methodology_files = ["oguz_erkan.md", "citrini.md", "mbi.md"]
    output_schema = EdgeVerdict

    async def run(
        self, candidate: Candidate, data: CompanyData, bear: BearCase
    ) -> EdgeVerdict:
        system = (
            "You are the Edge Gate. Answer one question: is this REALLY mispriced, and do WE have "
            "an edge? Require a concrete analytical_edge (what we understand that the market "
            "doesn't) AND/OR a behavioral_edge (what we tolerate that it won't — patience, "
            "contrarianism). Articulate the time_arbitrage_rationale: why the crowd ignores this "
            "and why it pays off over years (forced selling / panic / euphoria-driven neglect). "
            "If there is no real edge, FAIL it (passes=false). Information speed alone is not edge."
            f"\n\n{HOUSE_VIEW}\n\nMethodology:\n{self.load_methodology()}"
        )
        user = (
            f"Candidate (found by {candidate.scout.value}): {candidate.one_line_reason}\n"
            f"Theme: {candidate.theme}\n"
            f"Bear case: {bear.summary}\n"
            f"Asymmetry ratio: {bear.asymmetry_ratio}\n\n"
            f"{data.to_prompt()}\n\nIs there a real, durable edge here? Pass or fail it."
        )
        return await self._complete(system, user)
