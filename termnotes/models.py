"""Data models for notes."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Note:
    """Represents a note."""
    
    id: Optional[int]
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
