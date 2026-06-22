"""Common scaffolding for analysis agents: prompt assembly + structured Claude calls.

Each agent loads its methodology context, passes the candidate's dated data packet, and parses the
model's reply into the agent's pydantic schema via `src.llm.structured`. Centralizing it here keeps
the cost-routing (Haiku/Sonnet/Opus) and structured-output guardrails in one place. Tests mock
`src.llm.structured`, so agents are exercised deterministically without network.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

from .. import llm
from ..settings import settings

METHODOLOGY_DIR = Path(__file__).resolve().parents[2] / "methodology"

T = TypeVar("T", bound=BaseModel)

_TIER_MODELS = {
    "screen": "model_screen",        # Haiku — breadth
    "analysis": "model_analysis",    # Sonnet — mid-depth (Stages 2, 4, 6)
    "synthesis": "model_synthesis",  # Opus — depth (Stages 3, 5)
}


class Agent(ABC, Generic[T]):
    """An analysis stage backed by a single structured Claude call."""

    #: model tier — "analysis" (Sonnet) or "synthesis" (Opus); see src.settings
    model_tier: str = "analysis"
    #: methodology files to load into the system prompt, e.g. ["oguz_erkan.md", "mbi.md"]
    methodology_files: list[str] = []
    output_schema: type[T]
    max_tokens: int = 2000

    @property
    def model_id(self) -> str:
        return getattr(settings, _TIER_MODELS.get(self.model_tier, "model_analysis"))

    def load_methodology(self) -> str:
        """Concatenate this agent's methodology context (the masters' techniques it encodes)."""
        parts: list[str] = []
        for name in self.methodology_files:
            path = METHODOLOGY_DIR / name
            if path.exists():
                parts.append(path.read_text(encoding="utf-8"))
        return "\n\n---\n\n".join(parts)

    async def _complete(self, system: str, user: str) -> T:
        """Run the structured call with this agent's model tier + output schema."""
        return await llm.structured(
            model=self.model_id,
            system=system,
            user=user,
            schema=self.output_schema,
            max_tokens=self.max_tokens,
        )

    @abstractmethod
    async def run(self, *args, **kwargs) -> T:
        """Execute the stage and return its structured result."""
        ...

