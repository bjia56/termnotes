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
        self.scroll_offset: int = 0  # Top line currently displayed
        self.horizontal_scroll_offset: int = 0  # Leftmost column currently displayed
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
        self.scroll_offset = 0
        self.horizontal_scroll_offset = 0
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

    def move_cursor_up(self, visible_height: int = None):
        """Move cursor up"""
        if self.cursor_row > 0:
            self.cursor_row -= 1
            # Adjust column if necessary
            self.cursor_col = min(self.cursor_col, len(self.current_line))
            # Adjust scroll if visible_height provided
            if visible_height is not None:
                self.adjust_scroll(visible_height)

    def move_cursor_down(self, visible_height: int = None):
        """Move cursor down"""
        if self.cursor_row < len(self.lines) - 1:
            self.cursor_row += 1
            # Adjust column if necessary
            self.cursor_col = min(self.cursor_col, len(self.current_line))
            # Adjust scroll if visible_height provided
            if visible_height is not None:
                self.adjust_scroll(visible_height)

    def move_cursor_to_line_start(self):
        """Move cursor to start of line"""
        self.cursor_col = 0

    def move_cursor_to_line_end(self):
        """Move cursor to end of line"""
        self.cursor_col = len(self.current_line)

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
        self.cursor_col = min(self.cursor_col, len(self.current_line))

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
        self.cursor_col = min(self.cursor_col, len(self.current_line))

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
        self.cursor_col = min(self.cursor_col, len(self.current_line))

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
        self.cursor_col = min(self.cursor_col, len(self.current_line))

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

    def insert_newline(self, visible_height: int = None):
        """Insert a new line at cursor position"""
        line = self.lines[self.cursor_row]
        # Split current line at cursor
        self.lines[self.cursor_row] = line[:self.cursor_col]
        self.lines.insert(self.cursor_row + 1, line[self.cursor_col:])
        self.cursor_row += 1
        self.cursor_col = 0
        self.mark_dirty()
        # Adjust scroll if visible_height provided
        if visible_height is not None:
            self.adjust_scroll(visible_height)

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

    def insert_line_below(self, visible_height: int = None):
        """Insert a new empty line below current line"""
        self.lines.insert(self.cursor_row + 1, "")
        self.cursor_row += 1
        self.cursor_col = 0
        self.mark_dirty()
        # Adjust scroll if visible_height provided
        if visible_height is not None:
            self.adjust_scroll(visible_height)

    def insert_line_above(self, visible_height: int = None):
        """Insert a new empty line above current line"""
        self.lines.insert(self.cursor_row, "")
        self.cursor_col = 0
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
