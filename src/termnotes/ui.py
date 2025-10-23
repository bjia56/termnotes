"""
UI components using prompt_toolkit
"""

from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window, FormattedTextControl
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings

from .editor import EditorBuffer
from .modes import ModeManager
from .key_bindings import create_key_bindings
from .note_list import NoteListManager
from .focus import FocusManager
from .storage import NoteStorage
from .note import Note


class EditorUI:
    """Main editor UI using prompt_toolkit"""

    def __init__(self, initial_text: str = ""):
        # Core components
        self.storage = NoteStorage()  # In-memory SQLite database
        self.buffer = EditorBuffer(initial_text)
        self.mode_manager = ModeManager()
        self.note_list_manager = NoteListManager(self.storage)
        self.focus_manager = FocusManager()
        self.pending_note_switch = None  # For handling unsaved changes confirmation

        # Load first note into editor if no initial text
        if not initial_text and self.note_list_manager.selected_note:
            first_note = self.note_list_manager.selected_note
            self.buffer.load_content(first_note.content, first_note.id)

        # Create key bindings with all managers
        self.kb = create_key_bindings(
            self.buffer,
            self.mode_manager,
            self.note_list_manager,
            self.focus_manager,
            self  # Pass UI instance for save/load operations
        )

    def save_current_note(self):
        """Save the current buffer content to the database"""
        if self.buffer.current_note_id:
            note = Note(
                note_id=self.buffer.current_note_id,
                content=self.buffer.get_text()
            )
            self.storage.save_note(note)
            self.buffer.mark_clean()
            self.note_list_manager.reload_notes()

            # Update selection to point to the saved note (now at top of list)
            # Find the note in the reloaded list
            for i, n in enumerate(self.note_list_manager.notes):
                if n.id == self.buffer.current_note_id:
                    self.note_list_manager.selected_index = i
                    break

            self.mode_manager.set_message("Note saved")
        else:
            self.mode_manager.set_message("No note loaded")

    def load_note(self, note: Note):
        """
        Load a note into the editor

        Args:
            note: The note to load
        """
        if self.buffer.is_dirty:
            # Store pending switch and prompt user
            self.pending_note_switch = note
            self.mode_manager.set_message("Unsaved changes! :w to save, :e! to discard and load")
        else:
            # Load the note
            self.buffer.load_content(note.content, note.id)
            self.mode_manager.clear_message()

    def force_load_note(self, note: Note):
        """Force load a note, discarding any unsaved changes"""
        self.buffer.load_content(note.content, note.id)
        self.pending_note_switch = None
        self.mode_manager.clear_message()

    def get_text_content(self):
        """Get formatted text content for the editor window"""
        lines = self.buffer.get_display_lines()
        result = []

        # Only show cursor if editor is focused
        show_cursor = self.focus_manager.is_editor_focused()

        for i, line in enumerate(lines):
            if i == self.buffer.cursor_row and show_cursor:
                # Current line - show cursor (only when editor focused)
                line_with_cursor = self._add_cursor_to_line(line, self.buffer.cursor_col)
                result.extend(line_with_cursor)
            else:
                result.append(('', line))

            # Add newline for all but last line
            if i < len(lines) - 1:
                result.append(('', '\n'))

        return FormattedText(result)

    def _add_cursor_to_line(self, line: str, cursor_col: int):
        """Add cursor to a line at specified column"""
        result = []

        if cursor_col >= len(line):
            # Cursor at end of line
            result.append(('', line))
            result.append(('reverse', ' '))  # Show cursor as reversed space
        else:
            # Cursor in middle of line
            if cursor_col > 0:
                result.append(('', line[:cursor_col]))
            result.append(('reverse', line[cursor_col]))  # Reversed character
            if cursor_col < len(line) - 1:
                result.append(('', line[cursor_col + 1:]))

        return result

    def get_sidebar_content(self):
        """Get formatted text for sidebar showing note list"""
        result = []

        for i, note in enumerate(self.note_list_manager.notes):
            preview = note.get_preview(25)

            # Highlight selected note
            if i == self.note_list_manager.selected_index:
                # Show selection indicator and highlight
                if self.focus_manager.is_sidebar_focused():
                    # Focused sidebar - use reverse video
                    result.append(('reverse', f"> {preview}"))
                else:
                    # Unfocused sidebar - just show indicator
                    result.append(('', f"> {preview}"))
            else:
                result.append(('', f"  {preview}"))

            # Add newline except for last item
            if i < len(self.note_list_manager.notes) - 1:
                result.append(('', '\n'))

        return FormattedText(result)

    def get_status_bar_content(self):
        """Get formatted text for status bar"""
        # Get terminal width
        try:
            import shutil
            width = shutil.get_terminal_size().columns
        except:
            width = 80  # Default fallback

        # Mode indicator (left side)
        mode_str = self.mode_manager.get_mode_string()

        # Focus indicator
        focus_str = f"[{self.focus_manager.get_focus_name()}]"

        # Dirty indicator
        dirty_str = "[+]" if self.buffer.is_dirty else ""

        # Cursor position (right side)
        row = self.buffer.cursor_row + 1
        col = self.buffer.cursor_col + 1
        total_lines = self.buffer.line_count
        pos_str = f"{dirty_str} {row},{col}  {row}/{total_lines}".strip()

        # Message (middle)
        message = self.mode_manager.message

        # Build status bar with padding to fill width
        if message:
            left_part = f"{mode_str}  {message}  {focus_str}"
        else:
            left_part = f"{mode_str}  {focus_str}"

        # Calculate padding
        used_width = len(left_part) + len(pos_str)
        padding = ' ' * max(0, width - used_width)

        status = f"{left_part}{padding}{pos_str}"

        return FormattedText([('reverse', status)])

    def create_layout(self):
        """Create the UI layout with sidebar and editor"""
        # Sidebar window (note list)
        sidebar_window = Window(
            content=FormattedTextControl(
                text=self.get_sidebar_content,
                focusable=False,
                show_cursor=False,
            ),
            width=30,  # Fixed width for sidebar
            wrap_lines=False,
        )

        # Main editor window
        editor_window = Window(
            content=FormattedTextControl(
                text=self.get_text_content,
                focusable=False,
                show_cursor=False,
            ),
            wrap_lines=False,
        )

        # Status bar
        status_bar = Window(
            content=FormattedTextControl(
                text=self.get_status_bar_content,
            ),
            height=1,
            always_hide_cursor=True,
        )

        # Combine into layout: sidebar | editor (side by side), with status bar below
        layout = Layout(
            HSplit([
                VSplit([
                    sidebar_window,
                    editor_window,
                ]),
                status_bar,
            ])
        )

        return layout

    def run(self):
        """Run the editor application"""
        app = Application(
            layout=self.create_layout(),
            key_bindings=self.kb,
            full_screen=True,
            mouse_support=False,
        )
        app.ttimeoutlen = 0.05

        app.run()
