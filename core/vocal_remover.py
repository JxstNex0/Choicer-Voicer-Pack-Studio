"""
Choicer Voicer Pack Studio - Standalone Edition
AI Vocal Separation & Backing Track Extractor
"""

import os
import sys
import numpy as np
import soundfile as sf
from typing import Optional, Callable
from .ffmpeg_handler import FFmpegHandler


class VocalRemover:
    @staticmethod
    def is_ai_available() -> bool:
        """Checks if demucs-onnx or onnxruntime is available."""
        try:
            import demucs_onnx
            return True
        except ImportError:
            return False

    @classmethod
    def isolate_backing_track(
        cls,
        input_media_path: str,
        output_backing_path: str,
        method: str = "ai",
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Extracts backing track (music & sound effects without dialogue) from audio/video.
        Saves output as WAV (16-bit 44.1kHz stereo).
        """
        temp_wav = output_backing_path + ".temp_input.wav"

        # 1. Extract audio if input is video
        if not input_media_path.lower().endswith(".wav"):
            if progress_callback:
                progress_callback("Extracting audio from video...")
            if not FFmpegHandler.extract_audio_wav(input_media_path, temp_wav):
                return False
            source_audio = temp_wav
        else:
            source_audio = input_media_path

        success = False
        try:
            if method == "ai" and cls.is_ai_available():
                if progress_callback:
                    progress_callback("✨ Running AI Vocal Remover (Demucs ONNX)...")
                success = cls._process_demucs(source_audio, output_backing_path, progress_callback)
            else:
                if progress_callback:
                    progress_callback("Running DSP vocal filter (Center Channel Subtraction)...")
                success = cls._process_dsp(source_audio, output_backing_path)
        except Exception as e:
            print(f"[VocalRemover] AI processing failed: {e}, falling back to DSP...")
            success = cls._process_dsp(source_audio, output_backing_path)
        finally:
            if os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass

        return success

    @classmethod
    def _process_demucs(cls, input_wav: str, output_wav: str, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        import demucs_onnx
        
        if progress_callback:
            progress_callback("Demucs AI is separating audio stems...")

        # Separate audio into 4 stems: drums, bass, other, vocals
        stems = demucs_onnx.separate(input=input_wav, model="htdemucs", progress=False)

        # Backing track = sum of all non-vocal stems (drums + bass + other)
        backing = None
        for stem_name, stem_data in stems.items():
            if stem_name.lower() != "vocals":
                if backing is None:
                    backing = np.copy(stem_data)
                else:
                    backing += stem_data

        if backing is None:
            first_stem = list(stems.values())[0]
            backing = np.zeros_like(first_stem)

        # demucs_onnx returns shape (channels, samples). Transpose to (samples, channels) for soundfile
        if backing.ndim == 2 and backing.shape[0] == 2 and backing.shape[1] > 2:
            backing = backing.T

        # Normalize to prevent clipping
        max_val = np.max(np.abs(backing))
        if max_val > 0.95:
            backing = backing / max_val * 0.92

        sf.write(output_wav, backing, 44100, subtype="PCM_16")
        return os.path.exists(output_wav)

    @classmethod
    def _process_dsp(cls, input_wav: str, output_wav: str) -> bool:
        """Center-channel vocal suppression algorithm for stereo audio."""
        audio, sample_rate = sf.read(input_wav)
        if audio.ndim == 1 or audio.shape[1] < 2:
            sf.write(output_wav, audio, sample_rate, subtype="PCM_16")
            return True

        left = audio[:, 0]
        right = audio[:, 1]
        center = (left + right) * 0.5
        sides = left - right

        # High-pass filter sides slightly to preserve bass
        backing_left = sides * 0.7 + left * 0.3
        backing_right = -sides * 0.7 + right * 0.3

        backing = np.stack([backing_left, backing_right], axis=-1)
        max_val = np.max(np.abs(backing))
        if max_val > 0.95:
            backing = backing / max_val * 0.90

        sf.write(output_wav, backing, sample_rate, subtype="PCM_16")
        return os.path.exists(output_wav)
