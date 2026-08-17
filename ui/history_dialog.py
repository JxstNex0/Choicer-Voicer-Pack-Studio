"""
Choicer Voicer Pack Studio - Standalone Edition
Change History Dialog (Verlauf von Veränderungen)
"""

from typing import List, Dict, Any, Callable, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QWidget
)
from .theme import (
    COLOR_BG_DARK, COLOR_BG_PANEL, COLOR_BG_CARD,
    COLOR_CYAN_PRIMARY, COLOR_BORDER, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED
)


class HistoryDialog(QDialog):
    restore_index_requested = Signal(int)

    def __init__(
        self,
        undo_entries: List[Dict[str, Any]],
        redo_entries: List[Dict[str, Any]],
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setWindowTitle("Change History (Verlauf)")
        self.setFixedSize(480, 520)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_BG_DARK};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("📜 Change History / Verlauf")
        header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLOR_CYAN_PRIMARY};")
        layout.addWidget(header)

        sub = QLabel(f"Total steps recorded: {len(undo_entries) + len(redo_entries)}  |  Shortcuts: Ctrl+Z (Undo), Ctrl+Y (Redo)")
        sub.setStyleSheet("font-size: 11px; color: #a0aec0;")
        layout.addWidget(sub)

        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLOR_BG_PANEL};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 4px;
            }}
            QListWidget::item {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                margin: 2px 0px;
                padding: 8px 10px;
                color: {COLOR_TEXT_WHITE};
            }}
            QListWidget::item:hover {{
                border-color: {COLOR_CYAN_PRIMARY};
            }}
            QListWidget::item:selected {{
                background-color: #1a2a3f;
                border-color: {COLOR_CYAN_PRIMARY};
            }}
        """)
        layout.addWidget(self.list_widget, 1)

        # Populate
        all_items = []
        # Undone/past entries (chronological from oldest to newest)
        for i, entry in enumerate(undo_entries):
            desc = entry.get("description", "Change")
            ts = entry.get("timestamp", "")
            clips = entry.get("clips_count", 0)
            roles = entry.get("roles_count", 0)
            item = QListWidgetItem(f"✓  [{ts}]  {desc}  ({clips} clips, {roles} roles)")
            item.setData(Qt.UserRole, ("undo", i))
            self.list_widget.addItem(item)
            all_items.append(item)

        # Highlight current state
        if undo_entries:
            curr_item = QListWidgetItem("📍 --- CURRENT STATE ---")
            curr_item.setFlags(Qt.NoItemFlags)
            curr_item.setTextAlignment(Qt.AlignCenter)
            curr_item.setForeground(Qt.cyan)
            self.list_widget.addItem(curr_item)

        # Redo entries (forward steps)
        for i, entry in enumerate(reversed(redo_entries)):
            desc = entry.get("description", "Change")
            ts = entry.get("timestamp", "")
            item = QListWidgetItem(f"↷  [{ts}]  {desc} (Undone)")
            item.setForeground(Qt.gray)
            item.setData(Qt.UserRole, ("redo", i))
            self.list_widget.addItem(item)

        # Scroll to current state
        if all_items:
            self.list_widget.setCurrentItem(all_items[-1])

        # Bottom Buttons
        bottom_box = QHBoxLayout()
        bottom_box.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setFixedWidth(90)
        btn_close.clicked.connect(self.accept)
        bottom_box.addWidget(btn_close)

        layout.addLayout(bottom_box)
