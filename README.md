# GestureMouse AI 🖱️✨
### AI-Powered Hand Gesture Controlled Virtual Mouse System

**GestureMouse AI** is an intelligent, high-precision computer vision desktop application that allows users to interactively control their operating system cursor and mouse actions in real-time using intuitive hand gestures captured via a standard webcam.

Built with Python 3.11+, MediaPipe, OpenCV, PyAutoGUI, and CustomTkinter, it provides a desktop experience with jitter-free cursor interpolation, configurable gesture thresholds, drag-and-drop state machines, and fail-safe safety mechanisms.

---

## 🌟 Key Features

- **⚡ Real-Time Neural Hand Tracking**: Powered by MediaPipe 21-point 3D landmark skeletal detection.
- **🎯 Comprehensive Gesture Set**:
  - **Index Finger Only**: Move mouse cursor across the screen.
  - **Thumb + Index Pinch**: Single Left-Click (debounced, avoids repeated triggers).
  - **Thumb + Middle Pinch**: Right-Click (context menu).
  - **Index + Middle Tips Touch**: Double-Click.
  - **Two Fingers Upright (Index + Middle)**: Smooth dynamic vertical scrolling.
  - **Hold Pinch (>0.45s)**: Hold & Drag-and-Drop state machine.
  - **Closed Fist**: Immediate movement pause.
  - **Open Palm**: Re-activate mouse control.
  - **Thumb Extension**: Dynamic Volume Control.
- **🎮 Fruit Ninja Gesture Gaming Mode**:
  - Full arcade slashing game powered by Pygame & MediaPipe.
  - Slices Watermelons, Apples, Oranges, Bananas, Strawberries, and Coconuts using high-velocity index finger swipes.
  - Splitting halves, juice particle bursts, wall stains, dynamic glowing blade trail, and procedural audio effects.
  - Avoid Bombs, rack up multi-fruit combo streaks, and compete against saved high scores!
  - Closed Fist pauses the game; Open Palm resumes it.
- **🛡️ Failsafe & Emergency Stop**:
  - Dedicated hardware/software emergency stop shortcut (`[ESC]` key).
  - Automatic motion suspension when hand tracking is lost.
  - PyAutoGUI corner failsafe protection enabled.
- **🪄 Advanced Motion Smoothing**:
  - Exponential Moving Average (EMA) filtering removes physiological tremors and hand jitter.
  - Configurable deadzone radius suppresses involuntary micro-movements.
  - Active boundary box maps physical hand movements comfortably across all screen corners without awkward arm stretching.
- **🖥️ Modern CustomTkinter Dashboard**:
  - Dark mode with emerald green accents and cards.
  - Live webcam preview with glowing skeletal landmarks and HUD metrics.
  - Real-time telemetry: FPS counter, tracking confidence, active gesture badge, and connection status.
  - Live calibration sliders for sensitivity, pinch distance threshold, and click cooldown.

---

## 🖐️ Gesture Control Cheat Sheet

| Gesture | Visual | Action | Description |
|---|---|---|---|
| **Index finger only** | ☝️ | `Move Cursor` | Moves the cursor smoothly across the desktop screen |
| **Thumb + Index pinch** | 🤏 | `Left Click` | Single discrete left click (debounced) |
| **Thumb + Middle pinch** | ✌️ | `Right Click` | Right click to open context menus |
| **Index & Middle tips touch** | 👆+👆 | `Double Click` | Instant double click for folders and files |
| **Two fingers upright** | 🖖 | `Scroll Mode` | Move hand up or down to scroll documents and web pages |
| **Hold pinch (>0.45s)** | ⏳ | `Drag & Drop` | Holds left mouse down while pinched; releases when opened |
| **Closed fist** | ✊ | `Pause Control` | Freezes mouse cursor in place for reading or typing |
| **Open palm** | 🖐 | `Activate Control` | Re-enables cursor tracking and gesture input |
| **Thumb movement** | 👍 | `Volume Control` | Raise thumb to increase volume; lower to decrease |

---

## ⚙️ System Requirements

- **Operating System**: Windows 10/11, macOS 11+, or Linux (Ubuntu 20.04+).
- **Python**: Python 3.11 or compatible (tested with Python 3.11 - 3.14).
- **Webcam**: Any built-in or external USB webcam (720p 30fps recommended).
- **Hardware**: Standard x86_64 CPU with AVX support (MediaPipe / XNNPACK optimized).

---

## 🚀 Installation & Setup

### 1. Clone or Navigate to the Project Directory

```bash
cd GestureMouseAI
```

### 2. (Optional but Recommended) Create a Virtual Environment

```bash
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On macOS / Linux:
source venv/bin/activate
```

### 3. Install Dependencies

Install all verified packages:

```bash
pip install -r requirements.txt
```

*Required packages:*
- `opencv-python>=4.8.0`
- `mediapipe>=0.10.9`
- `pyautogui>=0.9.54`
- `customtkinter>=5.2.0`
- `pillow>=10.0.0`
- `numpy>=1.24.0`

---

## 🎮 How to Run

### Standard Launch

```bash
python main.py
```

### Launching Fruit Ninja Game Mode

You can launch Fruit Ninja directly or from inside the dashboard:

1. **From Dashboard**: Click the orange **`🎮 PLAY FRUIT NINJA`** button. The dashboard will automatically suspend virtual mouse operations, switch camera tracking to the game, and restore the dashboard cleanly when you return.
2. **Standalone Game Launch**:
```bash
python game/fruit_ninja.py
```

---

## 🧪 Running Automated Tests

Run the full test suite covering coordinate mapping, gesture classification, debouncing, UI lifecycle, and Fruit Ninja game physics:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

All 25 test cases will pass with `OK`.

---

## 🔧 Architecture & Modular Design

```
GestureMouseAI/
│
├── main.py                     # Application entrypoint & CLI argument parser
├── requirements.txt            # Locked and verified dependencies
├── README.md                   # Comprehensive documentation
│
├── modules/
│   ├── __init__.py             # Public module exports
│   ├── settings.py             # Dataclass holding configurable thresholds & screen metrics
│   ├── hand_tracker.py         # MediaPipe pipeline with dual Tasks/Solutions compatibility
│   ├── gesture_recognition.py  # 9-gesture geometric classifier, debounce filter & state machine
│   └── mouse_controller.py     # Screen mapping, EMA smoothing, and PyAutoGUI execution
│
├── ui/
│   ├── __init__.py             # UI module exports
│   ├── dashboard.py            # CustomTkinter dashboard window & webcam worker thread
│   └── components.py           # Reusable telemetry cards, sliders, and badges
│
├── models/
│   └── hand_landmarker.task    # MediaPipe hand landmark detection model (LiteRT/XNNPACK)
│
├── assets/
│   └── icons/
│       └── app_icon.png        # Application desktop window icon
│
└── tests/
    ├── test_gestures.py        # Unit tests for gesture logic & coordinates
    └── test_ui_app.py          # Integration tests for CustomTkinter GUI lifecycle
```

---

## 💡 Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| **"No Device" / Webcam not showing** | Camera is in use by Zoom, Teams, or another app | Close competing camera apps, verify camera permissions in Windows Settings, or launch with `--camera 1`. |
| **Cursor jitter / shaky movement** | Camera lighting is low or smoothing is low | Increase the **Smoothing** slider in the UI to `0.70`+ and ensure adequate lighting. |
| **Accidental clicks** | Hand is moving too close or threshold is high | Lower the **Pinch Distance Threshold** slider or increase **Click Cooldown**. |
| **Cursor stops moving suddenly** | PyAutoGUI Failsafe triggered by corner hit or `[ESC]` pressed | Toggle the **Virtual Mouse Control** switch back to `ACTIVE`, or press Open Palm gesture. |

---

## 🔮 Future Improvements

- [ ] Support multi-hand gestures (two hands for pinch-to-zoom and canvas rotation).
- [ ] User custom gesture recording / few-shot gesture training.
- [ ] Eye-gaze assisted cursor aiming for enhanced precision.
- [ ] Tray minimization mode with background overlay notifications.
