"""
Storage backends for termnotes

Provides flexible storage with multiple backend implementations:
- SQLiteBackend: Fast in-memory or file-based SQLite storage
- FilesystemBackend: JSON files on disk
- GoogleDriveBackend: JSON files in Google Drive
- CompositeBackend: Combines multiple backends (cache + persistent)
- EncryptedBackend: Wraps another backend with encryption/decryption
"""

import uuid
from .base import StorageBackend
from .sqlite_backend import SQLiteBackend
from .filesystem_backend import FilesystemBackend
from .composite_backend import CompositeBackend
from .gdrive_backend import GoogleDriveBackend
from .encrypted_backend import EncryptedBackend
from ..note import Note
from ..config import get_config

# Backward compatibility alias
NoteStorage = SQLiteBackend


def _create_backend(backend_type: str, config) -> StorageBackend:
    """
    Create a storage backend by type.

    Args:
        backend_type: Type of backend ("sqlite", "filesystem", "gdrive")
        config: Config instance

    Returns:
        StorageBackend instance
    """
    if backend_type == "sqlite":
        return SQLiteBackend(config.sqlite_path)
    elif backend_type == "gdrive":
        return GoogleDriveBackend(
            credentials_path=config.gdrive_credentials_path,
            token_path=config.gdrive_token_path,
            app_folder=config.gdrive_folder_name
        )
    elif backend_type == "filesystem":
        return FilesystemBackend(config.filesystem_directory)
    else:
        raise ValueError(f"Unknown storage backend: {backend_type}")


def _get_or_create_passphrase(config) -> str:
    """
    Get passphrase from key file or generate new one.

    Priority:
    1. Passphrase from key_file
    2. Generate new passphrase and save to key_file

    The key_file stores: UTF-8 passphrase string
    Salt is derived from the passphrase using BLAKE2b, so we don't need to store it.

    Args:
        config: Config instance

    Returns:
        Passphrase string
    """
    import os
    from pathlib import Path

    key_file_path = Path(config.encrypted_key_file)

    # Try to read from key file
    if key_file_path.exists():
        try:
            with open(key_file_path, "r", encoding='utf-8') as f:
                passphrase = f.read().strip()
            if passphrase:
                return passphrase
            else:
                print(f"Warning: Key file {key_file_path} is empty, regenerating")
        except Exception as e:
            print(f"Warning: Failed to read key file {key_file_path}: {e}")

    # Generate new passphrase
    print(f"Generating new encryption passphrase...")
    passphrase = EncryptedBackend.generate_passphrase()

    # Save to key file
    try:
        key_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(key_file_path, "w", encoding='utf-8') as f:
            f.write(passphrase)
        # Set restrictive permissions (owner read/write only)
        os.chmod(key_file_path, 0o600)

        print(f"✓ Generated passphrase: {passphrase}")
        print(f"✓ Saved to {key_file_path}")
        print(f"⚠️  Keep this passphrase secure! Write it down in a safe place.")
        print(f"⚠️  Without it, encrypted notes cannot be decrypted.")
    except Exception as e:
        print(f"Warning: Failed to save key file: {e}")

    print("Press Enter to continue...")
    input()

    return passphrase


def create_default_storage() -> StorageBackend:
    """
    Create the default storage backend for termnotes.

    Returns a composite backend with:
    - SQLite in-memory cache (fast reads/writes)
    - Configured persistent storage (filesystem, sqlite, gdrive, or encrypted)

    For encrypted backend, automatically generates and saves encryption key if needed.

    If the storage is empty, populates it with a welcome note.

    Returns:
        CompositeBackend configured with SQLite cache + persistent storage
    """
    config = get_config()
    cache = SQLiteBackend(":memory:")

    # Create persistent backend based on configuration
    backend_type = config.storage_backend

    if backend_type == "encrypted":
        # Get or create passphrase (salt will be derived from passphrase)
        passphrase = _get_or_create_passphrase(config)

        # Create the wrapped backend
        wrapped_type = config.encrypted_wraps
        wrapped_backend = _create_backend(wrapped_type, config)

        # Wrap with encryption (passphrase will be converted to key via PBKDF2)
        # Salt is derived from passphrase using BLAKE2b
        persistent = EncryptedBackend(wrapped_backend, passphrase)
    else:
        # Standard backend (no encryption)
        persistent = _create_backend(backend_type, config)

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
    "EncryptedBackend",
    "NoteStorage",
    "create_default_storage",
]
