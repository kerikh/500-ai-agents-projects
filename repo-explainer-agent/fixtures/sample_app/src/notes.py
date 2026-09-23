"""In-memory notes storage."""

from __future__ import annotations


class NotesStore:
    def __init__(self) -> None:
        self._notes: list[str] = []

    def add(self, text: str) -> str:
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Note text cannot be empty")
        self._notes.append(cleaned)
        return cleaned

    def list_notes(self) -> list[str]:
        return list(self._notes)
