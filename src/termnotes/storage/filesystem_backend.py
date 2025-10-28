"""
Filesystem-based note storage backend using JSON files
"""

import json
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from .base import StorageBackend
from ..utils import utc_now
from ..note import Note


class FilesystemBackend(StorageBackend):
    """Filesystem implementation of storage backend using JSON files"""

    def __init__(self, notes_dir: str = None):
        """
        Initialize filesystem storage backend

        Args:
            notes_dir: Directory to store note files. Defaults to ~/.termnotes/notes
        """
        if notes_dir is None:
            notes_dir = os.path.expanduser("~/.termnotes/notes")

        self.notes_dir = Path(notes_dir)
        self.notes_dir.mkdir(parents=True, exist_ok=True)

    def _get_note_path(self, note_id: str) -> Path:
        """Get the file path for a note"""
        return self.notes_dir / f"{note_id}.json"

    def get_all_notes(self) -> List[Note]:
        """Get all notes from the filesystem"""
        notes = []

        for note_file in self.notes_dir.glob("*.json"):
            try:
                with open(note_file, 'r') as f:
                    data = json.load(f)
                    note = self._note_from_dict(data)
                    notes.append(note)
            except (json.JSONDecodeError, KeyError, OSError):
                # Skip corrupted files
                continue

        # Sort by updated_at, most recent first
        notes.sort(key=lambda n: n.updated_at, reverse=True)
        return notes

    def get_note(self, note_id: str) -> Optional[Note]:
        """Get a specific note by ID"""
        note_path = self._get_note_path(note_id)

        if not note_path.exists():
            return None

        try:
            with open(note_path, 'r') as f:
                data = json.load(f)
                return self._note_from_dict(data)
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def save_note(self, note: Note):
        """Save or update a note"""
        # Update the updated_at timestamp
        note.updated_at = utc_now()

        note_path = self._get_note_path(note.id)
        data = self._note_to_dict(note)

        with open(note_path, 'w') as f:
            json.dump(data, f, indent=2)

    def delete_note(self, note_id: str):
        """Delete a note by ID"""
        note_path = self._get_note_path(note_id)
        if note_path.exists():
            note_path.unlink()

    def close(self):
        """Clean up resources (no-op for filesystem)"""
        pass

    def _note_to_dict(self, note: Note) -> dict:
        """Convert Note object to dictionary for JSON storage"""
        return {
            "id": note.id,
            "content": note.content,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(),
            "properties": note.properties
        }

    def _note_from_dict(self, data: dict) -> Note:
        """Create Note object from dictionary"""
        return Note(
            note_id=data["id"],
            content=data["content"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            properties=data.get("properties", {})
        )
