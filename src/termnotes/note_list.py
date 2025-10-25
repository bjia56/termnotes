"""
Note list management
"""

from typing import List, Optional
from .note import Note
from .storage import StorageBackend


class NoteListManager:
    """Manages a list of notes and selection state"""

    def __init__(self, storage: StorageBackend):
        """
        Initialize note list manager

        Args:
            storage: StorageBackend instance for persistence
        """
        self.storage = storage
        self.notes: List[Note] = []
        self.in_memory_note: Optional[Note] = None  # Track unsaved new note
        self.selected_index: int = 0
        self.reload_notes()

        # Search state for sidebar search
        self.search_matches: List[int] = []  # Indices of notes matching search
        self.current_match_index: int = -1  # Index in search_matches list

    def reload_notes(self):
        """Reload notes from storage"""
        self.notes = self.storage.get_all_notes()
        # Ensure selected_index is valid
        if self.selected_index >= len(self.notes):
            self.selected_index = max(0, len(self.notes) - 1)

    def get_all_notes_including_memory(self) -> List[Note]:
        """Get all notes including the in-memory note if present"""
        if self.in_memory_note:
            return [self.in_memory_note] + self.notes
        return self.notes

    @property
    def selected_note(self) -> Optional[Note]:
        """Get the currently selected note"""
        all_notes = self.get_all_notes_including_memory()
        if 0 <= self.selected_index < len(all_notes):
            return all_notes[self.selected_index]
        return None

    def move_selection_up(self):
        """Move selection up in the list"""
        if self.selected_index > 0:
            self.selected_index -= 1

    def move_selection_down(self):
        """Move selection down in the list"""
        all_notes = self.get_all_notes_including_memory()
        if self.selected_index < len(all_notes) - 1:
            self.selected_index += 1

    def get_note_count(self) -> int:
        """Get total number of notes"""
        return len(self.get_all_notes_including_memory())

    def get_note_at_index(self, index: int) -> Optional[Note]:
        """Get note at specified index"""
        all_notes = self.get_all_notes_including_memory()
        if 0 <= index < len(all_notes):
            return all_notes[index]
        return None

    def set_in_memory_note(self, note: Optional[Note]):
        """Set the in-memory note and select it"""
        self.in_memory_note = note
        if note:
            self.selected_index = 0  # Select the in-memory note (always at top)

    def clear_in_memory_note(self):
        """Clear the in-memory note"""
        self.in_memory_note = None

    def search_notes(self, query: str) -> bool:
        """
        Search for query across all note contents and store matching indices.

        Args:
            query: Search string

        Returns:
            True if any matches found, False otherwise
        """
        if not query:
            self.search_matches = []
            self.current_match_index = -1
            return False

        self.search_matches = []
        all_notes = self.get_all_notes_including_memory()

        # Find all notes containing the query (case-insensitive)
        query_lower = query.lower()
        for i, note in enumerate(all_notes):
            if query_lower in note.content.lower():
                self.search_matches.append(i)

        if self.search_matches:
            self.current_match_index = 0
            self.selected_index = self.search_matches[0]
            return True
        else:
            self.current_match_index = -1
            return False

    def search_next(self) -> bool:
        """
        Jump to next search match.

        Returns:
            True if a match was found, False otherwise
        """
        if not self.search_matches:
            return False

        # Move to next match (wrap around)
        self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)
        self.selected_index = self.search_matches[self.current_match_index]
        return True

    def search_previous(self) -> bool:
        """
        Jump to previous search match.

        Returns:
            True if a match was found, False otherwise
        """
        if not self.search_matches:
            return False

        # Move to previous match (wrap around)
        self.current_match_index = (self.current_match_index - 1) % len(self.search_matches)
        self.selected_index = self.search_matches[self.current_match_index]
        return True

    def clear_search(self):
        """Clear search state"""
        self.search_matches = []
        self.current_match_index = -1
