# 🚀 Deployment Guide: GestureMouse AI & Fruit Ninja

This guide covers all methods for deploying and distributing **GestureMouse AI** to end-users, portfolios, and platforms.

---

## 🌟 Method 1: Automated GitHub Release (Recommended)

The repository includes a GitHub Actions CI/CD pipeline ([`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)) that automatically runs all unit tests, compiles the standalone Windows executable, and publishes a downloadable `.zip` file under **GitHub Releases**.

### How to Trigger an Automatic Release:

1. Commit and push any new changes to GitHub:
   ```bash
   git add .
   git commit -m "Add deployment pipeline and standalone build scripts"
   git push origin main
   ```

2. Tag your version release and push the tag:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0: GestureMouse AI & Fruit Ninja"
   git push origin v1.0.0
   ```

3. **That's it!** GitHub Actions will automatically:
   - Spin up a Windows runner.
   - Run the 31 test cases to verify stability.
   - Package `GestureMouseAI.exe` using PyInstaller.
   - Bundle `models/`, `assets/`, `game/`, and themes into `GestureMouseAI-Windows-x64.zip`.
   - Publish a new release at `https://github.com/Saiteja-033/GestureMouse-AI/releases`!

---

## 📦 Method 2: Local Windows Executable Build (`.exe`)

You can generate a standalone executable on your Windows machine that runs on any computer without needing Python installed.

### Option A: Double-Click Batch Script
Double-click:
```
build_executable.bat
```

### Option B: Terminal Command
```powershell
python build_exe.py
```

### Output:
The completed distribution will be located at:
```
dist/GestureMouseAI/GestureMouseAI.exe
```
Zip this folder and share it with anyone!

---

## ⚡ Method 3: One-Click Portable Launcher (`run_app.bat`)

For colleagues, teachers, or collaborators who have Python installed and clone your repository:

Simply double-click:
```
run_app.bat
```
This script automatically:
1. Verifies Python on the user's system.
2. Auto-installs any missing dependencies from `requirements.txt`.
3. Launches the application immediately.

---

## 🌐 Method 4: Cloud Portfolio Showcase (Hugging Face Spaces)

If you want to showcase your AI computer vision project online on your resume or portfolio without users needing to download anything:

1. Create a free account at [huggingface.co](https://huggingface.co/).
2. Click **New Space** -> Select **Gradio** or **Streamlit** SDK.
3. Link your GitHub repository `Saiteja-033/GestureMouse-AI`.
4. Users can interact with your real-time hand-tracking visualizer directly inside their browser!

---

## 📋 Pre-Deployment Verification Checklist

Before publishing your release, make sure all tests pass:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Expected result:
```
Ran 31 tests in ~12s
OK
```
