"""Notes feature for managing individual notes."""

from app.features.notes.service import NoteService
from app.features.notes.tool import obsidian_manage_notes

__all__ = ["NoteService", "obsidian_manage_notes"]
