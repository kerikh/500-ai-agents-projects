# Repo Explainer Agent

An educational multi-stage AI agent that **breaks down an unfamiliar repository** into a clear onboarding guide for **new and junior developers**.

It answers the questions juniors actually ask:

- What is this project for?
- Which folders matter first?
- What language/framework is this?
- Where does the program start?
- What should I read this week?

## Intended use case

| Audience | Industry | Description |
| --- | --- | --- |
| New / junior developers, bootcamp grads, intern onboarding | Education / Software Development | Inspect a local git repo and generate a junior-friendly markdown guide (stack, folder map, mental model, learning path, glossary, first-week plan). |

## How the agent works

```text
Scout  →  Architect  →  Teacher  →  Report
  │           │            │          │
  │           │            │          └─ markdown onboarding guide
  │           │            └─ plain language, glossary, learning path
  │           └─ modules, entry points, data flow
  └─ tree, README signals, languages, frameworks
```

1. **Scout** maps the folder tree, README, and manifests (`package.json`, `requirements.txt`, …).
2. **Architect** guesses modules, entry points, and a simple runtime flow.
3. **Teacher** rewrites the analysis for juniors (optional LLM polish).
4. **Report** writes a single markdown guide you can drop into a wiki or PR.

Offline mode is the default (no API key required). If `OPENAI_API_KEY` is set and `openai` is installed, the Teacher stage can enrich the welcome note with an LLM.

## Quick start

```bash
cd repo-explainer-agent
pip install -r requirements.txt

# Explain the bundled sample app (no API key needed)
python run_demo.py

# Explain any local repository
python run_demo.py --repo /path/to/your/repo --output onboarding.md
```

### Expected output

- Console printout of the guide
- A markdown file (default: `examples/sample_output.md`) containing:
  - project summary
  - folder map
  - mental model + data flow
  - step-by-step learning path
  - glossary and first-week plan

### Runtime

- **CPU only**
- Bundled demo: usually **under 5 seconds**
- No GPU required

### Optional LLM enrichment

```bash
export OPENAI_API_KEY=sk-...
export REPO_EXPLAINER_MODEL=gpt-4o-mini   # optional
python run_demo.py --repo /path/to/repo
```

## Project layout

```text
repo-explainer-agent/
├── run_demo.py                 # CLI entrypoint
├── metadata.yaml               # catalog metadata
├── requirements.txt
├── src/repo_explainer/         # agent code
│   ├── agent.py                # orchestrator
│   ├── report.py
│   ├── llm.py                  # optional OpenAI helper
│   ├── stages/                 # Scout / Architect / Teacher
│   └── tools/                  # filesystem, stack detect, README parse
├── fixtures/sample_app/        # tiny repo used in the demo
├── examples/                   # generated sample guide
└── tests/                      # smoke tests
```

## Tests

```bash
pip install -r requirements.txt
pytest -q
```

Smoke tests run fully offline against `fixtures/sample_app`.

## Ethical considerations / Safety notes

- The agent **reads local files** you point it at. Only run it on repositories you are allowed to inspect.
- It may summarize README text and small source excerpts; do not feed it secrets or private customer data.
- LLM mode sends repository analysis JSON to the configured OpenAI-compatible API — use offline mode for sensitive codebases.
- Generated guides are teaching aids, not authoritative architecture docs. Have a teammate review before using them as official onboarding.

## License

MIT — see the repository root [LICENSE](../LICENSE).
