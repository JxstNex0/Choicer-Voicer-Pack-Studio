"""
Choicer Voicer Pack Studio - Standalone Edition
Interactive Waveform Track with Zoom, Pan, Cut Markers, Scene Dragging & Horizontal Scrollbar
"""

import math
from typing import List, Dict, Any, Optional
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollBar
from .theme import COLOR_CYAN_PRIMARY, COLOR_ACCENT_ORANGE, COLOR_BG_PANEL, get_character_color


class WaveformCanvas(QWidget):
    playhead_seeked = Signal(float)
    start_marker_changed = Signal(float)
    end_marker_changed = Signal(float)
    scene_modified = Signal(int, float, float)
    zoom_changed = Signal(float)
    scroll_changed = Signal(float)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(95)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        # Audio & Time parameters
        self.audio_peaks: List[float] = []
        self.duration_sec: float = 60.0
        self.playhead_sec: float = 0.0

        # Markers
        self.start_marker_sec: float = 0.0
        self.end_marker_sec: float = 3.0

        # Zoom & Pan
        self.zoom: float = 1.0  # 1.0x to 40.0x
        self.scroll_offset_sec: float = 0.0

        # Scene regions
        self.scenes: List[Dict[str, Any]] = []

        # Interaction state
        self._dragging_playhead: bool = False
        self._dragging_start_marker: bool = False
        self._dragging_end_marker: bool = False
        self._dragging_scene_idx: int = -1
        self._dragging_scene_mode: str = ""  # "start", "end", "move"
        self._scene_drag_orig_start: float = 0.0
        self._scene_drag_orig_end: float = 0.0
        self._scene_drag_orig_mouse_t: float = 0.0
        self._panning: bool = False
        self._pan_start_x: float = 0.0
        self._pan_start_offset: float = 0.0

    def get_visible_duration(self) -> float:
        return self.duration_sec / max(1.0, self.zoom)

    def time_to_x(self, t: float) -> float:
        vis_dur = self.get_visible_duration()
        if vis_dur <= 0:
            return 0.0
        return ((t - self.scroll_offset_sec) / vis_dur) * self.width()

    def x_to_time(self, x: float) -> float:
        vis_dur = self.get_visible_duration()
        if self.width() <= 0:
            return 0.0
        return self.scroll_offset_sec + (x / self.width()) * vis_dur

    def _clamp_scroll(self) -> None:
        vis_dur = self.get_visible_duration()
        max_offset = max(0.0, self.duration_sec - vis_dur)
        self.scroll_offset_sec = max(0.0, min(max_offset, self.scroll_offset_sec))
        self.scroll_changed.emit(self.scroll_offset_sec)

    def set_audio_data(self, peaks: List[float], duration: float) -> None:
        self.audio_peaks = peaks
        self.duration_sec = max(1.0, duration)
        self.zoom = 1.0
        self.scroll_offset_sec = 0.0
        self.update()
        self.scroll_changed.emit(0.0)

    def set_playhead(self, seconds: float) -> None:
        self.playhead_sec = max(0.0, min(self.duration_sec, seconds))
        # Auto-scroll if playhead goes out of view
        vis_dur = self.get_visible_duration()
        if self.playhead_sec > self.scroll_offset_sec + vis_dur:
            self.scroll_offset_sec = self.playhead_sec - vis_dur * 0.2
            self._clamp_scroll()
        elif self.playhead_sec < self.scroll_offset_sec:
            self.scroll_offset_sec = max(0.0, self.playhead_sec - vis_dur * 0.1)
            self._clamp_scroll()
        self.update()

    def set_cut_range(self, start_sec: float, end_sec: float) -> None:
        self.start_marker_sec = max(0.0, min(self.duration_sec, start_sec))
        self.end_marker_sec = max(self.start_marker_sec + 0.1, min(self.duration_sec, end_sec))
        self.update()

    def set_scenes(self, scenes: List[Dict[str, Any]]) -> None:
        self.scenes = scenes
        self.update()

    def set_zoom(self, zoom_val: float) -> None:
        self.zoom = max(1.0, min(40.0, zoom_val))
        self._clamp_scroll()
        self.zoom_changed.emit(self.zoom)
        self.update()

    def set_scroll_offset(self, offset: float) -> None:
        self.scroll_offset_sec = offset
        self._clamp_scroll()
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        w = self.width()
        h = self.height()
        cy = h / 2.0

        # 1. Background
        painter.fillRect(0, 0, w, h, QColor(COLOR_BG_PANEL))

        # 2. Time Ruler Top Area (16px)
        top_ruler_h = 16
        painter.fillRect(0, 0, w, top_ruler_h, QColor("#0d121d"))
        painter.setPen(QColor("#253346"))
        painter.drawLine(0, top_ruler_h, w, top_ruler_h)

        # Draw Ruler Time Marks
        vis_dur = self.get_visible_duration()
        if vis_dur > 0:
            step_sec = 1.0 if vis_dur < 15 else (5.0 if vis_dur < 60 else 10.0)
            start_mark = math.floor(self.scroll_offset_sec / step_sec) * step_sec
            cur_mark = start_mark
            painter.setFont(QFont("Segoe UI", 8))
            while cur_mark <= self.scroll_offset_sec + vis_dur:
                mx = self.time_to_x(cur_mark)
                if 0 <= mx <= w:
                    painter.setPen(QColor("#4a5568"))
                    painter.drawLine(int(mx), 8, int(mx), top_ruler_h)
                    mins = int(cur_mark // 60)
                    secs = int(cur_mark % 60)
                    painter.drawText(int(mx) + 3, 12, f"{mins}:{secs:02d}")
                cur_mark += step_sec

        # 3. Waveform Area
        wave_h = h - top_ruler_h
        wave_cy = top_ruler_h + wave_h / 2.0

        # Center line
        painter.setPen(QPen(QColor("#1e293b"), 1))
        painter.drawLine(0, int(wave_cy), w, int(wave_cy))

        # Draw Audio Peaks
        if self.audio_peaks:
            num_peaks = len(self.audio_peaks)
            dt_per_peak = self.duration_sec / max(1, num_peaks)

            pen_peak = QPen(QColor(COLOR_CYAN_PRIMARY), 1)
            painter.setPen(pen_peak)

            start_idx = max(0, int(self.scroll_offset_sec / dt_per_peak))
            end_idx = min(num_peaks, int((self.scroll_offset_sec + vis_dur) / dt_per_peak) + 2)

            for i in range(start_idx, end_idx):
                peak_time = i * dt_per_peak
                px = self.time_to_x(peak_time)
                if 0 <= px <= w:
                    val = self.audio_peaks[i]
                    bar_h = val * (wave_h * 0.45)
                    painter.drawLine(int(px), int(wave_cy - bar_h), int(px), int(wave_cy + bar_h))

        # 4. Draw Scenes Regions (Filled colored blocks)
        for idx, sc in enumerate(self.scenes):
            s_sec = float(sc.get("start", 0.0))
            e_sec = float(sc.get("end", 0.0))
            sx1 = self.time_to_x(s_sec)
            sx2 = self.time_to_x(e_sec)

            if sx2 >= 0 and sx1 <= w:
                col_hex = get_character_color(idx)
                base_color = QColor(col_hex)
                fill_color = QColor(base_color.red(), base_color.green(), base_color.blue(), 60)
                border_color = QColor(base_color.red(), base_color.green(), base_color.blue(), 200)

                rect_w = max(4.0, sx2 - sx1)
                scene_rect = QRectF(sx1, top_ruler_h + 2, rect_w, wave_h - 4)

                painter.fillRect(scene_rect, fill_color)
                painter.setPen(QPen(border_color, 1))
                painter.drawRect(scene_rect)

                # Resize edge indicator handles
                painter.setPen(QPen(border_color, 2))
                painter.drawLine(QPointF(sx1, top_ruler_h + 2), QPointF(sx1, h - 2))
                painter.drawLine(QPointF(sx2, top_ruler_h + 2), QPointF(sx2, h - 2))

                # Scene Label
                chars = sc.get("characters", [])
                c_name = chars[0] if chars else sc.get("character", f"#{idx+1}")
                painter.setPen(border_color)
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                painter.drawText(QRectF(sx1 + 4, top_ruler_h + 4, rect_w - 8, 14), Qt.AlignLeft, f"#{idx+1} {c_name}")

        # 5. Draw Active Selection / Cutter Range
        sel_x1 = self.time_to_x(self.start_marker_sec)
        sel_x2 = self.time_to_x(self.end_marker_sec)
        if sel_x2 >= 0 and sel_x1 <= w:
            sel_rect = QRectF(sel_x1, top_ruler_h, max(2.0, sel_x2 - sel_x1), wave_h)
            painter.fillRect(sel_rect, QColor(0, 242, 254, 30))

        # 6. Draw Cut Markers: [ Start and ] End
        if 0 <= sel_x1 <= w:
            painter.setPen(QPen(QColor(COLOR_CYAN_PRIMARY), 2))
            painter.drawLine(QPointF(sel_x1, top_ruler_h), QPointF(sel_x1, h))
            painter.fillRect(QRectF(sel_x1 - 6, top_ruler_h, 12, 16), QColor(COLOR_CYAN_PRIMARY))
            painter.setPen(QColor("#000000"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(QRectF(sel_x1 - 6, top_ruler_h, 12, 16), Qt.AlignCenter, "[")

        if 0 <= sel_x2 <= w:
            painter.setPen(QPen(QColor(COLOR_ACCENT_ORANGE), 2))
            painter.drawLine(QPointF(sel_x2, top_ruler_h), QPointF(sel_x2, h))
            painter.fillRect(QRectF(sel_x2 - 6, top_ruler_h, 12, 16), QColor(COLOR_ACCENT_ORANGE))
            painter.setPen(QColor("#000000"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(QRectF(sel_x2 - 6, top_ruler_h, 12, 16), Qt.AlignCenter, "]")

        # 7. Draw Playhead (White Line with Diamond Head)
        px = self.time_to_x(self.playhead_sec)
        if 0 <= px <= w:
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawLine(QPointF(px, top_ruler_h), QPointF(px, h))
            painter.setBrush(QBrush(QColor("#ffffff")))
            head = [QPointF(px - 5, top_ruler_h), QPointF(px + 5, top_ruler_h), QPointF(px, top_ruler_h + 8)]
            painter.drawPolygon(head)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        x = event.position().x()
        t = self.x_to_time(x)

        if event.button() == Qt.RightButton or event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start_x = x
            self._pan_start_offset = self.scroll_offset_sec
            self.setCursor(Qt.ClosedHandCursor)
            return

        if event.button() == Qt.LeftButton:
            # 1. Check cut marker collision (highest priority)
            sx1 = self.time_to_x(self.start_marker_sec)
            sx2 = self.time_to_x(self.end_marker_sec)

            if abs(x - sx1) < 8:
                self._dragging_start_marker = True
                return
            elif abs(x - sx2) < 8:
                self._dragging_end_marker = True
                return

            # 2. Check scene regions collision (resize left, resize right, or move whole scene)
            for idx, sc in enumerate(self.scenes):
                sc_s = float(sc.get("start", 0.0))
                sc_e = float(sc.get("end", 0.0))
                sc_x1 = self.time_to_x(sc_s)
                sc_x2 = self.time_to_x(sc_e)

                # Left edge resize
                if abs(x - sc_x1) < 7:
                    self._dragging_scene_idx = idx
                    self._dragging_scene_mode = "start"
                    self._scene_drag_orig_start = sc_s
                    self._scene_drag_orig_end = sc_e
                    self.setCursor(Qt.SizeHorCursor)
                    return
                # Right edge resize
                elif abs(x - sc_x2) < 7:
                    self._dragging_scene_idx = idx
                    self._dragging_scene_mode = "end"
                    self._scene_drag_orig_start = sc_s
                    self._scene_drag_orig_end = sc_e
                    self.setCursor(Qt.SizeHorCursor)
                    return
                # Body move
                elif sc_x1 < x < sc_x2:
                    self._dragging_scene_idx = idx
                    self._dragging_scene_mode = "move"
                    self._scene_drag_orig_start = sc_s
                    self._scene_drag_orig_end = sc_e
                    self._scene_drag_orig_mouse_t = t
                    self.setCursor(Qt.ClosedHandCursor)
                    return

            # 3. Playhead seek
            self._dragging_playhead = True
            self.set_playhead(t)
            self.playhead_seeked.emit(self.playhead_sec)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        x = event.position().x()
        t = max(0.0, min(self.duration_sec, self.x_to_time(x)))

        if self._panning:
            vis_dur = self.get_visible_duration()
            dx = event.position().x() - self._pan_start_x
            dt = (dx / max(1, self.width())) * vis_dur
            self.scroll_offset_sec = self._pan_start_offset - dt
            self._clamp_scroll()
            self.update()
            return

        if self._dragging_start_marker:
            self.start_marker_sec = min(t, self.end_marker_sec - 0.1)
            self.start_marker_changed.emit(self.start_marker_sec)
            self.update()
        elif self._dragging_end_marker:
            self.end_marker_sec = max(t, self.start_marker_sec + 0.1)
            self.end_marker_changed.emit(self.end_marker_sec)
            self.update()
        elif self._dragging_scene_idx >= 0 and self._dragging_scene_idx < len(self.scenes):
            idx = self._dragging_scene_idx
            if self._dragging_scene_mode == "start":
                new_s = max(0.0, min(t, self._scene_drag_orig_end - 0.1))
                self.scenes[idx]["start"] = new_s
                self.scene_modified.emit(idx, new_s, self.scenes[idx]["end"])
            elif self._dragging_scene_mode == "end":
                new_e = min(self.duration_sec, max(t, self._scene_drag_orig_start + 0.1))
                self.scenes[idx]["end"] = new_e
                self.scene_modified.emit(idx, self.scenes[idx]["start"], new_e)
            elif self._dragging_scene_mode == "move":
                dt = t - self._scene_drag_orig_mouse_t
                dur = self._scene_drag_orig_end - self._scene_drag_orig_start
                new_s = max(0.0, min(self.duration_sec - dur, self._scene_drag_orig_start + dt))
                new_e = new_s + dur
                self.scenes[idx]["start"] = new_s
                self.scenes[idx]["end"] = new_e
                self.scene_modified.emit(idx, new_s, new_e)
            self.update()
        elif self._dragging_playhead:
            self.set_playhead(t)
            self.playhead_seeked.emit(self.playhead_sec)
        else:
            # Hover cursor update
            sx1 = self.time_to_x(self.start_marker_sec)
            sx2 = self.time_to_x(self.end_marker_sec)
            if abs(x - sx1) < 8 or abs(x - sx2) < 8:
                self.setCursor(Qt.SizeHorCursor)
                return

            # Check scenes hover
            for sc in self.scenes:
                sc_x1 = self.time_to_x(float(sc.get("start", 0.0)))
                sc_x2 = self.time_to_x(float(sc.get("end", 0.0)))
                if abs(x - sc_x1) < 7 or abs(x - sc_x2) < 7:
                    self.setCursor(Qt.SizeHorCursor)
                    return
                elif sc_x1 < x < sc_x2:
                    self.setCursor(Qt.OpenHandCursor)
                    return

            self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._dragging_playhead = False
        self._dragging_start_marker = False
        self._dragging_end_marker = False
        self._dragging_scene_idx = -1
        self._dragging_scene_mode = ""
        self._panning = False
        self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        zoom_factor = 1.25 if delta > 0 else (1.0 / 1.25)
        mouse_t = self.x_to_time(event.position().x())

        new_zoom = max(1.0, min(40.0, self.zoom * zoom_factor))
        self.zoom = new_zoom

        # Adjust scroll offset so time under mouse stays stationary
        vis_dur = self.get_visible_duration()
        mouse_frac = event.position().x() / max(1, self.width())
        self.scroll_offset_sec = mouse_t - mouse_frac * vis_dur
        self._clamp_scroll()

        self.zoom_changed.emit(self.zoom)
        self.update()


class WaveformWidget(QWidget):
    """Compound widget hosting WaveformCanvas and a horizontal scrollbar for timeline navigation."""
    playhead_seeked = Signal(float)
    start_marker_changed = Signal(float)
    end_marker_changed = Signal(float)
    scene_modified = Signal(int, float, float)
    zoom_changed = Signal(float)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(112)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 1. Waveform Canvas
        self.canvas = WaveformCanvas(self)
        layout.addWidget(self.canvas)

        # Forward signals
        self.canvas.playhead_seeked.connect(self.playhead_seeked.emit)
        self.canvas.start_marker_changed.connect(self.start_marker_changed.emit)
        self.canvas.end_marker_changed.connect(self.end_marker_changed.emit)
        self.canvas.scene_modified.connect(self.scene_modified.emit)
        self.canvas.zoom_changed.connect(self._on_canvas_zoom_changed)
        self.canvas.scroll_changed.connect(self._on_canvas_scroll_changed)

        # 2. Sleek Horizontal Scrollbar
        self.scrollbar = QScrollBar(Qt.Horizontal, self)
        self.scrollbar.setFixedHeight(12)
        self.scrollbar.setStyleSheet("""
            QScrollBar:horizontal {
                background: #090d14;
                height: 12px;
                margin: 0px;
                border-radius: 4px;
                border: 1px solid #1a2332;
            }
            QScrollBar::handle:horizontal {
                background: #1e293b;
                min-width: 30px;
                border-radius: 3px;
                border: 1px solid #00f2fe;
            }
            QScrollBar::handle:horizontal:hover {
                background: #00f2fe;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                background: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        self.scrollbar.valueChanged.connect(self._on_scrollbar_moved)
        layout.addWidget(self.scrollbar)

        self._update_scrollbar_range()

    @property
    def start_marker_sec(self) -> float:
        return self.canvas.start_marker_sec

    @start_marker_sec.setter
    def start_marker_sec(self, val: float):
        self.canvas.start_marker_sec = val

    @property
    def end_marker_sec(self) -> float:
        return self.canvas.end_marker_sec

    @end_marker_sec.setter
    def end_marker_sec(self, val: float):
        self.canvas.end_marker_sec = val

    @property
    def duration_sec(self) -> float:
        return self.canvas.duration_sec

    @duration_sec.setter
    def duration_sec(self, val: float):
        self.canvas.duration_sec = val
        self._update_scrollbar_range()

    @property
    def zoom(self) -> float:
        return self.canvas.zoom

    def set_audio_data(self, peaks: List[float], duration: float) -> None:
        self.canvas.set_audio_data(peaks, duration)
        self._update_scrollbar_range()

    def set_playhead(self, seconds: float) -> None:
        self.canvas.set_playhead(seconds)

    def set_cut_range(self, start_sec: float, end_sec: float) -> None:
        self.canvas.set_cut_range(start_sec, end_sec)

    def set_scenes(self, scenes: List[Dict[str, Any]]) -> None:
        self.canvas.set_scenes(scenes)

    def set_zoom(self, zoom_val: float) -> None:
        self.canvas.set_zoom(zoom_val)
        self._update_scrollbar_range()

    def _update_scrollbar_range(self) -> None:
        dur = self.canvas.duration_sec
        vis_dur = self.canvas.get_visible_duration()
        max_offset = max(0.0, dur - vis_dur)

        self.scrollbar.blockSignals(True)
        self.scrollbar.setRange(0, int(max_offset * 100))
        self.scrollbar.setPageStep(int(vis_dur * 100))
        self.scrollbar.setValue(int(self.canvas.scroll_offset_sec * 100))
        self.scrollbar.blockSignals(False)

        # Show scrollbar always or highlight when zoomed
        self.scrollbar.setEnabled(max_offset > 0.05)

    def _on_canvas_zoom_changed(self, z: float) -> None:
        self._update_scrollbar_range()
        self.zoom_changed.emit(z)

    def _on_canvas_scroll_changed(self, offset: float) -> None:
        self.scrollbar.blockSignals(True)
        self.scrollbar.setValue(int(offset * 100))
        self.scrollbar.blockSignals(False)

    def _on_scrollbar_moved(self, val: int) -> None:
        self.canvas.set_scroll_offset(val / 100.0)
