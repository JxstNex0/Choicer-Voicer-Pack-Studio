# 🎬 Choicer Voicer - Pack Studio (Fan-Made Standalone Edition)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-cyan.svg)](https://www.python.org/downloads/)
[![PySide6 / Qt6](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-green.svg)](https://pypi.org/project/PySide6/)
[![Discord Community](https://img.shields.io/badge/Discord-Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.gg/)

An unofficial, fan-made standalone **Pack Studio Desktop Application** for [*The Choicer Voicer*]! Create, cut, subtitle, and share custom voice-over video packs for the community – fast, precise, and powered by state-of-the-art AI vocal separation.

---

## ⚖️ Disclaimer & Notice

> [!IMPORTANT]
> This is an **unofficial, non-commercial fan-made community tool** developed to help creators make custom packs. It is **not** an official software and is **not** affiliated with, endorsed by, or sponsored by the original developers/creators of *The Choicer Voicer*. All original game assets, trademarks, and intellectual properties belong entirely to their respective copyright holders.

---

## ✨ Features

- 🎥 **Native Video Player & Timeline Cutter:** Supports all major video formats (`.mp4`, `.mkv`, `.webm`, `.ogv`, `.mov`, `.avi`).
- 📱 **Automatic Aspect Ratio Support:** Full support for **vertical portrait videos** (TikTok / YouTube Shorts / 9:16) and landscape formats (16:9, 4:3) with dynamic zero-distortion letterboxing.
- 🌊 **Interactive Zoom Waveform (1x – 40x):** Precision cutting with zoom, draggable start/end handles, scene region resizing/dragging, and horizontal navigation scrollbar.
- ✨ **Integrated AI Vocal Remover (Demucs ONNX):** 1-Click extraction of background music and sound effects into a clean `_backing_track.wav` without dialogue.
- 👥 **Multi-Speaker & Dual Recording:** Assign multiple characters simultaneously to single lines for synchronous duets and dialogues.
- ⚡ **1-Click Discord ZIP Export:** Package finished packs directly to your Desktop as ready-to-share `.zip` archives.
- 🎮 **Direct Game Sync:** Automatically detects the game's pack directory (`%APPDATA%\YeahMaybe\ChoicerVoicer\game\packs_voice\`) for instant local testing.

---

## 🚀 Quickstart for Users

### Option 1: Download Standalone .exe (No Python Required)
1. Download the latest **`Choicer Voicer Pack Studio.exe`** from [GitHub Releases](https://github.com/).
2. Run the executable and start creating packs!

---

## 🛠️ Quickstart for Developers

Requirements: **Python 3.10+** and **FFmpeg** in your system path.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/choicer-voicer-pack-studio.git
   cd choicer-voicer-pack-studio
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch Pack Studio:**
   ```bash
   python main.py
   ```

---

## 📦 Build Your Own Executable

You can build a portable Windows `.exe` bundle using the included build script:

```bash
python build_exe.py
```
The resulting executable will be generated in `dist/Choicer Voicer Pack Studio/`.

---

## 📖 Guide: Create a Pack in 5 Steps

1. **Load Video:** Click **`📁 Load Video`** in the top bar.
2. **Setup Backing Track (Optional):** Open the **`🎵 Backing Track`** menu and select **`✨ AI Vocal Remover`** to automatically isolate background audio without dialogue.
3. **Configure Roles:** Add the character names for your video under **ROLES** (e.g., *Narrator*, *Hero*, *Villain*).
4. **Cut Scenes & Add Lines:**
   - Move the playhead to the desired position.
   - Click **`[ Start`** and **`] End`** or press **`⚡ Split`**.
   - Click **`+ Add Clip`** to create the scene.
   - Type your dialogue / subtitle in the scene card.
5. **Export & Share:** Click **`📦 Export ZIP`** to export a ready-to-share pack archive for Discord!

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are warmly welcomed! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## 📄 License

This project is licensed under the **MIT License** – see [LICENSE](LICENSE) for details.
"# Choicer-Voicer-Pack-Studio" 
