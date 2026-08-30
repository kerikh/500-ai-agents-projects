"""Optional LLM enrichment with a deterministic heuristic fallback.

The agent always works offline. When configured via a `.env` file (see
`.env.example`) and the `openai` package is installed, the Teacher stage can
polish explanations with an OpenAI-compatible API — including local servers
such as Ollama, LM Studio, or vLLM.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Project root: repo-explainer-agent/
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_LOADED = False


@dataclass(frozen=True)
class LLMConfig:
    """Resolved LLM settings (secrets loaded from `.env`)."""

    model: str
    base_url: str | None
    api_key: str | None
    is_local: bool

    @property
    def display_target(self) -> str:
        if self.base_url:
            return self.base_url
        return "https://api.openai.com/v1 (default)"


def _find_env_file() -> Path | None:
    candidates = [
        _PROJECT_ROOT / ".env",
        Path.cwd() / ".env",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def load_env(force: bool = False) -> Path | None:
    """Load secrets from the gitignored `.env` file once per process."""
    global _ENV_LOADED
    if _ENV_LOADED and not force:
        return _find_env_file()

    env_path = _find_env_file()
    try:
        from dotenv import load_dotenv
    except ImportError:
        _ENV_LOADED = True
        return env_path

    if env_path:
        load_dotenv(env_path, override=False)
    else:
        # Still allow a `.env` next to the cwd when running from elsewhere.
        load_dotenv(override=False)

    _ENV_LOADED = True
    return env_path


def get_llm_config() -> LLMConfig | None:
    """Return LLM config when enrichment is possible, else None."""
    load_env()

    base_url = _first_env(
        "REPO_EXPLAINER_BASE_URL",
        "OPENAI_BASE_URL",
    )
    api_key = _first_env(
        "REPO_EXPLAINER_API_KEY",
        "OPENAI_API_KEY",
    )
    model = _first_env(
        "REPO_EXPLAINER_MODEL",
        "OPENAI_MODEL",
        default="gpt-4o-mini",
    )

    # Local OpenAI-compatible servers often ignore the key; use a harmless placeholder.
    is_local = bool(base_url)
    if is_local and not api_key:
        api_key = "local"

    # Cloud OpenAI needs a real API key; local servers need base_url + model.
    if not api_key and not base_url:
        return None
    if not model:
        return None

    return LLMConfig(
        model=model,
        base_url=base_url,
        api_key=api_key,
        is_local=is_local,
    )


def llm_available() -> bool:
    if get_llm_config() is None:
        return False
    try:
        import openai  # noqa: F401
    except ImportError:
        return False
    return True


def build_openai_client():
    """Construct an OpenAI client from `.env` settings."""
    from openai import OpenAI

    config = get_llm_config()
    if config is None:
        raise RuntimeError("LLM is not configured. Copy .env.example to .env and set values.")

    kwargs: dict[str, str] = {}
    if config.api_key:
        kwargs["api_key"] = config.api_key
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return OpenAI(**kwargs), config


def enrich_with_llm(system: str, user: str, model: str | None = None) -> str | None:
    """Return LLM text or None if unavailable / on failure."""
    if not llm_available():
        return None
    try:
        client, config = build_openai_client()
        response = client.chat.completions.create(
            model=model or config.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=float(os.getenv("REPO_EXPLAINER_TEMPERATURE", "0.2")),
        )
        content = response.choices[0].message.content
        return content.strip() if content else None
    except Exception:
        return None


def dump_context(payload: dict[str, Any], limit: int = 10_000) -> str:
    text = json.dumps(payload, indent=2, default=str)
    return text[:limit]


def _first_env(*keys: str, default: str | None = None) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value is not None and value.strip():
            return value.strip()
    return default
