"""
Key binding handlers for different modes
"""

from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
from prompt_toolkit.keys import Keys
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
    is_visual_mode = Condition(lambda: mode_manager.is_visual_mode())
    is_visual_line_mode = Condition(lambda: mode_manager.is_visual_line_mode())
    is_any_visual_mode = Condition(lambda: mode_manager.is_any_visual_mode())
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

    @kb.add('o', filter=is_sidebar_focused & is_normal_mode)
    def sidebar_create_note(event):
        """Create a new empty note from sidebar, focus editor, and enter Insert mode"""
        ui.create_new_note()
        # Enter Insert mode after creating the note
        mode_manager.enter_insert_mode()

    @kb.add('d', filter=is_sidebar_focused & is_normal_mode & ~is_command_mode)
    def sidebar_delete_first_d(event):
        """Handle first 'd' in sidebar for dd deletion"""
        if mode_manager.command_buffer == 'd':
            # Second 'd' pressed - confirm deletion
            selected_note = note_list_manager.selected_note
            if selected_note:
                if ui.pending_deletion == selected_note.id:
                    # Confirmed - delete the note
                    ui.delete_note(selected_note.id)
                    mode_manager.clear_command_buffer()
                else:
                    # First dd - set pending deletion
                    ui.pending_deletion = selected_note.id
                    mode_manager.set_message("Delete note? Press dd again to confirm")
                    mode_manager.clear_command_buffer()
        else:
            # First 'd' pressed
            mode_manager.add_to_command_buffer('d')

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

    @kb.add('home', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def move_line_start_home(event):
        """Move to start of line with Home key"""
        buffer.move_cursor_to_line_start()
        mode_manager.clear_command_buffer()

    @kb.add('end', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def move_line_end_end(event):
        """Move to end of line with End key"""
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
    @kb.add('delete', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def delete_char(event):
        """Delete character under cursor"""
        buffer.delete_char_at_cursor()
        mode_manager.clear_command_buffer()

    @kb.add('p', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def paste_after(event):
        """Paste from yank register after cursor/line"""
        if buffer.yank_register:
            buffer.paste_from_register(after=True, visible_height=ui.editor_window_height)
            mode_manager.clear_message()
        else:
            mode_manager.set_message("Nothing in register to paste")
        mode_manager.clear_command_buffer()

    @kb.add('P', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def paste_before(event):
        """Paste from yank register before cursor/line"""
        if buffer.yank_register:
            buffer.paste_from_register(after=False, visible_height=ui.editor_window_height)
            mode_manager.clear_message()
        else:
            mode_manager.set_message("Nothing in register to paste")
        mode_manager.clear_command_buffer()

    @kb.add('u', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def undo_change(event):
        """Undo the last change"""
        if buffer.undo(ui.editor_window_height):
            mode_manager.clear_message()
        else:
            mode_manager.set_message("Already at oldest change")
        mode_manager.clear_command_buffer()

    @kb.add('c-r', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def redo_change(event):
        """Redo the last undone change"""
        if buffer.redo(ui.editor_window_height):
            mode_manager.clear_message()
        else:
            mode_manager.set_message("Already at newest change")
        mode_manager.clear_command_buffer()

    @kb.add('g', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def handle_g_key(event):
        """Handle first 'g' in gg sequence for jump to top"""
        if mode_manager.command_buffer == 'g':
            # Second 'g' pressed - jump to top
            buffer.jump_to_top(ui.editor_window_height)
            mode_manager.clear_command_buffer()
        else:
            # First 'g' pressed
            mode_manager.add_to_command_buffer('g')

    @kb.add('G', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def jump_to_bottom_key(event):
        """Jump to bottom of file (vim G)"""
        buffer.jump_to_bottom(ui.editor_window_height)
        mode_manager.clear_command_buffer()

    @kb.add('v', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def enter_visual_mode(event):
        """Enter visual mode"""
        mode_manager.enter_visual_mode(buffer.cursor_row, buffer.cursor_col)

    @kb.add('V', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def enter_visual_line_mode(event):
        """Enter visual line mode"""
        mode_manager.enter_visual_line_mode(buffer.cursor_row)

    @kb.add('n', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def repeat_search(event):
        """Repeat last search in same direction in editor"""
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
        """Repeat last search in opposite direction in editor"""
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

    @kb.add('n', filter=is_sidebar_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def sidebar_search_next(event):
        """Jump to next note matching search in sidebar"""
        if mode_manager.last_search:
            if mode_manager.last_search_direction == "forward":
                found = note_list_manager.search_next()
            else:
                found = note_list_manager.search_previous()
            if not found:
                mode_manager.set_message(f"Pattern not found: {mode_manager.last_search}")
            else:
                mode_manager.clear_message()
        else:
            mode_manager.set_message("No previous search pattern")
        mode_manager.clear_command_buffer()

    @kb.add('N', filter=is_sidebar_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def sidebar_search_previous(event):
        """Jump to previous note matching search in sidebar"""
        if mode_manager.last_search:
            if mode_manager.last_search_direction == "forward":
                found = note_list_manager.search_previous()
            else:
                found = note_list_manager.search_next()
            if not found:
                mode_manager.set_message(f"Pattern not found: {mode_manager.last_search}")
            else:
                mode_manager.clear_message()
        else:
            mode_manager.set_message("No previous search pattern")
        mode_manager.clear_command_buffer()

    # ===== VISUAL MODE BINDINGS (EDITOR ONLY) =====

    @kb.add('escape', filter=is_editor_focused & is_visual_mode)
    @kb.add('v', filter=is_editor_focused & is_visual_mode)
    def exit_visual_mode(event):
        """Exit visual mode back to normal mode"""
        mode_manager.enter_normal_mode()
        buffer.clamp_cursor()

    # Visual mode movement (extends selection)
    @kb.add('h', filter=is_editor_focused & is_visual_mode)
    @kb.add('left', filter=is_editor_focused & is_visual_mode)
    def visual_move_left(event):
        """Move cursor left in visual mode"""
        buffer.move_cursor_left()

    @kb.add('j', filter=is_editor_focused & is_visual_mode)
    @kb.add('down', filter=is_editor_focused & is_visual_mode)
    def visual_move_down(event):
        """Move cursor down in visual mode"""
        buffer.move_cursor_down(ui.editor_window_height)

    @kb.add('k', filter=is_editor_focused & is_visual_mode)
    @kb.add('up', filter=is_editor_focused & is_visual_mode)
    def visual_move_up(event):
        """Move cursor up in visual mode"""
        buffer.move_cursor_up(ui.editor_window_height)

    @kb.add('l', filter=is_editor_focused & is_visual_mode)
    @kb.add('right', filter=is_editor_focused & is_visual_mode)
    def visual_move_right(event):
        """Move cursor right in visual mode"""
        buffer.move_cursor_right()

    @kb.add('0', filter=is_editor_focused & is_visual_mode)
    @kb.add('home', filter=is_editor_focused & is_visual_mode)
    def visual_move_line_start(event):
        """Move to start of line in visual mode"""
        buffer.move_cursor_to_line_start()

    @kb.add('$', filter=is_editor_focused & is_visual_mode)
    @kb.add('end', filter=is_editor_focused & is_visual_mode)
    def visual_move_line_end(event):
        """Move to end of line in visual mode"""
        buffer.move_cursor_to_line_end()

    @kb.add('c-d', filter=is_editor_focused & is_visual_mode)
    def visual_half_page_down(event):
        """Scroll down half a page in visual mode"""
        buffer.half_page_down(ui.editor_window_height)

    @kb.add('c-u', filter=is_editor_focused & is_visual_mode)
    def visual_half_page_up(event):
        """Scroll up half a page in visual mode"""
        buffer.half_page_up(ui.editor_window_height)

    @kb.add('pagedown', filter=is_editor_focused & is_visual_mode)
    def visual_page_down(event):
        """Scroll down one page in visual mode"""
        buffer.page_down(ui.editor_window_height)

    @kb.add('pageup', filter=is_editor_focused & is_visual_mode)
    def visual_page_up(event):
        """Scroll up one page in visual mode"""
        buffer.page_up(ui.editor_window_height)

    @kb.add('g', filter=is_editor_focused & is_visual_mode)
    def visual_handle_g_key(event):
        """Handle first 'g' in gg sequence for jump to top in visual mode"""
        if mode_manager.command_buffer == 'g':
            # Second 'g' pressed - jump to top
            buffer.jump_to_top(ui.editor_window_height)
            mode_manager.clear_command_buffer()
        else:
            # First 'g' pressed
            mode_manager.add_to_command_buffer('g')

    @kb.add('G', filter=is_editor_focused & is_visual_mode)
    def visual_jump_to_bottom(event):
        """Jump to bottom of file in visual mode"""
        buffer.jump_to_bottom(ui.editor_window_height)
        mode_manager.clear_command_buffer()

    # Visual mode operations
    @kb.add('d', filter=is_editor_focused & is_visual_mode)
    @kb.add('x', filter=is_editor_focused & is_visual_mode)
    def visual_delete(event):
        """Delete selected text and return to normal mode"""
        start_row, start_col, end_row, end_col = mode_manager.get_visual_selection(
            buffer.cursor_row, buffer.cursor_col
        )
        buffer.yank_selection(start_row, start_col, end_row, end_col)
        buffer.delete_selection(start_row, start_col, end_row, end_col, ui.editor_window_height)
        mode_manager.enter_normal_mode()
        buffer.clamp_cursor()

    @kb.add('y', filter=is_editor_focused & is_visual_mode)
    def visual_yank(event):
        """Yank (copy) selected text and return to normal mode"""
        start_row, start_col, end_row, end_col = mode_manager.get_visual_selection(
            buffer.cursor_row, buffer.cursor_col
        )
        buffer.yank_selection(start_row, start_col, end_row, end_col)
        mode_manager.enter_normal_mode()
        buffer.clamp_cursor()
        mode_manager.set_message(f"Yanked {end_row - start_row + 1} line(s)")

    @kb.add('c', filter=is_editor_focused & is_visual_mode)
    def visual_change(event):
        """Delete selected text and enter insert mode"""
        start_row, start_col, end_row, end_col = mode_manager.get_visual_selection(
            buffer.cursor_row, buffer.cursor_col
        )
        buffer.yank_selection(start_row, start_col, end_row, end_col)
        buffer.delete_selection(start_row, start_col, end_row, end_col, ui.editor_window_height)
        mode_manager.enter_insert_mode()

    # ===== VISUAL LINE MODE BINDINGS (EDITOR ONLY) =====

    @kb.add('escape', filter=is_editor_focused & is_visual_line_mode)
    @kb.add('V', filter=is_editor_focused & is_visual_line_mode)
    def exit_visual_line_mode(event):
        """Exit visual line mode back to normal mode"""
        mode_manager.enter_normal_mode()
        buffer.clamp_cursor()

    # Visual line mode movement (extends selection by lines)
    @kb.add('j', filter=is_editor_focused & is_visual_line_mode)
    @kb.add('down', filter=is_editor_focused & is_visual_line_mode)
    def visual_line_move_down(event):
        """Move cursor down in visual line mode"""
        buffer.move_cursor_down(ui.editor_window_height)

    @kb.add('k', filter=is_editor_focused & is_visual_line_mode)
    @kb.add('up', filter=is_editor_focused & is_visual_line_mode)
    def visual_line_move_up(event):
        """Move cursor up in visual line mode"""
        buffer.move_cursor_up(ui.editor_window_height)

    @kb.add('c-d', filter=is_editor_focused & is_visual_line_mode)
    def visual_line_half_page_down(event):
        """Scroll down half a page in visual line mode"""
        buffer.half_page_down(ui.editor_window_height)

    @kb.add('c-u', filter=is_editor_focused & is_visual_line_mode)
    def visual_line_half_page_up(event):
        """Scroll up half a page in visual line mode"""
        buffer.half_page_up(ui.editor_window_height)

    @kb.add('pagedown', filter=is_editor_focused & is_visual_line_mode)
    def visual_line_page_down(event):
        """Scroll down one page in visual line mode"""
        buffer.page_down(ui.editor_window_height)

    @kb.add('pageup', filter=is_editor_focused & is_visual_line_mode)
    def visual_line_page_up(event):
        """Scroll up one page in visual line mode"""
        buffer.page_up(ui.editor_window_height)

    @kb.add('g', filter=is_editor_focused & is_visual_line_mode)
    def visual_line_handle_g_key(event):
        """Handle first 'g' in gg sequence for jump to top in visual line mode"""
        if mode_manager.command_buffer == 'g':
            # Second 'g' pressed - jump to top
            buffer.jump_to_top(ui.editor_window_height)
            mode_manager.clear_command_buffer()
        else:
            # First 'g' pressed
            mode_manager.add_to_command_buffer('g')

    @kb.add('G', filter=is_editor_focused & is_visual_line_mode)
    def visual_line_jump_to_bottom(event):
        """Jump to bottom of file in visual line mode"""
        buffer.jump_to_bottom(ui.editor_window_height)
        mode_manager.clear_command_buffer()

    # Visual line mode operations
    @kb.add('d', filter=is_editor_focused & is_visual_line_mode)
    @kb.add('x', filter=is_editor_focused & is_visual_line_mode)
    def visual_line_delete(event):
        """Delete selected lines and return to normal mode"""
        start_row, end_row = mode_manager.get_visual_line_selection(buffer.cursor_row)
        buffer.delete_lines(start_row, end_row, ui.editor_window_height)
        mode_manager.enter_normal_mode()
        buffer.clamp_cursor()

    @kb.add('y', filter=is_editor_focused & is_visual_line_mode)
    def visual_line_yank(event):
        """Yank (copy) selected lines and return to normal mode"""
        start_row, end_row = mode_manager.get_visual_line_selection(buffer.cursor_row)
        buffer.yank_lines(start_row, end_row)
        mode_manager.enter_normal_mode()
        buffer.clamp_cursor()
        num_lines = end_row - start_row + 1
        mode_manager.set_message(f"Yanked {num_lines} line(s)")

    @kb.add('c', filter=is_editor_focused & is_visual_line_mode)
    def visual_line_change(event):
        """Delete selected lines and enter insert mode"""
        start_row, end_row = mode_manager.get_visual_line_selection(buffer.cursor_row)
        buffer.delete_lines(start_row, end_row, ui.editor_window_height)
        mode_manager.enter_insert_mode()

    # Switch between visual modes
    @kb.add('v', filter=is_editor_focused & is_visual_line_mode)
    def switch_to_visual_char(event):
        """Switch from visual line to visual character mode"""
        mode_manager.enter_visual_mode(buffer.cursor_row, buffer.cursor_col)

    # ===== HORIZONTAL SCROLLING (NORMAL MODE, EDITOR FOCUSED) =====

    @kb.add('z', 'h', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def scroll_left_one(event):
        """Scroll view left by one column"""
        buffer.scroll_left(1)
        mode_manager.clear_command_buffer()

    @kb.add('z', 'l', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def scroll_right_one(event):
        """Scroll view right by one column"""
        buffer.scroll_right(1)
        mode_manager.clear_command_buffer()

    @kb.add('z', 'H', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def scroll_left_half_screen(event):
        """Scroll view left by half screen width"""
        buffer.scroll_half_screen_left(ui.editor_window_width)
        mode_manager.clear_command_buffer()

    @kb.add('z', 'L', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def scroll_right_half_screen(event):
        """Scroll view right by half screen width"""
        buffer.scroll_half_screen_right(ui.editor_window_width)
        mode_manager.clear_command_buffer()

    # ===== FOCUS SWITCHING (CTRL+W combinations in NORMAL MODE) =====

    @kb.add('c-w', 'h', filter=is_normal_mode & ~is_any_visual_mode)
    @kb.add('c-w', 'left', filter=is_normal_mode & ~is_any_visual_mode)
    def switch_to_sidebar(event):
        """Switch focus to sidebar"""
        focus_manager.switch_to_sidebar()
        mode_manager.clear_command_buffer()

    @kb.add('c-w', 'l', filter=is_normal_mode & ~is_any_visual_mode)
    @kb.add('c-w', 'right', filter=is_normal_mode & ~is_any_visual_mode)
    def switch_to_editor(event):
        """Switch focus to editor"""
        focus_manager.switch_to_editor()
        mode_manager.clear_command_buffer()

    # ===== COMMAND MODE (works in both sidebar and editor) =====

    @kb.add(':', filter=is_normal_mode & ~is_command_mode & ~is_search_mode)
    def command_mode(event):
        """Enter command mode"""
        mode_manager.add_to_command_buffer(':')

    # ===== SEARCH MODE (editor and sidebar) =====

    @kb.add('/', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def search_forward_mode(event):
        """Enter forward search mode in editor"""
        mode_manager.start_search_forward()

    @kb.add('?', filter=is_editor_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def search_backward_mode(event):
        """Enter backward search mode in editor"""
        mode_manager.start_search_backward()

    @kb.add('/', filter=is_sidebar_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def sidebar_search_forward_mode(event):
        """Enter forward search mode in sidebar"""
        mode_manager.start_search_forward()

    @kb.add('?', filter=is_sidebar_focused & is_normal_mode & ~is_command_mode & ~is_search_mode)
    def sidebar_search_backward_mode(event):
        """Enter backward search mode in sidebar"""
        mode_manager.start_search_backward()

    @kb.add('enter', filter=is_search_mode)
    def execute_search(event):
        """Execute the search when Enter is pressed"""
        is_forward = mode_manager.command_buffer.startswith('/')
        mode_manager.execute_search()
        # Perform the search
        if mode_manager.search_query:
            if focus_manager.is_sidebar_focused():
                # Search across notes in sidebar
                found = note_list_manager.search_notes(mode_manager.search_query)
                if not found:
                    mode_manager.set_message(f"Pattern not found: {mode_manager.search_query}")
                else:
                    mode_manager.clear_message()
            else:
                # Search within current note in editor
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
            # Force load pending note or create new note if there is one pending
            if ui.pending_note_switch:
                if ui.pending_note_switch == "NEW_NOTE":
                    # Create new note, discarding current changes
                    ui._do_create_new_note()
                else:
                    # Load pending note, discarding current changes
                    ui.force_load_note(ui.pending_note_switch)
                    if focus_manager.is_sidebar_focused():
                        focus_manager.switch_to_editor()
            else:
                mode_manager.set_message("No pending note to load")
            mode_manager.clear_command_buffer()
        elif command == ':new' or command == ':n':
            # Create a new empty note
            ui.create_new_note()
            mode_manager.clear_command_buffer()
        elif command == ':delete' or command == ':d':
            # Delete current note with confirmation
            if buffer.current_note_id:
                if ui.pending_deletion == buffer.current_note_id:
                    # Already pending - delete it
                    ui.delete_note(buffer.current_note_id)
                else:
                    # Set pending deletion
                    ui.pending_deletion = buffer.current_note_id
                    mode_manager.set_message("Delete note? :d again to confirm, :d! to force")
            else:
                mode_manager.set_message("No note loaded")
            mode_manager.clear_command_buffer()
        elif command == ':d!':
            # Force delete current note without confirmation
            if buffer.current_note_id:
                ui.delete_note(buffer.current_note_id)
            else:
                mode_manager.set_message("No note loaded")
            mode_manager.clear_command_buffer()
        elif command == ':sidebar' or command == ':sb':
            # Toggle sidebar visibility (only when editor is focused)
            if focus_manager.is_editor_focused():
                focus_manager.toggle_sidebar()
                mode_manager.clear_command_buffer()
            else:
                mode_manager.set_message("Sidebar toggle only available when editor is focused")
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
        # Clamp cursor to valid position for normal mode
        buffer.clamp_cursor()

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

    @kb.add('home', filter=is_editor_focused & is_insert_mode)
    def insert_move_home(event):
        """Move to start of line in insert mode"""
        buffer.move_cursor_to_line_start()

    @kb.add('end', filter=is_editor_focused & is_insert_mode)
    def insert_move_end(event):
        """Move to end of line in insert mode"""
        buffer.move_cursor_to_line_end()

    @kb.add('delete', filter=is_editor_focused & is_insert_mode)
    def insert_delete_char(event):
        """Delete character under cursor in insert mode"""
        buffer.delete_char_at_cursor()

    @kb.add('pagedown', filter=is_editor_focused & is_insert_mode)
    def insert_page_down(event):
        """Scroll down one page in insert mode"""
        buffer.page_down(ui.editor_window_height)

    @kb.add('pageup', filter=is_editor_focused & is_insert_mode)
    def insert_page_up(event):
        """Scroll up one page in insert mode"""
        buffer.page_up(ui.editor_window_height)

    # Catch all printable characters in insert mode
    @kb.add('<any>', filter=is_editor_focused & is_insert_mode)
    def insert_character(event):
        """Insert any printable character in insert mode"""
        if len(event.data) == 1 and event.data.isprintable():
            buffer.insert_char(event.data)

    # ===== BRACKETED PASTE (NATIVE TERMINAL PASTE) =====

    @kb.add(Keys.BracketedPaste, filter=is_editor_focused & is_insert_mode)
    def paste_from_terminal(event):
        """Handle native terminal paste (Ctrl+Shift+V, right-click in terminal)"""
        if not focus_manager.is_editor_focused():
            return

        pasted_text = event.data

        if mode_manager.is_insert_mode():
            buffer.paste_text(pasted_text, ui.editor_window_height)
        elif mode_manager.is_normal_mode() and not mode_manager.command_buffer:
            # Auto-enter insert mode on paste
            mode_manager.enter_insert_mode()
            buffer.paste_text(pasted_text, ui.editor_window_height)

    # Additional normal mode bindings to clear command buffer on other keys
    @kb.add('escape', filter=is_normal_mode & ~is_command_mode)
    def clear_command(event):
        """Clear command buffer and pending states in normal mode"""
        mode_manager.clear_command_buffer()
        mode_manager.clear_message()
        ui.pending_deletion = None

    # Global bindings
    @kb.add('c-c')
    @kb.add('c-q')
    def force_quit(event):
        """Force quit with Ctrl+C or Ctrl+Q"""
        event.app.exit()

    return kb
