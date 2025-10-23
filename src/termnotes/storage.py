"""
SQLite-based note storage
"""

import sqlite3
from typing import List, Optional
from .note import Note


class NoteStorage:
    """Manages note persistence with SQLite"""

    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize note storage

        Args:
            db_path: Path to SQLite database file, or ":memory:" for in-memory DB
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
        self._insert_dummy_data()

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

    def _insert_dummy_data(self):
        """Insert dummy notes if database is empty"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM notes")
        count = cursor.fetchone()[0]

        if count == 0:
            # Insert dummy notes
            dummy_notes = [
                ("1", "Welcome to termnotes!\n\nThis is a vim-like note taking application.\n\nUse Ctrl+W h/l to switch between sidebar and editor."),
                ("2", "Shopping List\n\n- Milk\n- Eggs\n- Bread\n- Coffee\n- Butter"),
                ("3", "Meeting Notes - January 2024\n\nAttendees: Team\n\nAgenda:\n1. Project status\n2. Next steps\n3. Q&A"),
                ("4", "Random Ideas\n\n- Add search functionality\n- Implement note tags\n- Add markdown support\n- Cloud sync?"),
                ("5", "Just a quick note to remember something important later."),
            ]

            cursor.executemany(
                "INSERT INTO notes (id, content) VALUES (?, ?)",
                dummy_notes
            )
            self.conn.commit()

    def get_all_notes(self) -> List[Note]:
        """Get all notes from the database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, content FROM notes ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        return [Note(note_id=row[0], content=row[1]) for row in rows]

    def get_note(self, note_id: str) -> Optional[Note]:
        """Get a specific note by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, content FROM notes WHERE id = ?", (note_id,))
        row = cursor.fetchone()
        if row:
            return Note(note_id=row[0], content=row[1])
        return None

    def save_note(self, note: Note):
        """Save or update a note"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO notes (id, content, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                content = excluded.content,
                updated_at = CURRENT_TIMESTAMP
        """, (note.id, note.content))
        self.conn.commit()

    def create_note(self) -> Note:
        """Create a new empty note with a unique ID"""
        cursor = self.conn.cursor()
        # Find next available ID
        cursor.execute("SELECT id FROM notes ORDER BY CAST(id AS INTEGER) DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            next_id = str(int(row[0]) + 1)
        else:
            next_id = "1"

        note = Note(note_id=next_id, content="")
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
