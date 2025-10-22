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

    def enter_insert_mode(self):
        """Enter insert mode"""
        self.set_mode(Mode.INSERT)

    def enter_normal_mode(self):
        """Enter normal mode"""
        self.set_mode(Mode.NORMAL)

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
        elif self.command_buffer:
            return self.command_buffer
        else:
            return ""
