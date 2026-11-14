"""
GestureMouse AI - Mouse Controller Module
Handles mapping of hand coordinates to screen coordinates, motion smoothing,
click actions, drag-and-drop, and scrolling with failsafes.
"""

import time
import math
from typing import Tuple, Optional, Dict, Any
import pyautogui
from modules.gesture_recognition import GestureType

# Minimize PyAutoGUI internal delay for high-frequency real-time response
pyautogui.PAUSE = 0.001
pyautogui.FAILSAFE = True


class MouseController:
    """
    Translates computer vision landmarks and recognized gestures into responsive,
    jitter-free desktop mouse operations.
    """

    def __init__(self, settings):
        self.settings = settings
        
        # Screen dimensions
        self.screen_w, self.screen_h = pyautogui.size()
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
        Clamps to screen dimensions.
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

        return target_x, target_y

    def smooth_cursor(self, target_x: float, target_y: float) -> Tuple[int, int]:
        """
        Applies Exponential Moving Average (EMA) and deadzone filtering
        to eliminate physiological hand jitter and cursor shaking.
        """
        dist = math.hypot(target_x - self.curr_x, target_y - self.curr_y)
        
        # Deadzone: ignore sub-pixel / micro jitter
        if dist < self.settings.deadzone_radius:
            return int(self.curr_x), int(self.curr_y)

        # Smoothing factor: 0.0 = instant, near 1.0 = heavy smoothing
        alpha = max(0.05, min(0.95, self.settings.smoothing_factor))
        self.curr_x = self.curr_x * alpha + target_x * (1.0 - alpha)
        self.curr_y = self.curr_y * alpha + target_y * (1.0 - alpha)

        return int(self.curr_x), int(self.curr_y)

    def execute_action(
        self,
        gesture: GestureType,
        hand_info: Optional[Dict[str, Any]],
        metrics: Dict[str, Any],
    ) -> None:
        """
        Main execution pipeline for mouse actions corresponding to the recognized gesture.
        """
        # Master killswitch or paused state
        if not self.settings.mouse_control_enabled or gesture == GestureType.PAUSE:
            self._ensure_mouse_up()
            self.prev_gesture = gesture
            return

        # If tracking lost, safely release drag
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
            # 1. Cursor Movement & Dragging
            if gesture in (GestureType.MOVE_MOUSE, GestureType.DRAG_AND_DROP, GestureType.LEFT_CLICK):
                target_x, target_y = self.map_coordinates(index_tip, frame_size)
                smooth_x, smooth_y = self.smooth_cursor(target_x, target_y)
                pyautogui.moveTo(smooth_x, smooth_y)

            # 2. Drag & Drop handling
            if gesture == GestureType.DRAG_AND_DROP:
                if not self.is_mouse_down:
                    pyautogui.mouseDown(button="left")
                    self.is_mouse_down = True
            else:
                self._ensure_mouse_up()

            # 3. Left Click (Single discrete click with cooldown & state edge detection)
            if gesture == GestureType.LEFT_CLICK:
                # Trigger click only on transition into LEFT_CLICK or when cooldown elapsed
                if self.prev_gesture != GestureType.LEFT_CLICK:
                    if (now - self.last_left_click_time) >= self.settings.click_cooldown:
                        pyautogui.click(button="left")
                        self.last_left_click_time = now

            # 4. Right Click
            elif gesture == GestureType.RIGHT_CLICK:
                if self.prev_gesture != GestureType.RIGHT_CLICK:
                    if (now - self.last_right_click_time) >= self.settings.click_cooldown:
                        pyautogui.click(button="right")
                        self.last_right_click_time = now

            # 5. Double Click
            elif gesture == GestureType.DOUBLE_CLICK:
                if self.prev_gesture != GestureType.DOUBLE_CLICK:
                    if (now - self.last_double_click_time) >= self.settings.double_click_cooldown:
                        pyautogui.doubleClick(button="left")
                        self.last_double_click_time = now

            # 6. Scroll Mode
            elif gesture == GestureType.SCROLL_MODE:
                # Average Y of index and middle finger tips
                mid_y = (lm[8][1] + lm[12][1]) / 2.0
                if self.prev_scroll_y is not None:
                    delta_y = mid_y - self.prev_scroll_y
                    if abs(delta_y) > self.settings.scroll_deadzone:
                        if (now - self.last_scroll_time) >= self.settings.scroll_cooldown:
                            # Moving fingers DOWN in camera -> scroll down (negative)
                            # Moving fingers UP in camera -> scroll up (positive)
                            scroll_amount = int(-delta_y * self.settings.scroll_sensitivity)
                            if scroll_amount != 0:
                                pyautogui.scroll(scroll_amount)
                                self.last_scroll_time = now
                self.prev_scroll_y = mid_y
            else:
                self.prev_scroll_y = None

            # 7. Volume Control (Optional gesture)
            if gesture == GestureType.VOLUME_CONTROL:
                thumb_y = lm[4][1]
                if self.prev_thumb_y is not None:
                    delta_thumb_y = thumb_y - self.prev_thumb_y
                    if (now - self.last_volume_time) >= 0.18:
                        if delta_thumb_y < -12:  # Moving thumb up
                            pyautogui.press("volumeup")
                            self.last_volume_time = now
                        elif delta_thumb_y > 12:  # Moving thumb down
                            pyautogui.press("volumedown")
                            self.last_volume_time = now
                self.prev_thumb_y = thumb_y
            else:
                self.prev_thumb_y = None

        except pyautogui.FailSafeException:
            # Emergency failsafe triggered by hitting the corner of screen
            self.settings.mouse_control_enabled = False
            self._ensure_mouse_up()
        except Exception:
            # Defensively catch any system OS mouse failure without crashing the app
            pass

        self.prev_gesture = gesture

    def _ensure_mouse_up(self):
        """Releases the mouse button if held down during drag mode."""
        if self.is_mouse_down:
            try:
                pyautogui.mouseUp(button="left")
            except Exception:
                pass
            self.is_mouse_down = False

    def emergency_stop(self):
        """Immediately abort all mouse operations and disable mouse control."""
        self.settings.mouse_control_enabled = False
        self._ensure_mouse_up()
        self.prev_scroll_y = None
        self.prev_thumb_y = None
