"""
Key binding handlers for different modes
"""

from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
from .editor import EditorBuffer
from .modes import ModeManager


def create_key_bindings(buffer: EditorBuffer, mode_manager: ModeManager) -> KeyBindings:
    """Create key bindings for the editor"""
    kb = KeyBindings()

    # Create filter conditions
    is_normal_mode = Condition(lambda: mode_manager.is_normal_mode())
    is_insert_mode = Condition(lambda: mode_manager.is_insert_mode())
    is_command_mode = Condition(lambda: mode_manager.command_buffer.startswith(':'))

    # ===== NORMAL MODE BINDINGS =====

    @kb.add('h', filter=is_normal_mode & ~is_command_mode)
    @kb.add('left', filter=is_normal_mode & ~is_command_mode)
    def move_left(event):
        """Move cursor left in normal mode"""
        buffer.move_cursor_left()
        mode_manager.clear_command_buffer()

    @kb.add('j', filter=is_normal_mode & ~is_command_mode)
    @kb.add('down', filter=is_normal_mode & ~is_command_mode)
    def move_down(event):
        """Move cursor down in normal mode"""
        buffer.move_cursor_down()
        mode_manager.clear_command_buffer()

    @kb.add('k', filter=is_normal_mode & ~is_command_mode)
    @kb.add('up', filter=is_normal_mode & ~is_command_mode)
    def move_up(event):
        """Move cursor up in normal mode"""
        buffer.move_cursor_up()
        mode_manager.clear_command_buffer()

    @kb.add('l', filter=is_normal_mode & ~is_command_mode)
    @kb.add('right', filter=is_normal_mode & ~is_command_mode)
    def move_right(event):
        """Move cursor right in normal mode"""
        buffer.move_cursor_right()
        mode_manager.clear_command_buffer()

    @kb.add('0', filter=is_normal_mode & ~is_command_mode)
    def move_line_start(event):
        """Move to start of line"""
        buffer.move_cursor_to_line_start()
        mode_manager.clear_command_buffer()

    @kb.add('$', filter=is_normal_mode & ~is_command_mode)
    def move_line_end(event):
        """Move to end of line"""
        buffer.move_cursor_to_line_end()
        mode_manager.clear_command_buffer()

    @kb.add('i', filter=is_normal_mode & ~is_command_mode)
    def enter_insert_mode(event):
        """Enter insert mode"""
        mode_manager.enter_insert_mode()
        mode_manager.clear_command_buffer()

    @kb.add('a', filter=is_normal_mode & ~is_command_mode)
    def append_mode(event):
        """Enter insert mode after cursor"""
        buffer.move_cursor_right()
        mode_manager.enter_insert_mode()
        mode_manager.clear_command_buffer()

    @kb.add('o', filter=is_normal_mode & ~is_command_mode)
    def open_line_below(event):
        """Open new line below and enter insert mode"""
        buffer.insert_line_below()
        mode_manager.enter_insert_mode()
        mode_manager.clear_command_buffer()

    @kb.add('O', filter=is_normal_mode & ~is_command_mode)
    def open_line_above(event):
        """Open new line above and enter insert mode"""
        buffer.insert_line_above()
        mode_manager.enter_insert_mode()
        mode_manager.clear_command_buffer()

    @kb.add('x', filter=is_normal_mode & ~is_command_mode)
    def delete_char(event):
        """Delete character under cursor"""
        buffer.delete_char_at_cursor()
        mode_manager.clear_command_buffer()

    @kb.add(':', filter=is_normal_mode & ~is_command_mode)
    def command_mode(event):
        """Enter command mode"""
        mode_manager.add_to_command_buffer(':')

    @kb.add('enter', filter=is_command_mode)
    def execute_command(event):
        """Execute the command when Enter is pressed"""
        command = mode_manager.command_buffer

        if command == ':q':
            event.app.exit()
        elif command == ':w':
            mode_manager.set_message("File saved (mock)")
            mode_manager.clear_command_buffer()
        elif command == ':wq':
            mode_manager.set_message("File saved (mock)")
            event.app.exit()
        else:
            mode_manager.set_message(f"Unknown command: {command}")
            mode_manager.clear_command_buffer()

    @kb.add('backspace', filter=is_command_mode)
    def command_backspace(event):
        """Remove last character from command buffer"""
        if len(mode_manager.command_buffer) > 1:  # Keep the ':'
            mode_manager.command_buffer = mode_manager.command_buffer[:-1]
        else:
            # If only ':' left, exit command mode
            mode_manager.clear_command_buffer()

    @kb.add('escape', filter=is_command_mode)
    def cancel_command(event):
        """Cancel command mode with Escape"""
        mode_manager.clear_command_buffer()

    # When in command mode (after :), capture printable characters
    @kb.add('<any>', filter=is_command_mode)
    def add_to_command(event):
        """Add character to command buffer"""
        if len(event.data) == 1 and event.data.isprintable():
            mode_manager.add_to_command_buffer(event.data)

    # ===== INSERT MODE BINDINGS =====

    @kb.add('escape', filter=is_insert_mode)
    def exit_insert_mode(event):
        """Exit insert mode"""
        mode_manager.enter_normal_mode()
        # Move cursor left in normal mode (vim behavior)
        buffer.move_cursor_left()

    @kb.add('enter', filter=is_insert_mode)
    def insert_newline(event):
        """Insert new line in insert mode"""
        buffer.insert_newline()

    @kb.add('backspace', filter=is_insert_mode)
    def backspace_char(event):
        """Delete character before cursor in insert mode"""
        buffer.backspace()

    # Arrow keys in insert mode
    @kb.add('left', filter=is_insert_mode)
    def insert_move_left(event):
        """Move cursor left in insert mode"""
        buffer.move_cursor_left()

    @kb.add('right', filter=is_insert_mode)
    def insert_move_right(event):
        """Move cursor right in insert mode"""
        buffer.move_cursor_right()

    @kb.add('up', filter=is_insert_mode)
    def insert_move_up(event):
        """Move cursor up in insert mode"""
        buffer.move_cursor_up()

    @kb.add('down', filter=is_insert_mode)
    def insert_move_down(event):
        """Move cursor down in insert mode"""
        buffer.move_cursor_down()

    # Catch all printable characters in insert mode
    @kb.add('<any>', filter=is_insert_mode)
    def insert_character(event):
        """Insert any printable character in insert mode"""
        if len(event.data) == 1 and event.data.isprintable():
            buffer.insert_char(event.data)

    # Additional normal mode bindings to clear command buffer on other keys
    @kb.add('escape', filter=is_normal_mode)
    def clear_command(event):
        """Clear command buffer in normal mode"""
        mode_manager.clear_command_buffer()
        mode_manager.clear_message()

    # Global bindings
    @kb.add('c-c')
    @kb.add('c-q')
    def force_quit(event):
        """Force quit with Ctrl+C or Ctrl+Q"""
        event.app.exit()

    return kb
