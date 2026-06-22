"""Common interface for all Stage-1 scouts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from ..schemas import Candidate, ScoutType


class Scout(ABC):
    """A single idea-sourcing pattern.

    Implementations combine cheap FMP screens (breadth) with optional Bigdata.com context
    (the unstructured edge), and may use the screening-tier model for triage. They must only
    use data dated <= `as_of` (no look-ahead).
    """

    scout_type: ScoutType

    @abstractmethod
    async def source(self, *, as_of: date, limit: int = 25) -> list[Candidate]:
        """Return up to `limit` candidates this scout flags as of `as_of`."""
        ...
