#!/usr/bin/env python3
"""Run the Repo Explainer Agent on a local repository path.

Examples:
  python run_demo.py
  python run_demo.py --repo ./fixtures/sample_app
  python run_demo.py --repo /path/to/any/repo --output onboarding.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from repo_explainer import RepoExplainerAgent  # noqa: E402
from repo_explainer.llm import get_llm_config, llm_available  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Break down a repository into a junior-friendly onboarding guide."
    )
    parser.add_argument(
        "--repo",
        default=str(ROOT / "fixtures" / "sample_app"),
        help="Path to the repository to explain (default: bundled sample app).",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "examples" / "sample_output.md"),
        help="Where to write the markdown guide.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stage progress logs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    agent = RepoExplainerAgent(verbose=not args.quiet)
    result = agent.explain(args.repo, output=args.output)

    print()
    print("=" * 72)
    print(result.markdown)
    print("=" * 72)
    print()
    print(f"Saved: {result.output_path}")
    if result.teacher.get("used_llm"):
        print("LLM enrichment: yes")
    elif llm_available():
        config = get_llm_config()
        target = config.display_target if config else "configured endpoint"
        print(f"LLM enrichment: no (configured for {target}, but call failed or returned empty)")
    else:
        print("LLM enrichment: no (offline mode — copy .env.example to .env to enable)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
