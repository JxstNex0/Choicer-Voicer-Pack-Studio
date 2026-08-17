"""
Choicer Voicer Pack Studio - Standalone Edition
Character Roles Manager with Multi-Speaker Badges & Colors
"""

from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QScrollArea, QFrame
)
from .theme import COLOR_BG_PANEL, COLOR_BORDER, COLOR_TEXT_WHITE, get_character_color


class CharacterPill(QWidget):
    toggled = Signal(str, bool)
    delete_requested = Signal(str)

    def __init__(self, name: str, color_hex: str, is_active: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.char_name = name
        self.color_hex = color_hex
        self.is_active = is_active

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # Toggle Button
        self.btn_toggle = QPushButton()
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setChecked(is_active)
        self.btn_toggle.clicked.connect(self._on_toggle)
        self._update_style()
        layout.addWidget(self.btn_toggle)

        # Delete Button (X)
        self.btn_del = QPushButton("✕")
        self.btn_del.setFixedSize(18, 18)
        self.btn_del.setStyleSheet("background: transparent; color: #e53e3e; border: none; font-weight: bold;")
        self.btn_del.setToolTip(f"Delete role '{name}'")
        self.btn_del.clicked.connect(lambda: self.delete_requested.emit(self.char_name))
        layout.addWidget(self.btn_del)

    def set_active(self, active: bool) -> None:
        self.is_active = active
        self.btn_toggle.setChecked(active)
        self._update_style()

    def _on_toggle(self) -> None:
        self.is_active = self.btn_toggle.isChecked()
        self._update_style()
        self.toggled.emit(self.char_name, self.is_active)

    def _update_style(self) -> None:
        prefix = "✓ " if self.is_active else "○ "
        self.btn_toggle.setText(f"{prefix}{self.char_name}")
        bg = f"rgba({int(self.color_hex[1:3], 16)}, {int(self.color_hex[3:5], 16)}, {int(self.color_hex[5:7], 16)}, 0.3)" if self.is_active else "#111722"
        self.btn_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {self.color_hex};
                border: 1px solid {self.color_hex};
                border-radius: 4px;
                padding: 3px 8px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {self.color_hex};
                color: #000000;
            }}
        """)


class CharacterRoster(QWidget):
    roster_changed = Signal(list)  # list of character names
    active_selection_changed = Signal(list)  # list of currently checked characters

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.characters: List[str] = []
        self.active_characters: List[str] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # Header with Add Row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        lbl = QLabel("ROLES / CHARACTERS")
        lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #a0aec0;")
        header_layout.addWidget(lbl)
        header_layout.addStretch()

        self.txt_new_role = QLineEdit()
        self.txt_new_role.setPlaceholderText("New Role...")
        self.txt_new_role.setFixedWidth(100)
        self.txt_new_role.returnPressed.connect(self._add_role)
        header_layout.addWidget(self.txt_new_role)

        self.btn_add = QPushButton("+ Add")
        self.btn_add.setFixedWidth(50)
        self.btn_add.clicked.connect(self._add_role)
        header_layout.addWidget(self.btn_add)

        main_layout.addLayout(header_layout)

        # Scrollable Pills List
        self.pills_container = QWidget()
        self.pills_layout = QVBoxLayout(self.pills_container)
        self.pills_layout.setContentsMargins(0, 0, 0, 0)
        self.pills_layout.setSpacing(3)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self.pills_container)
        scroll.setMinimumHeight(45)
        main_layout.addWidget(scroll, 1)

        self._rebuild_pills()

    def set_characters(self, characters: List[str], active: Optional[List[str]] = None) -> None:
        self.characters = list(characters) if characters else []
        if active is not None:
            self.active_characters = [c for c in active if c in self.characters]
        elif self.characters:
            self.active_characters = [self.characters[0]]
        else:
            self.active_characters = []
        self._rebuild_pills()

    def get_characters(self) -> List[str]:
        return self.characters

    def get_active_characters(self) -> List[str]:
        if self.active_characters:
            return self.active_characters
        if self.characters:
            return [self.characters[0]]
        return []

    def _add_role(self) -> None:
        name = self.txt_new_role.text().strip()
        if name and name not in self.characters:
            self.characters.append(name)
            if not self.active_characters:
                self.active_characters.append(name)
            self.txt_new_role.clear()
            self._rebuild_pills()
            self.roster_changed.emit(self.characters)
            self.active_selection_changed.emit(self.active_characters)

    def _delete_role(self, name: str) -> None:
        if name in self.characters:
            self.characters.remove(name)
            if name in self.active_characters:
                self.active_characters.remove(name)
            if not self.active_characters and self.characters:
                self.active_characters = [self.characters[0]]
            self._rebuild_pills()
            self.roster_changed.emit(self.characters)
            self.active_selection_changed.emit(self.active_characters)

    def _on_pill_toggled(self, name: str, is_active: bool) -> None:
        if is_active and name not in self.active_characters:
            self.active_characters.append(name)
        elif not is_active and name in self.active_characters:
            if len(self.active_characters) > 1:
                self.active_characters.remove(name)
            else:
                self._rebuild_pills()
                return

        self.active_selection_changed.emit(self.active_characters)

    def _rebuild_pills(self) -> None:
        # Clear existing
        while self.pills_layout.count():
            item = self.pills_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not self.characters:
            lbl_empty = QLabel("No roles added yet.\nType a name above and click '+ Add'.")
            lbl_empty.setStyleSheet("color: #718096; font-size: 11px; font-style: italic; padding: 6px 2px;")
            self.pills_layout.addWidget(lbl_empty)
        else:
            for idx, ch in enumerate(self.characters):
                col = get_character_color(idx)
                is_act = ch in self.active_characters
                pill = CharacterPill(ch, col, is_act)
                pill.toggled.connect(self._on_pill_toggled)
                pill.delete_requested.connect(self._delete_role)
                self.pills_layout.addWidget(pill)

        self.pills_layout.addStretch()
