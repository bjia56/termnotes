"""
Abstract base class for storage backends
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import uuid
from ..note import Note


class StorageBackend(ABC):
    """Abstract interface for note storage backends"""

    @abstractmethod
    def get_all_notes(self) -> List[Note]:
        """
        Get all notes from storage

        Returns:
            List of notes, sorted by most recently updated first
        """
        pass

    @abstractmethod
    def get_note(self, note_id: str) -> Optional[Note]:
        """
        Get a specific note by ID

        Args:
            note_id: Unique identifier for the note

        Returns:
            Note object if found, None otherwise
        """
        pass

    @abstractmethod
    def save_note(self, note: Note):
        """
        Save or update a note

        Args:
            note: Note object to save
        """
        pass

    def create_note(self) -> Note:
        """Create a new empty note with a unique ID"""
        # Generate a UUID v4 for the note
        note_id = str(uuid.uuid4())
        note = Note(note_id=note_id, content="")
        return note

    @abstractmethod
    def delete_note(self, note_id: str):
        """
        Delete a note by ID

        Args:
            note_id: ID of note to delete
        """
        pass

    @abstractmethod
    def close(self):
        """Clean up any resources (database connections, file handles, etc.)"""
        pass
