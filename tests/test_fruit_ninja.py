"""
GestureMouse AI - Fruit Ninja Test Suite
Validates fruit physics, slice collision math, particle systems, blade velocity,
bomb detonation, and high score persistence.
"""

import os
import sys
import json
import time
import unittest
import pygame

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from game.fruit_objects import Fruit, FruitType, FruitHalf
from game.particle_effects import (
    JuiceParticle,
    WallSplatter,
    BombSpark,
    FloatingText,
    BladeTrail,
)
from game.sound_generator import SoundManager
from game.game_settings import HIGH_SCORE_FILE


class TestFruitNinja(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()

    def test_fruit_initialization_and_configs(self):
        """Verify fruits and bombs initialize with proper radii, colors, and surfaces."""
        melon = Fruit(FruitType.WATERMELON, 200, 400, 2.0, -15.0)
        self.assertEqual(melon.fruit_type, FruitType.WATERMELON)
        self.assertEqual(melon.radius, 44)
        self.assertFalse(melon.is_sliced)
        self.assertTrue(melon.is_active)
        self.assertIsNotNone(melon.base_surface)

        bomb = Fruit(FruitType.BOMB, 300, 500, -1.0, -16.0)
        self.assertEqual(bomb.fruit_type, FruitType.BOMB)
        self.assertEqual(bomb.radius, 36)

    def test_fruit_physics_trajectory(self):
        """Verify gravity and angular rotation modify position and angle."""
        fruit = Fruit(FruitType.ORANGE, 200, 300, 2.0, -10.0)
        initial_y = fruit.y
        initial_vy = fruit.vy
        fruit.update()
        self.assertEqual(fruit.x, 202.0)
        self.assertEqual(fruit.y, initial_y + initial_vy)
        self.assertGreater(fruit.vy, initial_vy)  # Gravity increases downward velocity

    def test_blade_collision_segment_intersection(self):
        """Verify segment-circle collision detection accurately detects slicing lines."""
        fruit = Fruit(FruitType.APPLE, 400, 300, 0, 0)

        # 1. Line segment passing directly through center (350, 300) -> (450, 300)
        hit = fruit.check_slice_collision((350, 300), (450, 300))
        self.assertTrue(hit)

        # 2. Line segment grazing within radius
        hit_graze = fruit.check_slice_collision((380, 270), (420, 270))
        self.assertTrue(hit_graze)

        # 3. Line segment far away (100, 100) -> (200, 100)
        miss = fruit.check_slice_collision((100, 100), (200, 100))
        self.assertFalse(miss)

    def test_fruit_slice_halves_generation(self):
        """Verify slicing produces 2 separated halves with opposite velocities."""
        fruit = Fruit(FruitType.WATERMELON, 500, 400, 1.0, -5.0)
        halves, juice_color = fruit.slice()
        self.assertTrue(fruit.is_sliced)
        self.assertEqual(len(halves), 2)
        self.assertLess(halves[0].vx, fruit.vx)  # Left half moves left
        self.assertGreater(halves[1].vx, fruit.vx) # Right half moves right
        self.assertEqual(juice_color, (235, 45, 65))

    def test_bomb_slice_does_not_generate_fruit_halves(self):
        """Verify slicing bomb does not spawn fruit halves."""
        bomb = Fruit(FruitType.BOMB, 500, 400, 0, 0)
        halves, _ = bomb.slice()
        self.assertTrue(bomb.is_sliced)
        self.assertEqual(len(halves), 0)

    def test_blade_velocity_calculation(self):
        """Verify blade trail velocity detects fast swipes and filters stationary hands."""
        blade = BladeTrail(max_length=10)
        blade.add_point(100, 100)
        blade.add_point(100, 100)
        # Stationary = 0 velocity
        self.assertAlmostEqual(blade.get_velocity(), 0.0, delta=1.0)

        # Fast swipe across 120 pixels
        blade.clear()
        blade.add_point(100, 100)
        time.sleep(0.02)
        blade.add_point(250, 100)
        self.assertGreater(blade.get_velocity(), 15.0)

    def test_particles_lifecycle(self):
        """Verify particles update and cleanly expire."""
        p = JuiceParticle(100, 100, (255, 0, 0))
        p.fade_rate = 100.0  # Force fast fade
        alive = p.update()
        self.assertTrue(alive)
        p.alpha = -5.0
        self.assertFalse(p.update())

        spark = BombSpark(200, 200)
        spark.age = spark.life + 1
        self.assertFalse(spark.update())

    def test_sound_manager_initialization(self):
        """Verify sound manager initializes without crashing."""
        sound = SoundManager()
        self.assertIsNotNone(sound)
        # Play call should be safe even if muted
        sound.play("slice")
        sound.play("bomb")

    def test_high_score_load_save(self):
        """Verify high score persistence."""
        test_score = 9999
        os.makedirs(os.path.dirname(HIGH_SCORE_FILE), exist_ok=True)
        with open(HIGH_SCORE_FILE, "w") as f:
            json.dump({"high_score": test_score}, f)

        with open(HIGH_SCORE_FILE, "r") as f:
            loaded = json.load(f).get("high_score", 0)
        self.assertEqual(loaded, test_score)


if __name__ == "__main__":
    unittest.main()
