"""
Editor buffer and main editor class
"""

from typing import List
from enum import Enum


class Mode(Enum):
    """Editor modes"""
    NORMAL = "NORMAL"
    INSERT = "INSERT"


class EditorBuffer:
    """In-memory text buffer with cursor management"""

    def __init__(self, initial_text: str = ""):
        """Initialize the buffer with optional initial text"""
        if initial_text:
            self.lines: List[str] = initial_text.split('\n')
        else:
            self.lines: List[str] = [""]

        self.cursor_row: int = 0
        self.cursor_col: int = 0
        self.is_dirty: bool = False  # Track if buffer has unsaved changes
        self.current_note_id: str = None  # Track which note is currently loaded

    @property
    def current_line(self) -> str:
        """Get the current line text"""
        return self.lines[self.cursor_row]

    @property
    def line_count(self) -> int:
        """Get total number of lines"""
        return len(self.lines)

    def get_text(self) -> str:
        """Get all buffer text as a single string"""
        return '\n'.join(self.lines)

    def get_display_lines(self) -> List[str]:
        """Get lines for display"""
        return self.lines.copy()

    def mark_dirty(self):
        """Mark buffer as having unsaved changes"""
        self.is_dirty = True

    def mark_clean(self):
        """Mark buffer as saved (no unsaved changes)"""
        self.is_dirty = False

    def load_content(self, content: str, note_id: str = None):
        """
        Load new content into buffer

        Args:
            content: Text content to load
            note_id: ID of the note being loaded
        """
        if content:
            self.lines = content.split('\n')
        else:
            self.lines = [""]

        self.cursor_row = 0
        self.cursor_col = 0
        self.current_note_id = note_id
        self.is_dirty = False

    # Cursor movement
    def move_cursor_left(self):
        """Move cursor left"""
        if self.cursor_col > 0:
            self.cursor_col -= 1

    def move_cursor_right(self):
        """Move cursor right"""
        if self.cursor_col < len(self.current_line):
            self.cursor_col += 1

    def move_cursor_up(self):
        """Move cursor up"""
        if self.cursor_row > 0:
            self.cursor_row -= 1
            # Adjust column if necessary
            self.cursor_col = min(self.cursor_col, len(self.current_line))

    def move_cursor_down(self):
        """Move cursor down"""
        if self.cursor_row < len(self.lines) - 1:
            self.cursor_row += 1
            # Adjust column if necessary
            self.cursor_col = min(self.cursor_col, len(self.current_line))

    def move_cursor_to_line_start(self):
        """Move cursor to start of line"""
        self.cursor_col = 0

    def move_cursor_to_line_end(self):
        """Move cursor to end of line"""
        self.cursor_col = len(self.current_line)

    # Text modification
    def insert_char(self, char: str):
        """Insert a character at cursor position"""
        line = self.lines[self.cursor_row]
        self.lines[self.cursor_row] = (
            line[:self.cursor_col] + char + line[self.cursor_col:]
        )
        self.cursor_col += 1
        self.mark_dirty()

    def delete_char_at_cursor(self):
        """Delete character at cursor position"""
        line = self.lines[self.cursor_row]
        if self.cursor_col < len(line):
            self.lines[self.cursor_row] = (
                line[:self.cursor_col] + line[self.cursor_col + 1:]
            )
            self.mark_dirty()

    def backspace(self):
        """Delete character before cursor"""
        if self.cursor_col > 0:
            line = self.lines[self.cursor_row]
            self.lines[self.cursor_row] = (
                line[:self.cursor_col - 1] + line[self.cursor_col:]
            )
            self.cursor_col -= 1
            self.mark_dirty()
        elif self.cursor_row > 0:
            # Join with previous line
            prev_line = self.lines[self.cursor_row - 1]
            current_line = self.lines[self.cursor_row]
            self.cursor_col = len(prev_line)
            self.lines[self.cursor_row - 1] = prev_line + current_line
            self.lines.pop(self.cursor_row)
            self.cursor_row -= 1
            self.mark_dirty()

    def insert_newline(self):
        """Insert a new line at cursor position"""
        line = self.lines[self.cursor_row]
        # Split current line at cursor
        self.lines[self.cursor_row] = line[:self.cursor_col]
        self.lines.insert(self.cursor_row + 1, line[self.cursor_col:])
        self.cursor_row += 1
        self.cursor_col = 0
        self.mark_dirty()

    def delete_line(self):
        """Delete current line"""
        if len(self.lines) > 1:
            self.lines.pop(self.cursor_row)
            # Adjust cursor position
            if self.cursor_row >= len(self.lines):
                self.cursor_row = len(self.lines) - 1
            self.cursor_col = min(self.cursor_col, len(self.current_line))
        else:
            # Don't delete the last line, just clear it
            self.lines[0] = ""
            self.cursor_col = 0
        self.mark_dirty()

    def insert_line_below(self):
        """Insert a new empty line below current line"""
        self.lines.insert(self.cursor_row + 1, "")
        self.cursor_row += 1
        self.cursor_col = 0
        self.mark_dirty()

    def insert_line_above(self):
        """Insert a new empty line above current line"""
        self.lines.insert(self.cursor_row, "")
        self.cursor_col = 0
        self.mark_dirty()
