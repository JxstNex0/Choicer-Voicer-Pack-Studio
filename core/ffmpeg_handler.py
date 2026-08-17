"""
Choicer Voicer Pack Studio - Standalone Edition
FFmpeg Handler & Media Converter Utility
"""

import os
import sys
import shutil
import subprocess
from typing import Optional, Tuple, List, Dict, Any, Callable


class FFmpegHandler:
    @staticmethod
    def get_ffmpeg_path() -> Optional[str]:
        """Finds FFmpeg executable in PATH, local directory, or project folders."""
        # 1. Check PATH
        ffmpeg_cmd = shutil.which("ffmpeg")
        if ffmpeg_cmd:
            return ffmpeg_cmd

        # 2. Check current and parent directories
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(app_dir, "ffmpeg.exe"),
            os.path.join(app_dir, "bin", "ffmpeg.exe"),
            os.path.join(os.path.dirname(app_dir), "ffmpeg.exe"),
            "C:\\ffmpeg\\bin\\ffmpeg.exe",
            "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
        ]
        for c in candidates:
            if os.path.isfile(c) and os.access(c, os.X_OK):
                return c
        return None

    @staticmethod
    def get_ffprobe_path() -> Optional[str]:
        """Finds FFprobe executable."""
        ffprobe_cmd = shutil.which("ffprobe")
        if ffprobe_cmd:
            return ffprobe_cmd

        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(app_dir, "ffprobe.exe"),
            os.path.join(app_dir, "bin", "ffprobe.exe"),
            os.path.join(os.path.dirname(app_dir), "ffprobe.exe"),
            "C:\\ffmpeg\\bin\\ffprobe.exe",
            "/usr/bin/ffprobe",
            "/usr/local/bin/ffprobe",
        ]
        for c in candidates:
            if os.path.isfile(c) and os.access(c, os.X_OK):
                return c
        return None

    @classmethod
    def probe_media(cls, file_path: str) -> Dict[str, Any]:
        """Probes media file and returns duration, width, height, and audio stream info."""
        ffprobe = cls.get_ffprobe_path() or "ffprobe"
        result = {
            "duration": 60.0,
            "width": 1280,
            "height": 720,
            "has_audio": True,
            "aspect_ratio": 16.0 / 9.0
        }

        if not os.path.exists(file_path):
            return result

        try:
            # 1. Get duration
            cmd = [
                ffprobe, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            out = subprocess.check_output(cmd, startupinfo=startupinfo, stderr=subprocess.DEVNULL).decode().strip()
            dur = float(out)
            if dur > 0.1:
                result["duration"] = dur
        except Exception:
            pass

        try:
            # 2. Get video dimensions
            cmd = [
                ffprobe, "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0",
                file_path
            ]
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            out = subprocess.check_output(cmd, startupinfo=startupinfo, stderr=subprocess.DEVNULL).decode().strip()
            if "x" in out:
                w, h = map(int, out.split("x"))
                if w > 0 and h > 0:
                    result["width"] = w
                    result["height"] = h
                    result["aspect_ratio"] = float(w) / float(h)
        except Exception:
            pass

        return result

    @classmethod
    def extract_audio_wav(cls, video_path: str, output_wav: str) -> bool:
        """Extracts audio from video to 16-bit 44.1kHz stereo WAV for waveform & AI processing."""
        ffmpeg = cls.get_ffmpeg_path() or "ffmpeg"
        os.makedirs(os.path.dirname(os.path.abspath(output_wav)), exist_ok=True)

        cmd = [
            ffmpeg, "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            output_wav
        ]
        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            res = subprocess.run(cmd, startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return res.returncode == 0 and os.path.exists(output_wav)
        except Exception as e:
            print(f"[FFmpegHandler] Error extracting audio: {e}")
            return False

    @classmethod
    def slice_audio(cls, input_media_path: str, start_sec: float, end_sec: float, output_wav: str) -> bool:
        """Slices an audio segment from a video or audio file and saves as WAV."""
        ffmpeg = cls.get_ffmpeg_path() or "ffmpeg"
        os.makedirs(os.path.dirname(os.path.abspath(output_wav)), exist_ok=True)

        dur = max(0.1, end_sec - start_sec)
        cmd = [
            ffmpeg, "-y",
            "-ss", f"{start_sec:.3f}",
            "-t", f"{dur:.3f}",
            "-i", input_media_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            output_wav
        ]
        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            res = subprocess.run(cmd, startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return res.returncode == 0 and os.path.exists(output_wav)
        except Exception as e:
            print(f"[FFmpegHandler] Error slicing audio: {e}")
            return False

    @classmethod
    def convert_video_to_ogv(cls, video_path: str, output_ogv: str, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Converts video to Theora/Vorbis (.ogv) preserving exact orientation/aspect ratio."""
        ffmpeg = cls.get_ffmpeg_path() or "ffmpeg"
        os.makedirs(os.path.dirname(os.path.abspath(output_ogv)), exist_ok=True)

        if progress_callback:
            progress_callback("Konvertiere Video in Godot-kompatibles OGV Format...")

        # Orientation-aware scale: limits max dimension to 720p without distortion
        scale_filter = "scale='if(gt(iw,ih),min(720,iw),-2)':'if(gt(iw,ih),-2,min(720,ih))',fps=24"

        cmd = [
            ffmpeg, "-y",
            "-i", video_path,
            "-vf", scale_filter,
            "-c:v", "libtheora",
            "-q:v", "6",
            "-c:a", "libvorbis",
            "-q:a", "3",
            output_ogv
        ]

        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            res = subprocess.run(cmd, startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return res.returncode == 0 and os.path.exists(output_ogv)
        except Exception as e:
            print(f"[FFmpegHandler] Error converting to OGV: {e}")
            return False
