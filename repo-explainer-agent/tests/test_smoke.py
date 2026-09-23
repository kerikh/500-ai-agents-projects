"""Smoke and unit tests for Repo Explainer Agent."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from repo_explainer import RepoExplainerAgent
from repo_explainer.stages.scout import run_scout
from repo_explainer.tools.stack_detect import detect_stack


FIXTURE = ROOT / "fixtures" / "sample_app"


def test_scout_finds_python_sample():
    scout = run_scout(FIXTURE)
    assert scout["repo_name"] == "sample_app"
    assert "README.md" in " ".join(scout["top_level"]) or scout["docs"]["readme_path"]
    assert scout["stack"]["primary_language"] == "Python"


def test_stack_detects_fastapi_hint():
    stack = detect_stack(FIXTURE)
    assert "FastAPI" in stack["frameworks"]
    assert stack["has_tests"] is True


def test_agent_writes_onboarding_guide(tmp_path: Path):
    output = tmp_path / "ONBOARDING.md"
    agent = RepoExplainerAgent(verbose=False)
    result = agent.explain(FIXTURE, output=output)

    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "Junior Onboarding Guide" in text
    assert "sample_app" in text
    assert "Learning path" in text or "Suggested learning path" in text
    assert "Glossary" in text
    assert result.teacher["used_llm"] is False
    assert len(result.trace) >= 4


def test_missing_repo_raises():
    agent = RepoExplainerAgent(verbose=False)
    with pytest.raises(FileNotFoundError):
        agent.explain("/tmp/definitely-missing-repo-explainer-xyz")
