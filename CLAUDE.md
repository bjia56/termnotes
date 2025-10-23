# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

termnotes is a vim-like terminal note-taking application built with Python and `prompt_toolkit`. It features a dual-pane interface with a sidebar for note selection and an editor for note content, with vim-style modal editing (Normal/Insert modes).

## Development Commands

### Installation
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running the Application
```bash
# Run as module
python -m termnotes

# Or use installed command
termnotes

# Open with a specific file
termnotes filename.txt
```

### Testing
```bash
# Run tests (when available)
pytest
```

### Building Standalone Executable
The project uses Cosmopolitan Python to create a portable executable:
```bash
# The build process is automated in .github/workflows/build.yml
# It downloads Cosmopolitan Python, bundles dependencies, and creates termnotes.exe
python scripts/add_dir_into_zip.py <module_path> python.exe Lib/site-packages/<module>
```

## Architecture Overview

### Core Component Model
The application follows a component-based architecture where UI state is managed through separate manager classes:

- **EditorUI** ([ui.py](src/termnotes/ui.py)) - Main UI orchestrator, creates prompt_toolkit Application and coordinates all other components
- **EditorBuffer** ([editor.py](src/termnotes/editor.py)) - Text buffer with cursor management, tracks dirty state and current note ID
- **ModeManager** ([modes.py](src/termnotes/modes.py)) - Handles vim mode state (Normal/Insert) and command buffer (for `:`, `dd`, etc.)
- **FocusManager** ([focus.py](src/termnotes/focus.py)) - Tracks which pane (sidebar/editor) has focus
- **NoteListManager** ([note_list.py](src/termnotes/note_list.py)) - Manages note list display and selection state
- **NoteStorage** ([storage.py](src/termnotes/storage.py)) - SQLite-based persistence (defaults to in-memory database)

### Key Bindings Architecture
Key bindings ([key_bindings.py](src/termnotes/key_bindings.py)) use `prompt_toolkit` filters to create context-aware bindings:
- Filters combine mode state (Normal/Insert/Command) with focus state (Sidebar/Editor)
- Example: `@kb.add('j', filter=is_editor_focused & is_normal_mode)` - j moves cursor only when editor is focused in Normal mode
- Same key has different behavior based on context (e.g., `j` moves cursor in editor, moves selection in sidebar)

### Data Flow for Save/Load Operations
1. **Saving**: UI → EditorBuffer (get text) → NoteStorage (SQLite) → NoteListManager (reload) → UI updates selection
2. **Loading**: Sidebar selection → UI checks dirty state → EditorBuffer.load_content() → cursor reset
3. **Unsaved changes**: UI stores `pending_note_switch` and requires `:w` or `:e!` confirmation

### Layout Structure
Uses `prompt_toolkit.layout` with HSplit/VSplit:
```
HSplit [
  VSplit [
    sidebar (width=30),
    editor
  ],
  status_bar (height=1)
]
```

### Focus System
The FocusManager tracks which pane is active:
- Sidebar focused: `j/k` navigate notes, Enter loads selected note
- Editor focused: `j/k` move cursor, `i` enters Insert mode
- Switch with `Ctrl+W h/l` (vim-style window navigation)
- Only editor shows cursor when focused

### Storage Design
NoteStorage uses SQLite with a simple schema:
- In-memory by default (`:memory:`)
- Notes table: id (TEXT), content (TEXT), created_at, updated_at
- Updates bump updated_at timestamp, sorting notes by recency
- Includes dummy data initialization for first run

## Common Patterns

### Adding New Vim Commands
1. Define key binding in [key_bindings.py](src/termnotes/key_bindings.py) with appropriate filters
2. For multi-character commands (like `dd`), use `mode_manager.command_buffer`
3. For colon commands (like `:w`), add handler in `execute_command()` function

### Adding New Editor Operations
1. Add method to EditorBuffer class in [editor.py](src/termnotes/editor.py)
2. Call `self.mark_dirty()` if operation modifies content
3. Handle cursor position adjustments

### UI Updates
All UI content methods are called on every render:
- `get_text_content()` - editor display with cursor
- `get_sidebar_content()` - note list with selection
- `get_status_bar_content()` - mode, focus, position info
- Return `FormattedText` objects with style tuples
