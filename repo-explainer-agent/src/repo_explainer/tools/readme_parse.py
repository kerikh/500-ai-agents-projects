"""Lightweight README / manifest parsing for onboarding signals."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .filesystem import find_important_files, read_text_file


def gather_docs(repo: Path) -> dict:
    important = find_important_files(repo)
    readme_path = important.get("README")
    readme_text = read_text_file(readme_path) if readme_path else ""

    summary = _first_paragraph(readme_text)
    headings = _markdown_headings(readme_text)
    scripts = _package_scripts(important.get("package.json"))
    python_project = _python_project_name(important)

    return {
        "readme_path": str(readme_path.relative_to(repo)) if readme_path else None,
        "summary": summary,
        "headings": headings[:12],
        "quick_start_hints": _quick_start_hints(readme_text, scripts, important),
        "package_scripts": scripts,
        "python_project": python_project,
        "important_files": {k: str(v.relative_to(repo)) for k, v in important.items() if k != "README"},
        "readme_excerpt": readme_text[:2500] if readme_text else "",
    }


def _first_paragraph(text: str) -> str:
    if not text:
        return "No README found. The agent will lean on file structure and manifests instead."
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if lines:
                break
            continue
        if line.startswith("#"):
            continue
        if line.startswith("![") or line.startswith("[!["):
            continue
        lines.append(line)
        if len(" ".join(lines)) > 280:
            break
    paragraph = " ".join(lines).strip()
    return paragraph or "README exists but has little prose at the top."


def _markdown_headings(text: str) -> list[str]:
    headings = []
    for line in text.splitlines():
        match = re.match(r"^(#{1,3})\s+(.+)$", line.strip())
        if match:
            headings.append(match.group(2).strip())
    return headings


def _package_scripts(package_json: Path | None) -> dict[str, str]:
    if not package_json:
        return {}
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    scripts = data.get("scripts") or {}
    return {str(k): str(v) for k, v in scripts.items()}


def _python_project_name(important: dict[str, Path]) -> str | None:
    pyproject = important.get("pyproject.toml")
    if not pyproject:
        return None
    text = read_text_file(pyproject, max_chars=4000)
    match = re.search(r'(?m)^name\s*=\s*["\']([^"\']+)["\']', text)
    return match.group(1) if match else None


def _quick_start_hints(readme: str, scripts: dict[str, str], important: dict[str, Path]) -> list[str]:
    hints: list[str] = []
    lower = readme.lower()
    if "pip install" in lower:
        hints.append("README mentions `pip install` — start there for Python setup.")
    if "npm install" in lower or "pnpm install" in lower or "yarn" in lower:
        hints.append("README mentions a Node package manager install step.")
    if "requirements.txt" in important:
        hints.append("Install Python deps with: `pip install -r requirements.txt`")
    if "package.json" in important:
        hints.append("Install Node deps with: `npm install` (or yarn/pnpm if the project uses them)")
    for name in ("dev", "start", "test", "build"):
        if name in scripts:
            hints.append(f"npm script `{name}`: `{scripts[name]}`")
    if "Dockerfile" in important:
        hints.append("A Dockerfile is present — you may be able to run the app in a container.")
    if not hints:
        hints.append("Look for README install/run sections, then try the project's test command.")
    return hints[:8]
