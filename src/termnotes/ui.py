"""
UI components using prompt_toolkit
"""

import re
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window, FormattedTextControl
from prompt_toolkit.formatted_text import FormattedText
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.lexers.special import TextLexer
from pygments.util import ClassNotFound
from pygments.token import Token

from .editor import EditorBuffer
from .modes import ModeManager
from .key_bindings import create_key_bindings
from .note_list import NoteListManager
from .focus import FocusManager
from .storage import create_default_storage
from .note import Note


class EditorUI:
    """Main editor UI using prompt_toolkit"""

    def __init__(self, initial_text: str = ""):
        # Core components
        self.storage = create_default_storage()  # Composite: SQLite cache + filesystem
        self.mode_manager = ModeManager()
        self.buffer = EditorBuffer(initial_text, self.mode_manager)
        self.note_list_manager = NoteListManager(self.storage)
        self.focus_manager = FocusManager()
        self.pending_note_switch = None  # For handling unsaved changes confirmation
        self.pending_deletion = None  # For handling deletion confirmation
        self.editor_window_height = 24  # Default, will be updated dynamically
        self.editor_window_width = 80  # Default, will be updated dynamically

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

            # If this was a new unsaved note, it's now in storage
            if self.buffer.is_new_unsaved:
                self.buffer.is_new_unsaved = False
                # Clear the in-memory note from sidebar
                self.note_list_manager.clear_in_memory_note()

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
        if self.buffer.is_dirty or self.buffer.is_new_unsaved:
            # Store pending switch and prompt user
            self.pending_note_switch = note
            if self.buffer.is_new_unsaved:
                self.mode_manager.set_message("New note not saved! :w to save, :e! to discard and load")
            else:
                self.mode_manager.set_message("Unsaved changes! :w to save, :e! to discard and load")
        else:
            # Load the note
            self.buffer.load_content(note.content, note.id)
            self.mode_manager.clear_message()

    def force_load_note(self, note: Note):
        """Force load a note, discarding any unsaved changes"""
        # If we're discarding an in-memory note, clear it from sidebar
        if self.buffer.is_new_unsaved:
            self.note_list_manager.clear_in_memory_note()

        self.buffer.load_content(note.content, note.id)
        self.pending_note_switch = None
        self.mode_manager.clear_message()

    def create_new_note(self):
        """Create a new empty note and load it into the editor"""
        if self.buffer.is_dirty or self.buffer.is_new_unsaved:
            # Store that we want to create a new note
            self.pending_note_switch = "NEW_NOTE"
            if self.buffer.is_new_unsaved:
                self.mode_manager.set_message("New note not saved! :w to save, :e! to discard and create new")
            else:
                self.mode_manager.set_message("Unsaved changes! :w to save, :e! to discard and create new")
        else:
            self._do_create_new_note()

    def _do_create_new_note(self):
        """Internal method to actually create and load a new note"""
        # Clear any existing in-memory note first (if we're replacing it)
        self.note_list_manager.clear_in_memory_note()

        # Create new note ID (but don't save to storage yet)
        new_note = self.storage.create_note()

        # Add to note list manager as in-memory note
        self.note_list_manager.set_in_memory_note(new_note)

        # Load empty note into editor with is_new flag
        # This marks it as in-memory only until first save
        self.buffer.load_content(new_note.content, new_note.id, is_new=True)

        # Switch focus to editor
        self.focus_manager.switch_to_editor()

        # Clear any messages and pending state
        self.mode_manager.clear_message()
        self.pending_note_switch = None

    def delete_note(self, note_id: str):
        """
        Delete a note by ID

        Args:
            note_id: ID of the note to delete
        """
        # Check if this is the in-memory note
        if (self.note_list_manager.in_memory_note and
            self.note_list_manager.in_memory_note.id == note_id):
            # Just discard the in-memory note
            self.note_list_manager.clear_in_memory_note()
            self.buffer.load_content("", None)
            self.pending_deletion = None
            self.mode_manager.set_message("New note discarded")

            # Select first saved note if available
            if self.note_list_manager.notes:
                self.note_list_manager.selected_index = 0
                selected_note = self.note_list_manager.selected_note
                if selected_note:
                    self.buffer.load_content(selected_note.content, selected_note.id)
            return

        # Delete from storage
        self.storage.delete_note(note_id)

        # If we're deleting the currently loaded note, clear the buffer
        if self.buffer.current_note_id == note_id:
            self.buffer.load_content("", None)

        # Reload note list
        self.note_list_manager.reload_notes()

        # Select next note if available
        if self.note_list_manager.notes:
            # Keep selection index in bounds
            if self.note_list_manager.selected_index >= len(self.note_list_manager.notes):
                self.note_list_manager.selected_index = len(self.note_list_manager.notes) - 1

            # Load the newly selected note if buffer is empty
            if self.buffer.current_note_id is None:
                selected_note = self.note_list_manager.selected_note
                if selected_note:
                    self.buffer.load_content(selected_note.content, selected_note.id)

        # Clear pending deletion state
        self.pending_deletion = None
        self.mode_manager.set_message("Note deleted")

    def _apply_horizontal_scroll(self, formatted_segments, start_col: int, end_col: int):
        """
        Slice formatted text segments to show only columns [start_col, end_col)

        Args:
            formatted_segments: list of (style, text) tuples
            start_col: leftmost column to display (inclusive)
            end_col: rightmost column to display (exclusive)

        Returns:
            list of (style, text) tuples with sliced text
        """
        result = []
        char_pos = 0

        for style, text in formatted_segments:
            text_len = len(text)
            segment_end = char_pos + text_len

            # Skip segments entirely before visible range
            if segment_end <= start_col:
                char_pos = segment_end
                continue

            # Stop if we're past the visible range
            if char_pos >= end_col:
                break

            # Calculate slice within this segment
            slice_start = max(0, start_col - char_pos)
            slice_end = min(text_len, end_col - char_pos)

            if slice_start < slice_end:
                result.append((style, text[slice_start:slice_end]))

            char_pos = segment_end

        return result

    def get_text_content(self):
        """Get formatted text content for the editor window"""
        # Update window dimensions on each render to handle terminal resizing
        self.update_editor_window_height()
        self.update_editor_window_width()

        # Adjust horizontal scroll to keep cursor visible
        self.buffer.adjust_horizontal_scroll(self.editor_window_width)

        lines = self.buffer.get_display_lines()
        result = []

        # Only show cursor if editor is focused
        show_cursor = self.focus_manager.is_editor_focused()

        # Calculate visible line range based on scroll offset
        visible_start = self.buffer.scroll_offset
        visible_end = min(visible_start + self.editor_window_height, len(lines))

        # First pass: identify code blocks
        code_blocks = self._identify_code_blocks(lines)

        i = visible_start
        while i < visible_end:
            line = lines[i]

            # Check if this line is part of a code block
            if i in code_blocks:
                block_info = code_blocks[i]
                block_start = block_info['start']
                block_end = block_info['end']
                lang = block_info['lang']

                # Process the entire code block (but only visible parts)
                for block_i in range(block_start, block_end + 1):
                    # Skip lines outside visible range
                    if block_i < visible_start or block_i >= visible_end:
                        continue

                    block_line = lines[block_i]

                    if block_i == block_start or block_i == block_end:
                        # Opening/closing backticks
                        formatted_line = [('#ansigreen', block_line)]
                    else:
                        # Code content - use Pygments
                        formatted_line = self._highlight_code_line(block_line, lang)

                    # Add cursor if needed
                    if block_i == self.buffer.cursor_row and show_cursor:
                        line_with_cursor = self._add_cursor_to_formatted_line(formatted_line, self.buffer.cursor_col)
                        # Apply horizontal scrolling
                        scrolled_line = self._apply_horizontal_scroll(
                            line_with_cursor,
                            self.buffer.horizontal_scroll_offset,
                            self.buffer.horizontal_scroll_offset + self.editor_window_width
                        )
                        result.extend(scrolled_line)
                    else:
                        # Apply horizontal scrolling
                        scrolled_line = self._apply_horizontal_scroll(
                            formatted_line,
                            self.buffer.horizontal_scroll_offset,
                            self.buffer.horizontal_scroll_offset + self.editor_window_width
                        )
                        result.extend(scrolled_line)

                    # Add newline for all but last visible line
                    if block_i < visible_end - 1:
                        result.append(('', '\n'))

                # Skip to end of code block
                i = block_end + 1
            else:
                # Regular markdown line
                formatted_line = self._parse_markdown_line(line)

                if i == self.buffer.cursor_row and show_cursor:
                    line_with_cursor = self._add_cursor_to_formatted_line(formatted_line, self.buffer.cursor_col)
                    # Apply horizontal scrolling
                    scrolled_line = self._apply_horizontal_scroll(
                        line_with_cursor,
                        self.buffer.horizontal_scroll_offset,
                        self.buffer.horizontal_scroll_offset + self.editor_window_width
                    )
                    result.extend(scrolled_line)
                else:
                    # Apply horizontal scrolling
                    scrolled_line = self._apply_horizontal_scroll(
                        formatted_line,
                        self.buffer.horizontal_scroll_offset,
                        self.buffer.horizontal_scroll_offset + self.editor_window_width
                    )
                    result.extend(scrolled_line)

                # Add newline for all but last visible line
                if i < visible_end - 1:
                    result.append(('', '\n'))

                i += 1

        return FormattedText(result)

    def _identify_code_blocks(self, lines):
        """
        Identify code blocks in the text
        Returns a dict mapping line numbers to code block info
        """
        code_blocks = {}
        in_code_block = False
        block_start = None
        block_lang = None

        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                if not in_code_block:
                    # Start of code block
                    in_code_block = True
                    block_start = i
                    # Extract language if specified
                    lang_match = re.match(r'^```(\w+)', line.strip())
                    block_lang = lang_match.group(1) if lang_match else None
                else:
                    # End of code block
                    block_end = i
                    # Mark all lines in the block
                    for block_i in range(block_start, block_end + 1):
                        code_blocks[block_i] = {
                            'start': block_start,
                            'end': block_end,
                            'lang': block_lang
                        }
                    in_code_block = False
                    block_start = None
                    block_lang = None

        return code_blocks

    def _highlight_code_line(self, line: str, lang: str = None):
        """
        Highlight a single line of code using Pygments
        Returns a list of (style, text) tuples
        """
        if not line:
            return [('', '')]

        # Get lexer
        try:
            if lang:
                lexer = get_lexer_by_name(lang)
            else:
                lexer = TextLexer()
        except ClassNotFound:
            lexer = TextLexer()

        # Tokenize the line
        tokens = list(lex(line, lexer))

        # Map Pygments tokens to prompt_toolkit styles
        # Filter out newline tokens that Pygments adds
        result = []
        for token_type, text in tokens:
            # Skip any whitespace-only tokens that contain newlines
            if '\n' in text:
                # Replace newlines but keep other content
                text = text.replace('\n', '')
                if not text:  # If nothing left after removing newlines, skip
                    continue
            style = self._pygments_token_to_style(token_type)
            result.append((style, text))

        # If result is empty (line was only whitespace/newlines), return empty string
        if not result:
            return [('', '')]

        return result

    def _pygments_token_to_style(self, token_type):
        """Map Pygments token types to prompt_toolkit style strings"""
        # Map common token types to ANSI colors
        if token_type in Token.Keyword:
            return '#ansicyan bold'
        elif token_type in Token.String:
            return '#ansigreen'
        elif token_type in Token.Comment:
            return '#ansibrightblack italic'
        elif token_type in Token.Number:
            return '#ansiyellow'
        elif token_type in Token.Name.Function:
            return '#ansiblue'
        elif token_type in Token.Name.Class:
            return '#ansimagenta bold'
        elif token_type in Token.Operator:
            return '#ansired'
        elif token_type in Token.Name.Builtin:
            return '#ansicyan'
        else:
            return ''  # Default style

    def _parse_markdown_line(self, line: str):
        """
        Parse a line for markdown syntax and return formatted text segments
        Returns a list of (style, text) tuples
        """
        # Check for headers first (must be at start of line)
        header_match = re.match(r'^(#{1,6})\s+(.*)$', line)
        if header_match:
            hashes, text = header_match.groups()
            level = len(hashes)
            return [('#ansicyan bold', hashes), ('', ' '), ('#ansicyan bold', text)]

        # Check for code blocks (triple backticks)
        if line.strip().startswith('```'):
            return [('#ansigreen', line)]

        # Check for blockquotes
        if line.strip().startswith('>'):
            return [('#ansiyellow', line)]

        # Check for unordered lists
        if re.match(r'^\s*[-*+]\s+', line):
            match = re.match(r'^(\s*[-*+]\s+)(.*)$', line)
            if match:
                bullet, rest = match.groups()
                result = [('#ansimagenta bold', bullet)]
                result.extend(self._parse_inline_markdown(rest))
                return result

        # Check for ordered lists
        if re.match(r'^\s*\d+\.\s+', line):
            match = re.match(r'^(\s*\d+\.\s+)(.*)$', line)
            if match:
                number, rest = match.groups()
                result = [('#ansimagenta bold', number)]
                result.extend(self._parse_inline_markdown(rest))
                return result

        # Check for horizontal rules
        if re.match(r'^\s*[-*_]{3,}\s*$', line):
            return [('#ansicyan', line)]

        # Otherwise parse inline markdown
        return self._parse_inline_markdown(line)

    def _parse_inline_markdown(self, text: str):
        """
        Parse inline markdown elements (bold, italic, code, links)
        Returns a list of (style, text) tuples
        """
        result = []
        pos = 0

        # Pattern for inline code, bold, italic, and links
        # Order matters: try more specific patterns first
        patterns = [
            (r'`([^`]+)`', '#ansigreen'),           # Inline code
            (r'\*\*\*([^*]+)\*\*\*', '#ansired bold italic'),  # Bold+italic
            (r'___([^_]+)___', '#ansired bold italic'),        # Bold+italic
            (r'\*\*([^*]+)\*\*', '#ansired bold'),  # Bold
            (r'__([^_]+)__', '#ansired bold'),      # Bold
            (r'\*([^*]+)\*', '#ansired italic'),    # Italic
            (r'_([^_]+)_', '#ansired italic'),      # Italic
            (r'\[([^\]]+)\]\([^)]+\)', '#ansiblue underline'),  # Links
        ]

        while pos < len(text):
            # Try to match any pattern at current position
            matched = False
            for pattern, style in patterns:
                match = re.match(pattern, text[pos:])
                if match:
                    full_text = match.group(0)
                    result.append((style, full_text))
                    pos += len(full_text)
                    matched = True
                    break

            if not matched:
                # No pattern matched, add single character as normal text
                result.append(('', text[pos]))
                pos += 1

        return result

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

    def _add_cursor_to_formatted_line(self, formatted_segments, cursor_col: int):
        """
        Add cursor to an already-formatted line at specified column
        formatted_segments: list of (style, text) tuples
        cursor_col: character position where cursor should appear
        """
        result = []
        char_pos = 0
        cursor_added = False

        for style, text in formatted_segments:
            text_len = len(text)

            if cursor_added or cursor_col < char_pos or cursor_col >= char_pos + text_len:
                # Cursor not in this segment
                result.append((style, text))
                char_pos += text_len
            else:
                # Cursor is in this segment
                offset = cursor_col - char_pos

                # Add text before cursor
                if offset > 0:
                    result.append((style, text[:offset]))

                # Add cursor character
                result.append(('reverse', text[offset]))

                # Add text after cursor
                if offset < text_len - 1:
                    result.append((style, text[offset + 1:]))

                cursor_added = True
                char_pos += text_len

        # If cursor is at end of line, add a reversed space
        if not cursor_added:
            result.append(('reverse', ' '))

        return result

    def get_sidebar_content(self):
        """Get formatted text for sidebar showing note list"""
        result = []

        all_notes = self.note_list_manager.get_all_notes_including_memory()
        for i, note in enumerate(all_notes):
            preview = note.get_preview(25)

            # Add [NEW] indicator for in-memory note
            is_in_memory = (i == 0 and self.note_list_manager.in_memory_note is not None)
            if is_in_memory:
                preview = f"[NEW] {preview}"

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
            if i < len(all_notes) - 1:
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

        # Dirty/new indicator
        if self.buffer.is_new_unsaved:
            dirty_str = "[NEW]"
        elif self.buffer.is_dirty:
            dirty_str = "[+]"
        else:
            dirty_str = ""

        # Cursor position (right side)
        row = self.buffer.cursor_row + 1
        col = self.buffer.cursor_col + 1
        total_lines = self.buffer.line_count

        # Add horizontal scroll indicator if scrolled
        if self.buffer.horizontal_scroll_offset > 0:
            scroll_indicator = f" <{self.buffer.horizontal_scroll_offset}"
            pos_str = f"{dirty_str} {row},{col}{scroll_indicator}  {row}/{total_lines}".strip()
        else:
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

    def update_editor_window_height(self):
        """Update the cached editor window height based on terminal size"""
        try:
            import shutil
            terminal_height = shutil.get_terminal_size().lines
            # Subtract status bar (1 line)
            self.editor_window_height = max(1, terminal_height - 1)
        except:
            self.editor_window_height = 24  # Default fallback

    def update_editor_window_width(self):
        """Update the cached editor window width based on terminal size"""
        try:
            import shutil
            terminal_width = shutil.get_terminal_size().columns
            # Subtract sidebar (30 columns)
            self.editor_window_width = max(1, terminal_width - 30)
        except:
            self.editor_window_width = 80  # Default fallback

    def create_layout(self):
        """Create the UI layout with sidebar and editor"""
        # Update window height when creating layout
        self.update_editor_window_height()

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
