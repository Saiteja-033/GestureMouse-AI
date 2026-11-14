"""
GestureMouse AI - Fruit Ninja Game Settings & Difficulties
Configuration constants for graphics, physics, scoring, difficulty modes, and profile storage.
"""

import os
from dataclasses import dataclass

# Screen Dimensions
GAME_WIDTH = 1280
GAME_HEIGHT = 720
FPS = 60

# Difficulty Modes
DIFFICULTY_PRESETS = {
    "EASY": {
        "name": "EASY (Zen Mode)",
        "gravity": 0.28,             # Gentle gravity gives +50% air hang time!
        "min_slice_velocity": 6.5,   # Gentle hand swipes slice effortlessly
        "initial_lives": 5,          # 5 lives for relaxed play
        "bomb_spawn_chance": 0.10,   # Very rare bombs
        "spawn_interval": 1.6,       # Relaxed pacing
        "hitbox_margin": 10,         # Generous collision margin
    },
    "NORMAL": {
        "name": "NORMAL (Classic)",
        "gravity": 0.38,
        "min_slice_velocity": 10.0,
        "initial_lives": 3,
        "bomb_spawn_chance": 0.18,
        "spawn_interval": 1.25,
        "hitbox_margin": 5,
    },
    "HARD": {
        "name": "HARD (Frenzy)",
        "gravity": 0.44,
        "min_slice_velocity": 14.0,
        "initial_lives": 3,
        "bomb_spawn_chance": 0.25,
        "spawn_interval": 0.95,
        "hitbox_margin": 0,
    },
}

# Current Active Defaults
ACTIVE_DIFFICULTY = "EASY"
GRAVITY = DIFFICULTY_PRESETS[ACTIVE_DIFFICULTY]["gravity"]
MIN_SLICE_VELOCITY = DIFFICULTY_PRESETS[ACTIVE_DIFFICULTY]["min_slice_velocity"]
INITIAL_LIVES = DIFFICULTY_PRESETS[ACTIVE_DIFFICULTY]["initial_lives"]
BOMB_SPAWN_CHANCE = DIFFICULTY_PRESETS[ACTIVE_DIFFICULTY]["bomb_spawn_chance"]

# Launch Velocity Ranges (relaxed for comfortable tracking)
MIN_LAUNCH_VX = -2.8
MAX_LAUNCH_VX = 2.8
MIN_LAUNCH_VY = -16.5
MAX_LAUNCH_VY = -13.0
MIN_ANGULAR_VEL = -3.5
MAX_ANGULAR_VEL = 3.5

# Gesture Blade Settings
BLADE_TRAIL_LENGTH = 16
BLADE_COLOR_CORE = (255, 255, 255)
BLADE_COLOR_GLOW = (0, 240, 255)
BLADE_MAX_WIDTH = 10

# Gameplay & Rules
GAME_TIME_SECONDS = 90
POINTS_PER_FRUIT = 10
COMBO_TIME_WINDOW = 0.45      # Generous combo window
COMBO_BONUS_POINTS = 20
MAX_SIMULTANEOUS_FRUITS = 4

# Storage Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HIGH_SCORE_FILE = os.path.join(BASE_DIR, "assets", "highscore.json")
RECORDS_FILE = os.path.join(BASE_DIR, "assets", "game_records.json")
