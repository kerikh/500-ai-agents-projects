"""Detect languages, frameworks, and package managers from repo signals."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .filesystem import find_important_files, iter_files

LANGUAGE_BY_SUFFIX = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".swift": "Swift",
    ".vue": "Vue",
    ".svelte": "Svelte",
}

FRAMEWORK_HINTS = {
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "next": "Next.js",
    "react": "React",
    "vue": "Vue",
    "express": "Express",
    "nestjs": "NestJS",
    "spring": "Spring",
    "rails": "Rails",
    "laravel": "Laravel",
    "crewai": "CrewAI",
    "langgraph": "LangGraph",
    "langchain": "LangChain",
    "autogen": "AutoGen",
    "openai": "OpenAI SDK",
    "pytest": "pytest",
    "jest": "Jest",
    "vitest": "Vitest",
}


def detect_stack(repo: Path) -> dict:
    files = iter_files(repo)
    important = find_important_files(repo)

    lang_counts: Counter[str] = Counter()
    for path in files:
        lang = LANGUAGE_BY_SUFFIX.get(path.suffix.lower())
        if lang:
            lang_counts[lang] += 1

    package_managers: list[str] = []
    if "package.json" in important:
        package_managers.append("npm/yarn/pnpm (package.json)")
    if "requirements.txt" in important or "pyproject.toml" in important or "Pipfile" in important:
        package_managers.append("pip/uv/poetry (Python)")
    if "Cargo.toml" in important:
        package_managers.append("cargo")
    if "go.mod" in important:
        package_managers.append("go modules")
    if "Gemfile" in important:
        package_managers.append("bundler")
    if "composer.json" in important:
        package_managers.append("composer")
    if "pom.xml" in important or "build.gradle" in important or "build.gradle.kts" in important:
        package_managers.append("Maven/Gradle")

    frameworks = _detect_frameworks(repo, important)
    runtimes: list[str] = []
    if "Dockerfile" in important or "docker-compose.yml" in important or "docker-compose.yaml" in important:
        runtimes.append("Docker")
    if (repo / ".github" / "workflows").is_dir():
        runtimes.append("GitHub Actions CI")

    languages = [name for name, _ in lang_counts.most_common(6)]
    primary = languages[0] if languages else "Unknown"

    return {
        "primary_language": primary,
        "languages": languages,
        "language_counts": dict(lang_counts.most_common()),
        "package_managers": package_managers,
        "frameworks": frameworks,
        "tooling": runtimes,
        "has_tests": _has_tests(repo, files),
        "has_docs": any(k.startswith("README") or k in {"CONTRIBUTING.md", "CONTRIBUTION.md"} for k in important),
    }


def _detect_frameworks(repo: Path, important: dict[str, Path]) -> list[str]:
    haystacks: list[str] = []
    for key in ("package.json", "requirements.txt", "pyproject.toml", "Pipfile", "Cargo.toml", "go.mod"):
        path = important.get(key)
        if path:
            try:
                haystacks.append(path.read_text(encoding="utf-8", errors="replace").lower())
            except OSError:
                pass

    found: list[str] = []
    joined = "\n".join(haystacks)
    for needle, label in FRAMEWORK_HINTS.items():
        if needle in joined and label not in found:
            found.append(label)
    return found


def _has_tests(repo: Path, files: list[Path]) -> bool:
    for path in files:
        name = path.name.lower()
        parts = {p.lower() for p in path.relative_to(repo).parts}
        if "tests" in parts or "test" in parts or "spec" in parts:
            return True
        if name.startswith("test_") or name.endswith("_test.py") or ".test." in name or ".spec." in name:
            return True
    return False
