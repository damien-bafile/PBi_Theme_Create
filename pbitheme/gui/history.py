"""Undo/Redo history manager for theme editing."""

from __future__ import annotations

import copy
from typing import Callable

from ..model import PowerBITheme


class ThemeHistory:
    """Manages undo/redo history for theme edits."""

    def __init__(self, max_size: int = 20) -> None:
        """Initialize history with a maximum size.

        Args:
            max_size: Maximum number of states to keep (oldest discarded when exceeded)
        """
        self._max_size = max_size
        self._undo_stack: list[PowerBITheme] = []
        self._redo_stack: list[PowerBITheme] = []

    def push(self, theme: PowerBITheme) -> None:
        """Record the current theme state for undo.

        Args:
            theme: The theme state to save
        """
        # Deep copy to avoid reference issues
        self._undo_stack.append(copy.deepcopy(theme))

        # Clear redo stack (new edit after undo)
        self._redo_stack.clear()

        # Enforce max size by removing oldest
        if len(self._undo_stack) > self._max_size:
            self._undo_stack.pop(0)

    def undo(self) -> PowerBITheme | None:
        """Pop and return the previous theme state, or None if no history.

        Returns:
            Previous theme state, or None if nothing to undo
        """
        if not self._undo_stack:
            return None

        # Current state goes to redo
        # (This will be called after current theme is collected)
        state = self._undo_stack.pop()
        return state

    def redo(self) -> PowerBITheme | None:
        """Pop and return the next theme state, or None if no redo history.

        Returns:
            Next theme state, or None if nothing to redo
        """
        if not self._redo_stack:
            return None

        state = self._redo_stack.pop()
        return state

    def save_for_redo(self, theme: PowerBITheme) -> None:
        """Save the current theme to redo stack before undoing.

        Args:
            theme: The current theme state (becomes available for redo)
        """
        self._redo_stack.append(copy.deepcopy(theme))

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0

    def clear(self) -> None:
        """Clear all history (e.g., when opening a new file)."""
        self._undo_stack.clear()
        self._redo_stack.clear()

    def undo_depth(self) -> int:
        """Return the number of undo states available."""
        return len(self._undo_stack)

    def redo_depth(self) -> int:
        """Return the number of redo states available."""
        return len(self._redo_stack)
