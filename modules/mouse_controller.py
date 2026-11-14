"""
GestureMouse AI - Mouse Controller Module
Handles mapping of hand coordinates to screen coordinates, velocity-adaptive smoothing,
click actions, drag-and-drop, and scrolling with failsafes.
"""

import sys
import time
import math
from typing import Tuple, Optional, Dict, Any
import pyautogui
from modules.gesture_recognition import GestureType

# Ensure PyAutoGUI doesn't throw FailSafeException on screen edges
pyautogui.PAUSE = 0.001
pyautogui.FAILSAFE = False

# Native Windows cursor API for zero-latency, high-precision cursor control
IS_WINDOWS = sys.platform == "win32"
if IS_WINDOWS:
    import ctypes
    user32 = ctypes.windll.user32


class MouseController:
    """
    Translates computer vision landmarks and recognized gestures into responsive,
    jitter-free desktop mouse operations.
    """

    def __init__(self, settings):
        self.settings = settings
        
        # Screen dimensions
        try:
            self.screen_w, self.screen_h = pyautogui.size()
        except Exception:
            self.screen_w, self.screen_h = 1920, 1080

        self.settings.screen_width = self.screen_w
        self.settings.screen_height = self.screen_h

        # Cursor position tracking for smoothing
        self.curr_x: float = self.screen_w / 2.0
        self.curr_y: float = self.screen_h / 2.0
        
        # Action state management
        self.is_mouse_down: bool = False
        self.last_left_click_time: float = 0.0
        self.last_right_click_time: float = 0.0
        self.last_double_click_time: float = 0.0
        self.last_scroll_time: float = 0.0
        self.last_volume_time: float = 0.0
        
        # Previous gesture to detect transition edges
        self.prev_gesture: GestureType = GestureType.NONE
        
        # Scroll tracking
        self.prev_scroll_y: Optional[float] = None
        self.prev_thumb_y: Optional[float] = None

    def map_coordinates(
        self,
        point: Tuple[int, int],
        frame_size: Tuple[int, int],
    ) -> Tuple[float, float]:
        """
        Maps fingertip coordinates within the frame boundary to screen pixel coordinates.
        Clamps to screen dimensions with safety margins.
        """
        frame_w, frame_h = frame_size
        px, py = point

        margin_x = self.settings.boundary_margin_x
        margin_y = self.settings.boundary_margin_y

        # Active boundary width and height
        active_w = max(10, frame_w - 2 * margin_x)
        active_h = max(10, frame_h - 2 * margin_y)

        # Normalized coordinates relative to active boundary (0.0 to 1.0)
        norm_x = (px - margin_x) / float(active_w)
        norm_y = (py - margin_y) / float(active_h)

        # Clamp normalized coordinates to stay inside screen bounds
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))

        # Apply sensitivity multiplier anchored at center
        sens = self.settings.cursor_sensitivity
        norm_x = (norm_x - 0.5) * sens + 0.5
        norm_y = (norm_y - 0.5) * sens + 0.5

        # Re-clamp
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))

        target_x = norm_x * (self.screen_w - 1)
        target_y = norm_y * (self.screen_h - 1)

        # Clamp inside screen coordinates to prevent boundary lock
        target_x = max(2.0, min(float(self.screen_w - 3), target_x))
        target_y = max(2.0, min(float(self.screen_h - 3), target_y))

        return target_x, target_y

    def smooth_cursor(self, target_x: float, target_y: float) -> Tuple[int, int]:
        """
        Velocity-adaptive smoothing:
        - When moving rapidly: responsive (low latency).
        - When hovering or moving slowly: heavy smoothing to suppress physiological tremors.
        """
        dist = math.hypot(target_x - self.curr_x, target_y - self.curr_y)
        
        # Deadzone: ignore sub-pixel / micro jitter
        if dist < self.settings.deadzone_radius:
            return int(self.curr_x), int(self.curr_y)

        # Dynamic velocity-adaptive smoothing factor
        if dist > 60:
            alpha = 0.22  # Rapid movement: low latency
        elif dist > 25:
            alpha = 0.40  # Moderate movement
        else:
            alpha = max(0.40, min(0.85, self.settings.smoothing_factor))

        self.curr_x = self.curr_x * alpha + target_x * (1.0 - alpha)
        self.curr_y = self.curr_y * alpha + target_y * (1.0 - alpha)

        return int(self.curr_x), int(self.curr_y)

    def _move_cursor(self, x: int, y: int):
        """Moves OS cursor using fast win32 SetCursorPos or PyAutoGUI."""
        clamped_x = max(2, min(self.screen_w - 3, int(x)))
        clamped_y = max(2, min(self.screen_h - 3, int(y)))
        
        if IS_WINDOWS:
            try:
                user32.SetCursorPos(clamped_x, clamped_y)
                return
            except Exception:
                pass
        
        try:
            pyautogui.moveTo(clamped_x, clamped_y)
        except Exception:
            pass

    def _left_click(self):
        """Performs discrete left click."""
        if IS_WINDOWS:
            try:
                user32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
                time.sleep(0.015)
                user32.mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP
                return
            except Exception:
                pass
        try:
            pyautogui.click(button="left")
        except Exception:
            pass

    def _right_click(self):
        """Performs discrete right click."""
        if IS_WINDOWS:
            try:
                user32.mouse_event(0x0008, 0, 0, 0, 0)  # MOUSEEVENTF_RIGHTDOWN
                time.sleep(0.015)
                user32.mouse_event(0x0010, 0, 0, 0, 0)  # MOUSEEVENTF_RIGHTUP
                return
            except Exception:
                pass
        try:
            pyautogui.click(button="right")
        except Exception:
            pass

    def _double_click(self):
        """Performs double click."""
        self._left_click()
        time.sleep(0.05)
        self._left_click()

    def _mouse_down(self):
        """Presses and holds left mouse button down."""
        if not self.is_mouse_down:
            if IS_WINDOWS:
                try:
                    user32.mouse_event(0x0002, 0, 0, 0, 0)
                    self.is_mouse_down = True
                    return
                except Exception:
                    pass
            try:
                pyautogui.mouseDown(button="left")
            except Exception:
                pass
            self.is_mouse_down = True

    def _ensure_mouse_up(self):
        """Releases the mouse button if held down during drag mode."""
        if self.is_mouse_down:
            if IS_WINDOWS:
                try:
                    user32.mouse_event(0x0004, 0, 0, 0, 0)
                    self.is_mouse_down = False
                    return
                except Exception:
                    pass
            try:
                pyautogui.mouseUp(button="left")
            except Exception:
                pass
            self.is_mouse_down = False

    def execute_action(
        self,
        gesture: GestureType,
        hand_info: Optional[Dict[str, Any]],
        metrics: Dict[str, Any],
    ) -> None:
        """
        Main execution pipeline for mouse actions corresponding to the recognized gesture.
        """
        # 1. Open Palm gesture: re-activates mouse control if paused
        if gesture == GestureType.ACTIVATE:
            self.settings.mouse_control_enabled = True

        # 2. Closed Fist gesture: pauses mouse control
        if gesture == GestureType.PAUSE:
            self.settings.mouse_control_enabled = False
            self._ensure_mouse_up()
            self.prev_gesture = gesture
            return

        # 3. If mouse control is disabled or tracking is lost, safely ensure mouse is up
        if not self.settings.mouse_control_enabled:
            self._ensure_mouse_up()
            self.prev_gesture = gesture
            return

        if hand_info is None:
            self._ensure_mouse_up()
            self.prev_gesture = GestureType.NONE
            return

        now = time.time()
        lm = hand_info["pixel_landmarks"]
        frame_size = hand_info["frame_size"]

        # Finger index tip (index 8) is primary cursor reference
        index_tip = lm[8]

        try:
            # A. Cursor Movement & Dragging
            if gesture in (GestureType.MOVE_MOUSE, GestureType.DRAG_AND_DROP, GestureType.LEFT_CLICK):
                target_x, target_y = self.map_coordinates(index_tip, frame_size)
                smooth_x, smooth_y = self.smooth_cursor(target_x, target_y)
                self._move_cursor(smooth_x, smooth_y)

            # B. Drag & Drop handling
            if gesture == GestureType.DRAG_AND_DROP:
                self._mouse_down()
            else:
                self._ensure_mouse_up()

            # C. Left Click (Single discrete click with cooldown & state edge detection)
            if gesture == GestureType.LEFT_CLICK:
                if self.prev_gesture != GestureType.LEFT_CLICK:
                    if (now - self.last_left_click_time) >= self.settings.click_cooldown:
                        self._left_click()
                        self.last_left_click_time = now

            # D. Right Click
            elif gesture == GestureType.RIGHT_CLICK:
                if self.prev_gesture != GestureType.RIGHT_CLICK:
                    if (now - self.last_right_click_time) >= self.settings.click_cooldown:
                        self._right_click()
                        self.last_right_click_time = now

            # E. Double Click
            elif gesture == GestureType.DOUBLE_CLICK:
                if self.prev_gesture != GestureType.DOUBLE_CLICK:
                    if (now - self.last_double_click_time) >= self.settings.double_click_cooldown:
                        self._double_click()
                        self.last_double_click_time = now

            # F. Scroll Mode
            elif gesture == GestureType.SCROLL_MODE:
                mid_y = (lm[8][1] + lm[12][1]) / 2.0
                if self.prev_scroll_y is not None:
                    delta_y = mid_y - self.prev_scroll_y
                    if abs(delta_y) > self.settings.scroll_deadzone:
                        if (now - self.last_scroll_time) >= self.settings.scroll_cooldown:
                            scroll_amount = int(-delta_y * self.settings.scroll_sensitivity)
                            if scroll_amount != 0:
                                try:
                                    pyautogui.scroll(scroll_amount)
                                except Exception:
                                    pass
                                self.last_scroll_time = now
                self.prev_scroll_y = mid_y
            else:
                self.prev_scroll_y = None

            # G. Volume Control
            if gesture == GestureType.VOLUME_CONTROL:
                thumb_y = lm[4][1]
                if self.prev_thumb_y is not None:
                    delta_thumb_y = thumb_y - self.prev_thumb_y
                    if (now - self.last_volume_time) >= 0.18:
                        if delta_thumb_y < -12:
                            try:
                                pyautogui.press("volumeup")
                            except Exception:
                                pass
                            self.last_volume_time = now
                        elif delta_thumb_y > 12:
                            try:
                                pyautogui.press("volumedown")
                            except Exception:
                                pass
                            self.last_volume_time = now
                self.prev_thumb_y = thumb_y
            else:
                self.prev_thumb_y = None

        except Exception:
            pass

        self.prev_gesture = gesture

    def emergency_stop(self):
        """Immediately abort all mouse operations and disable mouse control."""
        self.settings.mouse_control_enabled = False
        self._ensure_mouse_up()
        self.prev_scroll_y = None
        self.prev_thumb_y = None
