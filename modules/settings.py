"""
GestureMouse AI - Settings & Configuration
Manages runtime configuration, thresholds, and calibration parameters.
"""

from dataclasses import dataclass, field
import pyautogui

@dataclass
class AppSettings:
    # Camera settings
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    target_fps: int = 30

    # Screen dimensions (dynamic)
    screen_width: int = field(default_factory=lambda: pyautogui.size()[0] if pyautogui else 1920)
    screen_height: int = field(default_factory=lambda: pyautogui.size()[1] if pyautogui else 1080)

    # Mouse cursor movement & smoothing
    mouse_control_enabled: bool = True
    cursor_sensitivity: float = 1.3
    smoothing_factor: float = 0.65  # Higher = smoother, lower = more responsive (0.1 - 0.95)
    deadzone_radius: float = 2.0     # Ignore movements under this distance to eliminate hand jitter
    
    # Active interaction boundary (margins from webcam frame edges)
    # Allows the user to reach all 4 screen corners without stretching hand to camera edges
    boundary_margin_x: int = 100
    boundary_margin_y: int = 80

    # Gesture thresholds (in normalized hand units, where 1.0 = wrist to middle-MCP distance)
    # Alternatively pixel thresholds calibrated to 640x480 frame
    pinch_threshold: float = 38.0             # Distance for Thumb + Index pinch
    right_click_threshold: float = 38.0       # Distance for Thumb + Middle pinch
    double_click_threshold: float = 35.0      # Distance between Index tip & Middle tip
    drag_hold_duration: float = 0.45          # Seconds to hold pinch before entering Drag & Drop
    
    # Cooldown & debounce
    click_cooldown: float = 0.35              # Minimum time between successive discrete clicks (seconds)
    double_click_cooldown: float = 0.55
    scroll_cooldown: float = 0.05             # Rate limiter for scroll events
    scroll_sensitivity: float = 1.8           # Multiplier for vertical finger motion to scroll steps
    scroll_deadzone: float = 6.0              # Min vertical delta before scrolling

    # Hand tracking parameters
    min_detection_confidence: float = 0.70
    min_tracking_confidence: float = 0.70
    max_num_hands: int = 1

    # Safety
    emergency_stop_key: str = "Escape"
    pyautogui_failsafe: bool = True

    def reset_defaults(self):
        """Reset all adjustable settings back to factory defaults."""
        self.cursor_sensitivity = 1.3
        self.smoothing_factor = 0.65
        self.pinch_threshold = 38.0
        self.click_cooldown = 0.35
        self.mouse_control_enabled = True
