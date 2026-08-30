"""Filesystem helpers for safely inspecting a repository."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

# Common noise to skip when mapping a repo for juniors.
SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".next",
    ".turbo",
    "coverage",
    ".idea",
    ".vscode",
    "target",
    "vendor",
}

SKIP_FILE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".so",
    ".dll",
    ".exe",
    ".bin",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".woff",
    ".woff2",
    ".mp4",
    ".mp3",
}

TEXT_LIKE_SUFFIXES = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".rb",
    ".php",
    ".cs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".swift",
    ".md",
    ".rst",
    ".txt",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".env.example",
    ".sh",
    ".bash",
    ".zsh",
    ".sql",
    ".html",
    ".css",
    ".scss",
    ".vue",
    ".svelte",
    ".dockerfile",
}

IMPORTANT_ROOT_FILES = (
    "README.md",
    "README.rst",
    "README.txt",
    "readme.md",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Gemfile",
    "composer.json",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "LICENSE",
    "LICENSE.md",
    "CONTRIBUTING.md",
    "CONTRIBUTION.md",
    ".env.example",
    "tsconfig.json",
    "setup.py",
    "setup.cfg",
)


def resolve_repo(path: str | Path) -> Path:
    repo = Path(path).expanduser().resolve()
    if not repo.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo}")
    if not repo.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {repo}")
    return repo


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES or name.startswith(".")


def iter_files(repo: Path, max_files: int = 400) -> list[Path]:
    """Walk the repo and return a capped list of file paths."""
    files: list[Path] = []
    for root, dirs, filenames in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if not should_skip_dir(d))
        for name in sorted(filenames):
            path = Path(root) / name
            if path.suffix.lower() in SKIP_FILE_SUFFIXES:
                continue
            files.append(path)
            if len(files) >= max_files:
                return files
    return files


def relative_tree(repo: Path, max_depth: int = 3, max_entries: int = 120) -> str:
    """Build a compact indented tree string for reports."""
    lines: list[str] = [repo.name + "/"]
    count = 0

    def walk(current: Path, prefix: str, depth: int) -> None:
        nonlocal count
        if depth > max_depth or count >= max_entries:
            return
        try:
            children = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return
        visible = [
            child
            for child in children
            if not (child.is_dir() and should_skip_dir(child.name))
            and child.suffix.lower() not in SKIP_FILE_SUFFIXES
        ]
        for index, child in enumerate(visible):
            if count >= max_entries:
                lines.append(prefix + "…")
                return
            last = index == len(visible) - 1
            branch = "└── " if last else "├── "
            suffix = "/" if child.is_dir() else ""
            lines.append(f"{prefix}{branch}{child.name}{suffix}")
            count += 1
            if child.is_dir():
                extension = "    " if last else "│   "
                walk(child, prefix + extension, depth + 1)

    walk(repo, "", 1)
    return "\n".join(lines)


def read_text_file(path: Path, max_chars: int = 12_000) -> str:
    """Read a text file with a size guard; return empty string on failure."""
    try:
        data = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if len(data) > max_chars:
        return data[:max_chars] + "\n\n… [truncated for brevity]"
    return data


def find_important_files(repo: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for name in IMPORTANT_ROOT_FILES:
        candidate = repo / name
        if candidate.is_file():
            found[name] = candidate
    # Prefer a canonical README key for downstream stages.
    for key in ("README.md", "README.rst", "README.txt", "readme.md"):
        if key in found:
            found["README"] = found[key]
            break
    return found


def top_level_entries(repo: Path) -> list[str]:
    try:
        return sorted(
            p.name + ("/" if p.is_dir() else "")
            for p in repo.iterdir()
            if not (p.is_dir() and should_skip_dir(p.name))
        )
    except PermissionError:
        return []


def sample_source_files(repo: Path, limit: int = 8) -> list[Path]:
    """Pick a few likely source files for architecture hints."""
    preferred_dirs = {"src", "app", "lib", "backend", "frontend", "api", "pkg", "cmd"}
    files = iter_files(repo, max_files=500)
    scored: list[tuple[int, Path]] = []
    for path in files:
        if path.suffix.lower() not in TEXT_LIKE_SUFFIXES:
            continue
        if path.name.lower().startswith("readme"):
            continue
        rel = path.relative_to(repo)
        parts = {p.lower() for p in rel.parts[:-1]}
        score = 0
        if parts & preferred_dirs:
            score += 5
        if path.suffix.lower() in {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"}:
            score += 2
        if path.name in {"main.py", "app.py", "index.ts", "index.js", "main.go", "main.rs"}:
            score += 4
        if "test" in path.name.lower() or "spec" in path.name.lower():
            score -= 3
        scored.append((score, path))
    scored.sort(key=lambda item: (-item[0], str(item[1])))
    return [path for _, path in scored[:limit]]
