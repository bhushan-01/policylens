"""Tiny LLM wrapper shared by the evidence-pack pipeline (OpenRouter or Anthropic)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from policylens.config import load_env


def available() -> bool:
    env = load_env()
    return bool(env.get("OPENROUTER_API_KEY") or env.get("ANTHROPIC_API_KEY"))


def complete(system: str, user: str, max_tokens: int = 1500) -> str:
    env = load_env()
    if env.get("OPENROUTER_API_KEY"):
        from openai import OpenAI

        client = OpenAI(api_key=env["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1")
        resp = client.chat.completions.create(
            model=env.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4.5"),
            max_tokens=max_tokens,
            temperature=0,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        return resp.choices[0].message.content or ""
    if env.get("ANTHROPIC_API_KEY"):
        from anthropic import Anthropic

        msg = Anthropic(api_key=env["ANTHROPIC_API_KEY"]).messages.create(
            model=env.get("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
            max_tokens=max_tokens,
            temperature=0,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text
    raise RuntimeError("missing_api_key")


def complete_json(system: str, user: str, max_tokens: int = 1500) -> dict:
    """Ask for JSON, tolerate code fences / chatter, raise ValueError if unparseable."""
    raw = complete(system, user, max_tokens)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        raise ValueError(f"no JSON in model output: {raw[:200]!r}")
    return json.loads(m.group(0))
