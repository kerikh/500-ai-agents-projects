"""Teacher stage — turn analysis into junior-friendly teaching material."""

from __future__ import annotations

from ..llm import dump_context, enrich_with_llm


JUNIOR_SYSTEM = """You are a patient senior engineer mentoring a brand-new junior developer.
Write clearly, avoid jargon unless you define it, and focus on what to open first.
Keep the tone encouraging and concrete. Use short paragraphs and bullet lists.
"""


def run_teacher(scout: dict, architect: dict) -> dict:
    glossary = _build_glossary(scout, architect)
    learning_path = _learning_path(scout, architect)
    plain_summary = _plain_summary(scout, architect)
    common_pitfalls = _pitfalls(scout)
    first_week_plan = _first_week_plan(scout, architect)

    llm_polish = enrich_with_llm(
        JUNIOR_SYSTEM,
        (
            "Using this repository analysis JSON, write a short onboarding pep talk "
            "(under 180 words) for a junior developer joining tomorrow.\n\n"
            + dump_context({"scout": _slim_scout(scout), "architect": _slim_architect(architect)})
        ),
    )

    return {
        "plain_summary": plain_summary,
        "pep_talk": llm_polish or _fallback_pep_talk(scout),
        "learning_path": learning_path,
        "glossary": glossary,
        "common_pitfalls": common_pitfalls,
        "first_week_plan": first_week_plan,
        "used_llm": bool(llm_polish),
    }


def _slim_scout(scout: dict) -> dict:
    return {
        "repo_name": scout.get("repo_name"),
        "stack": scout.get("stack"),
        "docs_summary": scout.get("docs", {}).get("summary"),
        "top_level": scout.get("top_level"),
        "sample_files": scout.get("sample_files"),
    }


def _slim_architect(architect: dict) -> dict:
    return {
        "mental_model": architect.get("mental_model"),
        "entry_points": architect.get("entry_points"),
        "modules": architect.get("modules"),
        "data_flow": architect.get("data_flow"),
    }


def _plain_summary(scout: dict, architect: dict) -> str:
    docs_summary = scout.get("docs", {}).get("summary") or ""
    stack = scout.get("stack", {})
    langs = ", ".join(stack.get("languages") or ["Unknown"])
    frameworks = ", ".join(stack.get("frameworks") or ["none detected"])
    return (
        f"This repository (`{scout.get('repo_name')}`) looks like a {stack.get('primary_language', 'mixed')} "
        f"codebase. Detected languages: {langs}. Frameworks/libraries: {frameworks}.\n\n"
        f"README gist: {docs_summary}\n\n"
        f"{architect.get('mental_model', '')}"
    )


def _fallback_pep_talk(scout: dict) -> str:
    name = scout.get("repo_name", "this repository")
    return (
        f"Welcome! You do not need to understand every file in `{name}` on day one. "
        "Start with the README, install dependencies, then open one entry-point file and "
        "trace what it imports. Use tests as living documentation. Ask questions about "
        "anything that feels magical — those are usually the best learning moments."
    )


def _learning_path(scout: dict, architect: dict) -> list[dict]:
    docs = scout.get("docs", {})
    path = [
        {
            "step": 1,
            "title": "Read the README",
            "why": "It explains the project's purpose and how to run it.",
            "do": f"Open `{docs.get('readme_path') or 'README.md'}` and skim headings: "
            + ", ".join(docs.get("headings") or ["(no headings found)"]),
        },
        {
            "step": 2,
            "title": "Install dependencies",
            "why": "You need a working environment before reading runtime code.",
            "do": "; ".join(docs.get("quick_start_hints") or ["Follow README setup."]),
        },
        {
            "step": 3,
            "title": "Find the entry point",
            "why": "Entry points show how the program boots.",
            "do": "Inspect: " + (", ".join(f"`{e}`" for e in architect.get("entry_points") or ["(search for main/app)"])),
        },
        {
            "step": 4,
            "title": "Walk one request/path through the code",
            "why": "Following a single flow beats reading folders randomly.",
            "do": "Use the mental model and data-flow bullets in this report as a map.",
        },
    ]
    if scout.get("stack", {}).get("has_tests"):
        path.append(
            {
                "step": 5,
                "title": "Run the tests",
                "why": "Tests show expected behavior with concrete examples.",
                "do": "Run the project's test command (pytest, npm test, go test, etc.).",
            }
        )
    else:
        path.append(
            {
                "step": 5,
                "title": "Write a tiny smoke check",
                "why": "If tests are missing, create a minimal check so you can explore safely.",
                "do": "Add a small script that imports the main module or hits a health endpoint.",
            }
        )
    return path


def _build_glossary(scout: dict, architect: dict) -> list[dict]:
    terms = [
        {
            "term": "Repository (repo)",
            "meaning": "The project folder tracked by Git — all the code and docs live here.",
        },
        {
            "term": "Entry point",
            "meaning": "The file or command where the program starts running.",
        },
        {
            "term": "Dependency",
            "meaning": "An external library your project needs (listed in requirements.txt, package.json, etc.).",
        },
        {
            "term": "Module / package",
            "meaning": "A folder or file that groups related code so other files can import it.",
        },
    ]
    for fw in scout.get("stack", {}).get("frameworks") or []:
        terms.append(
            {
                "term": fw,
                "meaning": f"A library/framework detected in this repo's manifests — look it up in the official docs while reading related code.",
            }
        )
    for ep in (architect.get("entry_points") or [])[:3]:
        if ep.startswith("npm "):
            continue
        terms.append(
            {
                "term": ep,
                "meaning": "Likely boot/start file for this project — open it early.",
            }
        )
    return terms


def _pitfalls(scout: dict) -> list[str]:
    pitfalls = [
        "Trying to read every file on day one — prefer one vertical slice instead.",
        "Skipping the README and guessing install commands.",
        "Editing code before you can run the existing demo/tests.",
    ]
    if "node_modules" not in " ".join(scout.get("top_level", [])):
        if any("npm" in p or "package.json" in p for p in (scout.get("docs", {}).get("important_files") or {})):
            pitfalls.append("Forgetting `npm install` before running Node scripts.")
    if scout.get("stack", {}).get("primary_language") == "Python":
        pitfalls.append("Installing packages globally instead of using a virtual environment (venv/uv).")
    return pitfalls


def _first_week_plan(scout: dict, architect: dict) -> list[str]:
    return [
        "Day 1: Clone, install, run the documented demo or tests.",
        "Day 2: Read README + top-level folders; sketch your own box-and-arrow diagram.",
        f"Day 3: Trace one entry point ({(architect.get('entry_points') or ['main file'])[0]}) through 2–3 imports.",
        "Day 4: Pair on a tiny bugfix or docs typo to practice the change workflow.",
        "Day 5: Explain the repo aloud (rubber-duck) using this onboarding guide; note remaining questions.",
    ]
