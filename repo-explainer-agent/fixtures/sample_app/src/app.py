"""Tiny in-memory notes app used as a demo repository."""

from __future__ import annotations

from .notes import NotesStore

store = NotesStore()


def main() -> None:
    store.add("Welcome to the sample notes API")
    store.add("Use the Repo Explainer Agent to understand unfamiliar codebases")
    print("Sample Notes API")
    print("----------------")
    for index, note in enumerate(store.list_notes(), start=1):
        print(f"{index}. {note}")


if __name__ == "__main__":
    main()
