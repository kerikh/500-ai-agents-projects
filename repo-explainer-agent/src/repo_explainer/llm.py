"""Optional LLM enrichment with a deterministic heuristic fallback.

The agent always works offline. When OPENAI_API_KEY is set and the `openai`
package is installed, the Teacher stage can polish explanations with an LLM.
"""

from __future__ import annotations

import json
import os
from typing import Any


def llm_available() -> bool:
    if not os.getenv("OPENAI_API_KEY"):
        return False
    try:
        import openai  # noqa: F401
    except ImportError:
        return False
    return True


def enrich_with_llm(system: str, user: str, model: str | None = None) -> str | None:
    """Return LLM text or None if unavailable / on failure."""
    if not llm_available():
        return None
    try:
        from openai import OpenAI

        client = OpenAI()
        response = client.chat.completions.create(
            model=model or os.getenv("REPO_EXPLAINER_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return content.strip() if content else None
    except Exception:
        return None


def dump_context(payload: dict[str, Any], limit: int = 10_000) -> str:
    text = json.dumps(payload, indent=2, default=str)
    return text[:limit]
