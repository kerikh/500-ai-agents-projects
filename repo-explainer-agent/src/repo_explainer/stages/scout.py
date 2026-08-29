"""Scout stage — map the repository landscape."""

from __future__ import annotations

from pathlib import Path

from ..tools.filesystem import (
    relative_tree,
    resolve_repo,
    sample_source_files,
    top_level_entries,
)
from ..tools.readme_parse import gather_docs
from ..tools.stack_detect import detect_stack


def run_scout(repo_path: str | Path) -> dict:
    repo = resolve_repo(repo_path)
    stack = detect_stack(repo)
    docs = gather_docs(repo)
    samples = sample_source_files(repo)
    return {
        "repo_path": str(repo),
        "repo_name": repo.name,
        "top_level": top_level_entries(repo),
        "tree": relative_tree(repo),
        "stack": stack,
        "docs": docs,
        "sample_files": [str(p.relative_to(repo)) for p in samples],
    }
