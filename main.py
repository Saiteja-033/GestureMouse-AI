"""
GestureMouse AI - Main Application Entrypoint
AI-Powered Hand Gesture Controlled Virtual Mouse.
"""

import sys
import argparse
from modules.settings import AppSettings
from ui.dashboard import DashboardApp


def main():
    parser = argparse.ArgumentParser(description="GestureMouse AI - Hand Gesture Controlled Virtual Mouse")
    parser.add_argument("--camera", type=int, default=0, help="Webcam device index (default: 0)")
    parser.add_argument("--sensitivity", type=float, default=1.3, help="Cursor sensitivity multiplier")
    parser.add_argument("--smoothing", type=float, default=0.65, help="Smoothing factor (0.1 to 0.95)")
    args = parser.parse_args()

    # Initialize configuration
    settings = AppSettings(
        camera_index=args.camera,
        cursor_sensitivity=args.sensitivity,
        smoothing_factor=args.smoothing,
    )

    print("=" * 60)
    print("  GestureMouse AI - Virtual Mouse System Initializing")
    print(f"  • Screen Resolution: {settings.screen_width} x {settings.screen_height}")
    print(f"  • Camera Index: {settings.camera_index}")
    print(f"  • Sensitivity: {settings.cursor_sensitivity}x")
    print("  • Emergency Stop Shortcut: Press [ESC] at any time")
    print("=" * 60)

    try:
        app = DashboardApp(settings=settings)
        app.mainloop()
    except KeyboardInterrupt:
        print("\n[GestureMouse AI] Interrupted by user. Exiting cleanly...")
    except Exception as e:
        print(f"[GestureMouse AI Error]: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
