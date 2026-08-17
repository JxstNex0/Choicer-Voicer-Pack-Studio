"""
Choicer Voicer Pack Studio - Standalone Edition
Main Desktop Application Window
"""

import os
import sys
import threading
from typing import Optional, List, Dict, Any

from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QIcon, QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QSplitter,
    QFileDialog, QMessageBox, QMenu, QStatusBar, QFrame
)

from .theme import APP_STYLESHEET, COLOR_CYAN_PRIMARY, COLOR_ACCENT_GREEN, COLOR_ACCENT_RED, COLOR_ACCENT_YELLOW, COLOR_TEXT_MUTED
from .video_widget import VideoPlayerWidget
from .waveform_widget import WaveformWidget
from .cutter_toolbar import CutterToolbar
from .character_roster import CharacterRoster
from .scene_card_list import SceneCardList
from .history_dialog import HistoryDialog

try:
    from core.pack_model import PackModel, SceneClip
    from core.pack_exporter import PackExporter
    from core.ffmpeg_handler import FFmpegHandler
    from core.vocal_remover import VocalRemover
    from core.history_manager import HistoryManager
except ImportError:
    from ..core.pack_model import PackModel, SceneClip
    from ..core.pack_exporter import PackExporter
    from ..core.ffmpeg_handler import FFmpegHandler
    from ..core.vocal_remover import VocalRemover
    from ..core.history_manager import HistoryManager


class AsyncWorkerThread(QThread):
    finished_signal = Signal(bool, str)
    progress_signal = Signal(str)

    def __init__(self, target_func, *args, **kwargs):
        super().__init__()
        self.target_func = target_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            res = self.target_func(progress_callback=self.progress_signal.emit, *self.args, **self.kwargs)
            if isinstance(res, dict):
                self.finished_signal.emit(res.get("success", True), res.get("path", "") or res.get("error", ""))
            else:
                self.finished_signal.emit(bool(res), "")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Choicer Voicer - Pack Studio (Standalone)")
        self.resize(1280, 720)
        self.setMinimumSize(960, 540)
        self.setStyleSheet(APP_STYLESHEET)

        self.pack = PackModel()
        self.history_manager = HistoryManager()
        self.current_preview_timer: Optional[QTimer] = None
        self._clip_preview_end_time: float = 0.0

        self._setup_ui()
        self._load_recent_or_default_pack()

    def _setup_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(12, 12, 12, 8)
        root_layout.setSpacing(8)

        # === TOP BAR ===
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        # 1. Open Pack Menu Button
        self.btn_open_pack = QPushButton("📂 Open Pack ▾")
        self.btn_open_pack.setMenu(QMenu(self.btn_open_pack))
        self.btn_open_pack.menu().aboutToShow.connect(self._populate_open_pack_menu)
        top_bar.addWidget(self.btn_open_pack)

        # 2. Pack Name Input
        self.txt_pack_name = QLineEdit(self.pack.name)
        self.txt_pack_name.setPlaceholderText("Pack Name...")
        self.txt_pack_name.setMinimumWidth(180)
        self.txt_pack_name.textChanged.connect(lambda t: setattr(self.pack, "name", t.strip()))
        top_bar.addWidget(self.txt_pack_name)

        # 3. Author Input
        self.txt_author = QLineEdit(self.pack.author)
        self.txt_author.setPlaceholderText("Author...")
        self.txt_author.setMinimumWidth(110)
        self.txt_author.textChanged.connect(lambda t: setattr(self.pack, "author", t.strip()))
        top_bar.addWidget(self.txt_author)

        top_bar.addSpacing(10)

        # 4. Backing Track Dropdown
        self.btn_backing_track = QPushButton("🎵 Backing Track ▾")
        self._setup_backing_track_menu()
        top_bar.addWidget(self.btn_backing_track)

        # 5. Load Video Button
        self.btn_load_video = QPushButton("📁 Load Video")
        self.btn_load_video.clicked.connect(self._on_load_video_clicked)
        top_bar.addWidget(self.btn_load_video)

        # 6. Remove Video Button
        self.btn_remove_video = QPushButton("🗑 Remove")
        self.btn_remove_video.setObjectName("DangerButton")
        self.btn_remove_video.clicked.connect(self._on_remove_video_clicked)
        top_bar.addWidget(self.btn_remove_video)

        top_bar.addSpacing(10)

        # 7. Undo, Redo & History Buttons
        self.btn_undo = QPushButton("↶ Undo")
        self.btn_undo.setToolTip("Undo last change (Ctrl+Z)")
        self.btn_undo.clicked.connect(self._on_undo)
        self.btn_undo.setEnabled(False)
        top_bar.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("↷ Redo")
        self.btn_redo.setToolTip("Redo last undone change (Ctrl+Y / Ctrl+Shift+Z)")
        self.btn_redo.clicked.connect(self._on_redo)
        self.btn_redo.setEnabled(False)
        top_bar.addWidget(self.btn_redo)

        self.btn_history = QPushButton("📜 History")
        self.btn_history.setToolTip("View Change History / Verlauf (Ctrl+H)")
        self.btn_history.clicked.connect(self._on_show_history)
        top_bar.addWidget(self.btn_history)

        top_bar.addStretch()

        # 8. Save Pack Button
        self.btn_save = QPushButton("💾 Save Pack")
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.clicked.connect(self._on_save_pack_clicked)
        top_bar.addWidget(self.btn_save)

        # 9. Export ZIP Button
        self.btn_export_zip = QPushButton("📦 Export ZIP")
        self.btn_export_zip.clicked.connect(self._on_export_zip_clicked)
        top_bar.addWidget(self.btn_export_zip)

        root_layout.addLayout(top_bar)

        # === SHORTCUTS (Ctrl+Z, Ctrl+Y, Ctrl+Shift+Z, Ctrl+H) ===
        QShortcut(QKeySequence.Undo, self, activated=self._on_undo)
        QShortcut(QKeySequence.Redo, self, activated=self._on_redo)
        QShortcut(QKeySequence("Ctrl+Y"), self, activated=self._on_redo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, activated=self._on_redo)
        QShortcut(QKeySequence("Ctrl+H"), self, activated=self._on_show_history)

        # === MAIN WORKSPACE SPLITTER (Horizontal: Left Workspace vs Right Sidebar) ===
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        # --- LEFT PANEL (Large Video Player + Bottom Timeline Controls) ---
        left_panel = QFrame()
        left_panel.setObjectName("PanelFrame")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(6)

        # Video Player (Expands to fill all available space)
        self.video_widget = VideoPlayerWidget(left_panel)
        self.video_widget.position_changed.connect(self._on_video_position_changed)
        self.video_widget.duration_changed.connect(self._on_video_duration_changed)
        self.video_widget.playback_state_changed.connect(self._on_video_playback_state_changed)
        left_layout.addWidget(self.video_widget, 1)

        # Waveform Track (Compact 112px)
        self.waveform_widget = WaveformWidget(left_panel)
        self.waveform_widget.playhead_seeked.connect(self.video_widget.seek)
        self.waveform_widget.start_marker_changed.connect(self._on_start_marker_changed)
        self.waveform_widget.end_marker_changed.connect(self._on_end_marker_changed)
        self.waveform_widget.scene_modified.connect(self._on_scene_modified_on_waveform)
        self.waveform_widget.zoom_changed.connect(self._on_waveform_zoom_changed)
        left_layout.addWidget(self.waveform_widget)

        # Cutter Toolbar
        self.cutter_toolbar = CutterToolbar(left_panel)
        self.cutter_toolbar.play_pause_clicked.connect(self.video_widget.toggle_play_pause)
        self.cutter_toolbar.set_start_clicked.connect(self._on_set_start_from_playhead)
        self.cutter_toolbar.set_end_clicked.connect(self._on_set_end_from_playhead)
        self.cutter_toolbar.split_clicked.connect(self._on_split_clicked)
        self.cutter_toolbar.auto_split_clicked.connect(self._on_auto_split_clicked)
        self.cutter_toolbar.add_scene_clicked.connect(self._on_add_scene_clicked)
        self.cutter_toolbar.timeline_seeked.connect(self.video_widget.seek)
        self.cutter_toolbar.zoom_in_clicked.connect(lambda: self.waveform_widget.set_zoom(self.waveform_widget.zoom * 1.4))
        self.cutter_toolbar.zoom_out_clicked.connect(lambda: self.waveform_widget.set_zoom(self.waveform_widget.zoom / 1.4))
        self.cutter_toolbar.zoom_fit_clicked.connect(lambda: self.waveform_widget.set_zoom(1.0))
        self.cutter_toolbar.zoom_slider_changed.connect(self.waveform_widget.set_zoom)
        left_layout.addWidget(self.cutter_toolbar)

        self.main_splitter.addWidget(left_panel)

        # --- RIGHT SIDE SPLITTER (Vertical: Roles vs Scenes) ---
        self.right_splitter = QSplitter(Qt.Vertical)
        self.right_splitter.setChildrenCollapsible(False)
        self.right_splitter.setMinimumWidth(260)

        # Upper: Character Roster Frame
        roster_frame = QFrame()
        roster_frame.setObjectName("PanelFrame")
        roster_layout = QVBoxLayout(roster_frame)
        roster_layout.setContentsMargins(6, 6, 6, 6)
        self.character_roster = CharacterRoster(roster_frame)
        self.character_roster.roster_changed.connect(self._on_roster_changed)
        self.character_roster.active_selection_changed.connect(self._on_active_roster_selection_changed)
        roster_layout.addWidget(self.character_roster)
        self.right_splitter.addWidget(roster_frame)

        # Lower: Scene Card List Frame
        scenes_frame = QFrame()
        scenes_frame.setObjectName("PanelFrame")
        scenes_layout = QVBoxLayout(scenes_frame)
        scenes_layout.setContentsMargins(6, 6, 6, 6)
        self.scene_card_list = SceneCardList(scenes_frame)
        self.scene_card_list.clip_delete_requested.connect(self._on_delete_clip)
        self.scene_card_list.clip_play_requested.connect(self._on_play_clip_preview)
        self.scene_card_list.clip_changed.connect(self._on_clip_data_changed)
        scenes_layout.addWidget(self.scene_card_list)
        self.right_splitter.addWidget(scenes_frame)

        self.main_splitter.addWidget(self.right_splitter)

        # Set default clean proportions (75% video workspace, 25% sidebar; 130px roles, remainder scenes)
        self.main_splitter.setStretchFactor(0, 7)
        self.main_splitter.setStretchFactor(1, 3)
        self.right_splitter.setStretchFactor(0, 2)
        self.right_splitter.setStretchFactor(1, 8)

        root_layout.addWidget(self.main_splitter, 1)

        QTimer.singleShot(50, lambda: self.main_splitter.setSizes([960, 320]))
        QTimer.singleShot(50, lambda: self.right_splitter.setSizes([130, 600]))

        # === STATUS BAR ===
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.show_status("Ready. Load a video or open an existing pack.", COLOR_CYAN_PRIMARY)

    def show_status(self, msg: str, color_hex: str = COLOR_CYAN_PRIMARY) -> None:
        self.status_bar.showMessage(msg)
        self.status_bar.setStyleSheet(f"color: {color_hex}; font-weight: bold; padding: 2px;")

    # === BACKING TRACK MENU ===

    def _setup_backing_track_menu(self) -> None:
        menu = QMenu(self.btn_backing_track)
        self.btn_backing_track.setMenu(menu)

        act_auto = menu.addAction("🎬 Auto (Original Video Audio)")
        act_auto.triggered.connect(self._set_backing_auto)

        act_ai = menu.addAction("✨ AI Vocal Remover: Isolate background & remove vocals")
        act_ai.triggered.connect(self._run_ai_vocal_remover)

        act_load = menu.addAction("📁 Load custom backing track file (.wav / .mp3)")
        act_load.triggered.connect(self._load_custom_backing_track)

        act_mute = menu.addAction("🔇 Mute backing audio")
        act_mute.triggered.connect(self._set_backing_muted)

    def _set_backing_auto(self) -> None:
        self.pack.backing_track_path = ""
        self.pack.is_backing_muted = False
        self.btn_backing_track.setText("🎬 Backing: Auto")
        self.show_status("Backing track set to original audio.", COLOR_ACCENT_GREEN)

    def _set_backing_muted(self) -> None:
        self.pack.is_backing_muted = True
        self.btn_backing_track.setText("🔇 Backing: Muted")
        self.show_status("Backing audio will be muted for recordings.", COLOR_ACCENT_YELLOW)

    def _load_custom_backing_track(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Backing Track File", "", "Audio Files (*.wav *.mp3 *.ogg *.flac)")
        if path:
            self.pack.backing_track_path = path
            self.pack.is_backing_muted = False
            self.btn_backing_track.setText(f"🎵 {os.path.basename(path)}")
            self.show_status(f"Custom backing track loaded: {os.path.basename(path)}", COLOR_ACCENT_GREEN)

    def _run_ai_vocal_remover(self) -> None:
        if not self.pack.video_path or not os.path.exists(self.pack.video_path):
            QMessageBox.warning(self, "No Video", "Please load a video first!")
            return

        self.show_status("✨ AI Vocal Remover is running... (Please wait)", COLOR_ACCENT_YELLOW)
        out_wav = os.path.join(os.path.expanduser("~"), ".cv_pack_temp", "cleaned_backing.wav")
        os.makedirs(os.path.dirname(out_wav), exist_ok=True)

        self.worker = AsyncWorkerThread(
            VocalRemover.isolate_backing_track,
            input_media_path=self.pack.video_path,
            output_backing_path=out_wav,
            method="ai"
        )
        self.worker.progress_signal.connect(lambda p: self.show_status(p, COLOR_ACCENT_YELLOW))
        self.worker.finished_signal.connect(self._on_ai_vocal_remover_finished)
        self.worker.start()

    def _on_ai_vocal_remover_finished(self, success: bool, msg: str) -> None:
        out_wav = os.path.join(os.path.expanduser("~"), ".cv_pack_temp", "cleaned_backing.wav")
        if success and os.path.exists(out_wav):
            self.pack.backing_track_path = out_wav
            self.pack.is_backing_muted = False
            self.btn_backing_track.setText("✨ Backing: AI Cleaned")
            self.show_status("✓ AI Vocal Remover completed! Clean background track created.", COLOR_ACCENT_GREEN)
        else:
            self.show_status(f"✗ AI Vocal Remover failed: {msg}", COLOR_ACCENT_RED)

    # === VIDEO MANAGEMENT ===

    def _on_load_video_clicked(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "",
            "Video Files (*.mp4 *.mkv *.ogv *.webm *.mov *.avi);;All Files (*)"
        )
        if not path:
            return

        self.pack.video_path = path
        info = FFmpegHandler.probe_media(path)
        self.video_widget.load_video(path, info["aspect_ratio"])

        # Extract waveform peaks asynchronously
        self._extract_waveform_peaks(path)
        self.show_status(f"✓ Video loaded: {os.path.basename(path)} ({info['width']}x{info['height']})", COLOR_ACCENT_GREEN)

    def _on_remove_video_clicked(self) -> None:
        self.pack.video_path = ""
        self.video_widget.unload_video()
        self.waveform_widget.set_audio_data([], 60.0)
        self.cutter_toolbar.set_duration(60.0)
        self.cutter_toolbar.set_position(0.0)
        self.show_status("Video removed.", COLOR_ACCENT_GREEN)

    def _extract_waveform_peaks(self, video_path: str) -> None:
        def job():
            temp_wav = os.path.join(os.path.expanduser("~"), ".cv_pack_temp", "wave_temp.wav")
            if FFmpegHandler.extract_audio_wav(video_path, temp_wav):
                try:
                    import soundfile as sf
                    import numpy as np
                    data, sr = sf.read(temp_wav)
                    dur = len(data) / float(sr)
                    if data.ndim > 1:
                        data = np.mean(data, axis=1)
                    # Resample to ~800 peaks
                    step = max(1, len(data) // 800)
                    peaks = [float(np.max(np.abs(data[i:i+step]))) for i in range(0, len(data), step)]
                    QTimer.singleShot(0, lambda: self.waveform_widget.set_audio_data(peaks, dur))
                except Exception as e:
                    print(f"[Waveform] Error: {e}")
                finally:
                    if os.path.exists(temp_wav):
                        try: os.remove(temp_wav)
                        except Exception: pass

        t = threading.Thread(target=job, daemon=True)
        t.start()

    # === PLAYHEAD & CUTTER LOGIC ===

    def _on_video_position_changed(self, pos: float) -> None:
        self.cutter_toolbar.set_position(pos)
        self.waveform_widget.set_playhead(pos)

    def _on_video_duration_changed(self, dur: float) -> None:
        self.cutter_toolbar.set_duration(dur)
        self.waveform_widget.duration_sec = dur
        self.waveform_widget.update()

    def _on_video_playback_state_changed(self, is_playing: bool) -> None:
        self.cutter_toolbar.set_playing_state(is_playing)

    def _on_start_marker_changed(self, t: float) -> None:
        self.cutter_toolbar.set_cut_markers(t, self.waveform_widget.end_marker_sec)

    def _on_end_marker_changed(self, t: float) -> None:
        self.cutter_toolbar.set_cut_markers(self.waveform_widget.start_marker_sec, t)

    def _on_waveform_zoom_changed(self, z: float) -> None:
        self.cutter_toolbar.set_zoom_label(z)

    def _on_set_start_from_playhead(self) -> None:
        pos = self.video_widget.get_position()
        self.waveform_widget.start_marker_sec = pos
        if self.waveform_widget.end_marker_sec <= pos:
            self.waveform_widget.end_marker_sec = min(self.video_widget.get_duration(), pos + 3.0)
        self.cutter_toolbar.set_cut_markers(self.waveform_widget.start_marker_sec, self.waveform_widget.end_marker_sec)
        self.waveform_widget.update()

    def _on_set_end_from_playhead(self) -> None:
        pos = self.video_widget.get_position()
        if pos > self.waveform_widget.start_marker_sec:
            self.waveform_widget.end_marker_sec = pos
            self.cutter_toolbar.set_cut_markers(self.waveform_widget.start_marker_sec, pos)
            self.waveform_widget.update()

    # === UNDO / REDO & HISTORY SYSTEM ===

    def _record_history(self, description: str) -> None:
        self.history_manager.push_state(description, self.pack.create_snapshot())
        self._update_undo_redo_buttons()

    def _update_undo_redo_buttons(self) -> None:
        self.btn_undo.setEnabled(self.history_manager.can_undo)
        self.btn_redo.setEnabled(self.history_manager.can_redo)
        if self.history_manager.can_undo:
            last = self.history_manager.undo_stack[-1].description
            self.btn_undo.setToolTip(f"Undo: {last} (Ctrl+Z)")
        else:
            self.btn_undo.setToolTip("Undo (Ctrl+Z)")

        if self.history_manager.can_redo:
            next_act = self.history_manager.redo_stack[-1].description
            self.btn_redo.setToolTip(f"Redo: {next_act} (Ctrl+Y / Ctrl+Shift+Z)")
        else:
            self.btn_redo.setToolTip("Redo (Ctrl+Y / Ctrl+Shift+Z)")

    def _on_undo(self) -> None:
        if not self.history_manager.can_undo:
            self.show_status("Nothing to undo.", COLOR_TEXT_MUTED)
            return
        curr_snap = self.pack.create_snapshot()
        entry = self.history_manager.undo(curr_snap)
        if entry:
            self.pack.restore_snapshot(entry.snapshot)
            self._sync_ui_with_pack()
            self._update_undo_redo_buttons()
            self.show_status(f"↶ Undone: {entry.description}", COLOR_CYAN_PRIMARY)

    def _on_redo(self) -> None:
        if not self.history_manager.can_redo:
            self.show_status("Nothing to redo.", COLOR_TEXT_MUTED)
            return
        curr_snap = self.pack.create_snapshot()
        entry = self.history_manager.redo(curr_snap)
        if entry:
            self.pack.restore_snapshot(entry.snapshot)
            self._sync_ui_with_pack()
            self._update_undo_redo_buttons()
            self.show_status(f"↷ Redone: {entry.description}", COLOR_CYAN_PRIMARY)

    def _on_show_history(self) -> None:
        undo_entries = self.history_manager.get_history_entries()
        redo_entries = [e.to_dict() for e in self.history_manager.redo_stack]
        dlg = HistoryDialog(undo_entries, redo_entries, self)
        dlg.exec_()

    # === WORKSPACE EVENT HANDLERS ===

    def _on_split_clicked(self) -> None:
        self._record_history("Split Clip")
        pos = self.video_widget.get_position()
        self.waveform_widget.end_marker_sec = pos
        self._on_add_scene_clicked(record_history=False)
        self.waveform_widget.start_marker_sec = pos
        self.waveform_widget.end_marker_sec = min(self.video_widget.get_duration(), pos + 3.0)
        self.cutter_toolbar.set_cut_markers(self.waveform_widget.start_marker_sec, self.waveform_widget.end_marker_sec)
        self.waveform_widget.update()

    def _on_auto_split_clicked(self) -> None:
        dur = self.video_widget.get_duration()
        if dur <= 2.0:
            return
        self._record_history("Auto-Split Clips")
        # Create 4-second blocks automatically
        self.pack.clips.clear()
        t = 0.0
        while t < dur:
            end_t = min(dur, t + 4.0)
            self.pack.add_clip(SceneClip(start_time=t, end_time=end_t, characters=list(self.pack.active_selected_characters)))
            t = end_t
        self._sync_ui_with_pack(scroll_to_bottom=True)
        self.show_status(f"✓ {len(self.pack.clips)} clips automatically generated.", COLOR_ACCENT_GREEN)

    def _on_add_scene_clicked(self, record_history: bool = True) -> None:
        if record_history:
            self._record_history("Add Clip")
        s = self.waveform_widget.start_marker_sec
        e = self.waveform_widget.end_marker_sec
        if e <= s:
            e = s + 1.0

        active_chars = list(self.character_roster.get_active_characters())
        clip = SceneClip(start_time=s, end_time=e, characters=active_chars, subtitle="")
        self.pack.add_clip(clip)

        # Advance start marker
        self.waveform_widget.start_marker_sec = e
        self.waveform_widget.end_marker_sec = min(self.video_widget.get_duration(), e + 3.0)
        self.cutter_toolbar.set_cut_markers(self.waveform_widget.start_marker_sec, self.waveform_widget.end_marker_sec)

        self._sync_ui_with_pack(scroll_to_bottom=True)
        self.show_status(f"✓ Clip #{len(self.pack.clips)} added ({s:.1f}s - {e:.1f}s)", COLOR_ACCENT_GREEN)

    def _on_delete_clip(self, idx: int) -> None:
        self._record_history(f"Delete Clip #{idx + 1}")
        self.pack.remove_clip(idx)
        self._sync_ui_with_pack()
        self.show_status("Clip removed.", COLOR_ACCENT_GREEN)

    def _on_play_clip_preview(self, start_t: float, end_t: float) -> None:
        self._clip_preview_start_time = max(0.0, start_t)
        self._clip_preview_end_time = max(start_t + 0.1, end_t)
        
        self.video_widget.seek(self._clip_preview_start_time)
        self.waveform_widget.set_playhead(self._clip_preview_start_time)
        self.cutter_toolbar.set_position(self._clip_preview_start_time)
        
        # Start playback
        self.video_widget.play()

        if not self.current_preview_timer:
            self.current_preview_timer = QTimer(self)
            self.current_preview_timer.timeout.connect(self._check_preview_end)
        self.current_preview_timer.start(25)

    def _check_preview_end(self) -> None:
        pos = self.video_widget.get_position()
        if pos >= self._clip_preview_end_time or (pos < self._clip_preview_start_time - 0.5 and pos > 0.1):
            self.video_widget.pause()
            if self.current_preview_timer:
                self.current_preview_timer.stop()

    def _on_scene_modified_on_waveform(self, idx: int, s: float, e: float) -> None:
        if 0 <= idx < len(self.pack.clips):
            self._record_history(f"Adjust Clip #{idx + 1} Timing")
            self.pack.clips[idx].start_time = s
            self.pack.clips[idx].end_time = e
            self.scene_card_list.set_data(self.pack.clips, self.pack.characters)

    def _on_clip_data_changed(self, idx: int, data: dict) -> None:
        if 0 <= idx < len(self.pack.clips):
            self._record_history(f"Edit Clip #{idx + 1}")
            self.pack.clips[idx] = SceneClip.from_dict(data)
            self.waveform_widget.set_scenes([c.to_dict() for c in self.pack.clips])

    def _on_roster_changed(self, roster: list) -> None:
        self._record_history("Update Roles Roster")
        self.pack.characters = roster
        self.scene_card_list.set_data(self.pack.clips, self.pack.characters)

    def _on_active_roster_selection_changed(self, active: list) -> None:
        self.pack.active_selected_characters = active

    # === SAVE & ZIP EXPORT ===

    def _on_save_pack_clicked(self) -> None:
        self.show_status("Saving pack...", COLOR_ACCENT_YELLOW)
        res = PackExporter.save_pack(self.pack, progress_callback=lambda m: self.show_status(m, COLOR_ACCENT_YELLOW))
        if res["success"]:
            self.show_status(f"✓ Pack successfully saved: {res['path']}", COLOR_ACCENT_GREEN)
            QMessageBox.information(self, "Saved", f"Pack '{self.pack.name}' was successfully saved to the game folder!")
        else:
            self.show_status(f"✗ Error: {res.get('error')}", COLOR_ACCENT_RED)
            QMessageBox.critical(self, "Error", f"Could not save pack: {res.get('error')}")

    def _on_export_zip_clicked(self) -> None:
        self.show_status("Building ZIP archive...", COLOR_ACCENT_YELLOW)
        res = PackExporter.export_to_zip(self.pack, progress_callback=lambda m: self.show_status(m, COLOR_ACCENT_YELLOW))
        if res["success"]:
            self.show_status(f"✓ ZIP exported to Desktop: {os.path.basename(res['path'])}", COLOR_ACCENT_GREEN)
            QMessageBox.information(self, "ZIP Exported", f"ZIP archive has been saved to your Desktop:\n{res['path']}\n\nReady to share on Discord!")
        else:
            self.show_status(f"✗ Error: {res.get('error')}", COLOR_ACCENT_RED)
            QMessageBox.critical(self, "Error", f"Could not export ZIP: {res.get('error')}")

    # === OPEN PACK MENU & BROWSER ===

    def _populate_open_pack_menu(self) -> None:
        menu = self.btn_open_pack.menu()
        menu.clear()

        act_new = menu.addAction("➕ Create New Empty Pack")
        act_new.triggered.connect(self._create_new_pack)

        act_browse = menu.addAction("📂 Browse & Manage All Packs...")
        act_browse.triggered.connect(self._show_pack_browser_dialog)

        menu.addSeparator()

        base_dir = PackExporter.get_game_packs_dir()
        if os.path.exists(base_dir):
            packs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and not d.startswith(".")]
            if packs:
                # Sort by modification time (most recent first)
                packs.sort(key=lambda d: os.path.getmtime(os.path.join(base_dir, d)), reverse=True)
                
                # Show top 5 recent packs
                for p_name in packs[:5]:
                    act_load = menu.addAction(f"🎬 {p_name}")
                    p_dir = os.path.join(base_dir, p_name)
                    act_load.triggered.connect(lambda _, path=p_dir: self._load_pack_from_dir(path))

        # Current pack delete option
        if self.pack.name:
            menu.addSeparator()
            act_del_cur = menu.addAction(f"🗑 Delete current pack ('{self.pack.name}')")
            act_del_cur.triggered.connect(lambda: self._delete_pack_from_disk(os.path.join(PackExporter.get_game_packs_dir(), self.pack.name)))

    def _show_pack_browser_dialog(self) -> None:
        from PySide6.QtWidgets import QDialog, QScrollArea

        dlg = QDialog(self)
        dlg.setWindowTitle("📂 Pack Browser & Manager")
        dlg.resize(560, 480)
        dlg.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Search Bar
        txt_search = QLineEdit()
        txt_search.setPlaceholderText("🔍 Search packs...")
        txt_search.setClearButtonEnabled(True)
        layout.addWidget(txt_search)

        # Scroll Area for rows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        rows_layout = QVBoxLayout(container)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.setSpacing(6)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        base_dir = PackExporter.get_game_packs_dir()

        def refresh_list(query: str = ""):
            while rows_layout.count():
                item = rows_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            if not os.path.exists(base_dir):
                return

            packs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and not d.startswith(".")]
            packs.sort(key=lambda d: os.path.getmtime(os.path.join(base_dir, d)), reverse=True)

            for p_name in packs:
                if query.lower() in p_name.lower():
                    p_dir = os.path.join(base_dir, p_name)
                    card = QFrame()
                    card.setStyleSheet("""
                        QFrame {
                            background-color: #111722;
                            border: 1px solid #253346;
                            border-left: 3px solid #00f2fe;
                            border-radius: 4px;
                            padding: 4px;
                        }
                    """)
                    row = QHBoxLayout(card)
                    row.setContentsMargins(8, 4, 8, 4)

                    lbl = QLabel(f"🎬 {p_name}")
                    lbl.setStyleSheet("font-weight: bold; color: #ffffff;")
                    row.addWidget(lbl, 1)

                    btn_open = QPushButton("📂 Open")
                    btn_open.setFixedWidth(75)
                    btn_open.clicked.connect(lambda _, path=p_dir: (self._load_pack_from_dir(path), dlg.accept()))
                    row.addWidget(btn_open)

                    btn_del = QPushButton("🗑 Delete")
                    btn_del.setObjectName("DangerButton")
                    btn_del.setFixedWidth(75)
                    btn_del.clicked.connect(lambda _, path=p_dir: (self._delete_pack_from_disk(path), refresh_list(txt_search.text().strip())))
                    row.addWidget(btn_del)

                    rows_layout.addWidget(card)

            rows_layout.addStretch()

        refresh_list()
        txt_search.textChanged.connect(refresh_list)
        dlg.exec_()

    def _create_new_pack(self) -> None:
        self.pack = PackModel()
        self.history_manager.clear()
        self._update_undo_redo_buttons()
        self.txt_pack_name.setText(self.pack.name)
        self.txt_author.setText(self.pack.author)
        self.character_roster.set_characters(self.pack.characters, self.pack.active_selected_characters)
        self._on_remove_video_clicked()
        self._sync_ui_with_pack()
        self.show_status("New empty pack created!", COLOR_CYAN_PRIMARY)

    def _load_pack_from_dir(self, pack_dir: str) -> None:
        loaded = PackModel.load_from_folder(pack_dir)
        if loaded:
            self.pack = loaded
            self.history_manager.clear()
            self._update_undo_redo_buttons()
            self.txt_pack_name.setText(self.pack.name)
            self.txt_author.setText(self.pack.author)
            self.character_roster.set_characters(self.pack.characters, self.pack.active_selected_characters)
            if self.pack.video_path and os.path.exists(self.pack.video_path):
                info = FFmpegHandler.probe_media(self.pack.video_path)
                self.video_widget.load_video(self.pack.video_path, info["aspect_ratio"])
                self._extract_waveform_peaks(self.pack.video_path)
            self._sync_ui_with_pack()
            self.show_status(f"✓ Pack '{self.pack.name}' loaded!", COLOR_ACCENT_GREEN)

    def _delete_pack_from_disk(self, pack_dir: str) -> None:
        name = os.path.basename(os.path.normpath(pack_dir))
        ret = QMessageBox.question(
            self, "Delete Pack?",
            f"Are you sure you want to permanently delete pack '{name}' from disk?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret == QMessageBox.Yes:
            import shutil
            shutil.rmtree(pack_dir, ignore_errors=True)
            self.show_status(f"✓ Pack '{name}' deleted.", COLOR_ACCENT_GREEN)
            if self.pack.name == name:
                self._create_new_pack()

    def _sync_ui_with_pack(self, scroll_to_bottom: bool = False) -> None:
        self.scene_card_list.set_data(self.pack.clips, self.pack.characters, scroll_to_bottom=scroll_to_bottom)
        self.waveform_widget.set_scenes([c.to_dict() for c in self.pack.clips])

    def _load_recent_or_default_pack(self) -> None:
        base_dir = PackExporter.get_game_packs_dir()
        if os.path.exists(base_dir):
            packs = [os.path.join(base_dir, d) for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and not d.startswith(".")]
            if packs:
                packs.sort(key=os.path.getmtime, reverse=True)
                self._load_pack_from_dir(packs[0])
                return
        self._sync_ui_with_pack()
