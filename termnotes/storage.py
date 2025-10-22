"""Storage backend configuration."""

import os
from pathlib import Path
from typing import Optional
from .database import Database


class StorageBackend:
    """Storage backend configuration."""
    
    @staticmethod
    def get_database(backend: Optional[str] = None) -> Database:
        """Get a configured database instance.
        
        Args:
            backend: Backend type. Options:
                - None or "memory": In-memory database
                - "filesystem" or path: Persistent file-based storage
                
        Returns:
            Configured Database instance
        """
        if backend is None or backend == "memory":
            return Database(":memory:")
        
        if backend == "filesystem":
            # Default filesystem location
            notes_dir = Path.home() / ".termnotes"
            notes_dir.mkdir(exist_ok=True)
            db_path = notes_dir / "notes.db"
            return Database(str(db_path))
        
        # Treat as custom path
        db_path = Path(backend)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return Database(str(db_path))
