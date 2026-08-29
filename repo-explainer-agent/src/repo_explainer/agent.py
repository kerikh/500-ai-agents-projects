"""Repo Explainer Agent orchestrator.

Pipeline (agent stages):
  Scout → Architect → Teacher → Report

Each stage has a single job so juniors can follow the agent's reasoning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .report import render_report
from .stages.architect import run_architect
from .stages.scout import run_scout
from .stages.teacher import run_teacher


@dataclass
class ExplanationResult:
    scout: dict[str, Any]
    architect: dict[str, Any]
    teacher: dict[str, Any]
    markdown: str
    output_path: Path | None = None
    trace: list[str] = field(default_factory=list)


class RepoExplainerAgent:
    """Multi-stage agent that explains a repository to junior developers."""

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose

    def explain(self, repo_path: str | Path, output: str | Path | None = None) -> ExplanationResult:
        trace: list[str] = []

        trace.append("Scout: mapping folders, stack, and docs…")
        self._log(trace[-1])
        scout = run_scout(repo_path)

        trace.append("Architect: inferring modules, entry points, and flow…")
        self._log(trace[-1])
        architect = run_architect(scout)

        trace.append("Teacher: writing junior-friendly onboarding material…")
        self._log(trace[-1])
        teacher = run_teacher(scout, architect)

        trace.append("Report: assembling markdown guide…")
        self._log(trace[-1])
        markdown = render_report(scout, architect, teacher)

        output_path = None
        if output is not None:
            output_path = Path(output).expanduser().resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
            trace.append(f"Wrote guide to {output_path}")
            self._log(trace[-1])

        return ExplanationResult(
            scout=scout,
            architect=architect,
            teacher=teacher,
            markdown=markdown,
            output_path=output_path,
            trace=trace,
        )

    def _log(self, message: str) -> None:
        if self.verbose:
            print(f"[repo-explainer] {message}")
