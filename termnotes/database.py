"""Database backend for notes storage."""

import sqlite3
from datetime import datetime
from typing import List, Optional
from .models import Note


class Database:
    """SQLite database handler for notes."""
    
    def __init__(self, db_path: str = ":memory:"):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file, or ":memory:" for in-memory DB
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create the notes table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)
        self.conn.commit()
    
    def create_note(self, title: str, content: str = "") -> Note:
        """Create a new note.
        
        Args:
            title: Note title
            content: Note content
            
        Returns:
            Created note with ID
        """
        now = datetime.now()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO notes (title, content, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (title, content, now, now))
        self.conn.commit()
        
        note_id = cursor.lastrowid
        return Note(id=note_id, title=title, content=content, 
                   created_at=now, updated_at=now)
    
    def get_note(self, note_id: int) -> Optional[Note]:
        """Get a note by ID.
        
        Args:
            note_id: Note ID
            
        Returns:
            Note if found, None otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, content, created_at, updated_at
            FROM notes WHERE id = ?
        """, (note_id,))
        
        row = cursor.fetchone()
        if row:
            return Note(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"])
            )
        return None
    
    def list_notes(self) -> List[Note]:
        """List all notes.
        
        Returns:
            List of all notes
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, content, created_at, updated_at
            FROM notes
            ORDER BY updated_at DESC
        """)
        
        notes = []
        for row in cursor.fetchall():
            notes.append(Note(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"])
            ))
        return notes
    
    def update_note(self, note_id: int, title: str = None, content: str = None) -> bool:
        """Update a note.
        
        Args:
            note_id: Note ID
            title: New title (optional)
            content: New content (optional)
            
        Returns:
            True if updated, False if note not found
        """
        note = self.get_note(note_id)
        if not note:
            return False
        
        if title is None:
            title = note.title
        if content is None:
            content = note.content
        
        now = datetime.now()
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE notes
            SET title = ?, content = ?, updated_at = ?
            WHERE id = ?
        """, (title, content, now, note_id))
        self.conn.commit()
        return True
    
    def delete_note(self, note_id: int) -> bool:
        """Delete a note.
        
        Args:
            note_id: Note ID
            
        Returns:
            True if deleted, False if note not found
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def close(self):
        """Close the database connection."""
        self.conn.close()
