"""
Choicer Voicer Pack Studio - Standalone Build Script
Packages the application into a single-file executable using PyInstaller.
"""

import os
import sys
import subprocess
import shutil

APP_NAME = "Choicer Voicer Pack Studio"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PY = os.path.join(SCRIPT_DIR, "main.py")
DIST_DIR = os.path.join(SCRIPT_DIR, "dist")
BUILD_DIR = os.path.join(SCRIPT_DIR, "build")


def build():
    print(f"==================================================")
    print(f"   Building {APP_NAME} Executable")
    print(f"==================================================")

    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("[!] PyInstaller is not installed. Installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Clean old build folders
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR, ignore_errors=True)
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR, ignore_errors=True)

    icon_path = os.path.join(SCRIPT_DIR, "assets", "icon.ico")
    icon_arg = ["--icon", icon_path] if os.path.exists(icon_path) else []

    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data", f"{os.path.join(SCRIPT_DIR, 'ui')}{os.pathsep}ui",
        "--add-data", f"{os.path.join(SCRIPT_DIR, 'core')}{os.pathsep}core",
        "--hidden-import", "PySide6",
        "--hidden-import", "PySide6.QtMultimedia",
        "--hidden-import", "PySide6.QtMultimediaWidgets",
        "--hidden-import", "soundfile",
        "--hidden-import", "numpy",
    ] + icon_arg + [MAIN_PY]

    print(f"Running command: {' '.join(pyinstaller_cmd)}\n")
    res = subprocess.run(pyinstaller_cmd, cwd=SCRIPT_DIR)

    if res.returncode == 0:
        print("\n==================================================")
        print(f" [✓] Build Successful!")
        print(f" Executable created in: {DIST_DIR}/{APP_NAME}/")
        print("==================================================")
    else:
        print("\n[✗] Build failed. See error output above.")


if __name__ == "__main__":
    build()
