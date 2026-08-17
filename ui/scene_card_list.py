"""
Choicer Voicer Pack Studio - Standalone Edition
Scene Cards List in Compact 2-Row Layout with Speaker Badges & Subtitles
"""

from typing import List, Dict, Any, Optional
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QScrollArea, QFrame, QMenu
)
from .theme import COLOR_BG_PANEL, COLOR_BG_CARD, COLOR_BORDER, COLOR_CYAN_PRIMARY, get_character_color
try:
    from core.pack_model import SceneClip
except ImportError:
    from ..core.pack_model import SceneClip


class SceneCard(QFrame):
    delete_requested = Signal(int)
    play_requested = Signal(float, float)
    changed = Signal(int, dict)

    def __init__(
        self,
        index: int,
        clip: SceneClip,
        all_characters: List[str],
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.index = index
        self.clip = clip
        self.all_characters = list(all_characters) if all_characters else []

        # Sanitize clip characters against existing all_characters
        if self.all_characters:
            valid_chars = [c for c in self.clip.characters if c in self.all_characters]
            if not valid_chars and self.clip.characters:
                # If characters were assigned but now invalid, fallback to first available
                valid_chars = [self.all_characters[0]]
            self.clip.characters = valid_chars
        else:
            self.clip.characters = []

        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("PanelFrame")
        self.setStyleSheet(f"""
            QFrame#PanelFrame {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-left: 3px solid {get_character_color(index)};
                border-radius: 6px;
                padding: 4px;
            }}
        """)

        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(6, 4, 6, 4)
        card_layout.setSpacing(3)

        # === ROW 1: Header (Number, Speaker Badge, Timing, Play, Delete) ===
        row1 = QHBoxLayout()
        row1.setSpacing(4)

        # Number #01
        self.lbl_num = QLabel(f"#{index + 1:02d}")
        self.lbl_num.setStyleSheet("font-weight: bold; color: #a0aec0; font-size: 11px;")
        self.lbl_num.setFixedWidth(26)
        row1.addWidget(self.lbl_num)

        # Speaker Badge Button (Click to open menu of available characters)
        self.btn_speaker = QPushButton()
        self.btn_speaker.setStyleSheet(f"""
            QPushButton {{
                background-color: #111722;
                color: {get_character_color(index)};
                border: 1px solid {get_character_color(index)};
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {get_character_color(index)};
                color: #000000;
            }}
        """)
        self._update_speaker_button_text()
        self.btn_speaker.clicked.connect(self._show_speaker_menu)
        row1.addWidget(self.btn_speaker)

        # Timing Badge (00:00.0 - 00:03.0)
        self.lbl_time = QLabel(f"{self._fmt(clip.start_time)} - {self._fmt(clip.end_time)}")
        self.lbl_time.setStyleSheet("font-family: monospace; font-size: 10px; color: #718096;")
        row1.addWidget(self.lbl_time)

        row1.addStretch()

        # Play Preview Button (▶)
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(26, 26)
        self.btn_play.setToolTip("Play this clip (Start to End)")
        self.btn_play.setStyleSheet("""
            QPushButton {
                background-color: #1a2332;
                color: #00f2fe;
                border: 1px solid #00f2fe;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #00f2fe;
                color: #000000;
            }
            QPushButton:pressed {
                background-color: #00c4d4;
                color: #000000;
            }
        """)
        self.btn_play.clicked.connect(lambda: self.play_requested.emit(self.clip.start_time, self.clip.end_time))
        row1.addWidget(self.btn_play)

        # Delete Button (✕)
        self.btn_del = QPushButton("✕")
        self.btn_del.setFixedSize(26, 26)
        self.btn_del.setToolTip("Delete this clip")
        self.btn_del.setStyleSheet("""
            QPushButton {
                background-color: #1a2332;
                color: #ff4d4f;
                border: 1px solid #ff4d4f;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #ff4d4f;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #d9363e;
                color: #ffffff;
            }
        """)
        self.btn_del.clicked.connect(lambda: self.delete_requested.emit(self.index))
        row1.addWidget(self.btn_del)

        card_layout.addLayout(row1)

        # === ROW 2+: Subtitle Input(s) (Dynamic 1 or multiple lines) ===
        self.subs_container = QVBoxLayout()
        self.subs_container.setContentsMargins(0, 2, 0, 0)
        self.subs_container.setSpacing(4)
        card_layout.addLayout(self.subs_container)

        self._rebuild_subtitles_layout()

    def _rebuild_subtitles_layout(self) -> None:
        # Clear existing subtitle widgets
        while self.subs_container.count():
            item = self.subs_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                sub_l = item.layout()
                while sub_l.count():
                    si = sub_l.takeAt(0)
                    if si.widget():
                        si.widget().deleteLater()
                sub_l.deleteLater()

        chars = self.clip.characters
        if len(chars) <= 1:
            # Single dialogue line
            c_name = chars[0] if chars else ""
            txt_edit = QLineEdit()
            txt_edit.setPlaceholderText(f"Enter dialogue for {c_name}..." if c_name else "Enter dialogue / subtitle here...")
            txt_edit.setText(self.clip.get_character_subtitle(c_name) if c_name else self.clip.subtitle)
            txt_edit.setStyleSheet("font-size: 11px; padding: 3px 6px;")
            txt_edit.textChanged.connect(lambda t: self._on_single_sub_changed(t, c_name))
            self.subs_container.addWidget(txt_edit)
        else:
            # Multiple speakers: Dedicated input line for each character
            for idx, ch in enumerate(chars):
                row = QHBoxLayout()
                row.setContentsMargins(0, 0, 0, 0)
                row.setSpacing(4)

                # Character colored badge
                char_idx = self.all_characters.index(ch) if ch in self.all_characters else idx
                col = get_character_color(char_idx)
                lbl_badge = QLabel(ch)
                lbl_badge.setStyleSheet(f"""
                    QLabel {{
                        background-color: #111722;
                        color: {col};
                        border: 1px solid {col};
                        border-radius: 4px;
                        padding: 2px 5px;
                        font-size: 10px;
                        font-weight: bold;
                    }}
                """)
                lbl_badge.setFixedWidth(75)
                row.addWidget(lbl_badge)

                # Dialogue input line
                txt_char = QLineEdit()
                txt_char.setPlaceholderText(f"What does {ch} say?...")
                txt_char.setText(self.clip.get_character_subtitle(ch))
                txt_char.setStyleSheet("font-size: 11px; padding: 3px 6px;")
                txt_char.textChanged.connect(lambda t, name=ch: self._on_char_sub_changed(name, t))
                row.addWidget(txt_char, 1)

                self.subs_container.addLayout(row)

    def _update_speaker_button_text(self) -> None:
        chars = self.clip.characters
        if len(chars) > 1:
            self.btn_speaker.setText(f"👥 {chars[0]} +{len(chars)-1}")
        elif chars:
            self.btn_speaker.setText(f"👤 {chars[0]}")
        else:
            self.btn_speaker.setText("👤 No Role")

    def _show_speaker_menu(self) -> None:
        if not self.all_characters:
            return
        menu = QMenu(self)
        for ch in self.all_characters:
            act = menu.addAction(ch)
            act.setCheckable(True)
            act.setChecked(ch in self.clip.characters)
            act.triggered.connect(lambda checked, name=ch: self._toggle_character(name, checked))
        menu.exec_(self.btn_speaker.mapToGlobal(self.btn_speaker.rect().bottomLeft()))

    def _toggle_character(self, name: str, checked: bool) -> None:
        if checked and name not in self.clip.characters:
            self.clip.characters.append(name)
        elif not checked and name in self.clip.characters:
            self.clip.characters.remove(name)
        self._update_speaker_button_text()
        self._rebuild_subtitles_layout()
        self.changed.emit(self.index, self.clip.to_dict())

    def _on_single_sub_changed(self, text: str, char_name: str) -> None:
        if char_name:
            self.clip.set_character_subtitle(char_name, text)
        else:
            self.clip.subtitle = text
        self.changed.emit(self.index, self.clip.to_dict())

    def _on_char_sub_changed(self, char_name: str, text: str) -> None:
        self.clip.set_character_subtitle(char_name, text)
        self.changed.emit(self.index, self.clip.to_dict())

    @staticmethod
    def _fmt(sec: float) -> str:
        mins = int(sec // 60)
        secs = int(sec % 60)
        msecs = int((sec * 10) % 10)
        return f"{mins:02d}:{secs:02d}.{msecs}"


class SceneCardList(QWidget):
    clip_delete_requested = Signal(int)
    clip_play_requested = Signal(float, float)
    clip_changed = Signal(int, dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.clips: List[SceneClip] = []
        self.all_characters: List[str] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # Header
        self.lbl_header = QLabel("SCENES / LINES (0 CLIPS)")
        self.lbl_header.setStyleSheet("font-weight: bold; font-size: 11px; color: #a0aec0;")
        main_layout.addWidget(self.lbl_header)

        # Scroll Area for cards
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(4)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setWidget(self.cards_container)
        main_layout.addWidget(self.scroll)

    def set_data(self, clips: List[SceneClip], all_characters: List[str], scroll_to_bottom: bool = False) -> None:
        self.clips = clips
        self.all_characters = all_characters
        self.lbl_header.setText(f"SCENES / LINES ({len(clips)} CLIPS)")

        # Clear existing
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for idx, clip in enumerate(self.clips):
            card = SceneCard(idx, clip, self.all_characters)
            card.delete_requested.connect(self.clip_delete_requested.emit)
            card.play_requested.connect(self.clip_play_requested.emit)
            card.changed.connect(self.clip_changed.emit)
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

        if scroll_to_bottom:
            self.scroll_to_bottom()

    def scroll_to_bottom(self) -> None:
        QTimer.singleShot(30, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))
        QTimer.singleShot(120, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))
