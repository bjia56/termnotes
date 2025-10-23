"""
Focus management for multi-pane UI
"""

from enum import Enum


class FocusState(Enum):
    """Represents which pane has focus"""
    SIDEBAR = "SIDEBAR"
    EDITOR = "EDITOR"


class FocusManager:
    """Manages focus state between sidebar and editor"""

    def __init__(self, initial_focus: FocusState = FocusState.SIDEBAR):
        """
        Initialize focus manager

        Args:
            initial_focus: Which pane should have focus initially
        """
        self.current_focus = initial_focus

    def is_sidebar_focused(self) -> bool:
        """Check if sidebar has focus"""
        return self.current_focus == FocusState.SIDEBAR

    def is_editor_focused(self) -> bool:
        """Check if editor has focus"""
        return self.current_focus == FocusState.EDITOR

    def switch_to_sidebar(self):
        """Switch focus to sidebar"""
        self.current_focus = FocusState.SIDEBAR

    def switch_to_editor(self):
        """Switch focus to editor"""
        self.current_focus = FocusState.EDITOR

    def toggle_focus(self):
        """Toggle focus between sidebar and editor"""
        if self.is_sidebar_focused():
            self.switch_to_editor()
        else:
            self.switch_to_sidebar()

    def get_focus_name(self) -> str:
        """Get name of currently focused pane for display"""
        return self.current_focus.value
