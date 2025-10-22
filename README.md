# Termnotes

A terminal-based note-taking application built with Python and prompt_toolkit.

## Features

- **Terminal UI**: Clean, intuitive interface with split-view layout
- **Markdown Support**: Write notes in Markdown with syntax highlighting
- **Mouse Support**: Click to select notes and position cursor
- **SQLite Backend**: Fast, reliable in-memory or persistent storage
- **Configurable Storage**: Choose between in-memory, filesystem, or custom database paths
- **CRUD Operations**: Create, read, update, and delete notes seamlessly

## Installation

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

## Usage

### In-Memory Mode (Default)
Notes are stored in memory and lost when you exit:

```bash
termnotes
```

### Persistent Mode
Notes are saved to `~/.termnotes/notes.db`:

```bash
termnotes --backend filesystem
```

### Custom Database Path
Specify a custom location for your notes database:

```bash
termnotes --backend /path/to/my/notes.db
```

## Keyboard Shortcuts

- **Ctrl+N**: Create a new note
- **Ctrl+S**: Save the current note
- **Ctrl+D**: Delete the current note
- **Ctrl+L**: Focus the note list
- **Ctrl+E**: Focus the editor
- **Ctrl+Q**: Quit the application
- **↑/↓**: Navigate through notes (when note list is focused)
- **Enter**: Select a note and switch to editor

## Interface

The application has a two-pane layout:

```
┌─ Notes ──────────┬─ Content ─────────────────────────────┐
│                  │                                        │
│  Welcome         │  # Welcome to Termnotes               │
│  Shopping List   │                                        │
│> My Ideas        │  This is a Markdown note.              │
│  Meeting Notes   │                                        │
│                  │  - Feature 1                           │
│                  │  - Feature 2                           │
│                  │                                        │
└──────────────────┴────────────────────────────────────────┘
^N: New | ^S: Save | ^D: Delete | ^L: List | ^E: Edit | ^Q: Quit
```

- **Left pane**: List of all notes (most recently updated first)
- **Right pane**: Content editor with Markdown syntax highlighting
- **Bottom bar**: Keyboard shortcuts reminder

## Note Management

### Creating Notes
1. Press **Ctrl+N** to create a new note
2. Start typing in the editor
3. The first line becomes the note title
4. Press **Ctrl+S** to save

### Editing Notes
1. Use **↑/↓** arrows or mouse to select a note
2. Press **Enter** or **Ctrl+E** to edit
3. Modify the content
4. Press **Ctrl+S** to save changes

### Deleting Notes
1. Select the note you want to delete
2. Press **Ctrl+D** to delete it

### Auto-Title
The note title is automatically extracted from the first line of content. If the first line starts with `#` (Markdown header), it's stripped from the title.

## Storage Backends

### In-Memory (`:memory:`)
- Fast and temporary
- Perfect for quick notes during a session
- Notes are lost when you exit

### Filesystem (`filesystem`)
- Persistent storage at `~/.termnotes/notes.db`
- Notes survive between sessions
- Automatic directory creation

### Custom Path
- Store notes at any location
- Useful for project-specific notes
- Example: `termnotes --backend ~/projects/my-project/notes.db`

## Requirements

- Python >= 3.8
- prompt_toolkit >= 3.0.0
- pygments >= 2.0.0

## License

See LICENSE file for details.
