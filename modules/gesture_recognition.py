"""
GestureMouse AI - Gesture Recognition Module
Analyzes hand landmarks, recognizes gestures in real-time, and manages gesture states.
"""

import math
import time
from enum import Enum
from typing import Dict, Any, List, Tuple, Optional
import numpy as np


class GestureType(Enum):
    NONE = "None"
    MOVE_MOUSE = "Move Cursor"
    LEFT_CLICK = "Left Click"
    RIGHT_CLICK = "Right Click"
    DOUBLE_CLICK = "Double Click"
    SCROLL_MODE = "Scroll Mode"
    DRAG_AND_DROP = "Drag & Drop"
    PAUSE = "Paused (Fist)"
    ACTIVATE = "Active (Palm)"
    VOLUME_CONTROL = "Volume Control"


class GestureRecognizer:
    """
    Robust gesture classification using landmark geometry, relative distance scaling,
    and temporal hysteresis.
    """

    def __init__(self, settings):
        self.settings = settings
        self.current_gesture = GestureType.NONE
        self.previous_gesture = GestureType.NONE
        
        # Timing and state machines
        self.pinch_start_time: Optional[float] = None
        self.is_dragging: bool = False
        self.last_click_time: float = 0.0
        self.last_double_click_time: float = 0.0
        self.last_right_click_time: float = 0.0
        self.last_scroll_time: float = 0.0
        
        # Debounce filter
        self.gesture_history: List[GestureType] = []
        self.history_size: int = 3

    def euclidean_dist(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """Euclidean distance between two 2D points in pixels."""
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def detect_fingers_up(self, lm: List[Tuple[int, int]], handedness: str = "Right") -> List[bool]:
        """
        Determines which of the 5 fingers are extended [thumb, index, middle, ring, pinky].
        Combines vertical coordinate comparisons and radial distance from wrist for robust detection
        in any hand orientation (upright, tilted, forward).
        """
        fingers = []
        wrist = lm[0]

        # Thumb: compare tip (4) to IP (3) and distance from pinky MCP (17)
        dist_thumb_pinky = self.euclidean_dist(lm[4], lm[17])
        dist_ip_pinky = self.euclidean_dist(lm[3], lm[17])
        dist_thumb_wrist = self.euclidean_dist(lm[4], wrist)
        dist_ip_wrist = self.euclidean_dist(lm[3], wrist)
        # Extended outward or extended away from wrist
        is_thumb_up = (dist_thumb_pinky > dist_ip_pinky * 1.15) or (dist_thumb_wrist > dist_ip_wrist * 1.15)
        fingers.append(is_thumb_up)

        # 4 Fingers: Index (8), Middle (12), Ring (16), Pinky (20)
        tip_ids = [8, 12, 16, 20]
        pip_ids = [6, 10, 14, 18]
        mcp_ids = [5, 9, 13, 17]

        for tip, pip, mcp in zip(tip_ids, pip_ids, mcp_ids):
            # 1. Vertical orientation check
            vert_extended = (lm[tip][1] < lm[pip][1]) and (lm[tip][1] < lm[mcp][1])
            # 2. Radial distance from wrist (invariant to hand rotation / pointing at screen)
            dist_tip_wrist = self.euclidean_dist(lm[tip], wrist)
            dist_pip_wrist = self.euclidean_dist(lm[pip], wrist)
            radial_extended = dist_tip_wrist > (dist_pip_wrist * 1.12)
            
            is_extended = vert_extended or radial_extended
            fingers.append(is_extended)

        return fingers

    def recognize(self, hand_info: Optional[Dict[str, Any]]) -> Tuple[GestureType, Dict[str, Any]]:
        """
        Classifies hand gesture from hand_info dictionary.
        Returns:
            gesture: Classified GestureType
            metrics: Dictionary of calculated distances and states
        """
        current_time = time.time()
        metrics: Dict[str, Any] = {
            "dist_thumb_index": 0.0,
            "dist_thumb_middle": 0.0,
            "dist_index_middle": 0.0,
            "fingers_up": [False] * 5,
            "is_dragging": self.is_dragging,
            "pinch_duration": 0.0,
        }

        if hand_info is None:
            # Tracking lost -> if we were dragging, cleanly release
            if self.is_dragging:
                self.is_dragging = False
            self.pinch_start_time = None
            self.current_gesture = GestureType.NONE
            return GestureType.NONE, metrics

        lm = hand_info["pixel_landmarks"]
        scale = hand_info.get("hand_scale", 100.0)
        handedness = hand_info.get("handedness", "Right")

        # Key landmark points
        thumb_tip = lm[4]
        index_tip = lm[8]
        middle_tip = lm[12]
        ring_tip = lm[16]
        pinky_tip = lm[20]

        # Calculate distances
        dist_ti = self.euclidean_dist(thumb_tip, index_tip)
        dist_tm = self.euclidean_dist(thumb_tip, middle_tip)
        dist_im = self.euclidean_dist(index_tip, middle_tip)

        metrics["dist_thumb_index"] = dist_ti
        metrics["dist_thumb_middle"] = dist_tm
        metrics["dist_index_middle"] = dist_im

        # Detect extended fingers: [thumb, index, middle, ring, pinky]
        fingers = self.detect_fingers_up(lm, handedness)
        metrics["fingers_up"] = fingers

        thumb_up, index_up, middle_up, ring_up, pinky_up = fingers
        num_fingers_up = sum(fingers)

        # Scale thresholds dynamically relative to hand distance (optional normalization)
        # Using configured base thresholds with sensible ratio
        pinch_thresh = self.settings.pinch_threshold
        right_click_thresh = self.settings.right_click_threshold
        double_click_thresh = self.settings.double_click_threshold

        raw_gesture = GestureType.NONE

        # 1. Closed Fist -> PAUSE
        if num_fingers_up == 0:
            raw_gesture = GestureType.PAUSE
            self.is_dragging = False
            self.pinch_start_time = None

        # 2. Open Palm -> ACTIVATE
        elif num_fingers_up >= 4 and not (dist_ti < pinch_thresh):
            raw_gesture = GestureType.ACTIVATE
            self.is_dragging = False
            self.pinch_start_time = None

        # 3. Double Click: Index + Middle finger tips pinched/touching together
        elif index_up and middle_up and not ring_up and not pinky_up and dist_im < double_click_thresh:
            raw_gesture = GestureType.DOUBLE_CLICK
            self.is_dragging = False
            self.pinch_start_time = None

        # 4. Thumb + Middle Pinch -> RIGHT CLICK
        elif dist_tm < right_click_thresh and dist_ti >= pinch_thresh:
            raw_gesture = GestureType.RIGHT_CLICK
            self.is_dragging = False
            self.pinch_start_time = None

        # 5. Thumb + Index Pinch -> LEFT CLICK or DRAG & DROP
        elif dist_ti < pinch_thresh:
            if self.pinch_start_time is None:
                self.pinch_start_time = current_time

            pinch_duration = current_time - self.pinch_start_time
            metrics["pinch_duration"] = pinch_duration

            if pinch_duration >= self.settings.drag_hold_duration:
                self.is_dragging = True
                raw_gesture = GestureType.DRAG_AND_DROP
            else:
                raw_gesture = GestureType.LEFT_CLICK

        # If pinch is released, reset drag state
        else:
            if self.is_dragging:
                # Drag just finished
                self.is_dragging = False
            self.pinch_start_time = None

            # 6. Two fingers upright (Index + Middle) -> SCROLL MODE
            if index_up and middle_up and not ring_up and not pinky_up and dist_im >= double_click_thresh:
                raw_gesture = GestureType.SCROLL_MODE

            # 7. Index finger only -> MOVE CURSOR
            elif index_up and not middle_up and not ring_up and not pinky_up:
                raw_gesture = GestureType.MOVE_MOUSE

            # 8. Thumb only extended -> VOLUME CONTROL
            elif thumb_up and not index_up and not middle_up and not ring_up and not pinky_up:
                raw_gesture = GestureType.VOLUME_CONTROL

            else:
                raw_gesture = GestureType.NONE

        # Apply short temporal debounce filter
        self.gesture_history.append(raw_gesture)
        if len(self.gesture_history) > self.history_size:
            self.gesture_history.pop(0)

        # Majority vote or latest if stable
        if len(self.gesture_history) >= 2 and self.gesture_history[-1] == self.gesture_history[-2]:
            stable_gesture = self.gesture_history[-1]
        else:
            stable_gesture = raw_gesture

        self.previous_gesture = self.current_gesture
        self.current_gesture = stable_gesture
        metrics["is_dragging"] = self.is_dragging

        return stable_gesture, metrics

    def reset(self):
        """Reset internal recognition states."""
        self.current_gesture = GestureType.NONE
        self.previous_gesture = GestureType.NONE
        self.pinch_start_time = None
        self.is_dragging = False
        self.gesture_history.clear()
