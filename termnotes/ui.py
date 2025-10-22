"""Terminal UI components using prompt_toolkit."""

from typing import List, Optional, Callable
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.formatted_text import HTML
from pygments.lexers.markup import MarkdownLexer
from pygments import lex
from pygments.token import Token

from .models import Note
from .database import Database


class NotesUI:
    """Terminal UI for notes application."""
    
    def __init__(self, database: Database):
        """Initialize the UI.
        
        Args:
            database: Database instance
        """
        self.database = database
        self.notes: List[Note] = []
        self.current_note: Optional[Note] = None
        self.selected_index = 0
        
        # Create UI components
        self.note_list_control = FormattedTextControl(
            text=self._get_note_list_text,
            focusable=True,
            key_bindings=self._create_note_list_bindings()
        )
        
        self.note_list_window = Window(
            content=self.note_list_control,
            width=30,
            always_hide_cursor=True
        )
        
        self.editor = TextArea(
            text="",
            multiline=True,
            scrollbar=True,
            lexer=MarkdownLexer(),
            focusable=True
        )
        
        self.status_bar = Window(
            content=FormattedTextControl(text=self._get_status_text),
            height=1,
            style="reverse"
        )
        
        # Create layout
        self.layout = Layout(
            HSplit([
                VSplit([
                    Frame(self.note_list_window, title="Notes"),
                    Frame(self.editor, title="Content"),
                ]),
                self.status_bar,
            ])
        )
        
        # Create key bindings
        self.kb = self._create_global_bindings()
        
        # Create application
        self.app = Application(
            layout=self.layout,
            key_bindings=self.kb,
            full_screen=True,
            mouse_support=True,
        )
        
        # Load initial notes
        self.refresh_notes()
    
    def _create_note_list_bindings(self) -> KeyBindings:
        """Create key bindings for the note list."""
        kb = KeyBindings()
        
        @kb.add("up")
        def move_up(event):
            if self.selected_index > 0:
                self.selected_index -= 1
                self._load_selected_note()
        
        @kb.add("down")
        def move_down(event):
            if self.selected_index < len(self.notes) - 1:
                self.selected_index += 1
                self._load_selected_note()
        
        @kb.add("enter")
        def select_note(event):
            self.app.layout.focus(self.editor)
        
        return kb
    
    def _create_global_bindings(self) -> KeyBindings:
        """Create global key bindings."""
        kb = KeyBindings()
        
        @kb.add("c-q")
        def quit_app(event):
            """Quit the application."""
            self._save_current_note()
            event.app.exit()
        
        @kb.add("c-n")
        def new_note(event):
            """Create a new note."""
            note = self.database.create_note("New Note", "")
            self.refresh_notes()
            # Select the new note
            for i, n in enumerate(self.notes):
                if n.id == note.id:
                    self.selected_index = i
                    self._load_selected_note()
                    break
            self.app.layout.focus(self.editor)
        
        @kb.add("c-s")
        def save_note(event):
            """Save the current note."""
            self._save_current_note()
        
        @kb.add("c-d")
        def delete_note(event):
            """Delete the current note."""
            if self.current_note:
                self.database.delete_note(self.current_note.id)
                self.current_note = None
                self.editor.text = ""
                self.refresh_notes()
                if self.notes:
                    self.selected_index = min(self.selected_index, len(self.notes) - 1)
                    self._load_selected_note()
        
        @kb.add("c-l")
        def focus_list(event):
            """Focus the note list."""
            self._save_current_note()
            self.app.layout.focus(self.note_list_window)
        
        @kb.add("c-e")
        def focus_editor(event):
            """Focus the editor."""
            self.app.layout.focus(self.editor)
        
        return kb
    
    def _get_note_list_text(self):
        """Get formatted text for the note list."""
        if not self.notes:
            return HTML("<i>No notes yet</i>\n\n<b>Ctrl+N:</b> New note")
        
        lines = []
        for i, note in enumerate(self.notes):
            title = note.title[:25]
            if i == self.selected_index:
                lines.append(HTML(f"<b><reverse> {title} </reverse></b>"))
            else:
                lines.append(HTML(f" {title}"))
        
        return HTML("\n").join(lines)
    
    def _get_status_text(self):
        """Get status bar text."""
        shortcuts = [
            "^N: New",
            "^S: Save",
            "^D: Delete",
            "^L: List",
            "^E: Edit",
            "^Q: Quit"
        ]
        return " | ".join(shortcuts)
    
    def refresh_notes(self):
        """Refresh the notes list from database."""
        self.notes = self.database.list_notes()
        if not self.notes and self.current_note:
            self.current_note = None
            self.editor.text = ""
        elif self.notes and self.selected_index >= len(self.notes):
            self.selected_index = len(self.notes) - 1
    
    def _load_selected_note(self):
        """Load the currently selected note into the editor."""
        if 0 <= self.selected_index < len(self.notes):
            # Save previous note before loading new one
            self._save_current_note()
            
            note = self.notes[self.selected_index]
            self.current_note = self.database.get_note(note.id)
            if self.current_note:
                self.editor.text = self.current_note.content
    
    def _save_current_note(self):
        """Save the current note if modified."""
        if self.current_note and self.editor.text != self.current_note.content:
            # Extract title from first line of content
            lines = self.editor.text.split("\n")
            title = lines[0].strip() if lines else "Untitled"
            
            # Remove markdown headers from title
            if title.startswith("#"):
                title = title.lstrip("#").strip()
            
            # Limit title length
            if len(title) > 100:
                title = title[:100]
            
            if not title:
                title = "Untitled"
            
            self.database.update_note(
                self.current_note.id,
                title=title,
                content=self.editor.text
            )
            self.refresh_notes()
    
    def run(self):
        """Run the application."""
        # Load first note if available
        if self.notes:
            self._load_selected_note()
        
        self.app.run()
