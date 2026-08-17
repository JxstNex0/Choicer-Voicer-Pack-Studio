"""
Choicer Voicer Pack Studio - Standalone Edition
Pack Data Model & Serialization
"""

import os
import json
import configparser
from typing import List, Dict, Any, Optional


class SceneClip:
    def __init__(
        self,
        start_time: float = 0.0,
        end_time: float = 3.0,
        characters: Optional[List[str]] = None,
        subtitle: str = "",
        character_subtitles: Optional[Dict[str, str]] = None
    ):
        self.start_time = float(start_time)
        self.end_time = float(end_time)
        self.characters = list(characters) if characters is not None else []
        self.subtitle = subtitle
        self.character_subtitles: Dict[str, str] = dict(character_subtitles) if character_subtitles else {}

        # Parse subtitle if provided and character_subtitles not explicitly set
        if self.subtitle and not self.character_subtitles:
            self._parse_subtitle_string(self.subtitle)

    def _parse_subtitle_string(self, sub: str) -> None:
        if " // " in sub:
            parts = sub.split(" // ")
            for p in parts:
                if ":" in p:
                    c, txt = p.split(":", 1)
                    self.character_subtitles[c.strip()] = txt.strip()
        elif len(self.characters) == 1:
            self.character_subtitles[self.characters[0]] = sub

    def get_character_subtitle(self, character: str) -> str:
        if character in self.character_subtitles:
            return self.character_subtitles[character]
        if len(self.characters) <= 1:
            return self.subtitle
        return ""

    def set_character_subtitle(self, character: str, text: str) -> None:
        self.character_subtitles[character] = text
        if len(self.characters) <= 1:
            self.subtitle = text
        else:
            parts = []
            for ch in self.characters:
                ch_txt = self.character_subtitles.get(ch, "")
                if ch_txt:
                    parts.append(f"{ch}: {ch_txt}")
            self.subtitle = " // ".join(parts) if parts else ""

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": round(self.start_time, 2),
            "end": round(self.end_time, 2),
            "characters": self.characters,
            "character": self.characters[0] if self.characters else "",
            "subtitle": self.subtitle,
            "character_subtitles": dict(self.character_subtitles)
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SceneClip":
        chars = d.get("characters")
        if chars is None:
            c = d.get("character", "")
            chars = [c] if c else []
        return cls(
            start_time=float(d.get("start", 0.0)),
            end_time=float(d.get("end", 3.0)),
            characters=list(chars),
            subtitle=str(d.get("subtitle", "")),
            character_subtitles=d.get("character_subtitles")
        )


class PackModel:
    def __init__(
        self,
        name: str = "My Custom Pack",
        author: str = "Nexo",
        subtitle: str = "Created with Choicer Voicer Pack Studio",
        video_path: str = "",
        backing_track_path: str = "",
        is_backing_muted: bool = False,
        characters: Optional[List[str]] = None,
        clips: Optional[List[SceneClip]] = None
    ):
        self.name = name
        self.author = author
        self.subtitle = subtitle
        self.video_path = video_path
        self.backing_track_path = backing_track_path
        self.is_backing_muted = is_backing_muted
        self.characters = list(characters) if characters is not None else []
        self.clips = list(clips) if clips is not None else []
        self.active_selected_characters: List[str] = [self.characters[0]] if self.characters else []

    def add_clip(self, clip: SceneClip) -> None:
        self.clips.append(clip)
        self.sort_clips()

    def remove_clip(self, index: int) -> None:
        if 0 <= index < len(self.clips):
            self.clips.pop(index)

    def sort_clips(self) -> None:
        self.clips.sort(key=lambda c: c.start_time)

    def create_snapshot(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "author": self.author,
            "subtitle": self.subtitle,
            "characters": list(self.characters),
            "active_selected_characters": list(self.active_selected_characters),
            "backing_track_path": self.backing_track_path,
            "is_backing_muted": self.is_backing_muted,
            "clips": [c.to_dict() for c in self.clips]
        }

    def restore_snapshot(self, snap: Dict[str, Any]) -> None:
        self.name = snap.get("name", self.name)
        self.author = snap.get("author", self.author)
        self.subtitle = snap.get("subtitle", self.subtitle)
        self.characters = list(snap.get("characters", []))
        self.active_selected_characters = list(snap.get("active_selected_characters", []))
        self.backing_track_path = snap.get("backing_track_path", "")
        self.is_backing_muted = snap.get("is_backing_muted", False)
        self.clips = [SceneClip.from_dict(c) for c in snap.get("clips", [])]

    def to_json_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "author": self.author,
            "subtitle": self.subtitle,
            "version": "1.0.0",
            "type": "dub",
            "characters": self.characters,
            "backing_track_path": self.backing_track_path,
            "is_backing_muted": self.is_backing_muted,
            "clips": [c.to_dict() for c in self.clips]
        }

    def generate_ini_content(self) -> str:
        lines = [
            "[data]",
            f'title="{self.name}"',
            f'subtitle="{self.subtitle}"',
            f'authors=["{self.author}"]',
            f'preselected_dub_characters={[c for c in self.characters]}',
            "",
            "[Main]",
            f'display_name="{self.name}"',
            f'author="{self.author}"',
            f'subtitle="{self.subtitle}"',
            "type=3",
            "has_backing_track=" + ("true" if self.backing_track_path and not self.is_backing_muted else "false"),
            ""
        ]
        if self.characters:
            lines.append("[Speakers]")
            for i, ch in enumerate(self.characters, start=1):
                lines.append(f'speaker_{i}="{ch}"')
            lines.append("")

        lines.append("[Clips]")
        clip_counter = 1
        for clip in self.clips:
            chars_in_clip = clip.characters if clip.characters else ["Default"]
            for ch in chars_in_clip:
                char_sub = clip.get_character_subtitle(ch)
                if not char_sub:
                    char_sub = clip.subtitle
                lines.append(f"clip_{clip_counter}_start={clip.start_time:.2f}")
                lines.append(f"clip_{clip_counter}_end={clip.end_time:.2f}")
                lines.append(f'clip_{clip_counter}_characters="{ch}"')
                lines.append(f'clip_{clip_counter}_subtitle="{char_sub}"')
                lines.append("")
                clip_counter += 1

        return "\n".join(lines)

    @classmethod
    def load_from_folder(cls, folder_path: str) -> Optional["PackModel"]:
        """Loads pack from folder containing pack_info.json or _pack_info.ini."""
        if not os.path.exists(folder_path):
            return None

        pack = cls(name=os.path.basename(folder_path))
        json_path = os.path.join(folder_path, "pack_info.json")
        ini_path = os.path.join(folder_path, "_pack_info.ini")

        # Find video
        for f in ["dub_video.ogv", "dub_video.mp4", "video.ogv", "video.mp4"]:
            v_test = os.path.join(folder_path, f)
            if os.path.exists(v_test):
                pack.video_path = v_test
                break

        # Find backing track
        for f in ["_backing_track.wav", "backing_track.wav", "_backing_track.mp3"]:
            b_test = os.path.join(folder_path, f)
            if os.path.exists(b_test):
                pack.backing_track_path = b_test
                break

        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                pack.name = data.get("name", pack.name)
                pack.author = data.get("author", "Nexo")
                pack.subtitle = data.get("subtitle", "Voice Pack")
                pack.characters = data.get("characters", [])
                pack.is_backing_muted = data.get("is_backing_muted", False)
                pack.clips = [SceneClip.from_dict(c) for c in data.get("clips", [])]
                return pack
            except Exception as e:
                print(f"[PackModel] Error reading json: {e}")

        if os.path.exists(ini_path):
            try:
                cp = configparser.ConfigParser()
                cp.read(ini_path, encoding="utf-8")
                if "Main" in cp:
                    pack.name = cp["Main"].get("display_name", pack.name).strip('"')
                    pack.author = cp["Main"].get("author", "Nexo").strip('"')
                    pack.subtitle = cp["Main"].get("subtitle", "").strip('"')

                if "Speakers" in cp:
                    spks = []
                    for k, v in cp["Speakers"].items():
                        spks.append(v.strip('"'))
                    if spks:
                        pack.characters = spks

                # Parse clips from INI
                if "Clips" in cp:
                    clip_dict = {}
                    for k, v in cp["Clips"].items():
                        parts = k.split("_")
                        if len(parts) >= 3 and parts[0] == "clip":
                            num = int(parts[1])
                            field = parts[2]
                            if num not in clip_dict:
                                clip_dict[num] = {}
                            clip_dict[num][field] = v.strip('"')

                    clips = []
                    for num in sorted(clip_dict.keys()):
                        info = clip_dict[num]
                        chars_raw = info.get("characters", info.get("character", ""))
                        if isinstance(chars_raw, str):
                            chars = [c.strip() for c in chars_raw.split(",") if c.strip()]
                        else:
                            chars = [str(chars_raw)] if chars_raw else []
                        clips.append(SceneClip(
                            start_time=float(info.get("start", 0.0)),
                            end_time=float(info.get("end", 3.0)),
                            characters=chars,
                            subtitle=info.get("subtitle", "")
                        ))
                    pack.clips = clips
                return pack
            except Exception as e:
                print(f"[PackModel] Error reading INI: {e}")

        return pack
