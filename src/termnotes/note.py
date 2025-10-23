"""
Note data model
"""


class Note:
    """Represents a single note"""

    def __init__(self, note_id: str, content: str = ""):
        """
        Initialize a note

        Args:
            note_id: Unique identifier for the note
            content: Full content of the note
        """
        self.id = note_id
        self.content = content

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

    def __repr__(self) -> str:
        preview = self.get_preview(20)
        return f"Note(id={self.id}, preview={preview})"
