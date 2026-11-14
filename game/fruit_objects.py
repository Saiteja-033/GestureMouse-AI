"""
GestureMouse AI - Fruit & Bomb Physics Objects
Procedurally renders crisp arcade fruits (Watermelon, Apple, Orange, Banana, Strawberry, Coconut)
and bombs with realistic parabolic physics, rotation, and half-splitting mechanics.
"""

import math
import random
import pygame
from typing import Tuple, List, Optional
from game.game_settings import GRAVITY


class FruitType:
    WATERMELON = "Watermelon"
    APPLE = "Apple"
    ORANGE = "Orange"
    BANANA = "Banana"
    STRAWBERRY = "Strawberry"
    COCONUT = "Coconut"
    BOMB = "Bomb"


FRUIT_CONFIGS = {
    FruitType.WATERMELON: {
        "radius": 44,
        "juice_color": (235, 45, 65),
        "rind_color": (34, 139, 34),
        "inner_color": (230, 40, 60),
    },
    FruitType.ORANGE: {
        "radius": 38,
        "juice_color": (255, 140, 0),
        "rind_color": (255, 120, 0),
        "inner_color": (255, 180, 50),
    },
    FruitType.APPLE: {
        "radius": 36,
        "juice_color": (220, 40, 40),
        "rind_color": (210, 25, 35),
        "inner_color": (250, 245, 215),
    },
    FruitType.BANANA: {
        "radius": 40,
        "juice_color": (255, 225, 40),
        "rind_color": (250, 220, 20),
        "inner_color": (250, 248, 210),
    },
    FruitType.STRAWBERRY: {
        "radius": 32,
        "juice_color": (225, 30, 55),
        "rind_color": (220, 25, 45),
        "inner_color": (245, 140, 155),
    },
    FruitType.COCONUT: {
        "radius": 40,
        "juice_color": (240, 240, 240),
        "rind_color": (100, 60, 30),
        "inner_color": (250, 250, 250),
    },
    FruitType.BOMB: {
        "radius": 36,
        "juice_color": (80, 80, 80),
        "rind_color": (40, 44, 52),
        "inner_color": (30, 32, 38),
    },
}


class FruitHalf:
    """A sliced half of a fruit falling away with outward momentum and rotation."""

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        angular_vel: float,
        surface: pygame.Surface,
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.angle = 0.0
        self.angular_vel = angular_vel
        self.base_surface = surface
        self.is_active = True

    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.vy += GRAVITY
        self.angle += self.angular_vel
        # Deactivate if fallen off bottom of screen
        if self.y > 850:
            self.is_active = False
        return self.is_active

    def draw(self, surface: pygame.Surface):
        if not self.is_active:
            return
        rotated = pygame.transform.rotate(self.base_surface, self.angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)


class Fruit:
    """
    Airborne arcade fruit or hazard bomb with parabolic trajectory,
    smooth rotation, and slice collision detection.
    """

    def __init__(self, fruit_type: str, x: float, y: float, vx: float, vy: float):
        self.fruit_type = fruit_type
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.angle = 0.0
        self.angular_vel = random.uniform(-4.0, 4.0)

        cfg = FRUIT_CONFIGS[fruit_type]
        self.radius = cfg["radius"]
        self.juice_color = cfg["juice_color"]
        self.rind_color = cfg["rind_color"]
        self.inner_color = cfg["inner_color"]

        self.is_sliced = False
        self.is_active = True
        self.halves: List[FruitHalf] = []
        self.fuse_spark_timer = 0

        # Pre-render graphical assets for this fruit
        self.base_surface, self.left_half_surf, self.right_half_surf = self._render_fruit_surfaces()

    def update(self) -> bool:
        """Advance trajectory and rotation. Returns True if object is still on screen."""
        if not self.is_sliced:
            self.x += self.vx
            self.y += self.vy
            self.vy += GRAVITY
            self.angle += self.angular_vel

            # Dropped off screen without being sliced
            if self.vy > 0 and self.y > 780:
                self.is_active = False
                return False
            return True
        else:
            # Update sliced halves
            alive_halves = False
            for half in self.halves:
                if half.update():
                    alive_halves = True
            if not alive_halves:
                self.is_active = False
            return alive_halves

    def slice(self) -> Tuple[List[FruitHalf], Tuple[int, int, int]]:
        """Splits fruit into two rotating halves and returns juice splash color."""
        if self.is_sliced:
            return [], self.juice_color

        self.is_sliced = True
        if self.fruit_type != FruitType.BOMB:
            # Spawn left and right halves with outward explosion velocity
            half_left = FruitHalf(
                x=self.x - 8,
                y=self.y,
                vx=self.vx - random.uniform(3.0, 5.0),
                vy=self.vy - random.uniform(1.0, 3.0),
                angular_vel=-random.uniform(4.0, 8.0),
                surface=self.left_half_surf,
            )
            half_right = FruitHalf(
                x=self.x + 8,
                y=self.y,
                vx=self.vx + random.uniform(3.0, 5.0),
                vy=self.vy - random.uniform(1.0, 3.0),
                angular_vel=random.uniform(4.0, 8.0),
                surface=self.right_half_surf,
            )
            self.halves = [half_left, half_right]

        return self.halves, self.juice_color

    def check_slice_collision(self, p1: Tuple[float, float], p2: Tuple[float, float], hitbox_margin: float = 10.0) -> bool:
        """
        Calculates distance from fruit center to blade line segment (p1 -> p2).
        Returns True if segment intersects fruit collision radius + generous margin.
        """
        if self.is_sliced or not self.is_active:
            return False

        x1, y1 = p1
        x2, y2 = p2
        cx, cy = self.x, self.y

        dx = x2 - x1
        dy = y2 - y1
        length_sq = dx * dx + dy * dy

        if length_sq < 0.001:
            # Point-to-circle check
            dist = math.hypot(cx - x1, cy - y1)
            return dist <= (self.radius + hitbox_margin)

        # Project fruit center onto segment clamped to [0, 1]
        t = max(0.0, min(1.0, ((cx - x1) * dx + (cy - y1) * dy) / length_sq))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy

        dist = math.hypot(cx - proj_x, cy - proj_y)
        return dist <= (self.radius + hitbox_margin)

    def draw(self, surface: pygame.Surface):
        """Render whole fruit or flying sliced halves."""
        if not self.is_sliced:
            rotated = pygame.transform.rotate(self.base_surface, self.angle)
            rect = rotated.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rotated, rect)

            # Special bomb fuse rendering
            if self.fruit_type == FruitType.BOMB:
                fuse_x = int(self.x + math.cos(math.radians(-self.angle - 90)) * (self.radius + 6))
                fuse_y = int(self.y + math.sin(math.radians(-self.angle - 90)) * (self.radius + 6))
                pygame.draw.circle(surface, (255, 230, 60), (fuse_x, fuse_y), 4)
                pygame.draw.circle(surface, (255, 100, 20), (fuse_x, fuse_y), 2)
        else:
            for half in self.halves:
                half.draw(surface)

    def _render_fruit_surfaces(self) -> Tuple[pygame.Surface, pygame.Surface, pygame.Surface]:
        """Procedurally draws full fruit and sliced half surfaces."""
        rad = self.radius
        size = rad * 2 + 10
        center = (size // 2, size // 2)

        full_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        left_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        right_surf = pygame.Surface((size, size), pygame.SRCALPHA)

        cx, cy = center

        if self.fruit_type == FruitType.BOMB:
            # Metallic bomb sphere
            pygame.draw.circle(full_surf, (30, 32, 40), center, rad)
            pygame.draw.circle(full_surf, (55, 60, 72), (cx - rad // 3, cy - rad // 3), rad // 3)
            # Rim highlight
            pygame.draw.circle(full_surf, (70, 75, 88), center, rad, 2)
            # Skull / Bomb Icon
            pygame.draw.rect(full_surf, (220, 50, 50), (cx - 10, cy - 10, 20, 20), border_radius=4)
            pygame.draw.line(full_surf, (255, 255, 255), (cx - 6, cy - 6), (cx + 6, cy + 6), 3)
            pygame.draw.line(full_surf, (255, 255, 255), (cx + 6, cy - 6), (cx - 6, cy + 6), 3)

        elif self.fruit_type == FruitType.WATERMELON:
            # Full green striped melon
            pygame.draw.circle(full_surf, self.rind_color, center, rad)
            # Dark green stripes
            for a in range(0, 360, 45):
                rad_a = math.radians(a)
                p1 = (int(cx + math.cos(rad_a) * (rad - 1)), int(cy + math.sin(rad_a) * (rad - 1)))
                p2 = (int(cx + math.cos(rad_a + 0.3) * (rad - 1)), int(cy + math.sin(rad_a + 0.3) * (rad - 1)))
                pygame.draw.line(full_surf, (15, 80, 20), p1, p2, 4)

            # Left Half (cut face showing red interior, white rind, seeds)
            pygame.draw.arc(left_surf, self.rind_color, (cx - rad, cy - rad, rad * 2, rad * 2), math.pi / 2, 3 * math.pi / 2, 6)
            pygame.draw.circle(left_surf, self.inner_color, center, rad - 5)
            # Clip right side
            left_surf.fill((0, 0, 0, 0), rect=(cx, 0, size - cx, size))
            # Seeds
            pygame.draw.circle(left_surf, (20, 20, 20), (cx - 14, cy - 8), 3)
            pygame.draw.circle(left_surf, (20, 20, 20), (cx - 18, cy + 10), 3)

            # Right Half
            pygame.draw.arc(right_surf, self.rind_color, (cx - rad, cy - rad, rad * 2, rad * 2), -math.pi / 2, math.pi / 2, 6)
            pygame.draw.circle(right_surf, self.inner_color, center, rad - 5)
            # Clip left side
            right_surf.fill((0, 0, 0, 0), rect=(0, 0, cx, size))
            # Seeds
            pygame.draw.circle(right_surf, (20, 20, 20), (cx + 14, cy - 8), 3)
            pygame.draw.circle(right_surf, (20, 20, 20), (cx + 18, cy + 10), 3)

        else:
            # Generic fruit: Apple, Orange, Banana, Strawberry, Coconut
            pygame.draw.circle(full_surf, self.rind_color, center, rad)
            # Gloss highlight
            pygame.draw.circle(full_surf, (255, 255, 255, 120), (cx - rad // 3, cy - rad // 3), rad // 3)

            # Left half
            pygame.draw.circle(left_surf, self.rind_color, center, rad)
            pygame.draw.circle(left_surf, self.inner_color, center, rad - 4)
            left_surf.fill((0, 0, 0, 0), rect=(cx, 0, size - cx, size))

            # Right half
            pygame.draw.circle(right_surf, self.rind_color, center, rad)
            pygame.draw.circle(right_surf, self.inner_color, center, rad - 4)
            right_surf.fill((0, 0, 0, 0), rect=(0, 0, cx, size))

        return full_surf, left_surf, right_surf
