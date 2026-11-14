"""
GestureMouse AI - Comprehensive Test Suite
Validates landmark detection, gesture classification, coordinate mapping, smoothing,
drag-and-drop state machine, and safety failsafes.
"""

import os
import sys
import time
import unittest
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.settings import AppSettings
from modules.gesture_recognition import GestureRecognizer, GestureType
from modules.mouse_controller import MouseController
from modules.hand_tracker import HandTracker


def create_mock_hand_landmarks(
    thumb_tip=(200, 300),
    index_tip=(250, 150),
    middle_tip=(300, 140),
    ring_tip=(350, 160),
    pinky_tip=(400, 180),
    fingers_curled=False,
):
    """
    Constructs a 21-landmark array in pixel coordinates for deterministic testing.
    Standard Hand Landmark indices:
      0: Wrist
      1-4: Thumb (CMC, MCP, IP, Tip)
      5-8: Index (MCP, PIP, DIP, Tip)
      9-12: Middle (MCP, PIP, DIP, Tip)
      13-16: Ring (MCP, PIP, DIP, Tip)
      17-20: Pinky (MCP, PIP, DIP, Tip)
    """
    lm = [(0, 0)] * 21
    lm[0] = (300, 420)  # Wrist

    # Thumb
    lm[1] = (260, 380)
    lm[2] = (240, 350)
    lm[3] = (220, 320)
    lm[4] = thumb_tip

    # Index finger
    lm[5] = (270, 280)  # MCP
    lm[6] = (265, 230)  # PIP
    lm[7] = (260, 190)  # DIP
    if fingers_curled:
        lm[8] = (270, 320)  # Curled below PIP
    else:
        lm[8] = index_tip   # Extended above PIP

    # Middle finger
    lm[9] = (300, 270)   # MCP
    lm[10] = (300, 220)  # PIP
    lm[11] = (300, 180)  # DIP
    if fingers_curled:
        lm[12] = (300, 320)
    else:
        lm[12] = middle_tip

    # Ring finger
    lm[13] = (330, 280)  # MCP
    lm[14] = (335, 230)  # PIP
    lm[15] = (340, 190)  # DIP
    if fingers_curled:
        lm[16] = (330, 320)
    else:
        lm[16] = ring_tip

    # Pinky finger
    lm[17] = (360, 300)  # MCP
    lm[18] = (365, 260)  # PIP
    lm[19] = (370, 220)  # DIP
    if fingers_curled:
        lm[20] = (360, 330)
    else:
        lm[20] = pinky_tip

    return {
        "pixel_landmarks": lm,
        "norm_landmarks": [(x / 640.0, y / 480.0, 0.0) for x, y in lm],
        "handedness": "Right",
        "confidence": 0.95,
        "hand_scale": 120.0,
        "bbox": (180, 120, 420, 440),
        "frame_size": (640, 480),
    }


class TestGestureMouseAI(unittest.TestCase):

    def setUp(self):
        self.settings = AppSettings()
        self.settings.mouse_control_enabled = False  # Keep disabled during automated tests
        self.recognizer = GestureRecognizer(self.settings)
        self.controller = MouseController(self.settings)

    def test_settings_defaults_and_reset(self):
        """Verify configuration initialization and reset behavior."""
        self.settings.cursor_sensitivity = 2.8
        self.settings.pinch_threshold = 55.0
        self.settings.reset_defaults()
        self.assertEqual(self.settings.cursor_sensitivity, 1.3)
        self.assertEqual(self.settings.pinch_threshold, 38.0)

    def test_coordinate_mapping(self):
        """Verify mapping of frame coordinates to screen coordinates."""
        # Top-left boundary point
        pt_tl = (self.settings.boundary_margin_x, self.settings.boundary_margin_y)
        sx, sy = self.controller.map_coordinates(pt_tl, (640, 480))
        self.assertGreaterEqual(sx, 0.0)
        self.assertGreaterEqual(sy, 0.0)

        # Center point
        pt_center = (320, 240)
        cx, cy = self.controller.map_coordinates(pt_center, (640, 480))
        expected_cx = self.settings.screen_width / 2.0
        expected_cy = self.settings.screen_height / 2.0
        self.assertAlmostEqual(cx, expected_cx, delta=10.0)
        self.assertAlmostEqual(cy, expected_cy, delta=10.0)

    def test_cursor_smoothing_and_deadzone(self):
        """Verify that micro-movements inside deadzone are suppressed."""
        self.controller.curr_x = 500.0
        self.controller.curr_y = 500.0
        
        # Sub-deadzone movement (1 pixel away)
        sm_x, sm_y = self.controller.smooth_cursor(501.0, 500.5)
        self.assertEqual(sm_x, 500)
        self.assertEqual(sm_y, 500)

        # Large movement should interpolate smoothly
        target_x, target_y = 600.0, 600.0
        sm_x2, sm_y2 = self.controller.smooth_cursor(target_x, target_y)
        # Position should move towards target but not jump completely
        self.assertGreater(sm_x2, 500)
        self.assertLess(sm_x2, 600)

    def test_gesture_move_cursor(self):
        """Test index finger only extended recognized as MOVE_MOUSE."""
        hand = create_mock_hand_landmarks(
            thumb_tip=(240, 340),  # Tucked thumb
            index_tip=(260, 140),  # Index extended up
            middle_tip=(300, 320), # Middle curled
            ring_tip=(330, 320),   # Ring curled
            pinky_tip=(360, 330),  # Pinky curled
        )
        # Need 2 steps to satisfy history stabilization
        self.recognizer.recognize(hand)
        gesture, _ = self.recognizer.recognize(hand)
        self.assertEqual(gesture, GestureType.MOVE_MOUSE)

    def test_gesture_left_click(self):
        """Test thumb and index pinch below threshold triggers LEFT_CLICK."""
        # Index tip and thumb tip positioned very close together (15px apart)
        hand = create_mock_hand_landmarks(
            thumb_tip=(250, 195),
            index_tip=(255, 190),
            middle_tip=(300, 320),
            ring_tip=(330, 320),
            pinky_tip=(360, 330),
        )
        self.recognizer.recognize(hand)
        gesture, _ = self.recognizer.recognize(hand)
        self.assertEqual(gesture, GestureType.LEFT_CLICK)

    def test_gesture_right_click(self):
        """Test thumb and middle finger pinch triggers RIGHT_CLICK."""
        hand = create_mock_hand_landmarks(
            thumb_tip=(295, 185),
            index_tip=(220, 140), # Index away
            middle_tip=(300, 190),# Middle touching thumb (dist ~7px)
            ring_tip=(330, 320),
            pinky_tip=(360, 330),
        )
        self.recognizer.recognize(hand)
        gesture, _ = self.recognizer.recognize(hand)
        self.assertEqual(gesture, GestureType.RIGHT_CLICK)

    def test_gesture_double_click(self):
        """Test index tip and middle tip touching together triggers DOUBLE_CLICK."""
        hand = create_mock_hand_landmarks(
            thumb_tip=(220, 340),
            index_tip=(275, 150),
            middle_tip=(285, 150), # 10px from index tip
            ring_tip=(330, 320),
            pinky_tip=(360, 330),
        )
        self.recognizer.recognize(hand)
        gesture, _ = self.recognizer.recognize(hand)
        self.assertEqual(gesture, GestureType.DOUBLE_CLICK)

    def test_gesture_closed_fist(self):
        """Test all fingers curled triggers PAUSE."""
        hand = create_mock_hand_landmarks(
            thumb_tip=(240, 350),
            index_tip=(270, 320),
            middle_tip=(300, 320),
            ring_tip=(330, 320),
            pinky_tip=(360, 330),
            fingers_curled=True,
        )
        self.recognizer.recognize(hand)
        gesture, _ = self.recognizer.recognize(hand)
        self.assertEqual(gesture, GestureType.PAUSE)

    def test_gesture_open_palm(self):
        """Test all fingers extended triggers ACTIVATE."""
        hand = create_mock_hand_landmarks(
            thumb_tip=(180, 270),  # Spread thumb
            index_tip=(250, 140),
            middle_tip=(300, 130),
            ring_tip=(350, 140),
            pinky_tip=(400, 160),
            fingers_curled=False,
        )
        self.recognizer.recognize(hand)
        gesture, _ = self.recognizer.recognize(hand)
        self.assertEqual(gesture, GestureType.ACTIVATE)

    def test_gesture_scroll_mode(self):
        """Test index and middle fingers extended apart triggers SCROLL_MODE."""
        hand = create_mock_hand_landmarks(
            thumb_tip=(220, 340),
            index_tip=(240, 140),
            middle_tip=(310, 140), # 70px apart (> double click threshold)
            ring_tip=(330, 320),
            pinky_tip=(360, 330),
        )
        self.recognizer.recognize(hand)
        gesture, _ = self.recognizer.recognize(hand)
        self.assertEqual(gesture, GestureType.SCROLL_MODE)

    def test_gesture_drag_and_drop_transition(self):
        """Test that holding a pinch beyond drag_hold_duration transitions to DRAG_AND_DROP."""
        self.settings.drag_hold_duration = 0.05  # Shorten for testing
        hand = create_mock_hand_landmarks(
            thumb_tip=(250, 195),
            index_tip=(255, 190),
            middle_tip=(300, 320),
            ring_tip=(330, 320),
            pinky_tip=(360, 330),
        )
        # First frame initializes pinch_start_time
        self.recognizer.recognize(hand)
        time.sleep(0.06)
        # Second frame after delay
        gesture, metrics = self.recognizer.recognize(hand)
        self.assertEqual(gesture, GestureType.DRAG_AND_DROP)
        self.assertTrue(metrics["is_dragging"])

    def test_failsafe_and_emergency_stop(self):
        """Verify emergency stop resets mouse down and disables mouse control."""
        self.controller.is_mouse_down = True
        self.settings.mouse_control_enabled = True
        self.controller.emergency_stop()
        self.assertFalse(self.settings.mouse_control_enabled)
        self.assertFalse(self.controller.is_mouse_down)

    def test_hand_tracker_blank_frame(self):
        """Verify hand tracker safely handles blank image without crashing."""
        tracker = HandTracker()
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_out, hand_info = tracker.process_frame(blank_frame, draw=True)
        self.assertIsNotNone(frame_out)
        self.assertIsNone(hand_info)
        tracker.release()


if __name__ == "__main__":
    unittest.main()
