"""
Note data model
"""

from typing import Optional, Dict, Any
from datetime import datetime
from .utils import utc_now


class Note:
    """Represents a single note with content and metadata properties"""

    def __init__(
        self,
        note_id: str,
        content: str = "",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a note

        Args:
            note_id: Unique identifier for the note
            content: Full content of the note
            created_at: When the note was created (optional)
            updated_at: When the note was last updated (optional)
            properties: Key-value metadata properties (optional)
                       Examples: {"encrypted": True, "tags": ["work", "todo"]}
        """
        self.id = note_id
        self.content = content
        self.created_at = created_at or utc_now()
        self.updated_at = updated_at or utc_now()
        self.properties = properties or {}

    def get_preview(self, max_length: int = 25) -> str:
        """
        Get a preview of the note for display in sidebar

        Args:
            max_length: Maximum number of characters to return

        Returns:
            Preview string (first line of content)
        """
        # Use first line of content, or empty string if no content
        if not self.content:
            preview_text = "(empty note)"
        else:
            preview_text = self.content.split('\n')[0]

        if len(preview_text) > max_length:
            return preview_text[:max_length - 3] + "..."
        return preview_text

    def get_property(self, key: str, default: Any = None) -> Any:
        """
        Get a property value

        Args:
            key: Property key
            default: Default value if key doesn't exist

        Returns:
            Property value or default
        """
        return self.properties.get(key, default)

    def set_property(self, key: str, value: Any):
        """
        Set a property value

        Args:
            key: Property key
            value: Property value (must be JSON-serializable)
        """
        self.properties[key] = value

    def has_property(self, key: str) -> bool:
        """
        Check if a property exists

        Args:
            key: Property key

        Returns:
            True if property exists
        """
        return key in self.properties

    def delete_property(self, key: str):
        """
        Delete a property

        Args:
            key: Property key
        """
        self.properties.pop(key, None)

    def __repr__(self) -> str:
        preview = self.get_preview(20)
        props_count = len(self.properties)
        return f"Note(id={self.id}, preview={preview}, properties={props_count})"
