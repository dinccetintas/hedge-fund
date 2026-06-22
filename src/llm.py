"""Minimal structured-output LLM helper (Anthropic).

A thin wrapper that asks a Claude model to return JSON matching a pydantic schema and parses it.
Used first by the qualitative scouts (Haiku tier) and reused by the Stage 2–7 agents in Phase 2.
Cost-aware: callers pass the model id (Haiku for breadth, Opus for depth) from `settings`.

Respects `ANTHROPIC_BASE_URL` automatically via the SDK, so it works behind the harness proxy.
"""

from __future__ import annotations

import json
import logging
from typing import TypeVar

from anthropic import AsyncAnthropic
from pydantic import BaseModel

from .settings import settings

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key or None)
    return _client


async def structured(
    *,
    model: str,
    system: str,
    user: str,
    schema: type[T],
    max_tokens: int = 2000,
) -> T:
    """Call `model` and parse its reply into `schema`.

    The schema's JSON shape is appended to the system prompt; we instruct JSON-only output and
    tolerate models that wrap it in a ```json fence.
    """
    client = _get_client()
    sys = (
        f"{system}\n\nReturn ONLY a JSON object matching this schema (no prose, no markdown):\n"
        f"{json.dumps(schema.model_json_schema())}"
    )
    resp = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=sys,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text").strip()
    return schema.model_validate_json(_strip_fence(text))


def _strip_fence(text: str) -> str:
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.removeprefix("json\n").removeprefix("json")
    return text.strip()
