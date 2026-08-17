"""
Choicer Voicer Pack Studio - Standalone Edition
Hardware-Accelerated Video Player with Dynamic Aspect Ratio & Letterboxing
"""

import os
from typing import Optional
from PySide6.QtCore import Qt, QUrl, Signal, QSize
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedLayout
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


class AspectRatioVideoContainer(QWidget):
    """Container that centers video widget with black letterbox bars maintaining exact aspect ratio."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.video_aspect_ratio: float = 16.0 / 9.0
        self.setStyleSheet("background-color: #000000; border-radius: 6px;")

        self.video_widget = QVideoWidget(self)
        self.video_widget.setStyleSheet("background-color: #000000;")

    def set_aspect_ratio(self, ratio: float) -> None:
        if ratio > 0.05:
            self.video_aspect_ratio = ratio
            self.resizeEvent(None)

    def resizeEvent(self, event) -> None:
        cw = self.width()
        ch = self.height()
        if ch <= 0 or cw <= 0:
            return

        container_ratio = float(cw) / float(ch)

        if container_ratio > self.video_aspect_ratio:
            # Container is wider than video -> pillarbox (black bars left/right)
            vw = int(ch * self.video_aspect_ratio)
            vh = ch
            vx = int((cw - vw) / 2)
            vy = 0
        else:
            # Container is taller than video -> letterbox (black bars top/bottom)
            vw = cw
            vh = int(cw / self.video_aspect_ratio)
            vx = 0
            vy = int((ch - vh) / 2)

        self.video_widget.setGeometry(vx, vy, vw, vh)


class VideoPlayerWidget(QWidget):
    position_changed = Signal(float)  # in seconds
    duration_changed = Signal(float)  # in seconds
    playback_state_changed = Signal(bool)  # True = playing, False = paused

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._duration_sec: float = 60.0
        self._is_seeking: bool = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Video container
        self.container = AspectRatioVideoContainer(self)
        layout.addWidget(self.container)

        # Qt6 Multimedia setup
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.container.video_widget)

        # Signals
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)

        # Overlay placeholder label
        self.placeholder_label = QLabel("No video loaded\nClick '📁 Load Video' above", self.container)
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("color: #718096; font-size: 15px; font-weight: bold; background: transparent;")
        self.placeholder_label.setAttribute(Qt.WA_TransparentForMouseEvents)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.placeholder_label.setGeometry(0, 0, self.width(), self.height())

    def load_video(self, file_path: str, aspect_ratio: float = 16.0 / 9.0) -> None:
        if not os.path.exists(file_path):
            return
        self.container.set_aspect_ratio(aspect_ratio)
        self.placeholder_label.hide()
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.player.pause()

    def unload_video(self) -> None:
        self.player.stop()
        self.player.setSource(QUrl())
        self.placeholder_label.show()
        self._duration_sec = 60.0
        self.duration_changed.emit(60.0)

    def play(self) -> None:
        self.player.play()

    def pause(self) -> None:
        self.player.pause()

    def toggle_play_pause(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.pause()
        else:
            self.play()

    def is_playing(self) -> bool:
        return self.player.playbackState() == QMediaPlayer.PlayingState

    def seek(self, seconds: float) -> None:
        ms = int(max(0.0, seconds) * 1000.0)
        self.player.setPosition(ms)

    def get_position(self) -> float:
        return self.player.position() / 1000.0

    def get_duration(self) -> float:
        return self._duration_sec

    def _on_position_changed(self, position_ms: int) -> None:
        if not self._is_seeking:
            self.position_changed.emit(position_ms / 1000.0)

    def _on_duration_changed(self, duration_ms: int) -> None:
        if duration_ms > 0:
            self._duration_sec = duration_ms / 1000.0
            self.duration_changed.emit(self._duration_sec)

    def _on_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        self.playback_state_changed.emit(state == QMediaPlayer.PlayingState)
