"""
Composite storage backend that combines multiple backends
"""

from typing import List, Optional
from .base import StorageBackend
from ..note import Note


class CompositeBackend(StorageBackend):
    """
    Composite backend with cache strategy.

    Uses a fast in-memory cache (SQLite) backed by persistent storage (filesystem).
    - Reads: Try cache first, fall back to persistent storage
    - Writes: Write to both backends
    - On init: Load all persistent notes into cache
    """

    def __init__(self, cache: StorageBackend, persistent: StorageBackend):
        """
        Initialize composite backend

        Args:
            cache: Fast in-memory backend (e.g., SQLiteBackend with :memory:)
            persistent: Persistent storage backend (e.g., FilesystemBackend)
        """
        self.cache = cache
        self.persistent = persistent

        # Populate cache from persistent storage on startup
        self._populate_cache()

    def _populate_cache(self):
        """Load all notes from persistent storage into cache"""
        persistent_notes = self.persistent.get_all_notes()

        for note in persistent_notes:
            self.cache.save_note(note)

    def get_all_notes(self) -> List[Note]:
        """Get all notes from cache (already loaded from persistent storage)"""
        return self.cache.get_all_notes()

    def get_note(self, note_id: str) -> Optional[Note]:
        """
        Get a specific note by ID

        Tries cache first, falls back to persistent storage if not found
        """
        # Try cache first (fast)
        note = self.cache.get_note(note_id)
        if note:
            return note

        # Cache miss - try persistent storage
        note = self.persistent.get_note(note_id)
        if note:
            # Populate cache for next time
            self.cache.save_note(note)

        return note

    def save_note(self, note: Note):
        """
        Save note to both cache and persistent storage

        Write-through cache: updates both immediately
        """
        # Save to cache (fast)
        self.cache.save_note(note)

        # Save to persistent storage (slower but durable)
        self.persistent.save_note(note)

    def create_note(self) -> Note:
        """
        Create a new note in both cache and persistent storage

        Uses persistent backend's ID generation to ensure uniqueness
        """
        # Create in persistent storage first (authoritative ID generation)
        note = self.persistent.create_note()

        # Add to cache
        self.cache.save_note(note)

        return note

    def delete_note(self, note_id: str):
        """Delete note from both cache and persistent storage"""
        self.cache.delete_note(note_id)
        self.persistent.delete_note(note_id)

    def close(self):
        """Close both backends"""
        self.cache.close()
        self.persistent.close()
