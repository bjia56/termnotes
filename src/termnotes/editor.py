"""
Editor buffer and main editor class
"""

from typing import List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class Mode(Enum):
    """Editor modes"""
    NORMAL = "NORMAL"
    INSERT = "INSERT"
    VISUAL = "VISUAL"
    VISUAL_LINE = "VISUAL_LINE"


class ChangeType(Enum):
    """Types of changes that can be recorded for undo"""
    INSERT_CHAR = "insert_char"
    DELETE_CHAR = "delete_char"
    BACKSPACE = "backspace"
    INSERT_NEWLINE = "insert_newline"
    DELETE_LINE = "delete_line"
    DELETE_SELECTION = "delete_selection"
    DELETE_LINES = "delete_lines"
    PASTE_TEXT = "paste_text"


@dataclass
class Change:
    """Represents a single change to the buffer"""
    type: ChangeType
    row: int
    col: int
    text: str = ""  # Text inserted or deleted
    lines_deleted: Optional[List[str]] = None  # Lines deleted (for multi-line ops)
    cursor_pos_before: Optional[Tuple[int, int]] = None  # Cursor position before change
    cursor_pos_after: Optional[Tuple[int, int]] = None  # Cursor position after change
    # For delete_selection
    end_row: Optional[int] = None
    end_col: Optional[int] = None


class UndoManager:
    """Manages undo/redo history with linear stack"""

    def __init__(self, max_history: int = 1000):
        """
        Initialize the undo manager

        Args:
            max_history: Maximum number of undo blocks to keep in history
        """
        self.history: List[List[Change]] = []  # List of change blocks
        self.current_index: int = -1  # Current position in history (-1 = no history)
        self.max_history: int = max_history

    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return self.current_index >= 0

    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return self.current_index < len(self.history) - 1

    def add_change_block(self, changes: List[Change]):
        """
        Add a new change block to history

        Args:
            changes: List of changes to add as a single undo block
        """
        if not changes:
            return

        # If we're not at the end of history, truncate future changes
        # (user made new change after undoing, so redo stack is cleared)
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]

        # Add the new change block
        self.history.append(changes)
        self.current_index += 1

        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1

    def get_undo_block(self) -> Optional[List[Change]]:
        """
        Get the next change block to undo

        Returns:
            List of changes to undo, or None if nothing to undo
        """
        if not self.can_undo():
            return None

        block = self.history[self.current_index]
        self.current_index -= 1
        return block

    def get_redo_block(self) -> Optional[List[Change]]:
        """
        Get the next change block to redo

        Returns:
            List of changes to redo, or None if nothing to redo
        """
        if not self.can_redo():
            return None

        self.current_index += 1
        return self.history[self.current_index]

    def clear(self):
        """Clear all undo/redo history"""
        self.history = []
        self.current_index = -1


class EditorBuffer:
    """In-memory text buffer with cursor management"""

    def __init__(self, initial_text: str = "", mode_manager=None):
        """Initialize the buffer with optional initial text"""
        if initial_text:
            self.lines: List[str] = initial_text.split('\n')
        else:
            self.lines: List[str] = [""]

        self.cursor_row: int = 0
        self.cursor_col: int = 0
        self.scroll_offset: int = 0  # Top line currently displayed
        self.horizontal_scroll_offset: int = 0  # Leftmost column currently displayed
        self.is_dirty: bool = False  # Track if buffer has unsaved changes
        self.current_note_id: str = None  # Track which note is currently loaded
        self.is_new_unsaved: bool = False  # Track if this is a new note not yet in storage
        self.mode_manager = mode_manager  # Reference to mode manager for mode-aware cursor behavior
        self.yank_register: str = ""  # Store yanked text for paste operations
        self.yank_is_linewise: bool = False  # Track if yanked text is line-wise or character-wise
        self.undo_manager: UndoManager = UndoManager()  # Undo/redo manager

    @property
    def current_line(self) -> str:
        """Get the current line text"""
        return self.lines[self.cursor_row]

    @property
    def line_count(self) -> int:
        """Get total number of lines"""
        return len(self.lines)

    def get_max_cursor_col(self, line: str = None) -> int:
        """
        Get the maximum cursor column position for the current mode.

        In Normal mode: cursor must be ON a character (max = len(line) - 1)
        In Insert mode: cursor can be AFTER the last character (max = len(line))

        Args:
            line: The line to check. If None, uses current line.

        Returns:
            Maximum valid cursor column position
        """
        if line is None:
            line = self.current_line

        # If we have a mode_manager and we're in normal mode
        if self.mode_manager and self.mode_manager.is_normal_mode():
            # Normal mode: cursor must be on a character
            # Empty line: cursor at 0, otherwise max is len-1
            return max(0, len(line) - 1) if line else 0
        else:
            # Insert mode (or no mode_manager): cursor can be after last char
            return len(line)

    def clamp_cursor(self):
        """
        Clamp cursor position to valid range for current mode.
        Call this after mode changes to ensure cursor is in valid position.
        """
        self.cursor_col = min(self.cursor_col, self.get_max_cursor_col())

    def get_text(self) -> str:
        """Get all buffer text as a single string"""
        return '\n'.join(self.lines)

    def get_display_lines(self) -> List[str]:
        """Get lines for display"""
        return self.lines.copy()

    def adjust_scroll(self, visible_height: int):
        """
        Adjust scroll offset to keep cursor visible within the window.

        Args:
            visible_height: Number of lines visible in the editor window
        """
        if visible_height <= 0:
            return

        # Scroll down if cursor is below visible area
        if self.cursor_row >= self.scroll_offset + visible_height:
            self.scroll_offset = self.cursor_row - visible_height + 1

        # Scroll up if cursor is above visible area
        if self.cursor_row < self.scroll_offset:
            self.scroll_offset = self.cursor_row

        # Ensure scroll_offset is non-negative
        self.scroll_offset = max(0, self.scroll_offset)

    def adjust_horizontal_scroll(self, visible_width: int):
        """
        Adjust horizontal scroll offset to keep cursor visible within the window.
        Scrolls only when cursor reaches the edge (no margin).

        Args:
            visible_width: Number of columns visible in the editor window
        """
        if visible_width <= 0:
            return

        # Scroll right if cursor is at or beyond right edge
        if self.cursor_col >= self.horizontal_scroll_offset + visible_width:
            self.horizontal_scroll_offset = self.cursor_col - visible_width + 1

        # Scroll left if cursor is before left edge
        if self.cursor_col < self.horizontal_scroll_offset:
            self.horizontal_scroll_offset = self.cursor_col

        # Ensure horizontal_scroll_offset is non-negative
        self.horizontal_scroll_offset = max(0, self.horizontal_scroll_offset)

    def scroll_left(self, amount: int = 1):
        """
        Scroll view left (decrease horizontal offset)

        Args:
            amount: Number of columns to scroll left
        """
        self.horizontal_scroll_offset = max(0, self.horizontal_scroll_offset - amount)

    def scroll_right(self, amount: int = 1):
        """
        Scroll view right (increase horizontal offset)

        Args:
            amount: Number of columns to scroll right
        """
        self.horizontal_scroll_offset += amount

    def scroll_half_screen_left(self, visible_width: int):
        """
        Scroll view left by half screen width

        Args:
            visible_width: Number of columns visible in the editor window
        """
        if visible_width <= 0:
            return
        half_width = max(1, visible_width // 2)
        self.scroll_left(half_width)

    def scroll_half_screen_right(self, visible_width: int):
        """
        Scroll view right by half screen width

        Args:
            visible_width: Number of columns visible in the editor window
        """
        if visible_width <= 0:
            return
        half_width = max(1, visible_width // 2)
        self.scroll_right(half_width)

    def mark_dirty(self):
        """Mark buffer as having unsaved changes"""
        self.is_dirty = True

    def mark_clean(self):
        """Mark buffer as saved (no unsaved changes)"""
        self.is_dirty = False

    def load_content(self, content: str, note_id: str = None, is_new: bool = False):
        """
        Load new content into buffer

        Args:
            content: Text content to load
            note_id: ID of the note being loaded
            is_new: Whether this is a new unsaved note (not yet in storage)
        """
        if content:
            self.lines = content.split('\n')
        else:
            self.lines = [""]

        self.cursor_row = 0
        self.cursor_col = 0
        self.scroll_offset = 0
        self.horizontal_scroll_offset = 0
        self.current_note_id = note_id
        self.is_dirty = False
        self.is_new_unsaved = is_new
        # Clear undo history when loading new content
        self.undo_manager.clear()

    # Cursor movement
    def move_cursor_left(self):
        """Move cursor left"""
        if self.cursor_col > 0:
            self.cursor_col -= 1

    def move_cursor_right(self):
        """Move cursor right"""
        max_col = self.get_max_cursor_col()
        if self.cursor_col < max_col:
            self.cursor_col += 1

    def move_cursor_up(self, visible_height: int = None):
        """Move cursor up"""
        if self.cursor_row > 0:
            self.cursor_row -= 1
            # Adjust column if necessary
            self.cursor_col = min(self.cursor_col, self.get_max_cursor_col())
            # Adjust scroll if visible_height provided
            if visible_height is not None:
                self.adjust_scroll(visible_height)

    def move_cursor_down(self, visible_height: int = None):
        """Move cursor down"""
        if self.cursor_row < len(self.lines) - 1:
            self.cursor_row += 1
            # Adjust column if necessary
            self.cursor_col = min(self.cursor_col, self.get_max_cursor_col())
            # Adjust scroll if visible_height provided
            if visible_height is not None:
                self.adjust_scroll(visible_height)

    def move_cursor_to_line_start(self):
        """Move cursor to start of line"""
        self.cursor_col = 0

    def move_cursor_to_line_end(self):
        """Move cursor to end of line"""
        self.cursor_col = self.get_max_cursor_col()

    def page_down(self, visible_height: int):
        """Move cursor down by one page (vim Ctrl+F behavior)"""
        if visible_height <= 0:
            return

        # Calculate cursor's current position relative to top of screen
        relative_pos = self.cursor_row - self.scroll_offset

        # Calculate new scroll offset
        new_scroll_offset = min(self.scroll_offset + visible_height,
                                max(0, len(self.lines) - visible_height))

        # Check if we're at the bottom (can't scroll further)
        if new_scroll_offset == self.scroll_offset and self.scroll_offset == max(0, len(self.lines) - visible_height):
            # Already at bottom, move cursor to last line
            self.cursor_row = len(self.lines) - 1
        else:
            # Normal scroll: update offset and try to keep relative position
            self.scroll_offset = new_scroll_offset
            new_row = self.scroll_offset + relative_pos
            # Clamp to valid range
            new_row = min(new_row, len(self.lines) - 1)
            new_row = max(new_row, self.scroll_offset)
            self.cursor_row = new_row

        # Adjust column if necessary
        self.cursor_col = min(self.cursor_col, self.get_max_cursor_col())

    def page_up(self, visible_height: int):
        """Move cursor up by one page (vim Ctrl+B behavior)"""
        if visible_height <= 0:
            return

        # Calculate cursor's current position relative to top of screen
        relative_pos = self.cursor_row - self.scroll_offset

        # Calculate new scroll offset
        new_scroll_offset = max(self.scroll_offset - visible_height, 0)

        # Check if we're at the top (can't scroll further)
        if new_scroll_offset == self.scroll_offset and self.scroll_offset == 0:
            # Already at top, move cursor to first line
            self.cursor_row = 0
        else:
            # Normal scroll: update offset and try to keep relative position
            self.scroll_offset = new_scroll_offset
            new_row = self.scroll_offset + relative_pos
            # Clamp to valid range
            new_row = max(new_row, 0)
            new_row = min(new_row, self.scroll_offset + visible_height - 1)
            self.cursor_row = new_row

        # Adjust column if necessary
        self.cursor_col = min(self.cursor_col, self.get_max_cursor_col())

    def half_page_down(self, visible_height: int):
        """Move cursor down by half a page (vim Ctrl+D)"""
        if visible_height <= 0:
            return

        half_page = max(1, visible_height // 2)

        # Calculate new positions
        new_row = min(self.cursor_row + half_page, len(self.lines) - 1)
        new_scroll_offset = min(self.scroll_offset + half_page,
                                max(0, len(self.lines) - visible_height))

        # Check if we've reached the bottom
        if new_row == len(self.lines) - 1 and self.cursor_row == len(self.lines) - 1:
            # Already at last line, do nothing more
            pass
        elif new_row == len(self.lines) - 1:
            # Moving to last line for the first time
            self.cursor_row = new_row
            self.scroll_offset = new_scroll_offset
        else:
            # Normal scroll
            self.cursor_row = new_row
            self.scroll_offset = new_scroll_offset

        # Adjust column if necessary
        self.cursor_col = min(self.cursor_col, self.get_max_cursor_col())

    def half_page_up(self, visible_height: int):
        """Move cursor up by half a page (vim Ctrl+U)"""
        if visible_height <= 0:
            return

        half_page = max(1, visible_height // 2)

        # Calculate new positions
        new_row = max(self.cursor_row - half_page, 0)
        new_scroll_offset = max(self.scroll_offset - half_page, 0)

        # Check if we've reached the top
        if new_row == 0 and self.cursor_row == 0:
            # Already at first line, do nothing more
            pass
        elif new_row == 0:
            # Moving to first line for the first time
            self.cursor_row = new_row
            self.scroll_offset = new_scroll_offset
        else:
            # Normal scroll
            self.cursor_row = new_row
            self.scroll_offset = new_scroll_offset

        # Adjust column if necessary
        self.cursor_col = min(self.cursor_col, self.get_max_cursor_col())

    # Text modification
    def insert_char(self, char: str):
        """Insert a character at cursor position"""
        # Record change for undo
        change = Change(
            type=ChangeType.INSERT_CHAR,
            row=self.cursor_row,
            col=self.cursor_col,
            text=char,
            cursor_pos_before=(self.cursor_row, self.cursor_col)
        )

        line = self.lines[self.cursor_row]
        self.lines[self.cursor_row] = (
            line[:self.cursor_col] + char + line[self.cursor_col:]
        )
        self.cursor_col += 1

        change.cursor_pos_after = (self.cursor_row, self.cursor_col)
        self.undo_manager.add_change_block([change])

        self.mark_dirty()

    def paste_text(self, text: str, visible_height: int = None):
        """
        Paste text at cursor position, handling multi-line content

        Args:
            text: Text to paste (can contain newlines)
            visible_height: Height of visible editor area for scroll adjustment
        """
        if not text:
            return

        # Record change for undo
        change = Change(
            type=ChangeType.PASTE_TEXT,
            row=self.cursor_row,
            col=self.cursor_col,
            text=text,
            cursor_pos_before=(self.cursor_row, self.cursor_col)
        )

        # Split pasted text into lines
        paste_lines = text.split('\n')

        if len(paste_lines) == 1:
            # Single line paste - insert into current line
            line = self.lines[self.cursor_row]
            self.lines[self.cursor_row] = (
                line[:self.cursor_col] + paste_lines[0] + line[self.cursor_col:]
            )
            self.cursor_col += len(paste_lines[0])
        else:
            # Multi-line paste
            current_line = self.lines[self.cursor_row]
            before_cursor = current_line[:self.cursor_col]
            after_cursor = current_line[self.cursor_col:]

            # First line: append to text before cursor
            self.lines[self.cursor_row] = before_cursor + paste_lines[0]

            # Insert middle lines
            for i, line in enumerate(paste_lines[1:-1], start=1):
                self.lines.insert(self.cursor_row + i, line)

            # Last line: prepend to text after cursor
            final_line_content = paste_lines[-1] + after_cursor
            self.lines.insert(self.cursor_row + len(paste_lines) - 1, final_line_content)

            # Move cursor to end of pasted content
            self.cursor_row += len(paste_lines) - 1
            self.cursor_col = len(paste_lines[-1])

        change.cursor_pos_after = (self.cursor_row, self.cursor_col)
        self.undo_manager.add_change_block([change])

        self.mark_dirty()

        # Adjust scroll if visible_height provided
        if visible_height is not None:
            self.adjust_scroll(visible_height)

    def delete_char_at_cursor(self):
        """Delete character at cursor position"""
        line = self.lines[self.cursor_row]
        if self.cursor_col < len(line):
            deleted_char = line[self.cursor_col]

            # Record change for undo
            change = Change(
                type=ChangeType.DELETE_CHAR,
                row=self.cursor_row,
                col=self.cursor_col,
                text=deleted_char,
                cursor_pos_before=(self.cursor_row, self.cursor_col)
            )

            self.lines[self.cursor_row] = (
                line[:self.cursor_col] + line[self.cursor_col + 1:]
            )

            change.cursor_pos_after = (self.cursor_row, self.cursor_col)
            self.undo_manager.add_change_block([change])

            self.mark_dirty()

    def backspace(self):
        """Delete character before cursor"""
        if self.cursor_col > 0:
            line = self.lines[self.cursor_row]
            deleted_char = line[self.cursor_col - 1]

            # Record change for undo
            change = Change(
                type=ChangeType.BACKSPACE,
                row=self.cursor_row,
                col=self.cursor_col - 1,
                text=deleted_char,
                cursor_pos_before=(self.cursor_row, self.cursor_col)
            )

            self.lines[self.cursor_row] = (
                line[:self.cursor_col - 1] + line[self.cursor_col:]
            )
            self.cursor_col -= 1

            change.cursor_pos_after = (self.cursor_row, self.cursor_col)
            self.undo_manager.add_change_block([change])

            self.mark_dirty()
        elif self.cursor_row > 0:
            # Join with previous line
            prev_line = self.lines[self.cursor_row - 1]
            current_line = self.lines[self.cursor_row]
            new_cursor_col = len(prev_line)

            # Record change for undo (backspace at line start = delete newline)
            change = Change(
                type=ChangeType.BACKSPACE,
                row=self.cursor_row - 1,
                col=len(prev_line),
                text="\n",  # Represent newline deletion
                cursor_pos_before=(self.cursor_row, self.cursor_col),
                lines_deleted=[current_line]  # Store current line for restoration
            )

            self.cursor_col = new_cursor_col
            self.lines[self.cursor_row - 1] = prev_line + current_line
            self.lines.pop(self.cursor_row)
            self.cursor_row -= 1

            change.cursor_pos_after = (self.cursor_row, self.cursor_col)
            self.undo_manager.add_change_block([change])

            self.mark_dirty()

    def insert_newline(self, visible_height: int = None):
        """Insert a new line at cursor position"""
        line = self.lines[self.cursor_row]

        # Record change for undo
        change = Change(
            type=ChangeType.INSERT_NEWLINE,
            row=self.cursor_row,
            col=self.cursor_col,
            text=line[self.cursor_col:],  # Store the part that moves to new line
            cursor_pos_before=(self.cursor_row, self.cursor_col)
        )

        # Split current line at cursor
        self.lines[self.cursor_row] = line[:self.cursor_col]
        self.lines.insert(self.cursor_row + 1, line[self.cursor_col:])
        self.cursor_row += 1
        self.cursor_col = 0

        change.cursor_pos_after = (self.cursor_row, self.cursor_col)
        self.undo_manager.add_change_block([change])

        self.mark_dirty()
        # Adjust scroll if visible_height provided
        if visible_height is not None:
            self.adjust_scroll(visible_height)

    def delete_line(self):
        """Delete current line"""
        deleted_line = self.lines[self.cursor_row]

        # Record change for undo
        change = Change(
            type=ChangeType.DELETE_LINE,
            row=self.cursor_row,
            col=self.cursor_col,
            cursor_pos_before=(self.cursor_row, self.cursor_col),
            lines_deleted=[deleted_line]
        )

        if len(self.lines) > 1:
            self.lines.pop(self.cursor_row)
            # Adjust cursor position
            if self.cursor_row >= len(self.lines):
                self.cursor_row = len(self.lines) - 1
            self.cursor_col = min(self.cursor_col, self.get_max_cursor_col())
        else:
            # Don't delete the last line, just clear it
            self.lines[0] = ""
            self.cursor_col = 0

        change.cursor_pos_after = (self.cursor_row, self.cursor_col)
        self.undo_manager.add_change_block([change])

        self.mark_dirty()

    def insert_line_below(self, visible_height: int = None):
        """Insert a new empty line below current line"""
        # Record change for undo
        change = Change(
            type=ChangeType.INSERT_NEWLINE,
            row=self.cursor_row,
            col=len(self.lines[self.cursor_row]),  # End of current line
            text="",  # Empty line content
            cursor_pos_before=(self.cursor_row, self.cursor_col)
        )

        self.lines.insert(self.cursor_row + 1, "")
        self.cursor_row += 1
        self.cursor_col = 0

        change.cursor_pos_after = (self.cursor_row, self.cursor_col)
        self.undo_manager.add_change_block([change])

        self.mark_dirty()
        # Adjust scroll if visible_height provided
        if visible_height is not None:
            self.adjust_scroll(visible_height)

    def insert_line_above(self, visible_height: int = None):
        """Insert a new empty line above current line"""
        # Record change for undo
        change = Change(
            type=ChangeType.INSERT_NEWLINE,
            row=self.cursor_row - 1 if self.cursor_row > 0 else 0,
            col=len(self.lines[self.cursor_row - 1]) if self.cursor_row > 0 else 0,
            text="",  # Empty line content
            cursor_pos_before=(self.cursor_row, self.cursor_col)
        )

        self.lines.insert(self.cursor_row, "")
        self.cursor_col = 0

        change.cursor_pos_after = (self.cursor_row, self.cursor_col)
        self.undo_manager.add_change_block([change])

        self.mark_dirty()
        # Adjust scroll if visible_height provided (cursor doesn't move down, but line inserted above)
        if visible_height is not None:
            self.adjust_scroll(visible_height)

    # Search functionality
    def search_forward(self, query: str, visible_height: int = None) -> bool:
        """
        Search for the next occurrence of query from current cursor position.

        Args:
            query: The search string to find
            visible_height: Height of visible editor area for scroll adjustment

        Returns:
            True if match found, False otherwise
        """
        if not query:
            return False

        # Start from current position + 1
        start_row = self.cursor_row
        start_col = self.cursor_col + 1

        # Search from current position to end of current line
        current_line = self.lines[start_row][start_col:]
        if query in current_line:
            match_col = current_line.index(query) + start_col
            self.cursor_col = match_col
            if visible_height is not None:
                self.adjust_scroll(visible_height)
            return True

        # Search remaining lines
        for row in range(start_row + 1, len(self.lines)):
            if query in self.lines[row]:
                self.cursor_row = row
                self.cursor_col = self.lines[row].index(query)
                if visible_height is not None:
                    self.adjust_scroll(visible_height)
                return True

        # Wrap around: search from beginning to current position
        for row in range(0, start_row):
            if query in self.lines[row]:
                self.cursor_row = row
                self.cursor_col = self.lines[row].index(query)
                if visible_height is not None:
                    self.adjust_scroll(visible_height)
                return True

        # Check beginning of current line (before cursor)
        beginning_of_line = self.lines[start_row][:start_col - 1]
        if query in beginning_of_line:
            self.cursor_row = start_row
            self.cursor_col = beginning_of_line.index(query)
            if visible_height is not None:
                self.adjust_scroll(visible_height)
            return True

        return False

    def search_backward(self, query: str, visible_height: int = None) -> bool:
        """
        Search for the previous occurrence of query from current cursor position.

        Args:
            query: The search string to find
            visible_height: Height of visible editor area for scroll adjustment

        Returns:
            True if match found, False otherwise
        """
        if not query:
            return False

        # Start from current position - 1
        start_row = self.cursor_row
        start_col = self.cursor_col - 1

        # Search from current position backward in current line
        if start_col >= 0:
            current_line = self.lines[start_row][:start_col + 1]
            if query in current_line:
                # Find the last occurrence in this substring
                match_col = current_line.rfind(query)
                self.cursor_col = match_col
                if visible_height is not None:
                    self.adjust_scroll(visible_height)
                return True

        # Search previous lines in reverse order
        for row in range(start_row - 1, -1, -1):
            if query in self.lines[row]:
                # Find the last occurrence in this line
                self.cursor_row = row
                self.cursor_col = self.lines[row].rfind(query)
                if visible_height is not None:
                    self.adjust_scroll(visible_height)
                return True

        # Wrap around: search from end to current position
        for row in range(len(self.lines) - 1, start_row, -1):
            if query in self.lines[row]:
                self.cursor_row = row
                self.cursor_col = self.lines[row].rfind(query)
                if visible_height is not None:
                    self.adjust_scroll(visible_height)
                return True

        # Check end of current line (after cursor)
        if start_col < len(self.lines[start_row]) - 1:
            end_of_line = self.lines[start_row][start_col + 1:]
            if query in end_of_line:
                match_col = end_of_line.rfind(query) + start_col + 1
                self.cursor_row = start_row
                self.cursor_col = match_col
                if visible_height is not None:
                    self.adjust_scroll(visible_height)
                return True

        return False

    # Visual mode operations
    def get_selection_text(self, start_row: int, start_col: int, end_row: int, end_col: int) -> str:
        """
        Get the text within the selection range

        Args:
            start_row: Starting row of selection
            start_col: Starting column of selection
            end_row: Ending row of selection
            end_col: Ending column of selection

        Returns:
            The selected text as a string
        """
        if start_row == end_row:
            # Single line selection
            return self.lines[start_row][start_col:end_col + 1]
        else:
            # Multi-line selection
            result = []
            # First line: from start_col to end
            result.append(self.lines[start_row][start_col:])
            # Middle lines: entire lines
            for row in range(start_row + 1, end_row):
                result.append(self.lines[row])
            # Last line: from start to end_col
            result.append(self.lines[end_row][:end_col + 1])
            return '\n'.join(result)

    def yank_selection(self, start_row: int, start_col: int, end_row: int, end_col: int):
        """
        Yank (copy) the selected text to the yank register

        Args:
            start_row: Starting row of selection
            start_col: Starting column of selection
            end_row: Ending row of selection
            end_col: Ending column of selection
        """
        self.yank_register = self.get_selection_text(start_row, start_col, end_row, end_col)
        self.yank_is_linewise = False

    def delete_selection(self, start_row: int, start_col: int, end_row: int, end_col: int, visible_height: int = None):
        """
        Delete the selected text

        Args:
            start_row: Starting row of selection
            start_col: Starting column of selection
            end_row: Ending row of selection
            end_col: Ending column of selection
            visible_height: Height of visible editor area for scroll adjustment
        """
        # Get the deleted text for undo
        deleted_text = self.get_selection_text(start_row, start_col, end_row, end_col)

        # Record change for undo
        change = Change(
            type=ChangeType.DELETE_SELECTION,
            row=start_row,
            col=start_col,
            text=deleted_text,
            cursor_pos_before=(self.cursor_row, self.cursor_col),
            end_row=end_row,
            end_col=end_col
        )

        if start_row == end_row:
            # Single line deletion
            line = self.lines[start_row]
            self.lines[start_row] = line[:start_col] + line[end_col + 1:]
            self.cursor_row = start_row
            self.cursor_col = start_col
        else:
            # Multi-line deletion
            # Combine the part before selection on first line with part after selection on last line
            first_line_before = self.lines[start_row][:start_col]
            last_line_after = self.lines[end_row][end_col + 1:]
            combined_line = first_line_before + last_line_after

            # Delete all lines in the selection range
            del self.lines[start_row:end_row + 1]

            # Insert the combined line
            self.lines.insert(start_row, combined_line)

            # Position cursor at start of deletion
            self.cursor_row = start_row
            self.cursor_col = start_col

        # Ensure cursor is in valid position
        self.cursor_col = min(self.cursor_col, self.get_max_cursor_col())

        change.cursor_pos_after = (self.cursor_row, self.cursor_col)
        self.undo_manager.add_change_block([change])

        self.mark_dirty()

        # Adjust scroll if visible_height provided
        if visible_height is not None:
            self.adjust_scroll(visible_height)

    def paste_from_register(self, after: bool = True, visible_height: int = None):
        """
        Paste text from yank register at cursor position

        Args:
            after: If True, paste after cursor/line (p). If False, paste before (P)
            visible_height: Height of visible editor area for scroll adjustment
        """
        if not self.yank_register:
            return

        if self.yank_is_linewise:
            # Line-wise paste: insert complete lines
            # Remove the trailing newline we added during yank
            text_to_paste = self.yank_register.rstrip('\n')
            lines_to_paste = text_to_paste.split('\n')

            if after:
                # Paste after current line (p)
                insert_pos = self.cursor_row + 1
            else:
                # Paste before current line (P)
                insert_pos = self.cursor_row

            # Insert the lines
            for i, line in enumerate(lines_to_paste):
                self.lines.insert(insert_pos + i, line)

            # Move cursor to first inserted line
            self.cursor_row = insert_pos
            self.cursor_col = 0

            self.mark_dirty()

            if visible_height is not None:
                self.adjust_scroll(visible_height)
        else:
            # Character-wise paste: use existing paste_text method
            if after:
                # Move cursor right before pasting (paste after current position)
                self.move_cursor_right()
            self.paste_text(self.yank_register, visible_height)

    # Visual line mode operations
    def yank_lines(self, start_row: int, end_row: int):
        """
        Yank (copy) entire lines to the yank register

        Args:
            start_row: Starting row (inclusive)
            end_row: Ending row (inclusive)
        """
        lines_to_yank = self.lines[start_row:end_row + 1]
        # Join with newlines and add trailing newline to indicate line-wise yank
        self.yank_register = '\n'.join(lines_to_yank) + '\n'
        self.yank_is_linewise = True

    def delete_lines(self, start_row: int, end_row: int, visible_height: int = None):
        """
        Delete entire lines

        Args:
            start_row: Starting row (inclusive)
            end_row: Ending row (inclusive)
            visible_height: Height of visible editor area for scroll adjustment
        """
        # Store the lines for yanking
        self.yank_lines(start_row, end_row)

        # Get deleted lines for undo
        deleted_lines = self.lines[start_row:end_row + 1].copy()

        # Record change for undo
        change = Change(
            type=ChangeType.DELETE_LINES,
            row=start_row,
            col=self.cursor_col,
            cursor_pos_before=(self.cursor_row, self.cursor_col),
            lines_deleted=deleted_lines,
            end_row=end_row
        )

        # Delete the lines
        del self.lines[start_row:end_row + 1]

        # If we deleted all lines, add an empty line
        if not self.lines:
            self.lines = [""]

        # Position cursor at start of deletion
        self.cursor_row = min(start_row, len(self.lines) - 1)
        self.cursor_col = 0

        # Ensure cursor is in valid position
        self.cursor_col = min(self.cursor_col, self.get_max_cursor_col())

        change.cursor_pos_after = (self.cursor_row, self.cursor_col)
        self.undo_manager.add_change_block([change])

        self.mark_dirty()

        # Adjust scroll if visible_height provided
        if visible_height is not None:
            self.adjust_scroll(visible_height)

    # Undo/Redo operations
    def undo(self, visible_height: int = None) -> bool:
        """
        Undo the last change

        Args:
            visible_height: Height of visible editor area for scroll adjustment

        Returns:
            True if undo was performed, False if nothing to undo
        """
        change_block = self.undo_manager.get_undo_block()
        if not change_block:
            return False

        # Apply changes in reverse order
        for change in reversed(change_block):
            self._undo_change(change)

        # Restore cursor position from first change in block
        if change_block and change_block[0].cursor_pos_before:
            self.cursor_row, self.cursor_col = change_block[0].cursor_pos_before

        # Adjust scroll if visible_height provided
        if visible_height is not None:
            self.adjust_scroll(visible_height)

        self.mark_dirty()
        return True

    def redo(self, visible_height: int = None) -> bool:
        """
        Redo the last undone change

        Args:
            visible_height: Height of visible editor area for scroll adjustment

        Returns:
            True if redo was performed, False if nothing to redo
        """
        change_block = self.undo_manager.get_redo_block()
        if not change_block:
            return False

        # Apply changes in forward order
        for change in change_block:
            self._redo_change(change)

        # Restore cursor position from last change in block
        if change_block and change_block[-1].cursor_pos_after:
            self.cursor_row, self.cursor_col = change_block[-1].cursor_pos_after

        # Adjust scroll if visible_height provided
        if visible_height is not None:
            self.adjust_scroll(visible_height)

        self.mark_dirty()
        return True

    def _undo_change(self, change: Change):
        """
        Undo a single change (inverse operation)

        Args:
            change: The change to undo
        """
        if change.type == ChangeType.INSERT_CHAR:
            # Undo insert: delete the character
            line = self.lines[change.row]
            self.lines[change.row] = line[:change.col] + line[change.col + 1:]

        elif change.type == ChangeType.DELETE_CHAR:
            # Undo delete: insert the character back
            line = self.lines[change.row]
            self.lines[change.row] = line[:change.col] + change.text + line[change.col:]

        elif change.type == ChangeType.BACKSPACE:
            if change.text == "\n":
                # Undo backspace at line start: split the line back
                line = self.lines[change.row]
                self.lines[change.row] = line[:change.col]
                if change.lines_deleted:
                    self.lines.insert(change.row + 1, change.lines_deleted[0])
            else:
                # Undo backspace: insert the character back
                line = self.lines[change.row]
                self.lines[change.row] = line[:change.col] + change.text + line[change.col:]

        elif change.type == ChangeType.INSERT_NEWLINE:
            # Undo newline: join the lines back
            if change.row + 1 < len(self.lines):
                line = self.lines[change.row]
                next_line = self.lines[change.row + 1]
                self.lines[change.row] = line + change.text
                self.lines.pop(change.row + 1)

        elif change.type == ChangeType.DELETE_LINE:
            # Undo delete line: restore the line
            if change.lines_deleted:
                if len(self.lines) == 1 and self.lines[0] == "":
                    # If buffer only has empty line, replace it
                    self.lines[0] = change.lines_deleted[0]
                else:
                    self.lines.insert(change.row, change.lines_deleted[0])

        elif change.type == ChangeType.DELETE_SELECTION:
            # Undo delete selection: restore the text
            self._restore_text_at_position(change.row, change.col, change.text)

        elif change.type == ChangeType.DELETE_LINES:
            # Undo delete lines: restore all deleted lines
            if change.lines_deleted:
                for i, line in enumerate(change.lines_deleted):
                    self.lines.insert(change.row + i, line)
                # Remove empty line if it was added
                if len(self.lines) > len(change.lines_deleted) and self.lines[-1] == "" and change.end_row is not None:
                    if change.end_row - change.row + 1 == len(change.lines_deleted):
                        # Check if last line should be removed (was added when buffer became empty)
                        pass

        elif change.type == ChangeType.PASTE_TEXT:
            # Undo paste: delete the pasted text
            paste_lines = change.text.split('\n')
            if len(paste_lines) == 1:
                # Single line paste - remove from current line
                line = self.lines[change.row]
                self.lines[change.row] = line[:change.col] + line[change.col + len(change.text):]
            else:
                # Multi-line paste - remove inserted lines
                # Restore original line
                current_line = self.lines[change.row]
                end_row = change.row + len(paste_lines) - 1
                last_line = self.lines[end_row] if end_row < len(self.lines) else ""

                # Get original content before and after paste
                before_paste = current_line[:change.col]
                after_paste = last_line[len(paste_lines[-1]):]

                # Remove all pasted lines
                del self.lines[change.row:end_row + 1]

                # Insert original line back
                self.lines.insert(change.row, before_paste + after_paste)

    def _redo_change(self, change: Change):
        """
        Redo a single change (re-apply operation)

        Args:
            change: The change to redo
        """
        if change.type == ChangeType.INSERT_CHAR:
            # Redo insert: insert the character
            line = self.lines[change.row]
            self.lines[change.row] = line[:change.col] + change.text + line[change.col:]

        elif change.type == ChangeType.DELETE_CHAR:
            # Redo delete: delete the character
            line = self.lines[change.row]
            self.lines[change.row] = line[:change.col] + line[change.col + 1:]

        elif change.type == ChangeType.BACKSPACE:
            if change.text == "\n":
                # Redo backspace at line start: join lines
                if change.row + 1 < len(self.lines):
                    prev_line = self.lines[change.row]
                    current_line = self.lines[change.row + 1]
                    self.lines[change.row] = prev_line + current_line
                    self.lines.pop(change.row + 1)
            else:
                # Redo backspace: delete the character
                line = self.lines[change.row]
                self.lines[change.row] = line[:change.col] + line[change.col + 1:]

        elif change.type == ChangeType.INSERT_NEWLINE:
            # Redo newline: split the line
            line = self.lines[change.row]
            self.lines[change.row] = line[:change.col]
            self.lines.insert(change.row + 1, change.text)

        elif change.type == ChangeType.DELETE_LINE:
            # Redo delete line: delete the line again
            if len(self.lines) > 1:
                self.lines.pop(change.row)
            else:
                self.lines[0] = ""

        elif change.type == ChangeType.DELETE_SELECTION:
            # Redo delete selection: delete the text again
            if change.end_row is not None and change.end_col is not None:
                start_row, start_col = change.row, change.col
                end_row, end_col = change.end_row, change.end_col

                if start_row == end_row:
                    line = self.lines[start_row]
                    self.lines[start_row] = line[:start_col] + line[end_col + 1:]
                else:
                    first_line_before = self.lines[start_row][:start_col]
                    last_line_after = self.lines[end_row][end_col + 1:]
                    combined_line = first_line_before + last_line_after
                    del self.lines[start_row:end_row + 1]
                    self.lines.insert(start_row, combined_line)

        elif change.type == ChangeType.DELETE_LINES:
            # Redo delete lines: delete the lines again
            if change.end_row is not None:
                del self.lines[change.row:change.end_row + 1]
                if not self.lines:
                    self.lines = [""]

        elif change.type == ChangeType.PASTE_TEXT:
            # Redo paste: paste the text again
            paste_lines = change.text.split('\n')
            if len(paste_lines) == 1:
                line = self.lines[change.row]
                self.lines[change.row] = line[:change.col] + change.text + line[change.col:]
            else:
                current_line = self.lines[change.row]
                before_cursor = current_line[:change.col]
                after_cursor = current_line[change.col:]

                self.lines[change.row] = before_cursor + paste_lines[0]

                for i, line in enumerate(paste_lines[1:-1], start=1):
                    self.lines.insert(change.row + i, line)

                final_line_content = paste_lines[-1] + after_cursor
                self.lines.insert(change.row + len(paste_lines) - 1, final_line_content)

    def _restore_text_at_position(self, row: int, col: int, text: str):
        """
        Restore text at a specific position (for undo of deletions)

        Args:
            row: Row to restore text at
            col: Column to restore text at
            text: Text to restore
        """
        text_lines = text.split('\n')
        if len(text_lines) == 1:
            # Single line restore
            line = self.lines[row]
            self.lines[row] = line[:col] + text + line[col:]
        else:
            # Multi-line restore
            current_line = self.lines[row]
            before = current_line[:col]
            after = current_line[col:]

            self.lines[row] = before + text_lines[0]

            for i, line in enumerate(text_lines[1:-1], start=1):
                self.lines.insert(row + i, line)

            self.lines.insert(row + len(text_lines) - 1, text_lines[-1] + after)
