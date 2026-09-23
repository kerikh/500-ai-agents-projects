"""Architect stage — infer modules, entry points, and how pieces connect."""

from __future__ import annotations

from pathlib import Path

from ..tools.filesystem import read_text_file, resolve_repo


ROLE_HINTS = {
    "src": "Application source code — usually the heart of the project.",
    "app": "Application package or Next.js/Rails-style app directory.",
    "lib": "Shared libraries and helpers used by the rest of the app.",
    "api": "HTTP/API layer — endpoints the outside world talks to.",
    "backend": "Server-side logic, often separate from the UI.",
    "frontend": "User interface code (web or desktop client).",
    "web": "Web-facing code or site content.",
    "cmd": "CLI entry points (common in Go projects).",
    "pkg": "Reusable packages (common in Go projects).",
    "tests": "Automated tests — great place to learn expected behavior.",
    "test": "Automated tests — great place to learn expected behavior.",
    "docs": "Human documentation beyond the README.",
    "scripts": "Utility scripts for setup, migration, or ops tasks.",
    "examples": "Example usage — often the fastest way to learn the API.",
    "fixtures": "Sample data used by demos or tests.",
    ".github": "CI workflows and GitHub project automation.",
}


def run_architect(scout: dict) -> dict:
    repo = resolve_repo(scout["repo_path"])
    modules = []
    for entry in scout.get("top_level", []):
        name = entry.rstrip("/")
        if entry.endswith("/"):
            modules.append(
                {
                    "name": name,
                    "kind": "directory",
                    "role": ROLE_HINTS.get(name.lower(), "Project folder — open it and read a couple of files."),
                }
            )
        else:
            modules.append(
                {
                    "name": name,
                    "kind": "file",
                    "role": _file_role(name),
                }
            )

    entry_points = _guess_entry_points(scout)
    file_sketches = []
    for rel in scout.get("sample_files", [])[:6]:
        path = repo / rel
        text = read_text_file(path, max_chars=2500)
        file_sketches.append(
            {
                "path": rel,
                "sketch": _sketch_file(rel, text),
            }
        )

    mental_model = _mental_model(scout, modules, entry_points)
    return {
        "modules": modules,
        "entry_points": entry_points,
        "file_sketches": file_sketches,
        "mental_model": mental_model,
        "data_flow": _data_flow(scout, entry_points),
    }


def _file_role(name: str) -> str:
    lower = name.lower()
    mapping = {
        "readme.md": "Start here — project purpose and setup.",
        "requirements.txt": "Python dependencies to install.",
        "pyproject.toml": "Python project metadata and tooling config.",
        "package.json": "Node project metadata, scripts, and dependencies.",
        "dockerfile": "How to build/run the app in a container.",
        "makefile": "Common developer commands.",
        "license": "How you may use and share the code.",
        "metadata.yaml": "Catalog metadata for this agent project.",
        "metadata.json": "Catalog metadata for this agent project.",
    }
    if lower in mapping:
        return mapping[lower]
    if lower.startswith("readme"):
        return "Start here — project purpose and setup."
    return "Root-level project file."


def _guess_entry_points(scout: dict) -> list[str]:
    found: list[str] = []
    samples = scout.get("sample_files", [])
    top = [t.rstrip("/") for t in scout.get("top_level", [])]
    candidates = [
        "main.py",
        "app.py",
        "run_demo.py",
        "manage.py",
        "index.js",
        "index.ts",
        "src/main.py",
        "src/index.ts",
        "src/index.js",
        "cmd/main.go",
        "main.go",
    ]
    for rel in samples + candidates:
        base = Path(rel).name
        if base in {"main.py", "app.py", "run_demo.py", "manage.py", "main.go", "index.js", "index.ts"}:
            if rel not in found and (rel in samples or Path(scout["repo_path"], rel).exists()):
                found.append(rel)
    scripts = scout.get("docs", {}).get("package_scripts") or {}
    for key in ("start", "dev", "serve"):
        if key in scripts and f"npm run {key}" not in found:
            found.append(f"npm run {key}")
    if "run_demo.py" in top and "run_demo.py" not in found:
        found.append("run_demo.py")
    return found[:8]


def _sketch_file(rel: str, text: str) -> str:
    if not text.strip():
        return "Empty or unreadable file."
    lines = [ln for ln in text.splitlines() if ln.strip()]
    imports = [ln for ln in lines if ln.startswith(("import ", "from ", "const ", "require(", "use "))]
    defs = [
        ln
        for ln in lines
        if ln.startswith(("def ", "class ", "function ", "export ", "async function ", "fn ", "pub fn ", "func "))
    ]
    bits = []
    if imports:
        bits.append("imports/uses: " + "; ".join(imports[:4]))
    if defs:
        bits.append("defines: " + "; ".join(defs[:5]))
    if not bits:
        bits.append("preview: " + " | ".join(lines[:3]))
    return f"{rel} → " + " · ".join(bits)


def _mental_model(scout: dict, modules: list[dict], entry_points: list[str]) -> str:
    name = scout.get("repo_name", "this project")
    primary = scout.get("stack", {}).get("primary_language", "Unknown")
    frameworks = scout.get("stack", {}).get("frameworks") or []
    framework_text = f" It leans on {', '.join(frameworks)}." if frameworks else ""
    dirs = [m["name"] for m in modules if m["kind"] == "directory"][:5]
    dir_text = ", ".join(dirs) if dirs else "a flat file layout"
    entry = entry_points[0] if entry_points else "the README and top-level files"
    return (
        f"**{name}** is primarily a {primary} project.{framework_text} "
        f"As a newcomer, think of it as folders like {dir_text}, "
        f"with execution often starting from `{entry}`. "
        "Read the README first, then open one entry point and follow the imports."
    )


def _data_flow(scout: dict, entry_points: list[str]) -> list[str]:
    steps = [
        "Developer or user starts from README / docs.",
        "Dependencies are installed via the package manager signals found in the repo.",
    ]
    if entry_points:
        steps.append(f"Runtime begins at `{entry_points[0]}` (or the documented start command).")
    else:
        steps.append("Runtime entry is not obvious — search for `main`, `app`, or framework boot files.")
    if scout.get("stack", {}).get("has_tests"):
        steps.append("Tests describe expected behavior — run them early to learn by example.")
    steps.append("Follow imports/calls from the entry point into modules (src/app/lib/api).")
    return steps
