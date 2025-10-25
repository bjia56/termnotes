"""
SQLite-based note storage backend
"""

import sqlite3
import uuid
from typing import List, Optional
from datetime import datetime
from .base import StorageBackend
from ..utils import utc_now
from ..note import Note


class SQLiteBackend(StorageBackend):
    """SQLite implementation of storage backend"""

    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize SQLite storage backend

        Args:
            db_path: Path to SQLite database file, or ":memory:" for in-memory DB
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        """Create the notes table if it doesn't exist"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def get_all_notes(self) -> List[Note]:
        """Get all notes from the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, content, created_at, updated_at
            FROM notes
            ORDER BY updated_at DESC
        """)
        rows = cursor.fetchall()
        return [
            Note(
                note_id=row[0],
                content=row[1],
                created_at=self._parse_timestamp(row[2]),
                updated_at=self._parse_timestamp(row[3])
            )
            for row in rows
        ]

    def get_note(self, note_id: str) -> Optional[Note]:
        """Get a specific note by ID"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, content, created_at, updated_at FROM notes WHERE id = ?",
            (note_id,)
        )
        row = cursor.fetchone()
        if row:
            return Note(
                note_id=row[0],
                content=row[1],
                created_at=self._parse_timestamp(row[2]),
                updated_at=self._parse_timestamp(row[3])
            )
        return None

    def save_note(self, note: Note):
        """Save or update a note"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO notes (id, content, created_at, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                content = excluded.content,
                updated_at = CURRENT_TIMESTAMP
        """, (note.id, note.content, note.created_at))
        self.conn.commit()

    def create_note(self) -> Note:
        """Create a new empty note with a unique ID"""
        # Generate a UUID v4 for the note
        note_id = str(uuid.uuid4())

        note = Note(note_id=note_id, content="")
        self.save_note(note)
        return note

    def delete_note(self, note_id: str):
        """Delete a note by ID"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.conn.commit()

    def close(self):
        """Close the database connection"""
        self.conn.close()

    def _parse_timestamp(self, ts_str: str) -> datetime:
        """Parse SQLite timestamp string to datetime"""
        try:
            return datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            return utc_now()
