"""
GestureMouse AI - UI and Integration Test Suite
Validates GUI initialization, widget creation, callbacks, and graceful destruction.
"""

import os
import sys
import unittest
import customtkinter as ctk

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.settings import AppSettings
from ui.dashboard import DashboardApp
from ui.components import StatusCard, SliderControl, GestureCard


class TestDashboardApp(unittest.TestCase):

    def setUp(self):
        self.settings = AppSettings()
        self.settings.mouse_control_enabled = False
        self.app = DashboardApp(settings=self.settings)
        # Pump Tkinter events once
        self.app.update_idletasks()
        self.app.update()

    def tearDown(self):
        if self.app:
            self.app.on_exit()

    def test_app_window_and_components_exist(self):
        """Verify window created with expected title, cards, and buttons."""
        self.assertIn("GestureMouse AI", self.app.title())
        self.assertIsNotNone(self.app.card_camera)
        self.assertIsNotNone(self.app.card_hand)
        self.assertIsNotNone(self.app.card_gesture)
        self.assertIsNotNone(self.app.card_fps)
        self.assertIsNotNone(self.app.start_btn)
        self.assertIsNotNone(self.app.stop_btn)
        self.assertIsNotNone(self.app.mouse_switch)

    def test_slider_callbacks(self):
        """Verify adjusting sliders properly updates AppSettings in real time."""
        # 1. Sensitivity slider
        self.app.sens_slider.set_value(2.25)
        self.assertAlmostEqual(self.settings.cursor_sensitivity, 2.25, places=2)

        # 2. Pinch slider
        self.app.pinch_slider.set_value(50.0)
        self.assertAlmostEqual(self.settings.pinch_threshold, 50.0, places=1)

        # 3. Cooldown slider
        self.app.cooldown_slider.set_value(0.50)
        self.assertAlmostEqual(self.settings.click_cooldown, 0.50, places=2)

    def test_emergency_stop_callback(self):
        """Verify ESC / emergency stop callback updates UI and controller state."""
        self.settings.mouse_control_enabled = True
        self.app.mouse_switch.select()
        self.app.on_emergency_stop()

        self.assertFalse(self.settings.mouse_control_enabled)
        self.assertFalse(self.app.mouse_controller.settings.mouse_control_enabled)
        self.assertEqual(self.app.mouse_switch.cget("text"), "MUTED")


if __name__ == "__main__":
    unittest.main()
