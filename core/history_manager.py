"""
Choicer Voicer Pack Studio - Standalone Edition
Undo / Redo & Change History Management
"""

import time
from typing import List, Dict, Any, Optional


class HistoryEntry:
    def __init__(self, description: str, snapshot: Dict[str, Any]):
        self.description = description
        self.snapshot = snapshot
        self.timestamp = time.strftime("%H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "timestamp": self.timestamp,
            "clips_count": len(self.snapshot.get("clips", [])),
            "roles_count": len(self.snapshot.get("characters", []))
        }


class HistoryManager:
    def __init__(self, max_history: int = 60):
        self.max_history = max_history
        self.undo_stack: List[HistoryEntry] = []
        self.redo_stack: List[HistoryEntry] = []

    @property
    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def push_state(self, description: str, snapshot: Dict[str, Any]) -> None:
        """Record a state before/after a change occurs."""
        entry = HistoryEntry(description, snapshot)
        self.undo_stack.append(entry)
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        # Any new mutation invalidates the redo branch
        self.redo_stack.clear()

    def undo(self, current_snapshot: Dict[str, Any]) -> Optional[HistoryEntry]:
        """Perform undo: current state is pushed to redo, and previous state is restored."""
        if not self.can_undo:
            return None
        prev_entry = self.undo_stack.pop()
        # Save current state to redo
        self.redo_stack.append(HistoryEntry(prev_entry.description, current_snapshot))
        return prev_entry

    def redo(self, current_snapshot: Dict[str, Any]) -> Optional[HistoryEntry]:
        """Perform redo: current state is pushed to undo, and next state is restored."""
        if not self.can_redo:
            return None
        next_entry = self.redo_stack.pop()
        self.undo_stack.append(HistoryEntry(next_entry.description, current_snapshot))
        return next_entry

    def get_history_entries(self) -> List[Dict[str, Any]]:
        """Return all history entries for UI display."""
        return [entry.to_dict() for entry in self.undo_stack]

    def clear(self) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()
