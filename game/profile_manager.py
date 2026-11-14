"""
GestureMouse AI - Fruit Ninja Profile & Record CRUD Manager
Manages persistence of Player Profiles, Custom Blades, and Game Records.
Supports full CRUD (Create, Read, Update, Delete) operations stored in JSON.
"""

import os
import json
import uuid
import time
from typing import List, Dict, Any, Optional

BLADE_COLORS = {
    "Cyan": (0, 240, 255),
    "Emerald": (0, 230, 118),
    "Gold": (255, 215, 0),
    "Crimson": (255, 45, 65),
    "Violet": (185, 75, 255),
}

DEFAULT_PROFILES = [
    {
        "id": "p-default-1",
        "name": "Ninja Master",
        "title": "Master of Slices",
        "blade_color": "Cyan",
        "high_score": 120,
        "total_fruits": 85,
        "games_played": 3,
        "created_at": "2026-11-13",
    },
    {
        "id": "p-default-2",
        "name": "Shadow Blade",
        "title": "Zen Slicer",
        "blade_color": "Emerald",
        "high_score": 90,
        "total_fruits": 50,
        "games_played": 2,
        "created_at": "2026-11-13",
    },
]


class ProfileCRUDManager:
    """
    CRUD Engine for Player Profiles, Dojo Ranks, and High Scores.
    """

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            self.storage_path = os.path.join(base_dir, "assets", "game_records.json")
        else:
            self.storage_path = storage_path

        self.profiles: List[Dict[str, Any]] = []
        self.active_profile_id: str = "p-default-1"
        self._load_data()

    def _load_data(self):
        """[READ] Loads profile database from JSON or initializes defaults."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if os.path.exists(self.storage_path) and os.path.getsize(self.storage_path) > 2:
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.profiles = data.get("profiles", [])
                    self.active_profile_id = data.get("active_profile_id", "p-default-1")
                    if not self.profiles:
                        self.profiles = [dict(p) for p in DEFAULT_PROFILES]
                        self.active_profile_id = self.profiles[0]["id"]
                        self._save_data()
                    return
            except Exception as e:
                print(f"[ProfileCRUDManager Warning] Failed to read database: {e}")

        # Seed with initial profiles
        self.profiles = [dict(p) for p in DEFAULT_PROFILES]
        self.active_profile_id = self.profiles[0]["id"]
        self._save_data()

    def _save_data(self):
        """Saves current state to JSON."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "active_profile_id": self.active_profile_id,
                        "profiles": self.profiles,
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            print(f"[ProfileCRUDManager Error] Failed to save database: {e}")

    # =========================================================================
    # CREATE (C)
    # =========================================================================
    def create_profile(
        self,
        name: str,
        blade_color: str = "Cyan",
        title: str = "Novice Slicer",
    ) -> Dict[str, Any]:
        """
        [CREATE] Adds a new player profile record with unique ID and starting stats.
        """
        clean_name = name.strip() or "Anonymous Ninja"
        color_choice = blade_color if blade_color in BLADE_COLORS else "Cyan"

        new_profile = {
            "id": f"p-{uuid.uuid4().hex[:8]}",
            "name": clean_name,
            "title": title.strip() or "Apprentice Ninja",
            "blade_color": color_choice,
            "high_score": 0,
            "total_fruits": 0,
            "games_played": 0,
            "created_at": time.strftime("%Y-%m-%d"),
        }
        self.profiles.append(new_profile)
        self.active_profile_id = new_profile["id"]
        self._save_data()
        return new_profile

    # =========================================================================
    # READ (R)
    # =========================================================================
    def get_all_profiles(self) -> List[Dict[str, Any]]:
        """[READ] Returns all profiles sorted by high score descending."""
        return sorted(self.profiles, key=lambda p: p.get("high_score", 0), reverse=True)

    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """[READ] Retrieves single profile by ID."""
        for p in self.profiles:
            if p["id"] == profile_id:
                return p
        return None

    def get_active_profile(self) -> Dict[str, Any]:
        """[READ] Retrieves the currently selected active player profile."""
        profile = self.get_profile(self.active_profile_id)
        if profile is None and self.profiles:
            profile = self.profiles[0]
            self.active_profile_id = profile["id"]
        elif profile is None:
            profile = self.create_profile("Player 1")
        return profile

    def get_active_blade_rgb(self) -> tuple:
        """Returns the RGB tuple for the active profile's blade."""
        active = self.get_active_profile()
        color_name = active.get("blade_color", "Cyan")
        return BLADE_COLORS.get(color_name, (0, 240, 255))

    # =========================================================================
    # UPDATE (U)
    # =========================================================================
    def set_active_profile(self, profile_id: str) -> bool:
        """[UPDATE] Switches the current active profile."""
        if self.get_profile(profile_id):
            self.active_profile_id = profile_id
            self._save_data()
            return True
        return False

    def update_profile(
        self,
        profile_id: str,
        name: Optional[str] = None,
        blade_color: Optional[str] = None,
        title: Optional[str] = None,
    ) -> bool:
        """[UPDATE] Modifies an existing profile's metadata (Name, Blade, Title)."""
        profile = self.get_profile(profile_id)
        if not profile:
            return False

        if name is not None and name.strip():
            profile["name"] = name.strip()
        if blade_color is not None and blade_color in BLADE_COLORS:
            profile["blade_color"] = blade_color
        if title is not None and title.strip():
            profile["title"] = title.strip()

        self._save_data()
        return True

    def record_match_stats(self, profile_id: str, match_score: int, fruits_sliced: int) -> bool:
        """[UPDATE] Updates match history, best score, and total sliced fruits."""
        profile = self.get_profile(profile_id)
        if not profile:
            return False

        profile["games_played"] = profile.get("games_played", 0) + 1
        profile["total_fruits"] = profile.get("total_fruits", 0) + fruits_sliced
        if match_score > profile.get("high_score", 0):
            profile["high_score"] = match_score

        self._save_data()
        return True

    # =========================================================================
    # DELETE (D)
    # =========================================================================
    def delete_profile(self, profile_id: str) -> bool:
        """
        [DELETE] Removes a profile record from storage.
        Ensures at least one profile remains available.
        """
        if len(self.profiles) <= 1:
            # Prevent deleting the last remaining profile
            return False

        initial_len = len(self.profiles)
        self.profiles = [p for p in self.profiles if p["id"] != profile_id]

        if len(self.profiles) < initial_len:
            # If the deleted profile was active, switch to first available
            if self.active_profile_id == profile_id and self.profiles:
                self.active_profile_id = self.profiles[0]["id"]
            self._save_data()
            return True
        return False
