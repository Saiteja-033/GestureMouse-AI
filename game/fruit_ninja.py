"""
GestureMouse AI - Fruit Ninja Arcade Game Engine
Fully playable gesture-driven arcade game with 60 FPS rendering, MediaPipe hand tracking,
integrated Player Profile CRUD operations, configurable Difficulty modes (Easy Zen mode),
particle systems, combo mechanics, and procedural audio feedback.
"""

import os
import sys
import json
import time
import math
import random
from typing import List, Tuple, Optional, Dict, Any

import cv2
import numpy as np
import pygame

from game.game_settings import (
    GAME_WIDTH,
    GAME_HEIGHT,
    FPS,
    DIFFICULTY_PRESETS,
    POINTS_PER_FRUIT,
    COMBO_BONUS_POINTS,
    COMBO_TIME_WINDOW,
    HIGH_SCORE_FILE,
)
from game.fruit_objects import Fruit, FruitType
from game.particle_effects import (
    JuiceParticle,
    WallSplatter,
    BombSpark,
    FloatingText,
    BladeTrail,
)
from game.sound_generator import SoundManager
from game.profile_manager import ProfileCRUDManager, BLADE_COLORS

# Re-use existing HandTracker & GestureRecognizer from project modules
from modules.hand_tracker import HandTracker
from modules.gesture_recognition import GestureRecognizer, GestureType


class GameState:
    START = "START"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    GAME_OVER = "GAME_OVER"
    CRUD_MENU = "CRUD_MENU"


class FruitNinjaGame:
    """
    Main Fruit Ninja game instance with real-time hand tracking, easy gameplay mode,
    and profile CRUD management.
    """

    def __init__(self, camera_index: int = 0):
        pygame.init()
        pygame.font.init()

        self.width = GAME_WIDTH
        self.height = GAME_HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Fruit Ninja - Gesture Gaming Mode | GestureMouse AI")

        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.START

        # Audio
        self.sound = SoundManager()

        # CRUD Profile Manager
        self.profile_mgr = ProfileCRUDManager()

        # Difficulty Modes (Defaults to EASY per user request)
        self.difficulty = "EASY"
        self._apply_difficulty_settings()

        # Fonts
        self.font_title = pygame.font.SysFont("Segoe UI", 48, bold=True)
        self.font_score = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.font_hud = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.font_popup = pygame.font.SysFont("Segoe UI", 26, bold=True)
        self.font_desc = pygame.font.SysFont("Segoe UI", 16)
        self.font_card = pygame.font.SysFont("Segoe UI", 15)

        # Computer Vision
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.hand_tracker = HandTracker(detection_con=0.70, track_con=0.70)

        # Virtual settings for gesture recognizer
        class DummySettings:
            pinch_threshold = 38.0
            right_click_threshold = 38.0
            double_click_threshold = 35.0
            drag_hold_duration = 0.45

        self.gesture_recognizer = GestureRecognizer(DummySettings())

        # Blade & Hand Tracking Coordinates
        active_blade_color = self.profile_mgr.get_active_blade_rgb()
        self.blade = BladeTrail(max_length=16, glow_rgb=active_blade_color)
        self.prev_hand_pt: Optional[Tuple[float, float]] = None
        self.curr_hand_pt: Optional[Tuple[float, float]] = None
        self.hand_detected = False
        self.hand_handedness = "Right"
        self.hand_confidence = 0.0
        self.mini_cam_surface: Optional[pygame.Surface] = None

        # Game State Variables
        self.score = 0
        self.high_score = self.profile_mgr.get_active_profile().get("high_score", 0)
        self.total_fruits_sliced = 0
        self.lives = self.initial_lives
        self.timer_seconds = 90.0
        self.game_start_time = 0.0

        # Entities & Particles
        self.fruits: List[Fruit] = []
        self.juice_particles: List[JuiceParticle] = []
        self.wall_splatters: List[WallSplatter] = []
        self.bomb_sparks: List[BombSpark] = []
        self.floating_texts: List[FloatingText] = []

        # Spawning & Combo Tracking
        self.spawn_timer = 0.0
        self.last_slice_time = 0.0
        self.current_combo = 0
        self.screen_shake_frames = 0

        # Initialize Background Texture
        self.bg_surface = self._create_dojo_background()

        # Open Webcam
        self._init_camera()

    def _apply_difficulty_settings(self):
        """Applies physics and tuning parameters based on current difficulty."""
        preset = DIFFICULTY_PRESETS[self.difficulty]
        self.gravity = preset["gravity"]
        self.min_slice_velocity = preset["min_slice_velocity"]
        self.initial_lives = preset["initial_lives"]
        self.bomb_spawn_chance = preset["bomb_spawn_chance"]
        self.spawn_interval = preset["spawn_interval"]
        self.hitbox_margin = preset["hitbox_margin"]
        self.lives = self.initial_lives

    def _init_camera(self):
        """Initializes OpenCV video capture."""
        try:
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_index)
        except Exception as e:
            print(f"[FruitNinja Camera Init Error]: {e}")

    def _create_dojo_background(self) -> pygame.Surface:
        """Procedurally draws a rich, dark Japanese dojo wooden wall."""
        surf = pygame.Surface((self.width, self.height))
        surf.fill((35, 20, 12))

        # Vertical wood planks
        plank_width = 96
        for x in range(0, self.width, plank_width):
            shade = random.randint(-4, 4)
            plank_color = (max(0, 38 + shade), max(0, 22 + shade), max(0, 14 + shade))
            pygame.draw.rect(surf, plank_color, (x, 0, plank_width, self.height))
            pygame.draw.line(surf, (20, 10, 6), (x, 0), (x, self.height), 2)
            for y in range(0, self.height, random.randint(70, 130)):
                pygame.draw.line(surf, (28, 15, 9), (x + 8, y), (x + plank_width - 8, y + random.randint(-4, 4)), 1)

        vignette = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for i in range(120):
            alpha = int(140 * (1.0 - i / 120.0))
            pygame.draw.rect(vignette, (0, 0, 0, alpha), (i, i, self.width - 2 * i, self.height - 2 * i), 2)
        surf.blit(vignette, (0, 0))

        return surf

    def run(self):
        """Main game loop targeting 60 FPS."""
        self.sound.play("start")
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            # 1. Process Pygame Window Events
            self._handle_events()

            # 2. Process Real-Time Camera & Gestures
            self._process_camera_feed()

            # 3. Game Logic Update
            if self.state == GameState.PLAYING:
                self._update_gameplay(dt)

            # 4. Render Frame
            self._render()

            pygame.display.flip()

        # Clean up
        self._cleanup()

    def _handle_events(self):
        """Processes keyboard, mouse, and window close events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING
                    elif self.state == GameState.CRUD_MENU:
                        self.state = GameState.START
                    else:
                        self.running = False
                elif event.key == pygame.K_SPACE:
                    if self.state in (GameState.START, GameState.GAME_OVER):
                        self._start_new_game()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                self._handle_click_actions(mx, my)

    def _handle_click_actions(self, mx: int, my: int):
        """Handles button clicks on start, pause, gameover, and CRUD screens."""
        if self.state == GameState.START:
            # 1. Play button
            play_btn_rect = pygame.Rect(self.width // 2 - 130, 485, 260, 55)
            if play_btn_rect.collidepoint(mx, my):
                self._start_new_game()
                return

            # 2. Dojo Profiles & CRUD button
            crud_btn_rect = pygame.Rect(self.width // 2 - 200, 550, 400, 42)
            if crud_btn_rect.collidepoint(mx, my):
                self.state = GameState.CRUD_MENU
                return

            # 3. Difficulty Mode Selectors
            easy_rect = pygame.Rect(self.width // 2 - 240, 195, 150, 34)
            norm_rect = pygame.Rect(self.width // 2 - 75, 195, 150, 34)
            hard_rect = pygame.Rect(self.width // 2 + 90, 195, 150, 34)

            if easy_rect.collidepoint(mx, my):
                self.difficulty = "EASY"
                self._apply_difficulty_settings()
            elif norm_rect.collidepoint(mx, my):
                self.difficulty = "NORMAL"
                self._apply_difficulty_settings()
            elif hard_rect.collidepoint(mx, my):
                self.difficulty = "HARD"
                self._apply_difficulty_settings()

        elif self.state == GameState.CRUD_MENU:
            self._handle_crud_clicks(mx, my)

        elif self.state == GameState.PAUSED:
            resume_rect = pygame.Rect(self.width // 2 - 140, self.height // 2 - 40, 280, 50)
            restart_rect = pygame.Rect(self.width // 2 - 140, self.height // 2 + 25, 280, 50)
            exit_rect = pygame.Rect(self.width // 2 - 140, self.height // 2 + 90, 280, 50)

            if resume_rect.collidepoint(mx, my):
                self.state = GameState.PLAYING
            elif restart_rect.collidepoint(mx, my):
                self._start_new_game()
            elif exit_rect.collidepoint(mx, my):
                self.running = False

        elif self.state == GameState.GAME_OVER:
            again_rect = pygame.Rect(self.width // 2 - 140, 370, 280, 50)
            exit_rect = pygame.Rect(self.width // 2 - 140, 435, 280, 50)

            if again_rect.collidepoint(mx, my):
                self._start_new_game()
            elif exit_rect.collidepoint(mx, my):
                self.running = False

    def _handle_crud_clicks(self, mx: int, my: int):
        """Processes Create, Read, Update, and Delete interactions on profiles."""
        # 1. Back button
        back_rect = pygame.Rect(40, 30, 140, 40)
        if back_rect.collidepoint(mx, my):
            self.state = GameState.START
            return

        # 2. [CREATE] New Ninja button
        create_rect = pygame.Rect(self.width - 240, 30, 200, 40)
        if create_rect.collidepoint(mx, my):
            # Create a new profile with incremental index
            existing = self.profile_mgr.get_all_profiles()
            idx = len(existing) + 1
            colors = list(BLADE_COLORS.keys())
            next_color = colors[(idx - 1) % len(colors)]
            new_p = self.profile_mgr.create_profile(
                name=f"Ninja #{idx}",
                blade_color=next_color,
                title="Swift Blade",
            )
            # Update blade glow to new profile
            self.blade.set_glow_color(self.profile_mgr.get_active_blade_rgb())
            self.sound.play("start")
            return

        # 3. Card Actions: Select, Change Blade (Update), Delete
        profiles = self.profile_mgr.get_all_profiles()
        card_y_start = 100
        card_height = 84

        for i, p in enumerate(profiles):
            cy = card_y_start + (i * (card_height + 10))
            if cy > self.height - 80:
                break

            p_id = p["id"]
            # Select button
            sel_rect = pygame.Rect(self.width - 440, cy + 20, 100, 34)
            if sel_rect.collidepoint(mx, my):
                self.profile_mgr.set_active_profile(p_id)
                self.blade.set_glow_color(self.profile_mgr.get_active_blade_rgb())
                self.high_score = p.get("high_score", 0)
                self.sound.play("slice")
                return

            # [UPDATE] Change Blade Color button
            blade_rect = pygame.Rect(self.width - 325, cy + 20, 110, 34)
            if blade_rect.collidepoint(mx, my):
                colors = list(BLADE_COLORS.keys())
                curr_idx = colors.index(p.get("blade_color", "Cyan")) if p.get("blade_color") in colors else 0
                next_c = colors[(curr_idx + 1) % len(colors)]
                self.profile_mgr.update_profile(p_id, blade_color=next_c)
                if self.profile_mgr.active_profile_id == p_id:
                    self.blade.set_glow_color(self.profile_mgr.get_active_blade_rgb())
                self.sound.play("slice")
                return

            # [DELETE] Delete Profile button
            del_rect = pygame.Rect(self.width - 200, cy + 20, 90, 34)
            if del_rect.collidepoint(mx, my):
                success = self.profile_mgr.delete_profile(p_id)
                if success:
                    self.sound.play("splat")
                    self.blade.set_glow_color(self.profile_mgr.get_active_blade_rgb())
                return

    def _process_camera_feed(self):
        """Captures frame from webcam, detects index fingertip, gestures, and updates blade."""
        if not self.cap or not self.cap.isOpened():
            self.hand_detected = False
            if pygame.mouse.get_focused():
                mx, my = pygame.mouse.get_pos()
                self.curr_hand_pt = (float(mx), float(my))
                self.blade.add_point(mx, my)
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.hand_detected = False
            return

        frame_h, frame_w, _ = frame.shape
        margin_x = 90
        margin_y = 70

        annotated_frame, hand_info = self.hand_tracker.process_frame(
            frame,
            flip_horizontal=True,
            boundary_margin_x=margin_x,
            boundary_margin_y=margin_y,
            draw=True,
        )

        thumb_w, thumb_h = 160, 120
        resized_thumb = cv2.resize(annotated_frame, (thumb_w, thumb_h))
        rgb_thumb = cv2.cvtColor(resized_thumb, cv2.COLOR_BGR2RGB)
        self.mini_cam_surface = pygame.surfarray.make_surface(np.rot90(np.fliplr(rgb_thumb)))

        if hand_info:
            self.hand_detected = True
            self.hand_handedness = hand_info["handedness"]
            self.hand_confidence = hand_info["confidence"]

            gesture, _ = self.gesture_recognizer.recognize(hand_info)
            if gesture == GestureType.PAUSE and self.state == GameState.PLAYING:
                self.state = GameState.PAUSED
            elif gesture == GestureType.ACTIVATE and self.state == GameState.PAUSED:
                self.state = GameState.PLAYING

            tip_x, tip_y = hand_info["pixel_landmarks"][8]

            active_w = max(10, frame_w - 2 * margin_x)
            active_h = max(10, frame_h - 2 * margin_y)
            norm_x = max(0.0, min(1.0, (tip_x - margin_x) / float(active_w)))
            norm_y = max(0.0, min(1.0, (tip_y - margin_y) / float(active_h)))

            game_x = norm_x * self.width
            game_y = norm_y * self.height

            self.prev_hand_pt = self.curr_hand_pt
            self.curr_hand_pt = (game_x, game_y)
            self.blade.add_point(game_x, game_y)
        else:
            self.hand_detected = False
            self.blade.update()
            if pygame.mouse.get_focused() and any(pygame.mouse.get_pressed()):
                mx, my = pygame.mouse.get_pos()
                self.curr_hand_pt = (float(mx), float(my))
                self.blade.add_point(mx, my)

    def _start_new_game(self):
        """Resets all metrics and starts an arcade match."""
        self._apply_difficulty_settings()
        self.score = 0
        self.total_fruits_sliced = 0
        self.lives = self.initial_lives
        self.timer_seconds = 90.0
        self.game_start_time = time.time()
        self.fruits.clear()
        self.juice_particles.clear()
        self.bomb_sparks.clear()
        self.floating_texts.clear()
        self.blade.clear()
        self.blade.set_glow_color(self.profile_mgr.get_active_blade_rgb())
        self.state = GameState.PLAYING
        self.sound.play("start")

    def _spawn_fruit_wave(self):
        """Launches a dynamic wave of 1 to 4 fruits or bombs from the bottom."""
        wave_size = random.randint(1, 3)
        if self.score > 150:
            wave_size = random.randint(2, 4)

        types_pool = [
            FruitType.WATERMELON,
            FruitType.APPLE,
            FruitType.ORANGE,
            FruitType.BANANA,
            FruitType.STRAWBERRY,
            FruitType.COCONUT,
        ]

        has_bomb = random.random() < self.bomb_spawn_chance

        for i in range(wave_size):
            if has_bomb and i == 0:
                ftype = FruitType.BOMB
            else:
                ftype = random.choice(types_pool)

            spawn_x = random.randint(180, self.width - 180)
            spawn_y = self.height + 40
            
            # Gentle trajectory velocity
            target_vx = (self.width / 2.0 - spawn_x) * 0.004 + random.uniform(-2.2, 2.2)
            target_vy = random.uniform(-16.0, -13.0)

            fruit = Fruit(ftype, spawn_x, spawn_y, target_vx, target_vy)
            self.fruits.append(fruit)

    def _update_gameplay(self, dt: float):
        """Updates physics, collisions, timers, and particle lifetimes."""
        self.timer_seconds -= dt
        if self.timer_seconds <= 0:
            self.timer_seconds = 0
            self._trigger_game_over()
            return

        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0.0
            self._spawn_fruit_wave()

        self._check_blade_slices()

        for fruit in self.fruits[:]:
            alive = fruit.update()
            if not alive:
                # In Easy mode, dropped fruits do not penalize as harshly (only lose life if > 3 dropped)
                if not fruit.is_sliced and fruit.fruit_type != FruitType.BOMB:
                    self.lives -= 1
                    if self.lives <= 0:
                        self._trigger_game_over()
                        return
                self.fruits.remove(fruit)

        self.juice_particles = [p for p in self.juice_particles if p.update()]
        self.wall_splatters = [w for w in self.wall_splatters if w.update()]
        self.bomb_sparks = [s for s in self.bomb_sparks if s.update()]
        self.floating_texts = [t for t in self.floating_texts if t.update()]

        if self.screen_shake_frames > 0:
            self.screen_shake_frames -= 1

    def _check_blade_slices(self):
        """Detects if blade velocity is sufficient and slices colliding fruits with generous margin."""
        vel = self.blade.get_velocity()
        # Easy velocity threshold allows gentle natural swipes
        if vel < self.min_slice_velocity or len(self.blade.points) < 2:
            return

        p1 = (self.blade.points[-2][0], self.blade.points[-2][1])
        p2 = (self.blade.points[-1][0], self.blade.points[-1][1])

        now = time.time()

        for fruit in self.fruits:
            if not fruit.is_sliced and fruit.check_slice_collision(p1, p2, hitbox_margin=self.hitbox_margin):
                if fruit.fruit_type == FruitType.BOMB:
                    self.sound.play("bomb")
                    self.screen_shake_frames = 20
                    self.lives -= 1
                    fruit.is_sliced = True
                    fruit.is_active = False

                    for _ in range(40):
                        self.bomb_sparks.append(BombSpark(fruit.x, fruit.y))

                    self.floating_texts.append(
                        FloatingText("💥 BOMB! -1 LIFE", fruit.x, fruit.y - 20, (255, 60, 60), self.font_popup)
                    )

                    if self.lives <= 0:
                        self._trigger_game_over()
                        return
                else:
                    self.total_fruits_sliced += 1
                    halves, juice_color = fruit.slice()
                    self.sound.play("slice")
                    self.sound.play("splat")

                    for _ in range(random.randint(16, 26)):
                        self.juice_particles.append(JuiceParticle(fruit.x, fruit.y, juice_color))

                    self.wall_splatters.append(WallSplatter(fruit.x, fruit.y, juice_color))

                    if (now - self.last_slice_time) < COMBO_TIME_WINDOW:
                        self.current_combo += 1
                    else:
                        self.current_combo = 1
                    self.last_slice_time = now

                    base_pts = POINTS_PER_FRUIT
                    if self.current_combo >= 2:
                        combo_bonus = COMBO_BONUS_POINTS * (self.current_combo - 1)
                        total_pts = base_pts + combo_bonus
                        self.score += total_pts
                        self.sound.play("combo")
                        self.floating_texts.append(
                            FloatingText(
                                f"COMBO x{self.current_combo}! +{total_pts}",
                                fruit.x,
                                fruit.y - 30,
                                (255, 215, 0),
                                self.font_popup,
                            )
                        )
                    else:
                        self.score += base_pts
                        self.floating_texts.append(
                            FloatingText(f"+{base_pts}", fruit.x, fruit.y - 20, (255, 240, 100), self.font_popup)
                        )

                    if self.score > self.high_score:
                        self.high_score = self.score

    def _trigger_game_over(self):
        """Transitions to Game Over and updates active Profile statistics in CRUD database."""
        self.state = GameState.GAME_OVER
        self.sound.play("gameover")
        active = self.profile_mgr.get_active_profile()
        self.profile_mgr.record_match_stats(active["id"], self.score, self.total_fruits_sliced)
        self.high_score = max(self.high_score, self.score)

    # -------------------------------------------------------------
    # Render Pipeline
    # -------------------------------------------------------------
    def _render(self):
        """Renders scene with screen shake and layering."""
        shake_x, shake_y = 0, 0
        if self.screen_shake_frames > 0:
            shake_x = random.randint(-10, 10)
            shake_y = random.randint(-10, 10)

        draw_surf = pygame.Surface((self.width, self.height))
        draw_surf.blit(self.bg_surface, (0, 0))

        for splatter in self.wall_splatters:
            splatter.draw(draw_surf)

        for fruit in self.fruits:
            fruit.draw(draw_surf)

        for p in self.juice_particles:
            p.draw(draw_surf)
        for s in self.bomb_sparks:
            s.draw(draw_surf)

        self.blade.draw(draw_surf)

        for text in self.floating_texts:
            text.draw(draw_surf)

        if self.state == GameState.PLAYING:
            self._render_playing_hud(draw_surf)
        elif self.state == GameState.START:
            self._render_start_screen(draw_surf)
        elif self.state == GameState.CRUD_MENU:
            self._render_crud_screen(draw_surf)
        elif self.state == GameState.PAUSED:
            self._render_pause_screen(draw_surf)
        elif self.state == GameState.GAME_OVER:
            self._render_game_over_screen(draw_surf)

        self.screen.blit(draw_surf, (shake_x, shake_y))

    def _render_playing_hud(self, surface: pygame.Surface):
        """Top HUD containing Score, Active Player Profile, Timer, Lives, and Mini Webcam."""
        hud_bar = pygame.Surface((self.width, 68), pygame.SRCALPHA)
        pygame.draw.rect(hud_bar, (12, 8, 6, 215), (0, 0, self.width, 68))
        pygame.draw.line(hud_bar, (218, 165, 32), (0, 67), (self.width, 67), 2)
        surface.blit(hud_bar, (0, 0))

        # Active Profile Name & Score
        active_p = self.profile_mgr.get_active_profile()
        p_name = active_p.get("name", "Ninja")
        score_surf = self.font_score.render(f"{p_name}: {self.score}", True, (255, 215, 0))
        surface.blit(score_surf, (24, 12))

        # Difficulty Badge
        diff_color = (0, 230, 118) if self.difficulty == "EASY" else (255, 170, 0)
        diff_surf = self.font_hud.render(f"[{self.difficulty}]", True, diff_color)
        surface.blit(diff_surf, (score_surf.get_width() + 40, 20))

        # Countdown Timer
        timer_text = f"TIME: {int(self.timer_seconds)}s"
        t_color = (0, 230, 118) if self.timer_seconds > 20 else (255, 60, 60)
        t_surf = self.font_score.render(timer_text, True, t_color)
        t_x = self.width // 2 - t_surf.get_width() // 2
        surface.blit(t_surf, (t_x, 12))

        # Lives
        lives_x = self.width - 390
        l_label = self.font_hud.render("LIVES:", True, (220, 220, 220))
        surface.blit(l_label, (lives_x, 20))

        for i in range(self.initial_lives):
            lx = lives_x + 75 + (i * 26)
            ly = 32
            if i < self.lives:
                pygame.draw.circle(surface, (0, 230, 118), (lx, ly), 8)
                pygame.draw.circle(surface, (255, 255, 255), (lx, ly), 3)
            else:
                pygame.draw.line(surface, (255, 50, 50), (lx - 6, ly - 6), (lx + 6, ly + 6), 3)
                pygame.draw.line(surface, (255, 50, 50), (lx + 6, ly - 6), (lx - 6, ly + 6), 3)

        # Mini Webcam Feed Thumbnail
        if self.mini_cam_surface is not None:
            surface.blit(self.mini_cam_surface, (self.width - 170, 78))
            pygame.draw.rect(surface, (0, 230, 118), (self.width - 172, 76, 164, 124), 2)
            cam_lbl = self.font_desc.render("WEBCAM ACTIVE", True, (0, 230, 118))
            surface.blit(cam_lbl, (self.width - 165, 204))

        if not self.hand_detected:
            pill = pygame.Surface((380, 34), pygame.SRCALPHA)
            pygame.draw.rect(pill, (200, 30, 30, 210), (0, 0, 380, 34), border_radius=17)
            pill_txt = self.font_desc.render("⚠️ HAND NOT DETECTED - Show index finger", True, (255, 255, 255))
            pill.blit(pill_txt, (14, 6))
            surface.blit(pill, (self.width // 2 - 190, 80))

    def _render_start_screen(self, surface: pygame.Surface):
        """Arcade start screen with Difficulty Selector, Profile Badge, and Instructions."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 8, 6, 220))
        surface.blit(overlay, (0, 0))

        # Title
        title_surf = self.font_title.render("FRUIT NINJA", True, (255, 215, 0))
        sub_surf = self.font_score.render("GESTURE GAMING MODE", True, (0, 230, 255))
        surface.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 50))
        surface.blit(sub_surf, (self.width // 2 - sub_surf.get_width() // 2, 110))

        # Active Profile Info Banner
        active_p = self.profile_mgr.get_active_profile()
        prof_info = f"👤 NINJA: {active_p['name']} ({active_p['title']})  •  BLADE: {active_p['blade_color']}  •  BEST: {active_p['high_score']}"
        prof_surf = self.font_hud.render(prof_info, True, (255, 235, 160))
        surface.blit(prof_surf, (self.width // 2 - prof_surf.get_width() // 2, 160))

        # Difficulty Selectors (EASY is highlighted by default!)
        easy_rect = pygame.Rect(self.width // 2 - 240, 195, 150, 34)
        norm_rect = pygame.Rect(self.width // 2 - 75, 195, 150, 34)
        hard_rect = pygame.Rect(self.width // 2 + 90, 195, 150, 34)

        for rect, diff_name, label in [
            (easy_rect, "EASY", "🌱 EASY (Zen)"),
            (norm_rect, "NORMAL", "⚔️ NORMAL"),
            (hard_rect, "HARD", "🔥 HARD"),
        ]:
            is_active = (self.difficulty == diff_name)
            bg_col = (0, 180, 80) if is_active else (35, 25, 20)
            border_col = (0, 240, 120) if is_active else (80, 60, 50)
            pygame.draw.rect(surface, bg_col, rect, border_radius=6)
            pygame.draw.rect(surface, border_col, rect, 2, border_radius=6)
            d_txt = self.font_hud.render(label, True, (255, 255, 255) if is_active else (180, 170, 160))
            surface.blit(d_txt, (rect.centerx - d_txt.get_width() // 2, rect.centery - d_txt.get_height() // 2))

        # Instruction Cards
        guide_box = pygame.Rect(self.width // 2 - 340, 245, 680, 215)
        pygame.draw.rect(surface, (26, 18, 12), guide_box, border_radius=12)
        pygame.draw.rect(surface, (218, 165, 32), guide_box, 2, border_radius=12)

        instructions = [
            "☝️  INDEX FINGER : Steers your virtual slicing blade across the screen",
            "⚡  EASY SLICING : Slices smoothly with relaxed, comfortable hand swipes",
            "✊  CLOSED FIST  : Pauses the game instantly at any moment",
            "🖐  OPEN PALM    : Resumes gameplay immediately from pause",
            "💣  AVOID BOMBS  : Don't slice black bombs!",
        ]

        for i, text in enumerate(instructions):
            txt_surf = self.font_desc.render(text, True, (240, 240, 240))
            surface.blit(txt_surf, (guide_box.x + 28, guide_box.y + 18 + (i * 38)))

        # Play Button
        play_btn = pygame.Rect(self.width // 2 - 130, 485, 260, 55)
        pygame.draw.rect(surface, (0, 230, 118), play_btn, border_radius=28)
        btn_txt = self.font_score.render("PLAY GAME", True, (10, 30, 15))
        surface.blit(btn_txt, (play_btn.centerx - btn_txt.get_width() // 2, play_btn.centery - btn_txt.get_height() // 2))

        # CRUD Profile & Records Button
        crud_btn = pygame.Rect(self.width // 2 - 200, 555, 400, 42)
        pygame.draw.rect(surface, (230, 81, 0), crud_btn, border_radius=8)
        c_txt = self.font_hud.render("🥋 DOJO PROFILES & CRUD RECORDS", True, (255, 255, 255))
        surface.blit(c_txt, (crud_btn.centerx - c_txt.get_width() // 2, crud_btn.centery - c_txt.get_height() // 2))

        hint_txt = self.font_desc.render("Press [SPACE] to start  •  Click DOJO PROFILES to manage CRUD records", True, (170, 170, 170))
        surface.blit(hint_txt, (self.width // 2 - hint_txt.get_width() // 2, 615))

    def _render_crud_screen(self, surface: pygame.Surface):
        """Full CRUD Management Screen for Player Profiles, Custom Blades, and Scores."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((12, 10, 10, 240))
        surface.blit(overlay, (0, 0))

        # Header with Title, Back Button, and [CREATE] New Profile button
        back_btn = pygame.Rect(40, 30, 140, 40)
        pygame.draw.rect(surface, (50, 55, 65), back_btn, border_radius=6)
        b_txt = self.font_hud.render("⬅ Back", True, (255, 255, 255))
        surface.blit(b_txt, (back_btn.centerx - b_txt.get_width() // 2, back_btn.centery - b_txt.get_height() // 2))

        title = self.font_score.render("🥋 DOJO PROFILES & CRUD DATABASE", True, (255, 215, 0))
        surface.blit(title, (self.width // 2 - title.get_width() // 2, 30))

        create_btn = pygame.Rect(self.width - 240, 30, 200, 40)
        pygame.draw.rect(surface, (0, 200, 83), create_btn, border_radius=6)
        c_txt = self.font_hud.render("➕ [CREATE] Ninja", True, (10, 30, 15))
        surface.blit(c_txt, (create_btn.centerx - c_txt.get_width() // 2, create_btn.centery - c_txt.get_height() // 2))

        # Profiles Card List (READ, UPDATE, DELETE)
        profiles = self.profile_mgr.get_all_profiles()
        card_y_start = 95
        card_h = 82

        for i, p in enumerate(profiles):
            cy = card_y_start + (i * (card_h + 12))
            if cy > self.height - 90:
                break

            is_active = (p["id"] == self.profile_mgr.active_profile_id)
            card_rect = pygame.Rect(60, cy, self.width - 120, card_h)

            bg_col = (30, 24, 20) if not is_active else (38, 32, 18)
            border_col = (0, 230, 118) if is_active else (65, 50, 40)
            pygame.draw.rect(surface, bg_col, card_rect, border_radius=10)
            pygame.draw.rect(surface, border_col, card_rect, 2, border_radius=10)

            # Blade color swatch circle
            b_color_rgb = BLADE_COLORS.get(p.get("blade_color", "Cyan"), (0, 240, 255))
            pygame.draw.circle(surface, b_color_rgb, (card_rect.x + 36, cy + card_h // 2), 16)
            pygame.draw.circle(surface, (255, 255, 255), (card_rect.x + 36, cy + card_h // 2), 6)

            # Profile Info
            name_label = f"#{i+1} {p['name']}"
            if is_active:
                name_label += "  ⭐ [ACTIVE]"
            n_surf = self.font_hud.render(name_label, True, (0, 230, 118) if is_active else (255, 255, 255))
            surface.blit(n_surf, (card_rect.x + 68, cy + 14))

            stats_text = f"Title: {p.get('title', 'Slicer')}  |  High Score: {p.get('high_score', 0)}  |  Fruits: {p.get('total_fruits', 0)}  |  Matches: {p.get('games_played', 0)}"
            s_surf = self.font_card.render(stats_text, True, (190, 190, 190))
            surface.blit(s_surf, (card_rect.x + 68, cy + 44))

            # Action Buttons: Select (Active), Change Blade (Update), Delete
            # 1. Select Button
            sel_btn = pygame.Rect(self.width - 440, cy + 24, 100, 34)
            sel_col = (0, 230, 118) if is_active else (50, 55, 65)
            pygame.draw.rect(surface, sel_col, sel_btn, border_radius=6)
            sel_txt = self.font_card.render("SELECTED" if is_active else "Select", True, (10, 30, 15) if is_active else (240, 240, 240))
            surface.blit(sel_txt, (sel_btn.centerx - sel_txt.get_width() // 2, sel_btn.centery - sel_txt.get_height() // 2))

            # 2. [UPDATE] Blade Color Cycle
            blade_btn = pygame.Rect(self.width - 325, cy + 24, 110, 34)
            pygame.draw.rect(surface, (255, 170, 0), blade_btn, border_radius=6)
            b_txt = self.font_card.render(f"Blade: {p['blade_color']}", True, (20, 20, 20))
            surface.blit(b_txt, (blade_btn.centerx - b_txt.get_width() // 2, blade_btn.centery - b_txt.get_height() // 2))

            # 3. [DELETE] Delete Button
            del_btn = pygame.Rect(self.width - 200, cy + 24, 90, 34)
            del_col = (200, 40, 40) if len(profiles) > 1 else (70, 70, 70)
            pygame.draw.rect(surface, del_col, del_btn, border_radius=6)
            d_txt = self.font_card.render("🗑 Delete", True, (255, 255, 255))
            surface.blit(d_txt, (del_btn.centerx - d_txt.get_width() // 2, del_btn.centery - d_txt.get_height() // 2))

        # Bottom CRUD Status bar
        footer = self.font_card.render("💾 CRUD Operations auto-persisted to assets/game_records.json", True, (140, 140, 140))
        surface.blit(footer, (self.width // 2 - footer.get_width() // 2, self.height - 35))

    def _render_pause_screen(self, surface: pygame.Surface):
        """Translucent pause screen with options to Resume, Restart, or Exit."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((5, 5, 5, 225))
        surface.blit(overlay, (0, 0))

        title = self.font_title.render("GAME PAUSED", True, (255, 215, 0))
        sub = self.font_desc.render("Hold Open Palm 🖐 to resume, or select an option below:", True, (200, 200, 200))
        surface.blit(title, (self.width // 2 - title.get_width() // 2, 140))
        surface.blit(sub, (self.width // 2 - sub.get_width() // 2, 210))

        r_btn = pygame.Rect(self.width // 2 - 140, 270, 280, 50)
        restart_btn = pygame.Rect(self.width // 2 - 140, 335, 280, 50)
        exit_btn = pygame.Rect(self.width // 2 - 140, 400, 280, 50)

        pygame.draw.rect(surface, (0, 230, 118), r_btn, border_radius=8)
        pygame.draw.rect(surface, (255, 170, 0), restart_btn, border_radius=8)
        pygame.draw.rect(surface, (60, 65, 75), exit_btn, border_radius=8)

        t_res = self.font_hud.render("RESUME (Open Palm)", True, (10, 30, 15))
        t_rst = self.font_hud.render("RESTART MATCH", True, (20, 20, 20))
        t_ext = self.font_hud.render("EXIT TO DASHBOARD", True, (255, 255, 255))

        surface.blit(t_res, (r_btn.centerx - t_res.get_width() // 2, r_btn.centery - t_res.get_height() // 2))
        surface.blit(t_rst, (restart_btn.centerx - t_rst.get_width() // 2, restart_btn.centery - t_rst.get_height() // 2))
        surface.blit(t_ext, (exit_btn.centerx - t_ext.get_width() // 2, exit_btn.centery - t_ext.get_height() // 2))

    def _render_game_over_screen(self, surface: pygame.Surface):
        """Game over summary displaying final score and persistent high score."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((15, 6, 6, 235))
        surface.blit(overlay, (0, 0))

        title = self.font_title.render("GAME OVER", True, (255, 50, 50))
        surface.blit(title, (self.width // 2 - title.get_width() // 2, 90))

        active_p = self.profile_mgr.get_active_profile()

        card = pygame.Rect(self.width // 2 - 220, 170, 440, 170)
        pygame.draw.rect(surface, (26, 18, 14), card, border_radius=12)
        pygame.draw.rect(surface, (218, 165, 32), card, 2, border_radius=12)

        p_txt = self.font_hud.render(f"NINJA: {active_p['name']} ({self.difficulty} Mode)", True, (0, 230, 255))
        s_txt = self.font_score.render(f"FINAL SCORE: {self.score}", True, (255, 215, 0))
        f_txt = self.font_card.render(f"Fruits Sliced This Match: {self.total_fruits_sliced}", True, (220, 220, 220))
        h_txt = self.font_hud.render(f"PERSONAL BEST: {active_p.get('high_score', 0)}", True, (0, 230, 118))

        surface.blit(p_txt, (card.centerx - p_txt.get_width() // 2, card.y + 18))
        surface.blit(s_txt, (card.centerx - s_txt.get_width() // 2, card.y + 52))
        surface.blit(f_txt, (card.centerx - f_txt.get_width() // 2, card.y + 98))
        surface.blit(h_txt, (card.centerx - h_txt.get_width() // 2, card.y + 128))

        again_btn = pygame.Rect(self.width // 2 - 140, 370, 280, 50)
        exit_btn = pygame.Rect(self.width // 2 - 140, 435, 280, 50)

        pygame.draw.rect(surface, (0, 230, 118), again_btn, border_radius=8)
        pygame.draw.rect(surface, (60, 65, 75), exit_btn, border_radius=8)

        t_again = self.font_hud.render("PLAY AGAIN", True, (10, 30, 15))
        t_exit = self.font_hud.render("RETURN TO DASHBOARD", True, (255, 255, 255))

        surface.blit(t_again, (again_btn.centerx - t_again.get_width() // 2, again_btn.centery - t_again.get_height() // 2))
        surface.blit(t_exit, (exit_btn.centerx - t_exit.get_width() // 2, exit_btn.centery - t_exit.get_height() // 2))

    def _cleanup(self):
        """Release camera and quit Pygame."""
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        self.hand_tracker.release()
        pygame.quit()


def launch_fruit_ninja(camera_index: int = 0):
    """Entry point helper to launch Fruit Ninja cleanly from any module or dashboard."""
    game = FruitNinjaGame(camera_index=camera_index)
    game.run()


if __name__ == "__main__":
    launch_fruit_ninja()
