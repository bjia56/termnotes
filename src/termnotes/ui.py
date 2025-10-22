"""
UI components using prompt_toolkit
"""

from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings

from .editor import EditorBuffer
from .modes import ModeManager
from .key_bindings import create_key_bindings


class EditorUI:
    """Main editor UI using prompt_toolkit"""

    def __init__(self, initial_text: str = ""):
        self.buffer = EditorBuffer(initial_text)
        self.mode_manager = ModeManager()
        self.kb = create_key_bindings(self.buffer, self.mode_manager)

    def get_text_content(self):
        """Get formatted text content for the editor window"""
        lines = self.buffer.get_display_lines()
        result = []

        for i, line in enumerate(lines):
            if i == self.buffer.cursor_row:
                # Current line - show cursor
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

        # Cursor position (right side)
        row = self.buffer.cursor_row + 1
        col = self.buffer.cursor_col + 1
        total_lines = self.buffer.line_count
        pos_str = f"{row},{col}  {row}/{total_lines}"

        # Message (middle)
        message = self.mode_manager.message

        # Build status bar with padding to fill width
        if message:
            left_part = f"{mode_str}  {message}"
        else:
            left_part = mode_str

        # Calculate padding
        used_width = len(left_part) + len(pos_str)
        padding = ' ' * max(0, width - used_width)

        status = f"{left_part}{padding}{pos_str}"

        return FormattedText([('reverse', status)])

    def create_layout(self):
        """Create the UI layout"""
        # Main text window
        text_window = Window(
            content=FormattedTextControl(
                text=self.get_text_content,
                focusable=True,
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

        # Combine into layout
        layout = Layout(
            HSplit([
                text_window,
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
