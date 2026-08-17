"""
Choicer Voicer Pack Studio - Standalone Edition
Cutter Toolbar with Precision Timing, Split, Auto-Cutter & Zoom Controls
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QSlider, QSizePolicy
)
from .theme import COLOR_CYAN_PRIMARY, COLOR_ACCENT_ORANGE, COLOR_TEXT_WHITE


class CutterToolbar(QWidget):
    play_pause_clicked = Signal()
    set_start_clicked = Signal()
    set_end_clicked = Signal()
    split_clicked = Signal()
    auto_split_clicked = Signal()
    add_scene_clicked = Signal()
    timeline_seeked = Signal(float)
    zoom_in_clicked = Signal()
    zoom_out_clicked = Signal()
    zoom_fit_clicked = Signal()
    zoom_slider_changed = Signal(float)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.duration_sec: float = 60.0
        self.current_time_sec: float = 0.0
        self._slider_dragging: bool = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 4, 0, 4)
        main_layout.setSpacing(4)

        # === ROW 1: Playbar (Play/Pause, Slider, Timecode) ===
        row_playbar = QHBoxLayout()
        row_playbar.setSpacing(8)

        self.btn_play_pause = QPushButton("▶ Play")
        self.btn_play_pause.setObjectName("PrimaryButton")
        self.btn_play_pause.setMinimumWidth(80)
        self.btn_play_pause.clicked.connect(self.play_pause_clicked.emit)
        row_playbar.addWidget(self.btn_play_pause)

        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setRange(0, 600)  # in tenths of a second
        self.timeline_slider.sliderMoved.connect(self._on_slider_moved)
        self.timeline_slider.sliderPressed.connect(self._on_slider_pressed)
        self.timeline_slider.sliderReleased.connect(self._on_slider_released)
        row_playbar.addWidget(self.timeline_slider)

        self.lbl_timecode = QLabel("00:00.0")
        self.lbl_timecode.setStyleSheet("font-family: monospace; font-size: 13px; font-weight: bold; color: #a0aec0;")
        self.lbl_timecode.setMinimumWidth(65)
        row_playbar.addWidget(self.lbl_timecode)

        main_layout.addLayout(row_playbar)

        # === ROW 2: Cutter & Zoom Action Buttons ===
        row_cutter = QHBoxLayout()
        row_cutter.setSpacing(6)

        self.btn_start = QPushButton("[ Start: 00:00.0")
        self.btn_start.setStyleSheet(f"border-left: 3px solid {COLOR_CYAN_PRIMARY};")
        self.btn_start.clicked.connect(self.set_start_clicked.emit)
        row_cutter.addWidget(self.btn_start)

        self.btn_end = QPushButton("] End: 00:03.0")
        self.btn_end.setStyleSheet(f"border-left: 3px solid {COLOR_ACCENT_ORANGE};")
        self.btn_end.clicked.connect(self.set_end_clicked.emit)
        row_cutter.addWidget(self.btn_end)

        self.btn_split = QPushButton("⚡ Split")
        self.btn_split.setToolTip("Splits the clip at current playhead position")
        self.btn_split.clicked.connect(self.split_clicked.emit)
        row_cutter.addWidget(self.btn_split)

        self.btn_auto = QPushButton("⊞ Auto")
        self.btn_auto.setToolTip("Automatically cuts clips across timeline")
        self.btn_auto.clicked.connect(self.auto_split_clicked.emit)
        row_cutter.addWidget(self.btn_auto)

        self.btn_add_scene = QPushButton("+ Add Clip")
        self.btn_add_scene.setObjectName("PrimaryButton")
        self.btn_add_scene.setToolTip("Adds current [ Start .. End ] selection as a new clip")
        self.btn_add_scene.clicked.connect(self.add_scene_clicked.emit)
        row_cutter.addWidget(self.btn_add_scene)

        row_cutter.addSpacing(10)

        # Zoom controls
        self.btn_zoom_out = QPushButton("🔍-")
        self.btn_zoom_out.setFixedWidth(32)
        self.btn_zoom_out.clicked.connect(self.zoom_out_clicked.emit)
        row_cutter.addWidget(self.btn_zoom_out)

        self.slider_zoom = QSlider(Qt.Horizontal)
        self.slider_zoom.setRange(10, 400)  # 1.0x to 40.0x
        self.slider_zoom.setValue(10)
        self.slider_zoom.setFixedWidth(70)
        self.slider_zoom.valueChanged.connect(lambda v: self.zoom_slider_changed.emit(v / 10.0))
        row_cutter.addWidget(self.slider_zoom)

        self.btn_zoom_in = QPushButton("🔍+")
        self.btn_zoom_in.setFixedWidth(32)
        self.btn_zoom_in.clicked.connect(self.zoom_in_clicked.emit)
        row_cutter.addWidget(self.btn_zoom_in)

        self.btn_zoom_fit = QPushButton("Fit 1x")
        self.btn_zoom_fit.setFixedWidth(50)
        self.btn_zoom_fit.clicked.connect(self.zoom_fit_clicked.emit)
        row_cutter.addWidget(self.btn_zoom_fit)

        self.lbl_zoom = QLabel("1.0x")
        self.lbl_zoom.setStyleSheet("color: #718096; font-size: 11px;")
        self.lbl_zoom.setFixedWidth(32)
        row_cutter.addWidget(self.lbl_zoom)

        main_layout.addLayout(row_cutter)

    def set_duration(self, seconds: float) -> None:
        self.duration_sec = max(1.0, seconds)
        self.timeline_slider.setRange(0, int(self.duration_sec * 10))

    def set_position(self, seconds: float) -> None:
        self.current_time_sec = seconds
        if not self._slider_dragging:
            self.timeline_slider.setValue(int(seconds * 10))
        self.lbl_timecode.text = self._format_time(seconds)

    def set_cut_markers(self, start_sec: float, end_sec: float) -> None:
        self.btn_start.setText(f"[ Start: {self._format_time(start_sec)}")
        self.btn_end.setText(f"] End: {self._format_time(end_sec)}")

    def set_playing_state(self, is_playing: bool) -> None:
        self.btn_play_pause.setText("⏸ Pause" if is_playing else "▶ Play")

    def set_zoom_label(self, zoom_val: float) -> None:
        self.lbl_zoom.setText(f"{zoom_val:.1f}x")
        self.slider_zoom.blockSignals(True)
        self.slider_zoom.setValue(int(zoom_val * 10))
        self.slider_zoom.blockSignals(False)

    def _on_slider_moved(self, val: int) -> None:
        sec = val / 10.0
        self.lbl_timecode.text = self._format_time(sec)
        self.timeline_seeked.emit(sec)

    def _on_slider_pressed(self) -> None:
        self._slider_dragging = True

    def _on_slider_released(self) -> None:
        self._slider_dragging = False
        sec = self.timeline_slider.value() / 10.0
        self.timeline_seeked.emit(sec)

    @staticmethod
    def _format_time(seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        msecs = int((seconds * 10) % 10)
        return f"{mins:02d}:{secs:02d}.{msecs}"
