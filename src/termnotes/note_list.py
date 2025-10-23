"""
Note list management
"""

from typing import List, Optional
from .note import Note
from .storage import NoteStorage


class NoteListManager:
    """Manages a list of notes and selection state"""

    def __init__(self, storage: NoteStorage):
        """
        Initialize note list manager

        Args:
            storage: NoteStorage instance for persistence
        """
        self.storage = storage
        self.notes: List[Note] = []
        self.selected_index: int = 0
        self.reload_notes()

    def reload_notes(self):
        """Reload notes from storage"""
        self.notes = self.storage.get_all_notes()
        # Ensure selected_index is valid
        if self.selected_index >= len(self.notes):
            self.selected_index = max(0, len(self.notes) - 1)

    @property
    def selected_note(self) -> Optional[Note]:
        """Get the currently selected note"""
        if 0 <= self.selected_index < len(self.notes):
            return self.notes[self.selected_index]
        return None

    def move_selection_up(self):
        """Move selection up in the list"""
        if self.selected_index > 0:
            self.selected_index -= 1

    def move_selection_down(self):
        """Move selection down in the list"""
        if self.selected_index < len(self.notes) - 1:
            self.selected_index += 1

    def get_note_count(self) -> int:
        """Get total number of notes"""
        return len(self.notes)

    def get_note_at_index(self, index: int) -> Optional[Note]:
        """Get note at specified index"""
        if 0 <= index < len(self.notes):
            return self.notes[index]
        return None
