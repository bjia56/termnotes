"""
Storage backends for termnotes

Provides flexible storage with multiple backend implementations:
- SQLiteBackend: Fast in-memory or file-based SQLite storage
- FilesystemBackend: JSON files on disk
- GoogleDriveBackend: JSON files in Google Drive
- CompositeBackend: Combines multiple backends (cache + persistent)
"""

import uuid
from .base import StorageBackend
from .sqlite_backend import SQLiteBackend
from .filesystem_backend import FilesystemBackend
from .composite_backend import CompositeBackend
from .gdrive_backend import GoogleDriveBackend
from ..note import Note

# Backward compatibility alias
NoteStorage = SQLiteBackend


def create_default_storage() -> StorageBackend:
    """
    Create the default storage backend for termnotes.

    Returns a composite backend with:
    - SQLite in-memory cache (fast reads/writes)
    - Filesystem persistent storage (durable)

    If the storage is empty, populates it with a welcome note.

    Returns:
        CompositeBackend configured with SQLite cache + filesystem storage
    """
    cache = SQLiteBackend(":memory:")
    persistent = FilesystemBackend()  # Uses ~/.termnotes/notes by default

    storage = CompositeBackend(cache, persistent)

    # Insert welcome note if storage is empty
    if len(storage.get_all_notes()) == 0:
        welcome_content = """# Welcome to termnotes!

A vim-like terminal note-taking application with markdown support.

## Quick Start Guide

### Navigation
- `Ctrl+W h` - Switch to sidebar
- `Ctrl+W l` - Switch to editor
- `j/k` - Move down/up (in both sidebar and editor)
- `h/l` - Move left/right in editor

### Creating Notes
- `:new` or `:n` - Create new empty note
- `o` - Create new note (when sidebar is focused)

### Deleting Notes
- `dd` - Delete selected note (when sidebar is focused, confirms with second dd)
- `:delete` or `:d` - Delete current note (confirms with second :d)
- `:d!` - Force delete current note without confirmation

### Editing
- `i` - Enter Insert mode
- `Esc` - Return to Normal mode
- `dd` - Delete current line (when editor is focused)
- `o` - Insert new line below (when editor is focused)
- `O` - Insert new line above

### Vim Commands
- `:w` - Save current note
- `:e!` - Discard changes and reload
- `:q` - Quit (prompts if unsaved changes)
- `:wq` - Save and quit

## Code Highlighting Example

termnotes supports syntax highlighting for code blocks:

```python
def fibonacci(n):
    \"\"\"Calculate the nth Fibonacci number\"\"\"
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Generate first 10 Fibonacci numbers
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
```

Happy note-taking!
"""
        welcome_note = Note(note_id=str(uuid.uuid4()), content=welcome_content)
        storage.save_note(welcome_note)

    return storage


__all__ = [
    "StorageBackend",
    "SQLiteBackend",
    "FilesystemBackend",
    "GoogleDriveBackend",
    "CompositeBackend",
    "NoteStorage",
    "create_default_storage",
]
