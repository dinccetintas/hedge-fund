"""Minimal structured-output LLM helper (Anthropic or OpenRouter).

A thin wrapper that asks a model to return JSON matching a pydantic schema and parses it.
Used first by the qualitative scouts (breadth tier) and reused by the Stage 2–7 agents.
Cost-aware: callers pass the model id (cheap for breadth, strong for depth) from `settings`.

Two providers, selected by `settings.llm_provider`:
  - "anthropic" (default): the Anthropic SDK. Respects `ANTHROPIC_BASE_URL` automatically.
  - "openrouter": the OpenAI-compatible OpenRouter gateway (https://openrouter.ai/docs/quickstart),
    authenticated with `Authorization: Bearer <OPENROUTER_API_KEY>`. Lets us route to cheap
    open models (DeepSeek, GLM, …). NOTE: this path needs the `Authorization` header to reach
    OpenRouter — some egress proxies strip it, in which case use the "anthropic" provider instead.
"""

from __future__ import annotations

import json
import logging
from typing import TypeVar

import httpx
from anthropic import AsyncAnthropic
from pydantic import BaseModel

from .settings import settings

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_client: AsyncAnthropic | None = None
_or_client: httpx.AsyncClient | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key or None)
    return _client


def _get_openrouter_client() -> httpx.AsyncClient:
    global _or_client
    if _or_client is None:
        _or_client = httpx.AsyncClient(
            base_url=settings.openrouter_base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
                # Optional OpenRouter attribution headers (https://openrouter.ai/docs/quickstart).
                "HTTP-Referer": "https://github.com/dinccetintas/hedge-fund",
                "X-Title": "Project Bear Stearns",
            },
            timeout=60.0,
        )
    return _or_client


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
    tolerate models that wrap it in a ```json fence. Routes to Anthropic or OpenRouter based on
    `settings.llm_provider`.
    """
    sys = (
        f"{system}\n\nReturn ONLY a JSON object matching this schema (no prose, no markdown):\n"
        f"{json.dumps(schema.model_json_schema())}"
    )
    if settings.llm_provider == "openrouter":
        text = await _call_openrouter(model=model, system=sys, user=user, max_tokens=max_tokens)
    else:
        text = await _call_anthropic(model=model, system=sys, user=user, max_tokens=max_tokens)
    return schema.model_validate_json(_extract_json(text))


async def _call_anthropic(*, model: str, system: str, user: str, max_tokens: int) -> str:
    client = _get_client()
    resp = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in resp.content if block.type == "text").strip()


async def _call_openrouter(*, model: str, system: str, user: str, max_tokens: int) -> str:
    """OpenAI-compatible chat-completions call to OpenRouter; returns the assistant text."""
    client = _get_openrouter_client()
    resp = await client.post(
        "/chat/completions",
        json={
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def _strip_fence(text: str) -> str:
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.removeprefix("json\n").removeprefix("json")
    return text.strip()


def _extract_json(text: str) -> str:
    """Return the first balanced top-level JSON object, tolerating leading/trailing prose.

    Smaller/cheaper models sometimes wrap the object in a ```fence``` or trail it with a sentence
    of commentary; a plain `model_validate_json` then fails on the extra characters. We scan from
    the first `{` to its matching `}`, ignoring braces inside strings, and validate just that slice.
    """
    text = _strip_fence(text)
    start = text.find("{")
    if start == -1:
        return text  # let pydantic raise a clear error on the original payload
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return text[start:]  # unbalanced (e.g. truncated) — surface the original parse error
