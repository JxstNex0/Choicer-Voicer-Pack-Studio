"""
Choicer Voicer Pack Studio - Standalone Edition
Pack Exporter & ZIP Generator
"""

import os
import sys
import shutil
import zipfile
from typing import Dict, Any, Optional, Callable
from .pack_model import PackModel
from .ffmpeg_handler import FFmpegHandler


class PackExporter:
    @staticmethod
    def get_game_packs_dir() -> str:
        """Finds or creates the user's game packs_voice directory."""
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                target = os.path.join(appdata, "YeahMaybe", "ChoicerVoicer", "game", "packs_voice")
                os.makedirs(target, exist_ok=True)
                return target

        # Linux / Fallback
        home = os.path.expanduser("~")
        target = os.path.join(home, ".local", "share", "godot", "app_userdata", "ChoicerVoicer", "game", "packs_voice")
        os.makedirs(target, exist_ok=True)
        return target

    @classmethod
    def save_pack(
        cls,
        pack: PackModel,
        destination_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Saves pack to game folder or custom directory."""
        safe_name = "".join(c for c in pack.name if c.isalnum() or c in (" ", "_", "-")).strip()
        if not safe_name:
            safe_name = "CustomPack"

        if not destination_dir:
            base_dir = cls.get_game_packs_dir()
            target_dir = os.path.join(base_dir, safe_name)
        else:
            target_dir = destination_dir

        os.makedirs(target_dir, exist_ok=True)

        if progress_callback:
            progress_callback(f"Saving pack to: {target_dir}...")

        # 1. Write pack_info.json
        json_path = os.path.join(target_dir, "pack_info.json")
        try:
            import json
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(pack.to_json_dict(), jf, indent=2, ensure_ascii=False)
        except Exception as e:
            return {"success": False, "error": f"Failed to write pack_info.json: {e}"}

        # 2. Write _pack_info.ini
        ini_path = os.path.join(target_dir, "_pack_info.ini")
        try:
            with open(ini_path, "w", encoding="utf-8") as inf:
                inf.write(pack.generate_ini_content())
        except Exception as e:
            return {"success": False, "error": f"Failed to write _pack_info.ini: {e}"}

        # 3. Copy / Convert Video to dub_video.ogv
        if pack.video_path and os.path.exists(pack.video_path):
            dest_ogv = os.path.join(target_dir, "dub_video.ogv")
            if pack.video_path.lower().endswith(".ogv"):
                if os.path.abspath(pack.video_path) != os.path.abspath(dest_ogv):
                    shutil.copy2(pack.video_path, dest_ogv)
            else:
                if progress_callback:
                    progress_callback("Converting video to dub_video.ogv...")
                FFmpegHandler.convert_video_to_ogv(pack.video_path, dest_ogv, progress_callback)

        # 4. Copy / Handle Backing Track
        if pack.backing_track_path and not pack.is_backing_muted and os.path.exists(pack.backing_track_path):
            dest_backing = os.path.join(target_dir, "_backing_track.wav")
            if os.path.abspath(pack.backing_track_path) != os.path.abspath(dest_backing):
                shutil.copy2(pack.backing_track_path, dest_backing)

        # 5. Extract dialogue audio clips & write .ini metadata for game compatibility
        if pack.video_path and os.path.exists(pack.video_path) and pack.clips:
            if progress_callback:
                progress_callback("Extracting dialogue audio clips...")
            
            # Clean obsolete audio slices and inis
            for f in os.listdir(target_dir):
                if (f.endswith((".wav", ".ini", ".txt")) and 
                    not f.startswith(("_pack_info", "_backing_track", "dub_video")) and
                    not f == "pack_info.json"):
                    try:
                        os.remove(os.path.join(target_dir, f))
                    except Exception:
                        pass

            source_audio = pack.video_path
            clip_counter = 1
            for scene_idx, clip in enumerate(pack.clips, start=1):
                chars_in_clip = clip.characters if clip.characters else ["Default"]
                for ch in chars_in_clip:
                    char_slug = "".join(c for c in ch if c.isalnum()) or "Clip"
                    base_clip_name = f"{clip_counter:02d}_{char_slug}"
                    clip_audio_path = os.path.join(target_dir, f"{base_clip_name}.wav")
                    clip_ini_path = os.path.join(target_dir, f"{base_clip_name}.ini")

                    # Get the individual line for this character
                    char_subtitle = clip.get_character_subtitle(ch)
                    if not char_subtitle:
                        char_subtitle = clip.subtitle

                    # Slice audio using ffmpeg
                    FFmpegHandler.slice_audio(source_audio, clip.start_time, clip.end_time, clip_audio_path)

                    # Write clip .ini metadata for Choicer Voicer
                    ini_content = (
                        "[data]\n\n"
                        f'caption="{char_subtitle}"\n'
                        f"dub_timestamps=[{clip.start_time:.3f}]\n"
                        f'dub_characters=["{ch}"]\n'
                        "dub_only=true\n"
                    )
                    try:
                        with open(clip_ini_path, "w", encoding="utf-8") as cif:
                            cif.write(ini_content)
                    except Exception as e:
                        print(f"[PackExporter] Error writing {clip_ini_path}: {e}")

                    clip_counter += 1

        return {"success": True, "path": target_dir}

    @classmethod
    def export_to_zip(
        cls,
        pack: PackModel,
        destination_zip: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Creates a ready-to-share .zip package on the Desktop or custom location."""
        safe_name = "".join(c for c in pack.name if c.isalnum() or c in (" ", "_", "-")).strip()
        if not safe_name:
            safe_name = "VoicePack"

        # Determine Desktop path
        if not destination_zip:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.expanduser("~")
            zip_path = os.path.join(desktop, f"{safe_name}.zip")
        else:
            zip_path = destination_zip

        # 1. First save to a temp folder
        temp_pack_dir = os.path.join(os.path.expanduser("~"), ".cv_pack_temp", safe_name)
        if os.path.exists(temp_pack_dir):
            shutil.rmtree(temp_pack_dir, ignore_errors=True)

        res = cls.save_pack(pack, destination_dir=temp_pack_dir, progress_callback=progress_callback)
        if not res["success"]:
            return res

        # 2. Package into ZIP
        if progress_callback:
            progress_callback(f"Building ZIP archive: {os.path.basename(zip_path)}...")

        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(temp_pack_dir):
                    for file in files:
                        full_f = os.path.join(root, file)
                        # Archive relative to safe_name/
                        rel_f = os.path.join(safe_name, os.path.relpath(full_f, temp_pack_dir))
                        zf.write(full_f, rel_f)
        except Exception as e:
            return {"success": False, "error": f"Failed to create ZIP: {e}"}
        finally:
            shutil.rmtree(temp_pack_dir, ignore_errors=True)

        return {"success": True, "path": zip_path}
