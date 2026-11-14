"""
GestureMouse AI - Modern Desktop Dashboard
CustomTkinter GUI with asynchronous webcam processing thread, real-time HUD overlays,
safety controls, and live gesture state cards.
"""

import os
import threading
import time
import cv2
import numpy as np
from PIL import Image
import customtkinter as ctk
from typing import Optional

from modules.settings import AppSettings
from modules.hand_tracker import HandTracker
from modules.gesture_recognition import GestureRecognizer, GestureType
from modules.mouse_controller import MouseController
from ui.components import (
    StatusCard,
    SliderControl,
    GestureCard,
    COLOR_BG_DARK,
    COLOR_CARD_BG,
    COLOR_ACCENT_GREEN,
    COLOR_ACCENT_CYAN,
    COLOR_ACCENT_RED,
    COLOR_ACCENT_YELLOW,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class DashboardApp(ctk.CTk):
    """
    Main application window for GestureMouse AI.
    """

    def __init__(self, settings: Optional[AppSettings] = None):
        super().__init__()

        self.settings = settings or AppSettings()
        self.hand_tracker = HandTracker(
            detection_con=self.settings.min_detection_confidence,
            track_con=self.settings.min_tracking_confidence,
        )
        self.gesture_recognizer = GestureRecognizer(self.settings)
        self.mouse_controller = MouseController(self.settings)

        # Threading & Camera State
        self.camera_thread: Optional[threading.Thread] = None
        self.is_camera_running = False
        self.cap: Optional[cv2.VideoCapture] = None
        self.latest_frame: Optional[Image.Image] = None
        self.frame_lock = threading.Lock()
        
        # FPS calculation
        self.fps: float = 0.0
        self.frame_counter: int = 0
        self.fps_start_time: float = time.time()
        self.current_gesture_type = GestureType.NONE
        self.hand_status_text = "No Hand Detected"
        self.hand_confidence: float = 0.0

        # Window Configuration
        self.title("GestureMouse AI - Hand Gesture Controlled Virtual Mouse")
        self.geometry("1240x820")
        self.minsize(1050, 720)
        self.configure(fg_color=COLOR_BG_DARK)

        # Set window icon if available
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "app_icon.png"))
        if os.path.exists(icon_path):
            try:
                from PIL import ImageTk
                self._app_icon = ImageTk.PhotoImage(file=icon_path)
                self.iconphoto(False, self._app_icon)
            except Exception:
                pass

        # Bind emergency stop keys
        self.bind("<Escape>", self.on_emergency_stop)

        # Protocol for clean window exit
        self.is_closing = False
        self.after_id = None
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

        # Build GUI Layout
        self._build_ui()

        # Start periodic GUI updater (60Hz timer)
        self.after_id = self.after(30, self._update_gui_loop)

    def _build_ui(self):
        """Builds modern dark responsive dashboard layout."""
        # Main container with two columns: Left Controls/Feed, Right Instructions & Settings
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. TOP HEADER BAR
        self._build_header()

        # 2. MAIN BODY
        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body_frame.grid_columnconfigure(0, weight=7)  # Left column (Preview & Quick Stats)
        body_frame.grid_columnconfigure(1, weight=5)  # Right column (Controls & Gestures)
        body_frame.grid_rowconfigure(0, weight=1)

        # Left Column: Video Feed & Live Status Cards
        left_col = ctk.CTkFrame(body_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left_col.grid_rowconfigure(1, weight=1)
        left_col.grid_columnconfigure(0, weight=1)

        self._build_status_cards(left_col)
        self._build_video_panel(left_col)

        # Right Column: Controls, Sliders & Gesture Guide
        right_col = ctk.CTkFrame(body_frame, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        right_col.grid_rowconfigure(2, weight=1)
        right_col.grid_columnconfigure(0, weight=1)

        self._build_quick_controls(right_col)
        self._build_tuning_sliders(right_col)
        self._build_gesture_guide(right_col)

    def _build_header(self):
        """Top navigation bar with logo, title, and exit action."""
        header = ctk.CTkFrame(self, height=64, fg_color=COLOR_CARD_BG, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(1, weight=1)

        # Logo / Badge
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=12, sticky="w")

        logo_icon = ctk.CTkLabel(
            logo_frame,
            text="✨",
            font=ctk.CTkFont(size=24),
        )
        logo_icon.pack(side="left", padx=(0, 10))

        title_lbl = ctk.CTkLabel(
            logo_frame,
            text="GestureMouse AI",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        title_lbl.pack(side="left")

        subtitle_lbl = ctk.CTkLabel(
            logo_frame,
            text="v2.0 • Real-time Neural Vision Controller",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED,
        )
        subtitle_lbl.pack(side="left", padx=(12, 0), pady=(3, 0))

        # Right Header Actions
        actions_frame = ctk.CTkFrame(header, fg_color="transparent")
        actions_frame.grid(row=0, column=2, padx=20, pady=12, sticky="e")

        self.emergency_btn = ctk.CTkButton(
            actions_frame,
            text="Emergency Stop (ESC)",
            command=self.on_emergency_stop,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            text_color=COLOR_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=34,
            corner_radius=6,
        )
        self.emergency_btn.pack(side="left", padx=8)

        exit_btn = ctk.CTkButton(
            actions_frame,
            text="Exit",
            command=self.on_exit,
            fg_color="#26354A",
            hover_color="#37474F",
            width=70,
            height=34,
            corner_radius=6,
        )
        exit_btn.pack(side="left")

    def _build_status_cards(self, parent):
        """Top row of live telemetry status cards."""
        cards_row = ctk.CTkFrame(parent, fg_color="transparent")
        cards_row.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        cards_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_camera = StatusCard(
            cards_row,
            title="Camera Feed",
            initial_value="Offline",
            indicator_color=COLOR_ACCENT_RED,
        )
        self.card_camera.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.card_hand = StatusCard(
            cards_row,
            title="Hand Tracking",
            initial_value="Waiting...",
            indicator_color=COLOR_ACCENT_YELLOW,
        )
        self.card_hand.grid(row=0, column=1, padx=6, sticky="ew")

        self.card_gesture = StatusCard(
            cards_row,
            title="Active Gesture",
            initial_value="None",
            indicator_color=COLOR_ACCENT_CYAN,
        )
        self.card_gesture.grid(row=0, column=2, padx=6, sticky="ew")

        self.card_fps = StatusCard(
            cards_row,
            title="Performance",
            initial_value="0 FPS",
            indicator_color=COLOR_ACCENT_GREEN,
        )
        self.card_fps.grid(row=0, column=3, padx=(6, 0), sticky="ew")

    def _build_video_panel(self, parent):
        """Center video preview container with futuristic HUD frame."""
        feed_container = ctk.CTkFrame(
            parent,
            fg_color=COLOR_CARD_BG,
            border_color="#222C3A",
            border_width=1,
            corner_radius=12,
        )
        feed_container.grid(row=1, column=0, sticky="nsew")
        feed_container.grid_rowconfigure(0, weight=1)
        feed_container.grid_columnconfigure(0, weight=1)

        # Video label
        self.video_label = ctk.CTkLabel(
            feed_container,
            text="Camera is currently stopped.\n\nClick 'Start Camera' to initialize real-time gesture tracking.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self.video_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def _build_quick_controls(self, parent):
        """Top section of right column: Camera toggles and mouse switch."""
        ctrl_card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_CARD_BG,
            border_color="#222C3A",
            border_width=1,
            corner_radius=10,
        )
        ctrl_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        # Title
        title_lbl = ctk.CTkLabel(
            ctrl_card,
            text="SYSTEM CONTROLS",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_MUTED,
        )
        title_lbl.pack(anchor="w", padx=16, pady=(12, 8))

        # Button Row
        btn_row = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 12))

        self.start_btn = ctk.CTkButton(
            btn_row,
            text="▶ Start Camera",
            command=self.start_camera,
            fg_color=COLOR_ACCENT_GREEN,
            hover_color="#00C853",
            text_color="#0A1E14",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=38,
            corner_radius=6,
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.stop_btn = ctk.CTkButton(
            btn_row,
            text="⏹ Stop Camera",
            command=self.stop_camera,
            fg_color="#37474F",
            hover_color="#455A64",
            text_color=COLOR_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=38,
            corner_radius=6,
            state="disabled",
        )
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))

        # Mouse control master toggle
        toggle_frame = ctk.CTkFrame(ctrl_card, fg_color="#141B24", corner_radius=6)
        toggle_frame.pack(fill="x", padx=16, pady=(0, 14))

        toggle_lbl = ctk.CTkLabel(
            toggle_frame,
            text="Virtual Mouse Control",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        toggle_lbl.pack(side="left", padx=12, pady=10)

        self.mouse_switch = ctk.CTkSwitch(
            toggle_frame,
            text="ACTIVE",
            command=self._on_mouse_switch_toggle,
            progress_color=COLOR_ACCENT_GREEN,
            button_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_ACCENT_GREEN,
        )
        self.mouse_switch.select()
        self.mouse_switch.pack(side="right", padx=12, pady=10)

        # 🎮 Fruit Ninja Arcade Game Mode Button
        self.game_btn = ctk.CTkButton(
            ctrl_card,
            text="🎮 PLAY FRUIT NINJA",
            command=self.on_play_fruit_ninja,
            fg_color="#E65100",
            hover_color="#F57C00",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=40,
            corner_radius=8,
        )
        self.game_btn.pack(fill="x", padx=16, pady=(0, 14))

    def on_play_fruit_ninja(self):
        """Launches Fruit Ninja gesture gaming mode, temporarily disabling virtual mouse."""
        was_camera_running = self.is_camera_running
        was_mouse_enabled = self.settings.mouse_control_enabled

        # Disable virtual mouse and stop dashboard camera
        self.settings.mouse_control_enabled = False
        self.mouse_controller.emergency_stop()
        if was_camera_running:
            self.stop_camera()

        self.game_btn.configure(state="disabled", text="🎮 Running Fruit Ninja...")
        self.withdraw()

        def run_game_worker():
            try:
                from game.fruit_ninja import launch_fruit_ninja
                launch_fruit_ninja(camera_index=self.settings.camera_index)
            except Exception as e:
                print(f"[FruitNinja Launch Error]: {e}")
            finally:
                self.after(100, lambda: self._on_game_closed(was_camera_running, was_mouse_enabled))

        threading.Thread(target=run_game_worker, daemon=True).start()

    def _on_game_closed(self, was_camera_running: bool, was_mouse_enabled: bool):
        """Restores dashboard state when user exits Fruit Ninja."""
        self.deiconify()
        self.game_btn.configure(state="normal", text="🎮 PLAY FRUIT NINJA")
        if was_camera_running:
            self.start_camera()
        if was_mouse_enabled and bool(self.mouse_switch.get()):
            self.settings.mouse_control_enabled = True

    def _build_tuning_sliders(self, parent):
        """Slider panel for calibration and customization."""
        slider_card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_CARD_BG,
            border_color="#222C3A",
            border_width=1,
            corner_radius=10,
        )
        slider_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        title_lbl = ctk.CTkLabel(
            slider_card,
            text="SENSITIVITY & THRESHOLD CALIBRATION",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_MUTED,
        )
        title_lbl.pack(anchor="w", padx=16, pady=(12, 10))

        content = ctk.CTkFrame(slider_card, fg_color="transparent")
        content.pack(fill="x", padx=16, pady=(0, 14))

        # 1. Cursor Sensitivity
        self.sens_slider = SliderControl(
            content,
            label="Cursor Sensitivity",
            from_val=0.5,
            to_val=3.0,
            initial_val=self.settings.cursor_sensitivity,
            unit="x",
            on_change=self._on_sensitivity_change,
        )
        self.sens_slider.pack(fill="x", pady=(0, 12))

        # 2. Gesture Pinch Threshold
        self.pinch_slider = SliderControl(
            content,
            label="Pinch Distance Threshold",
            from_val=20.0,
            to_val=75.0,
            initial_val=self.settings.pinch_threshold,
            unit=" px",
            is_float=False,
            on_change=self._on_pinch_threshold_change,
        )
        self.pinch_slider.pack(fill="x", pady=(0, 12))

        # 3. Click Cooldown
        self.cooldown_slider = SliderControl(
            content,
            label="Click Cooldown Debounce",
            from_val=0.10,
            to_val=0.80,
            initial_val=self.settings.click_cooldown,
            unit=" s",
            on_change=self._on_cooldown_change,
        )
        self.cooldown_slider.pack(fill="x", pady=(0, 6))

        # Reset defaults button
        reset_btn = ctk.CTkButton(
            content,
            text="↺ Reset Defaults",
            command=self._on_reset_settings,
            fg_color="transparent",
            hover_color="#26354A",
            text_color=COLOR_TEXT_SECONDARY,
            height=26,
            font=ctk.CTkFont(family="Segoe UI", size=11),
        )
        reset_btn.pack(anchor="e")

    def _build_gesture_guide(self, parent):
        """Scrollable / clean list showing all 9 supported gestures."""
        guide_card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_CARD_BG,
            border_color="#222C3A",
            border_width=1,
            corner_radius=10,
        )
        guide_card.grid(row=2, column=0, sticky="nsew")
        guide_card.grid_rowconfigure(1, weight=1)
        guide_card.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(
            guide_card,
            text="GESTURE INSTRUCTION REFERENCE",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_MUTED,
        )
        title_lbl.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 8))

        scrollable = ctk.CTkScrollableFrame(
            guide_card,
            fg_color="transparent",
            scrollbar_button_color="#26354A",
            scrollbar_button_hover_color="#37474F",
        )
        scrollable.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        gestures = [
            ("☝️ Index finger only", "Move mouse cursor smoothly across screen"),
            ("🤏 Thumb + Index pinch", "Left click (instant single click)"),
            ("✌️ Thumb + Middle pinch", "Right click (context menu)"),
            ("🖖 Two fingers (Index + Middle)", "Scroll mode (move vertically to scroll)"),
            ("👆+👆 Index & Middle tips touch", "Double click"),
            ("✊ Closed fist", "Pause mouse movement safely"),
            ("🖐 Open palm", "Activate mouse control"),
            ("⏳ Hold pinch (> 0.45s)", "Drag and drop (move while holding)"),
            ("👍 Thumb movement", "Volume control (up = louder, down = quieter)"),
        ]

        for g_name, a_desc in gestures:
            card = GestureCard(
                scrollable,
                gesture_name=g_name,
                action_name=a_desc,
                icon_str="🎯",
            )
            card.pack(fill="x", pady=3)

    # -------------------------------------------------------------
    # Settings callbacks
    # -------------------------------------------------------------
    def _on_sensitivity_change(self, val: float):
        self.settings.cursor_sensitivity = val

    def _on_pinch_threshold_change(self, val: float):
        self.settings.pinch_threshold = val

    def _on_cooldown_change(self, val: float):
        self.settings.click_cooldown = val

    def _on_reset_settings(self):
        self.settings.reset_defaults()
        self.sens_slider.set_value(self.settings.cursor_sensitivity)
        self.pinch_slider.set_value(self.settings.pinch_threshold)
        self.cooldown_slider.set_value(self.settings.click_cooldown)

    def _on_mouse_switch_toggle(self):
        enabled = bool(self.mouse_switch.get())
        self.settings.mouse_control_enabled = enabled
        if enabled:
            self.mouse_switch.configure(text="ACTIVE", text_color=COLOR_ACCENT_GREEN)
        else:
            self.mouse_switch.configure(text="MUTED", text_color=COLOR_ACCENT_RED)
            self.mouse_controller.emergency_stop()

    def on_emergency_stop(self, event=None):
        """Immediately disables mouse control (ESC shortcut or button)."""
        self.settings.mouse_control_enabled = False
        self.mouse_switch.deselect()
        self.mouse_switch.configure(text="MUTED", text_color=COLOR_ACCENT_RED)
        self.mouse_controller.emergency_stop()
        self.card_gesture.set_value("STOPPED (ESC)", COLOR_ACCENT_RED)
        self.card_gesture.set_indicator_color(COLOR_ACCENT_RED)

    # -------------------------------------------------------------
    # Camera thread and loop
    # -------------------------------------------------------------
    def start_camera(self):
        """Launches background webcam capture and processing thread."""
        if self.is_camera_running:
            return

        self.is_camera_running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.card_camera.set_value("Connecting...", COLOR_ACCENT_YELLOW)
        self.card_camera.set_indicator_color(COLOR_ACCENT_YELLOW)

        self.camera_thread = threading.Thread(target=self._camera_worker, daemon=True)
        self.camera_thread.start()

    def stop_camera(self):
        """Signals camera worker thread to stop and releases hardware."""
        self.is_camera_running = False
        self.mouse_controller.emergency_stop()

        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

        self.card_camera.set_value("Offline", COLOR_ACCENT_RED)
        self.card_camera.set_indicator_color(COLOR_ACCENT_RED)
        self.card_hand.set_value("Waiting...", COLOR_ACCENT_YELLOW)
        self.card_hand.set_indicator_color(COLOR_ACCENT_YELLOW)
        self.card_gesture.set_value("None", COLOR_ACCENT_CYAN)
        self.card_fps.set_value("0 FPS", COLOR_TEXT_MUTED)

        # Clear preview image
        self.video_label.configure(
            image="",
            text="Camera is stopped.\n\nClick 'Start Camera' to resume.",
        )

    def _camera_worker(self):
        """Background thread executing video capture, vision processing, and control."""
        try:
            # Prefer DirectShow on Windows for fast webcam init
            self.cap = cv2.VideoCapture(self.settings.camera_index, cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                # Fallback to default backend
                self.cap = cv2.VideoCapture(self.settings.camera_index)

            if not self.cap or not self.cap.isOpened():
                self.card_camera.set_value("No Device", COLOR_ACCENT_RED)
                self.card_camera.set_indicator_color(COLOR_ACCENT_RED)
                self.video_label.configure(
                    image="",
                    text="Error: Could not access webcam.\n\nPlease verify that your webcam is connected\nand not used by another application.",
                )
                self.is_camera_running = False
                self.start_btn.configure(state="normal")
                self.stop_btn.configure(state="disabled")
                return

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.frame_height)

            self.card_camera.set_value("Connected", COLOR_ACCENT_GREEN)
            self.card_camera.set_indicator_color(COLOR_ACCENT_GREEN)

            frame_count = 0
            start_t = time.time()

            while self.is_camera_running and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    time.sleep(0.01)
                    continue

                frame_count += 1
                now = time.time()
                elapsed = now - start_t
                if elapsed >= 1.0:
                    self.fps = frame_count / elapsed
                    frame_count = 0
                    start_t = now

                # 1. Hand tracking & visual overlays
                annotated_frame, hand_info = self.hand_tracker.process_frame(
                    frame,
                    flip_horizontal=True,
                    boundary_margin_x=self.settings.boundary_margin_x,
                    boundary_margin_y=self.settings.boundary_margin_y,
                    draw=True,
                )

                # 2. Gesture classification
                gesture, metrics = self.gesture_recognizer.recognize(hand_info)
                self.current_gesture_type = gesture

                if hand_info:
                    self.hand_status_text = f"Tracked ({hand_info['handedness']})"
                    self.hand_confidence = hand_info["confidence"]
                else:
                    self.hand_status_text = "No Hand Detected"
                    self.hand_confidence = 0.0

                # 3. Virtual mouse control
                self.mouse_controller.execute_action(gesture, hand_info, metrics)

                # 4. Draw HUD banner onto frame
                self._draw_hud(annotated_frame, gesture, hand_info)

                # Convert to PIL Image for Tkinter rendering
                rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb)

                with self.frame_lock:
                    self.latest_frame = pil_img

                time.sleep(0.005)  # Yield CPU

        except Exception as e:
            print(f"[Webcam Error]: {e}")
        finally:
            if self.cap:
                self.cap.release()
                self.cap = None

    def _draw_hud(self, frame: np.ndarray, gesture: GestureType, hand_info: Optional[dict]):
        """Render tech HUD overlays (gesture banner, status badge, FPS counter)."""
        h, w, _ = frame.shape

        # Top gesture banner background
        cv2.rectangle(frame, (0, 0), (w, 42), (15, 20, 28), -1)
        cv2.line(frame, (0, 42), (w, 42), (38, 53, 74), 1)

        # Gesture status text
        gesture_str = gesture.value
        if gesture == GestureType.PAUSE:
            badge_color = (82, 82, 255)  # Red
        elif gesture in (GestureType.LEFT_CLICK, GestureType.RIGHT_CLICK, GestureType.DOUBLE_CLICK):
            badge_color = (255, 214, 0)   # Yellow
        elif gesture == GestureType.DRAG_AND_DROP:
            badge_color = (255, 0, 229)   # Magenta
        elif gesture == GestureType.SCROLL_MODE:
            badge_color = (255, 229, 0)   # Cyan
        elif gesture == GestureType.MOVE_MOUSE:
            badge_color = (118, 230, 0)   # Green
        else:
            badge_color = (174, 164, 144)

        # Draw indicator dot
        cv2.circle(frame, (20, 21), 6, badge_color, -1, cv2.LINE_AA)

        cv2.putText(
            frame,
            f"GESTURE: {gesture_str.upper()}",
            (35, 27),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        # FPS & Confidence on right side of top banner
        info_str = f"FPS: {self.fps:.1f} | Conf: {self.hand_confidence * 100:.0f}%"
        cv2.putText(
            frame,
            info_str,
            (w - 220, 27),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 230, 118),
            1,
            cv2.LINE_AA,
        )

    def _update_gui_loop(self):
        """Periodic main-thread GUI updater running at ~30Hz."""
        # 1. Update Video Feed
        with self.frame_lock:
            frame_img = self.latest_frame
            self.latest_frame = None

        if frame_img is not None and self.is_camera_running:
            # Fit to container width/height while maintaining aspect ratio
            display_w = max(400, self.video_label.winfo_width() - 10)
            display_h = max(300, self.video_label.winfo_height() - 10)

            # Resize keeping aspect ratio
            orig_w, orig_h = frame_img.size
            ratio = min(display_w / orig_w, display_h / orig_h)
            new_size = (max(10, int(orig_w * ratio)), max(10, int(orig_h * ratio)))
            resized = frame_img.resize(new_size, Image.Resampling.BILINEAR)

            ctk_img = ctk.CTkImage(light_image=resized, dark_image=resized, size=new_size)
            self.video_label.configure(image=ctk_img, text="")

        # 2. Update Status Cards
        if self.is_camera_running:
            # Gesture Card
            g_name = self.current_gesture_type.value
            color = COLOR_TEXT_PRIMARY
            ind_color = COLOR_ACCENT_GREEN
            if self.current_gesture_type == GestureType.PAUSE:
                color = COLOR_ACCENT_RED
                ind_color = COLOR_ACCENT_RED
            elif self.current_gesture_type == GestureType.NONE:
                ind_color = COLOR_TEXT_MUTED
            elif "Click" in g_name or "Drag" in g_name:
                ind_color = COLOR_ACCENT_YELLOW

            self.card_gesture.set_value(g_name, color)
            self.card_gesture.set_indicator_color(ind_color)

            # Hand Card
            if "Tracked" in self.hand_status_text:
                self.card_hand.set_value(self.hand_status_text, COLOR_ACCENT_GREEN)
                self.card_hand.set_indicator_color(COLOR_ACCENT_GREEN)
            else:
                self.card_hand.set_value(self.hand_status_text, COLOR_ACCENT_YELLOW)
                self.card_hand.set_indicator_color(COLOR_ACCENT_YELLOW)

            # FPS Card
            fps_str = f"{self.fps:.1f} FPS"
            self.card_fps.set_value(fps_str, COLOR_ACCENT_GREEN)

        if not self.is_closing:
            self.after_id = self.after(30, self._update_gui_loop)

    def on_exit(self):
        """Safely cleans up all background threads, devices, and exits window."""
        self.is_closing = True
        if hasattr(self, "after_id") and self.after_id:
            try:
                self.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None
        self.stop_camera()
        self.hand_tracker.release()
        try:
            self.destroy()
        except Exception:
            pass
