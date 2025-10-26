"""
Mode management for the editor
"""

from .editor import Mode


class ModeManager:
    """Manages editor mode state and transitions"""

    def __init__(self):
        self.current_mode = Mode.NORMAL
        self.command_buffer = ""  # For commands like :q, :w, dd, etc.
        self.message = ""  # Status message to display
        self.search_query = ""  # Current search query
        self.last_search = ""  # Last executed search for n command
        self.last_search_direction = "forward"  # Direction of last search: "forward" or "backward"
        # Visual mode state
        self.visual_start_row = 0  # Starting row of visual selection
        self.visual_start_col = 0  # Starting column of visual selection

    def set_mode(self, mode: Mode):
        """Change the current mode"""
        self.current_mode = mode
        self.command_buffer = ""

    def is_normal_mode(self) -> bool:
        """Check if in normal mode"""
        return self.current_mode == Mode.NORMAL

    def is_insert_mode(self) -> bool:
        """Check if in insert mode"""
        return self.current_mode == Mode.INSERT

    def is_visual_mode(self) -> bool:
        """Check if in visual mode"""
        return self.current_mode == Mode.VISUAL

    def enter_insert_mode(self):
        """Enter insert mode"""
        self.set_mode(Mode.INSERT)

    def enter_normal_mode(self):
        """Enter normal mode"""
        self.set_mode(Mode.NORMAL)

    def enter_visual_mode(self, start_row: int, start_col: int):
        """
        Enter visual mode with the given starting position

        Args:
            start_row: Starting row of the selection
            start_col: Starting column of the selection
        """
        self.current_mode = Mode.VISUAL
        self.visual_start_row = start_row
        self.visual_start_col = start_col
        self.command_buffer = ""

    def get_visual_selection(self, current_row: int, current_col: int):
        """
        Get the visual selection range, normalized so start is before end

        Args:
            current_row: Current cursor row
            current_col: Current cursor column

        Returns:
            Tuple of (start_row, start_col, end_row, end_col) where start is always before end
        """
        # Normalize selection so start is always before end
        if self.visual_start_row < current_row:
            return (self.visual_start_row, self.visual_start_col, current_row, current_col)
        elif self.visual_start_row > current_row:
            return (current_row, current_col, self.visual_start_row, self.visual_start_col)
        else:
            # Same row
            if self.visual_start_col <= current_col:
                return (self.visual_start_row, self.visual_start_col, current_row, current_col)
            else:
                return (current_row, current_col, self.visual_start_row, self.visual_start_col)

    def add_to_command_buffer(self, char: str):
        """Add a character to the command buffer (for multi-key commands)"""
        self.command_buffer += char

    def clear_command_buffer(self):
        """Clear the command buffer"""
        self.command_buffer = ""

    def set_message(self, message: str):
        """Set a status message"""
        self.message = message

    def clear_message(self):
        """Clear the status message"""
        self.message = ""

    def get_mode_string(self) -> str:
        """Get display string for current mode"""
        if self.current_mode == Mode.INSERT:
            return "-- INSERT --"
        elif self.current_mode == Mode.VISUAL:
            return "-- VISUAL --"
        elif self.command_buffer.startswith('/') or self.command_buffer.startswith('?'):
            return self.command_buffer
        elif self.command_buffer:
            return self.command_buffer
        else:
            return ""

    def is_search_mode(self) -> bool:
        """Check if in search mode"""
        return self.command_buffer.startswith('/') or self.command_buffer.startswith('?')

    def is_forward_search(self) -> bool:
        """Check if in forward search mode"""
        return self.command_buffer.startswith('/')

    def is_backward_search(self) -> bool:
        """Check if in backward search mode"""
        return self.command_buffer.startswith('?')

    def start_search_forward(self):
        """Start forward search mode"""
        self.command_buffer = "/"
        self.search_query = ""

    def start_search_backward(self):
        """Start backward search mode"""
        self.command_buffer = "?"
        self.search_query = ""

    def execute_search(self):
        """Execute the current search and save it"""
        if self.command_buffer.startswith('/'):
            self.search_query = self.command_buffer[1:]  # Remove '/' prefix
            self.last_search_direction = "forward"
        elif self.command_buffer.startswith('?'):
            self.search_query = self.command_buffer[1:]  # Remove '?' prefix
            self.last_search_direction = "backward"
        self.last_search = self.search_query
        self.command_buffer = ""
