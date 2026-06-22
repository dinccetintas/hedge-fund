"""Common scaffolding for analysis agents: prompt assembly + structured Claude calls.

Phase 2 implements `run()` — an Anthropic call that loads the agent's methodology context, passes
the relevant evidence, and parses the response into the agent's pydantic schema. Centralizing it
here keeps the no-look-ahead and cost-routing guardrails in one place.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

METHODOLOGY_DIR = Path(__file__).resolve().parents[2] / "methodology"

T = TypeVar("T", bound=BaseModel)


class Agent(ABC, Generic[T]):
    """An analysis stage backed by a single structured Claude call."""

    #: model tier — "analysis" (Sonnet) or "synthesis" (Opus); see src.settings
    model_tier: str = "analysis"
    #: methodology files to load into the system prompt, e.g. ["oguz_erkan.md", "mbi.md"]
    methodology_files: list[str] = []
    output_schema: type[T]

    def load_methodology(self) -> str:
        """Concatenate this agent's methodology context (the masters' techniques it encodes)."""
        parts: list[str] = []
        for name in self.methodology_files:
            path = METHODOLOGY_DIR / name
            if path.exists():
                parts.append(path.read_text(encoding="utf-8"))
        return "\n\n---\n\n".join(parts)

    @abstractmethod
    async def run(self, *args, **kwargs) -> T:
        """Execute the stage and return its structured result. Implemented in Phase 2."""
        ...
