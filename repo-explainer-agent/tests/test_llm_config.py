"""Tests for .env-driven LLM configuration."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import repo_explainer.llm as llm


@pytest.fixture(autouse=True)
def reset_env_loader(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("REPO_EXPLAINER_API_KEY", raising=False)
    monkeypatch.delenv("REPO_EXPLAINER_BASE_URL", raising=False)
    monkeypatch.delenv("REPO_EXPLAINER_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    llm._ENV_LOADED = False


def test_get_llm_config_cloud_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("REPO_EXPLAINER_MODEL", "gpt-4o-mini")

    config = llm.get_llm_config()
    assert config is not None
    assert config.api_key == "sk-test-key"
    assert config.base_url is None
    assert config.model == "gpt-4o-mini"
    assert config.is_local is False


def test_get_llm_config_local_openai_compatible(monkeypatch):
    monkeypatch.setenv("REPO_EXPLAINER_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("REPO_EXPLAINER_MODEL", "llama3.2")

    config = llm.get_llm_config()
    assert config is not None
    assert config.base_url == "http://localhost:11434/v1"
    assert config.api_key == "local"
    assert config.model == "llama3.2"
    assert config.is_local is True


def test_load_env_reads_gitignored_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "REPO_EXPLAINER_BASE_URL=http://127.0.0.1:1234/v1\n"
        "REPO_EXPLAINER_MODEL=mistral\n"
        "REPO_EXPLAINER_API_KEY=secret-from-file\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(llm, "_PROJECT_ROOT", tmp_path)
    llm._ENV_LOADED = False

    loaded = llm.load_env(force=True)
    assert loaded == env_file

    config = llm.get_llm_config()
    assert config is not None
    assert config.base_url == "http://127.0.0.1:1234/v1"
    assert config.model == "mistral"
    assert config.api_key == "secret-from-file"


def test_llm_available_false_without_config(monkeypatch):
    monkeypatch.setitem(sys.modules, "openai", object())
    assert llm.get_llm_config() is None
    assert llm.llm_available() is False


def test_build_openai_client_passes_base_url(monkeypatch):
    monkeypatch.setenv("REPO_EXPLAINER_BASE_URL", "http://localhost:8080/v1")
    monkeypatch.setenv("REPO_EXPLAINER_MODEL", "qwen2.5")

    captured: dict = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setitem(sys.modules, "openai", type("m", (), {"OpenAI": FakeOpenAI}))

    client, config = llm.build_openai_client()
    assert client is not None
    assert captured["base_url"] == "http://localhost:8080/v1"
    assert captured["api_key"] == "local"
    assert config.model == "qwen2.5"
