"""
GestureMouse AI - Hand Tracker Module
Integrates MediaPipe Hands for high-precision real-time hand and landmark detection.
Supports both modern MediaPipe Tasks (1.0+) and classic solutions API with automated model setup.
"""

import os
import sys
import urllib.request
import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any, List

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision
except ImportError:
    mp = None
    mp_python = None
    mp_vision = None


HAND_CONNECTIONS = [
    # Thumb
    (0, 1), (1, 2), (2, 3), (3, 4),
    # Index
    (0, 5), (5, 6), (6, 7), (7, 8),
    # Middle
    (9, 10), (10, 11), (11, 12),
    # Ring
    (13, 14), (14, 15), (15, 16),
    # Pinky
    (0, 17), (17, 18), (18, 19), (19, 20),
    # Palm Knuckles
    (5, 9), (9, 13), (13, 17),
]


class HandTracker:
    """
    Handles webcam frame processing, hand landmark detection, and visualization overlays.
    """

    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_FINGER_MCP = 5
    INDEX_FINGER_PIP = 6
    INDEX_FINGER_DIP = 7
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_MCP = 9
    MIDDLE_FINGER_PIP = 10
    MIDDLE_FINGER_DIP = 11
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_MCP = 13
    RING_FINGER_PIP = 14
    RING_FINGER_DIP = 15
    RING_FINGER_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

    def __init__(
        self,
        mode: bool = False,
        max_hands: int = 1,
        detection_con: float = 0.7,
        track_con: float = 0.7,
    ):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con

        self.use_tasks_api = False
        self.detector = None
        self.legacy_hands = None

        self._init_detector()

    def _get_model_path(self) -> str:
        """Finds or downloads the required hand_landmarker model."""
        base_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        models_dir = os.path.join(base_dir, "models")
        os.makedirs(models_dir, exist_ok=True)
        model_path = os.path.join(models_dir, "hand_landmarker.task")

        if not os.path.exists(model_path) or os.path.getsize(model_path) < 1000:
            print(f"[HandTracker] Downloading MediaPipe hand model to {model_path}...")
            try:
                urllib.request.urlretrieve(self.MODEL_URL, model_path)
                print("[HandTracker] Hand model downloaded successfully.")
            except Exception as e:
                print(f"[HandTracker Warning] Model download failed: {e}")

        return model_path

    def _init_detector(self):
        """Initializes either Tasks API (MediaPipe 1.x+) or Legacy Solutions API."""
        if mp is None:
            return

        # 1. Try Legacy Solutions API first if available
        if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
            try:
                self.mp_hands = mp.solutions.hands
                self.legacy_hands = self.mp_hands.Hands(
                    static_image_mode=self.mode,
                    max_num_hands=self.max_hands,
                    min_detection_confidence=self.detection_con,
                    min_tracking_confidence=self.track_con,
                )
                self.use_tasks_api = False
                return
            except Exception:
                pass

        # 2. Modern Tasks API (MediaPipe 1.0+)
        if mp_vision is not None and mp_python is not None:
            try:
                model_path = self._get_model_path()
                if os.path.exists(model_path):
                    base_options = mp_python.BaseOptions(model_asset_path=model_path)
                    options = mp_vision.HandLandmarkerOptions(
                        base_options=base_options,
                        num_hands=self.max_hands,
                        min_hand_detection_confidence=self.detection_con,
                        min_tracking_confidence=self.track_con,
                        running_mode=mp_vision.RunningMode.IMAGE,
                    )
                    self.detector = mp_vision.HandLandmarker.create_from_options(options)
                    self.use_tasks_api = True
            except Exception as e:
                print(f"[HandTracker Error] Failed initializing Tasks API: {e}")

    def process_frame(
        self,
        frame: np.ndarray,
        flip_horizontal: bool = True,
        boundary_margin_x: int = 80,
        boundary_margin_y: int = 60,
        draw: bool = True,
    ) -> Tuple[np.ndarray, Optional[Dict[str, Any]]]:
        """
        Process a single BGR camera frame.
        """
        if frame is None:
            return frame, None

        if flip_horizontal:
            frame = cv2.flip(frame, 1)

        h, w, c = frame.shape
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        hand_info: Optional[Dict[str, Any]] = None

        # Mode A: Tasks API
        if self.use_tasks_api and self.detector is not None:
            try:
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
                results = self.detector.detect(mp_img)

                if results and results.hand_landmarks and len(results.hand_landmarks) > 0:
                    primary_landmarks = results.hand_landmarks[0]
                    
                    # Handedness
                    handedness_label = "Right"
                    confidence = 0.90
                    if results.handedness and len(results.handedness) > 0:
                        handedness_label = results.handedness[0][0].category_name
                        confidence = float(results.handedness[0][0].score)

                    pixel_landmarks: List[Tuple[int, int]] = []
                    norm_landmarks: List[Tuple[float, float, float]] = []

                    for lm in primary_landmarks:
                        px = int(lm.x * w)
                        py = int(lm.y * h)
                        pixel_landmarks.append((px, py))
                        norm_landmarks.append((lm.x, lm.y, getattr(lm, "z", 0.0)))

                    wrist_px = np.array(pixel_landmarks[self.WRIST])
                    middle_mcp_px = np.array(pixel_landmarks[self.MIDDLE_FINGER_MCP])
                    hand_scale = float(np.linalg.norm(wrist_px - middle_mcp_px))
                    if hand_scale < 10.0:
                        hand_scale = 100.0

                    xs = [p[0] for p in pixel_landmarks]
                    ys = [p[1] for p in pixel_landmarks]
                    bbox = (max(0, min(xs) - 15), max(0, min(ys) - 15),
                            min(w, max(xs) + 15), min(h, max(ys) + 15))

                    hand_info = {
                        "pixel_landmarks": pixel_landmarks,
                        "norm_landmarks": norm_landmarks,
                        "handedness": handedness_label,
                        "confidence": confidence,
                        "hand_scale": hand_scale,
                        "bbox": bbox,
                        "frame_size": (w, h),
                    }

                    if draw:
                        self._draw_custom_landmarks(frame, pixel_landmarks)
            except Exception as e:
                print(f"[HandTracker Process Error]: {e}")

        # Mode B: Legacy API
        elif not self.use_tasks_api and self.legacy_hands is not None:
            try:
                results = self.legacy_hands.process(img_rgb)
                if results.multi_hand_landmarks and results.multi_handedness:
                    primary_landmarks = results.multi_hand_landmarks[0]
                    handedness_info = results.multi_handedness[0]
                    handedness_label = handedness_info.classification[0].label
                    confidence = float(handedness_info.classification[0].score)

                    pixel_landmarks = []
                    norm_landmarks = []

                    for lm in primary_landmarks.landmark:
                        px = int(lm.x * w)
                        py = int(lm.y * h)
                        pixel_landmarks.append((px, py))
                        norm_landmarks.append((lm.x, lm.y, lm.z))

                    wrist_px = np.array(pixel_landmarks[self.WRIST])
                    middle_mcp_px = np.array(pixel_landmarks[self.MIDDLE_FINGER_MCP])
                    hand_scale = float(np.linalg.norm(wrist_px - middle_mcp_px))
                    if hand_scale < 10.0:
                        hand_scale = 100.0

                    xs = [p[0] for p in pixel_landmarks]
                    ys = [p[1] for p in pixel_landmarks]
                    bbox = (max(0, min(xs) - 15), max(0, min(ys) - 15),
                            min(w, max(xs) + 15), min(h, max(ys) + 15))

                    hand_info = {
                        "pixel_landmarks": pixel_landmarks,
                        "norm_landmarks": norm_landmarks,
                        "handedness": handedness_label,
                        "confidence": confidence,
                        "hand_scale": hand_scale,
                        "bbox": bbox,
                        "frame_size": (w, h),
                    }

                    if draw:
                        self._draw_custom_landmarks(frame, pixel_landmarks)
            except Exception as e:
                print(f"[HandTracker Legacy Error]: {e}")

        if draw:
            self._draw_boundary_zone(frame, w, h, boundary_margin_x, boundary_margin_y)

        return frame, hand_info

    def _draw_boundary_zone(
        self,
        frame: np.ndarray,
        w: int,
        h: int,
        margin_x: int,
        margin_y: int,
    ) -> None:
        """Draw active boundary box where hand movements are mapped to screen corners."""
        pt1 = (margin_x, margin_y)
        pt2 = (w - margin_x, h - margin_y)

        # Subtle glowing boundary rectangle
        cv2.rectangle(frame, pt1, pt2, (0, 230, 118), 2, cv2.LINE_AA)

        # Tech corner accents
        corner_len = 16
        color = (0, 255, 136)
        thick = 3
        # Top-left
        cv2.line(frame, (pt1[0], pt1[1]), (pt1[0] + corner_len, pt1[1]), color, thick)
        cv2.line(frame, (pt1[0], pt1[1]), (pt1[0], pt1[1] + corner_len), color, thick)
        # Top-right
        cv2.line(frame, (pt2[0], pt1[1]), (pt2[0] - corner_len, pt1[1]), color, thick)
        cv2.line(frame, (pt2[0], pt1[1]), (pt2[0], pt1[1] + corner_len), color, thick)
        # Bottom-left
        cv2.line(frame, (pt1[0], pt2[1]), (pt1[0] + corner_len, pt2[1]), color, thick)
        cv2.line(frame, (pt1[0], pt2[1]), (pt1[0], pt2[1] - corner_len), color, thick)
        # Bottom-right
        cv2.line(frame, (pt2[0], pt2[1]), (pt2[0] - corner_len, pt2[1]), color, thick)
        cv2.line(frame, (pt2[0], pt2[1]), (pt2[0], pt2[1] - corner_len), color, thick)

        # Label
        cv2.putText(
            frame,
            "ACTIVE CONTROL ZONE",
            (pt1[0] + 8, pt1[1] - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 230, 118),
            1,
            cv2.LINE_AA,
        )

    def _draw_custom_landmarks(
        self,
        frame: np.ndarray,
        pixel_landmarks: List[Tuple[int, int]],
    ) -> None:
        """Draw high-contrast skeleton connections and stylish glowing landmark nodes."""
        # Draw connection lines
        line_color = (200, 240, 200)
        for p1_idx, p2_idx in HAND_CONNECTIONS:
            p1 = pixel_landmarks[p1_idx]
            p2 = pixel_landmarks[p2_idx]
            cv2.line(frame, p1, p2, line_color, 2, cv2.LINE_AA)

        # Draw nodes
        for idx, pt in enumerate(pixel_landmarks):
            # Normal joint
            cv2.circle(frame, pt, 4, (0, 200, 83), -1, cv2.LINE_AA)
            cv2.circle(frame, pt, 6, (0, 100, 40), 1, cv2.LINE_AA)

        # Highlight primary control fingertip (Index Finger Tip - #8)
        idx_tip = pixel_landmarks[self.INDEX_FINGER_TIP]
        thumb_tip = pixel_landmarks[self.THUMB_TIP]
        middle_tip = pixel_landmarks[self.MIDDLE_FINGER_TIP]

        # Draw glowing halo around index fingertip (cursor tracking point)
        cv2.circle(frame, idx_tip, 10, (0, 255, 230), -1, cv2.LINE_AA)
        cv2.circle(frame, idx_tip, 15, (0, 230, 118), 2, cv2.LINE_AA)

        # Distinct colors for other key fingertips
        cv2.circle(frame, thumb_tip, 7, (255, 170, 0), -1, cv2.LINE_AA)
        cv2.circle(frame, middle_tip, 7, (0, 180, 255), -1, cv2.LINE_AA)

    def release(self):
        """Cleanly close resources."""
        if self.detector is not None:
            try:
                self.detector.close()
            except Exception:
                pass
            self.detector = None

        if self.legacy_hands is not None:
            try:
                self.legacy_hands.close()
            except Exception:
                pass
            self.legacy_hands = None
