"""
Key binding handlers for different modes
"""

from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
from .editor import EditorBuffer
from .modes import ModeManager
from .note_list import NoteListManager
from .focus import FocusManager


def create_key_bindings(
    buffer: EditorBuffer,
    mode_manager: ModeManager,
    note_list_manager: NoteListManager,
    focus_manager: FocusManager,
    ui  # EditorUI instance for save/load operations
) -> KeyBindings:
    """Create key bindings for the editor with sidebar support"""
    kb = KeyBindings()

    # Create filter conditions
    is_normal_mode = Condition(lambda: mode_manager.is_normal_mode())
    is_insert_mode = Condition(lambda: mode_manager.is_insert_mode())
    is_command_mode = Condition(lambda: mode_manager.command_buffer.startswith(':'))
    is_search_mode = Condition(lambda: mode_manager.is_search_mode())
    is_sidebar_focused = Condition(lambda: focus_manager.is_sidebar_focused())
    is_editor_focused = Condition(lambda: focus_manager.is_editor_focused())

    # ===== SIDEBAR NAVIGATION (NORMAL MODE, SIDEBAR FOCUSED) =====

    @kb.add('j', filter=is_sidebar_focused & is_normal_mode)
    @kb.add('down', filter=is_sidebar_focused & is_normal_mode)
    def sidebar_move_down(event):
        """Move selection down in sidebar"""
        note_list_manager.move_selection_down()

    @kb.add('k', filter=is_sidebar_focused & is_normal_mode)
    @kb.add('up', filter=is_sidebar_focused & is_normal_mode)
    def sidebar_move_up(event):
        """Move selection up in sidebar"""
        note_list_manager.move_selection_up()

    @kb.add('enter', filter=is_sidebar_focused & is_normal_mode)
    def sidebar_select_note(event):
        """Select note and load into editor"""
        selected_note = note_list_manager.selected_note
        if selected_note:
            # Use UI's load_note which checks for unsaved changes
            ui.load_note(selected_note)
            # Switch focus to editor if load was successful
            if not buffer.is_dirty or buffer.current_note_id == selected_note.id:
                focus_manager.switch_to_editor()

    # ===== EDITOR NORMAL MODE BINDINGS (ONLY WHEN EDITOR FOCUSED) =====

    @kb.add('h', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    @kb.add('left', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def move_left(event):
        """Move cursor left in normal mode"""
        buffer.move_cursor_left()
        mode_manager.clear_command_buffer()

    @kb.add('j', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    @kb.add('down', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def move_down(event):
        """Move cursor down in normal mode"""
        buffer.move_cursor_down(ui.editor_window_height)
        mode_manager.clear_command_buffer()

    @kb.add('k', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    @kb.add('up', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def move_up(event):
        """Move cursor up in normal mode"""
        buffer.move_cursor_up(ui.editor_window_height)
        mode_manager.clear_command_buffer()

    @kb.add('l', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    @kb.add('right', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def move_right(event):
        """Move cursor right in normal mode"""
        buffer.move_cursor_right()
        mode_manager.clear_command_buffer()

    @kb.add('0', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def move_line_start(event):
        """Move to start of line"""
        buffer.move_cursor_to_line_start()
        mode_manager.clear_command_buffer()

    @kb.add('$', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def move_line_end(event):
        """Move to end of line"""
        buffer.move_cursor_to_line_end()
        mode_manager.clear_command_buffer()

    @kb.add('c-d', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def half_page_down(event):
        """Scroll down half a page"""
        buffer.half_page_down(ui.editor_window_height)
        mode_manager.clear_command_buffer()

    @kb.add('c-u', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def half_page_up(event):
        """Scroll up half a page"""
        buffer.half_page_up(ui.editor_window_height)
        mode_manager.clear_command_buffer()

    @kb.add('pagedown', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def page_down_key(event):
        """Scroll down one page"""
        buffer.page_down(ui.editor_window_height)
        mode_manager.clear_command_buffer()

    @kb.add('pageup', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def page_up_key(event):
        """Scroll up one page"""
        buffer.page_up(ui.editor_window_height)
        mode_manager.clear_command_buffer()

    @kb.add('i', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def enter_insert_mode(event):
        """Enter insert mode"""
        mode_manager.enter_insert_mode()
        mode_manager.clear_command_buffer()

    @kb.add('a', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def append_mode(event):
        """Enter insert mode after cursor"""
        buffer.move_cursor_right()
        mode_manager.enter_insert_mode()
        mode_manager.clear_command_buffer()

    @kb.add('o', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def open_line_below(event):
        """Open new line below and enter insert mode"""
        buffer.insert_line_below(ui.editor_window_height)
        mode_manager.enter_insert_mode()
        mode_manager.clear_command_buffer()

    @kb.add('O', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def open_line_above(event):
        """Open new line above and enter insert mode"""
        buffer.insert_line_above(ui.editor_window_height)
        mode_manager.enter_insert_mode()
        mode_manager.clear_command_buffer()

    @kb.add('x', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def delete_char(event):
        """Delete character under cursor"""
        buffer.delete_char_at_cursor()
        mode_manager.clear_command_buffer()

    @kb.add('n', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def repeat_search(event):
        """Repeat last search in same direction"""
        if mode_manager.last_search:
            if mode_manager.last_search_direction == "forward":
                found = buffer.search_forward(mode_manager.last_search, ui.editor_window_height)
            else:
                found = buffer.search_backward(mode_manager.last_search, ui.editor_window_height)
            if not found:
                mode_manager.set_message(f"Pattern not found: {mode_manager.last_search}")
            else:
                mode_manager.clear_message()
        else:
            mode_manager.set_message("No previous search pattern")
        mode_manager.clear_command_buffer()

    @kb.add('N', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def repeat_search_opposite(event):
        """Repeat last search in opposite direction"""
        if mode_manager.last_search:
            if mode_manager.last_search_direction == "forward":
                found = buffer.search_backward(mode_manager.last_search, ui.editor_window_height)
            else:
                found = buffer.search_forward(mode_manager.last_search, ui.editor_window_height)
            if not found:
                mode_manager.set_message(f"Pattern not found: {mode_manager.last_search}")
            else:
                mode_manager.clear_message()
        else:
            mode_manager.set_message("No previous search pattern")
        mode_manager.clear_command_buffer()

    # ===== FOCUS SWITCHING (CTRL+W combinations in NORMAL MODE) =====

    @kb.add('c-w', 'h', filter=is_normal_mode)
    @kb.add('c-w', 'left', filter=is_normal_mode)
    def switch_to_sidebar(event):
        """Switch focus to sidebar"""
        focus_manager.switch_to_sidebar()
        mode_manager.clear_command_buffer()

    @kb.add('c-w', 'l', filter=is_normal_mode)
    @kb.add('c-w', 'right', filter=is_normal_mode)
    def switch_to_editor(event):
        """Switch focus to editor"""
        focus_manager.switch_to_editor()
        mode_manager.clear_command_buffer()

    # ===== COMMAND MODE (works in both sidebar and editor) =====

    @kb.add(':', filter=is_normal_mode & ~is_command_mode & ~is_search_mode)
    def command_mode(event):
        """Enter command mode"""
        mode_manager.add_to_command_buffer(':')

    # ===== SEARCH MODE (editor only) =====

    @kb.add('/', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def search_forward_mode(event):
        """Enter forward search mode"""
        mode_manager.start_search_forward()

    @kb.add('?', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def search_backward_mode(event):
        """Enter backward search mode"""
        mode_manager.start_search_backward()

    @kb.add('enter', filter=is_search_mode)
    def execute_search(event):
        """Execute the search when Enter is pressed"""
        is_forward = mode_manager.command_buffer.startswith('/')
        mode_manager.execute_search()
        # Perform the search
        if mode_manager.search_query:
            if is_forward:
                found = buffer.search_forward(mode_manager.search_query, ui.editor_window_height)
            else:
                found = buffer.search_backward(mode_manager.search_query, ui.editor_window_height)
            if not found:
                mode_manager.set_message(f"Pattern not found: {mode_manager.search_query}")
            else:
                mode_manager.clear_message()
        else:
            mode_manager.clear_message()

    @kb.add('backspace', filter=is_search_mode)
    def search_backspace(event):
        """Remove last character from search buffer"""
        if len(mode_manager.command_buffer) > 1:  # Keep the '/' or '?'
            mode_manager.command_buffer = mode_manager.command_buffer[:-1]
        else:
            # If only '/' or '?' left, exit search mode
            mode_manager.clear_command_buffer()

    @kb.add('escape', filter=is_search_mode)
    def cancel_search(event):
        """Cancel search mode with Escape"""
        mode_manager.clear_command_buffer()

    # When in search mode (after /), capture printable characters
    @kb.add('<any>', filter=is_search_mode)
    def add_to_search(event):
        """Add character to search buffer"""
        if len(event.data) == 1 and event.data.isprintable():
            mode_manager.add_to_command_buffer(event.data)

    @kb.add('enter', filter=is_command_mode)
    def execute_command(event):
        """Execute the command when Enter is pressed"""
        command = mode_manager.command_buffer

        if command == ':q':
            if buffer.is_dirty:
                mode_manager.set_message("Unsaved changes! :w to save, :q! to quit without saving")
                mode_manager.clear_command_buffer()
            else:
                event.app.exit()
        elif command == ':q!':
            event.app.exit()
        elif command == ':w':
            ui.save_current_note()
            mode_manager.clear_command_buffer()
        elif command == ':wq':
            ui.save_current_note()
            event.app.exit()
        elif command == ':e!':
            # Force load pending note if there is one
            if ui.pending_note_switch:
                ui.force_load_note(ui.pending_note_switch)
                if focus_manager.is_sidebar_focused():
                    focus_manager.switch_to_editor()
            else:
                mode_manager.set_message("No pending note to load")
            mode_manager.clear_command_buffer()
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

    # ===== INSERT MODE BINDINGS (EDITOR ONLY) =====

    @kb.add('escape', filter=is_editor_focused & is_insert_mode)
    def exit_insert_mode(event):
        """Exit insert mode"""
        mode_manager.enter_normal_mode()
        # Move cursor left in normal mode (vim behavior)
        buffer.move_cursor_left()

    @kb.add('enter', filter=is_editor_focused & is_insert_mode)
    def insert_newline(event):
        """Insert new line in insert mode"""
        buffer.insert_newline(ui.editor_window_height)

    @kb.add('backspace', filter=is_editor_focused & is_insert_mode)
    def backspace_char(event):
        """Delete character before cursor in insert mode"""
        buffer.backspace()

    @kb.add('tab', filter=is_editor_focused & is_insert_mode)
    def insert_tab(event):
        """Insert tab as 4 spaces in insert mode"""
        for _ in range(4):
            buffer.insert_char(' ')

    # Arrow keys in insert mode
    @kb.add('left', filter=is_editor_focused & is_insert_mode)
    def insert_move_left(event):
        """Move cursor left in insert mode"""
        buffer.move_cursor_left()

    @kb.add('right', filter=is_editor_focused & is_insert_mode)
    def insert_move_right(event):
        """Move cursor right in insert mode"""
        buffer.move_cursor_right()

    @kb.add('up', filter=is_editor_focused & is_insert_mode)
    def insert_move_up(event):
        """Move cursor up in insert mode"""
        buffer.move_cursor_up(ui.editor_window_height)

    @kb.add('down', filter=is_editor_focused & is_insert_mode)
    def insert_move_down(event):
        """Move cursor down in insert mode"""
        buffer.move_cursor_down(ui.editor_window_height)

    # Catch all printable characters in insert mode
    @kb.add('<any>', filter=is_editor_focused & is_insert_mode)
    def insert_character(event):
        """Insert any printable character in insert mode"""
        if len(event.data) == 1 and event.data.isprintable():
            buffer.insert_char(event.data)

    # Additional normal mode bindings to clear command buffer on other keys
    @kb.add('escape', filter=is_normal_mode & ~is_command_mode)
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
