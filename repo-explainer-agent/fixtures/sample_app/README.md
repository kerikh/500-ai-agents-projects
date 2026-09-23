# Sample Notes API

A tiny FastAPI-style learning app used as a **fixture** for the Repo Explainer Agent.

It is intentionally small so juniors can see how the agent talks about a real layout.

## Quick start

```bash
pip install -r requirements.txt
python -m src.app
```

## Tests

```bash
pytest -q
```

## What it does

Stores notes in memory and exposes simple `list` / `add` helpers. No database, no auth.
