"""
GestureMouse AI - Test Suite for Game CRUD Operations & Easy Mode Tuning
Validates Profile Create, Read, Update, Delete persistence, Blade Customization,
and Easy Mode difficulty configurations.
"""

import os
import sys
import unittest
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from game.profile_manager import ProfileCRUDManager, BLADE_COLORS
from game.game_settings import DIFFICULTY_PRESETS


class TestProfileCRUDAndDifficulty(unittest.TestCase):

    def setUp(self):
        # Use a temporary file for isolated test database
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.mgr = ProfileCRUDManager(storage_path=self.temp_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
            except Exception:
                pass

    def test_crud_create_profile(self):
        """[CREATE] Verify creating a new profile initializes all fields properly."""
        p = self.mgr.create_profile(name="DragonSlayer", blade_color="Gold", title="Grandmaster")
        self.assertIsNotNone(p["id"])
        self.assertEqual(p["name"], "DragonSlayer")
        self.assertEqual(p["blade_color"], "Gold")
        self.assertEqual(p["title"], "Grandmaster")
        self.assertEqual(p["high_score"], 0)
        self.assertEqual(p["total_fruits"], 0)
        self.assertEqual(p["games_played"], 0)
        # Active profile should point to newly created profile
        self.assertEqual(self.mgr.active_profile_id, p["id"])

    def test_crud_read_profiles(self):
        """[READ] Verify reading all profiles, active profile, and single profile."""
        profiles = self.mgr.get_all_profiles()
        self.assertGreaterEqual(len(profiles), 1)

        active = self.mgr.get_active_profile()
        self.assertIsNotNone(active)

        found = self.mgr.get_profile(active["id"])
        self.assertEqual(found["id"], active["id"])

        # Test non-existent profile returns None
        self.assertIsNone(self.mgr.get_profile("non-existent-id-999"))

    def test_crud_update_profile(self):
        """[UPDATE] Verify updating profile metadata and recording match stats."""
        p = self.mgr.create_profile(name="OriginalName", blade_color="Cyan")
        p_id = p["id"]

        # 1. Update metadata
        success = self.mgr.update_profile(p_id, name="UpdatedName", blade_color="Crimson", title="Elite")
        self.assertTrue(success)
        updated = self.mgr.get_profile(p_id)
        self.assertEqual(updated["name"], "UpdatedName")
        self.assertEqual(updated["blade_color"], "Crimson")
        self.assertEqual(updated["title"], "Elite")

        # 2. Record match stats
        self.mgr.record_match_stats(p_id, match_score=250, fruits_sliced=25)
        updated2 = self.mgr.get_profile(p_id)
        self.assertEqual(updated2["high_score"], 250)
        self.assertEqual(updated2["total_fruits"], 25)
        self.assertEqual(updated2["games_played"], 1)

    def test_crud_delete_profile(self):
        """[DELETE] Verify deleting a profile removes it from storage."""
        p1 = self.mgr.create_profile(name="NinjaToDelete", blade_color="Violet")
        p2 = self.mgr.create_profile(name="SurvivorNinja", blade_color="Emerald")
        count_before = len(self.mgr.get_all_profiles())

        # Delete p1
        del_success = self.mgr.delete_profile(p1["id"])
        self.assertTrue(del_success)
        self.assertEqual(len(self.mgr.get_all_profiles()), count_before - 1)
        self.assertIsNone(self.mgr.get_profile(p1["id"]))

    def test_crud_delete_last_profile_prevention(self):
        """[DELETE SAFETY] Verify safety rule preventing deletion of the last remaining profile."""
        # Delete until only 1 profile remains
        while len(self.mgr.profiles) > 1:
            self.mgr.delete_profile(self.mgr.profiles[0]["id"])

        self.assertEqual(len(self.mgr.profiles), 1)
        last_id = self.mgr.profiles[0]["id"]

        # Attempt to delete the final profile
        can_delete_last = self.mgr.delete_profile(last_id)
        self.assertFalse(can_delete_last)
        self.assertEqual(len(self.mgr.profiles), 1)

    def test_easy_mode_preset_values(self):
        """[EASY MODE] Verify Easy Mode parameters provide gentle, accessible gameplay."""
        easy = DIFFICULTY_PRESETS["EASY"]
        self.assertEqual(easy["initial_lives"], 5)          # 5 lives
        self.assertLess(easy["gravity"], 0.32)              # Low gravity (long hang time)
        self.assertLess(easy["min_slice_velocity"], 8.0)    # Low slice velocity required
        self.assertLessEqual(easy["bomb_spawn_chance"], 0.12) # Rare bombs
        self.assertGreater(easy["hitbox_margin"], 5)        # Generous hitbox margin


if __name__ == "__main__":
    unittest.main()
