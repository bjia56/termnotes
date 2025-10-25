"""Configuration management for termnotes."""

import os
import tomllib
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager for termnotes."""

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _get_config_paths(self) -> list[Path]:
        """Get list of config file paths in priority order."""
        paths = []

        # Working directory config (highest priority)
        paths.append(Path.cwd() / "termnotes.toml")

        # XDG config directory
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            paths.append(Path(config_home) / "termnotes" / "config.toml")
        else:
            paths.append(Path.home() / ".config" / "termnotes" / "config.toml")

        # Fallback home directory config
        paths.append(Path.home() / ".termnotes.toml")

        return paths

    def _load_config(self):
        """Load configuration from file."""
        for path in self._get_config_paths():
            if path.exists():
                try:
                    with open(path, "rb") as f:
                        self._config = tomllib.load(f)
                    return
                except Exception as e:
                    print(f"Warning: Failed to load config from {path}: {e}")

        # No config found, use defaults
        self._config = self._get_defaults()

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "storage": {
                "backend": "sqlite",
                "sqlite": {
                    "path": "~/.local/share/termnotes/notes.db"
                },
                "gdrive": {
                    "credentials_path": "~/.config/termnotes/gdrive_credentials.json",
                    "token_path": "~/.config/termnotes/gdrive_token.json",
                    "folder_name": "termnotes"
                },
                "filesystem": {
                    "directory": "~/.local/share/termnotes/notes/"
                }
            }
        }

    def _expand_path(self, path: str) -> str:
        """Expand ~ and environment variables in path."""
        return os.path.expanduser(os.path.expandvars(path))

    @property
    def storage_backend(self) -> str:
        """Get the configured storage backend."""
        return self._config.get("storage", {}).get("backend", "sqlite")

    @property
    def sqlite_path(self) -> str:
        """Get the SQLite database path."""
        path = self._config.get("storage", {}).get("sqlite", {}).get(
            "path", "~/.local/share/termnotes/notes.db"
        )
        return self._expand_path(path)

    @property
    def gdrive_credentials_path(self) -> str:
        """Get the Google Drive credentials path."""
        path = self._config.get("storage", {}).get("gdrive", {}).get(
            "credentials_path", "~/.config/termnotes/gdrive_credentials.json"
        )
        return self._expand_path(path)

    @property
    def gdrive_token_path(self) -> str:
        """Get the Google Drive token path."""
        path = self._config.get("storage", {}).get("gdrive", {}).get(
            "token_path", "~/.config/termnotes/gdrive_token.json"
        )
        return self._expand_path(path)

    @property
    def gdrive_folder_name(self) -> str:
        """Get the Google Drive folder name."""
        return self._config.get("storage", {}).get("gdrive", {}).get(
            "folder_name", "termnotes"
        )

    @property
    def filesystem_directory(self) -> str:
        """Get the filesystem storage directory."""
        path = self._config.get("storage", {}).get("filesystem", {}).get(
            "directory", "~/.local/share/termnotes/notes/"
        )
        return self._expand_path(path)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def get_example_config() -> str:
    """Get example configuration file content."""
    return """# termnotes configuration file
# Copy this to one of the following locations:
#   - ~/.config/termnotes/config.toml (recommended)
#   - ~/.termnotes.toml
#   - ./termnotes.toml (in your working directory)

[storage]
# Backend type: "sqlite", "gdrive", or "filesystem"
backend = "sqlite"

# SQLite backend configuration
[storage.sqlite]
# Path to SQLite database file
# Default: ~/.local/share/termnotes/notes.db
path = "~/.local/share/termnotes/notes.db"

# Google Drive backend configuration
[storage.gdrive]
# Path to OAuth2 credentials JSON file (download from Google Cloud Console)
# Default: ~/.config/termnotes/gdrive_credentials.json
credentials_path = "~/.config/termnotes/gdrive_credentials.json"

# Path to store user access token (generated on first auth)
# Default: ~/.config/termnotes/gdrive_token.json
token_path = "~/.config/termnotes/gdrive_token.json"

# Folder name in Google Drive root to store notes
# Default: termnotes
folder_name = "termnotes"

# Filesystem backend configuration
[storage.filesystem]
# Directory to store note files as JSON
# Default: ~/.local/share/termnotes/notes/
directory = "~/.local/share/termnotes/notes/"
"""
