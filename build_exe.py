"""
GestureMouse AI - Standalone Executable Build Script
Uses PyInstaller to package the application, assets, models, and dependencies into
a standalone Windows distribution folder / executable.
"""

import os
import sys
import shutil
import subprocess
import customtkinter


def build():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    ctk_path = os.path.dirname(customtkinter.__file__)

    icon_path = os.path.join(base_dir, "assets", "icons", "app_icon.ico")
    models_dir = os.path.join(base_dir, "models")
    assets_dir = os.path.join(base_dir, "assets")

    # Separator for PyInstaller --add-data on Windows is ';'
    sep = ";"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name=GestureMouseAI",
        f"--icon={icon_path}",
        f"--add-data={models_dir}{sep}models",
        f"--add-data={assets_dir}{sep}assets",
        f"--add-data={ctk_path}{sep}customtkinter",
        "--hidden-import=customtkinter",
        "--hidden-import=PIL",
        "--hidden-import=cv2",
        "--hidden-import=mediapipe",
        "--hidden-import=pyautogui",
        "--hidden-import=pygame",
        "--hidden-import=numpy",
        os.path.join(base_dir, "main.py"),
    ]

    print("=" * 60)
    print("  GestureMouse AI - Packaging Standalone Executable")
    print(f"  Base Directory: {base_dir}")
    print("=" * 60)
    print("Running command:", " ".join(cmd))

    ret = subprocess.call(cmd, cwd=base_dir)
    if ret == 0:
        print("\n" + "=" * 60)
        print("  BUILD SUCCESSFUL!")
        print(f"  Distribution directory: {os.path.join(base_dir, 'dist', 'GestureMouseAI')}")
        print("  Executable: GestureMouseAI.exe")
        print("=" * 60)
    else:
        print("\n[Build Error] PyInstaller exited with code:", ret, file=sys.stderr)
        sys.exit(ret)


if __name__ == "__main__":
    build()
