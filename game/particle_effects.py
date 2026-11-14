"""
GestureMouse AI - Particle Effects & Blade Trail System
Renders glowing motion blade trails, juice splatter bursts, background wall stains,
bomb fuse sparks, and floating score notifications.
"""

import math
import random
import time
import pygame
from typing import List, Tuple, Dict, Any


class JuiceParticle:
    """Individual flying droplet of fruit juice."""

    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3.0, 10.5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(1.0, 4.0)
        self.radius = random.uniform(3.0, 7.5)
        self.gravity = 0.35
        self.alpha = 255.0
        self.fade_rate = random.uniform(5.0, 9.0)

    def update(self) -> bool:
        """Update position and fade. Returns True if alive."""
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.97
        self.alpha -= self.fade_rate
        self.radius = max(0.8, self.radius * 0.98)
        return self.alpha > 0

    def draw(self, surface: pygame.Surface):
        if self.alpha <= 0:
            return
        draw_color = (*self.color, max(0, min(255, int(self.alpha))))
        p_surf = pygame.Surface((int(self.radius * 2 + 2), int(self.radius * 2 + 2)), pygame.SRCALPHA)
        pygame.draw.circle(p_surf, draw_color, (int(self.radius + 1), int(self.radius + 1)), int(self.radius))
        surface.blit(p_surf, (int(self.x - self.radius), int(self.y - self.radius)))


class WallSplatter:
    """Semi-permanent juice splash stuck against the background dojo wall."""

    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        self.alpha = 180.0
        self.fade_rate = 0.45  # Stays visible for ~6-7 seconds
        
        # Pre-render splatter stamp
        self.size = random.randint(45, 80)
        self.surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        center = (self.size, self.size)
        # Main splash
        pygame.draw.circle(self.surface, color, center, random.randint(14, 26))
        # Surrounding droplets
        for _ in range(random.randint(6, 12)):
            offset_angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(15, self.size - 8)
            drop_x = int(center[0] + math.cos(offset_angle) * dist)
            drop_y = int(center[1] + math.sin(offset_angle) * dist)
            drop_rad = random.randint(2, 6)
            pygame.draw.circle(self.surface, color, (drop_x, drop_y), drop_rad)

    def update(self) -> bool:
        self.alpha -= self.fade_rate
        return self.alpha > 0

    def draw(self, surface: pygame.Surface):
        if self.alpha <= 0:
            return
        stamp = self.surface.copy()
        stamp.set_alpha(max(0, min(255, int(self.alpha))))
        surface.blit(stamp, (int(self.x - self.size), int(self.y - self.size)))


class BombSpark:
    """Fiery spark flying from a lit bomb fuse."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        angle = random.uniform(-math.pi, math.pi)
        speed = random.uniform(1.5, 4.5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 1.0
        self.life = random.randint(10, 20)
        self.age = 0
        self.color = random.choice([(255, 240, 60), (255, 160, 20), (255, 80, 20)])

    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.age += 1
        return self.age < self.life

    def draw(self, surface: pygame.Surface):
        rad = max(1, int(3 * (1 - self.age / self.life)))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), rad)


class FloatingText:
    """Animated rising score notification (e.g. '+10', 'COMBO x3! +50')."""

    def __init__(self, text: str, x: float, y: float, color: Tuple[int, int, int], font: pygame.font.Font):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.font = font
        self.vy = -2.2
        self.alpha = 255.0
        self.fade_rate = 5.5

    def update(self) -> bool:
        self.y += self.vy
        self.vy *= 0.96
        self.alpha -= self.fade_rate
        return self.alpha > 0

    def draw(self, surface: pygame.Surface):
        if self.alpha <= 0:
            return
        # Render text with outline
        text_surf = self.font.render(self.text, True, self.color)
        outline_surf = self.font.render(self.text, True, (0, 0, 0))

        t_w, t_h = text_surf.get_size()
        draw_surf = pygame.Surface((t_w + 6, t_h + 6), pygame.SRCALPHA)

        # Draw black outline
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]:
            draw_surf.blit(outline_surf, (dx + 3, dy + 3))
        draw_surf.blit(text_surf, (3, 3))

        draw_surf.set_alpha(max(0, min(255, int(self.alpha))))
        surface.blit(draw_surf, (int(self.x - t_w / 2), int(self.y - t_h / 2)))


class BladeTrail:
    """
    High-tech glowing slicing trail mapped to the player's index fingertip.
    Connects recent coordinates with tapering line widths and customizable glow colors.
    """

    def __init__(self, max_length: int = 16, glow_rgb: Tuple[int, int, int] = (0, 240, 255)):
        self.max_length = max_length
        self.glow_rgb = glow_rgb
        self.points: List[Tuple[float, float, float]] = []  # (x, y, timestamp)

    def set_glow_color(self, rgb: Tuple[int, int, int]):
        self.glow_rgb = rgb

    def add_point(self, x: float, y: float):
        """Append a new fingertip position with current wall clock."""
        now = time.time()
        self.points.append((x, y, now))
        if len(self.points) > self.max_length:
            self.points.pop(0)

    def clear(self):
        self.points.clear()

    def update(self):
        """Remove points that are older than 0.22 seconds."""
        now = time.time()
        self.points = [(x, y, t) for x, y, t in self.points if now - t < 0.22]

    def get_velocity(self) -> float:
        """Returns velocity in pixels per frame between last two recorded points."""
        if len(self.points) < 2:
            return 0.0
        p1 = self.points[-2]
        p2 = self.points[-1]
        dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        dt = max(0.001, p2[2] - p1[2])
        # Approximate px per 60fps frame
        return (dist / dt) / 60.0

    def draw(self, surface: pygame.Surface):
        """Renders layered glowing polygon/lines for the blade trail."""
        if len(self.points) < 2:
            return

        now = time.time()
        total_pts = len(self.points)

        for i in range(total_pts - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]

            # Progression factor (0.0 oldest -> 1.0 newest tip)
            t_factor = (i + 1) / float(total_pts)
            age = now - p2[2]
            alpha_ratio = max(0.0, 1.0 - (age / 0.22)) * t_factor

            # Outer glow
            glow_width = max(2, int(10 * t_factor))
            glow_color = (*self.glow_rgb, int(170 * alpha_ratio))
            
            # Inner white blade core
            core_width = max(1, int(4 * t_factor))
            core_color = (255, 255, 255, int(255 * alpha_ratio))

            start_pos = (int(p1[0]), int(p1[1]))
            end_pos = (int(p2[0]), int(p2[1]))

            # Glow line
            glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.line(glow_surf, glow_color, start_pos, end_pos, glow_width)
            pygame.draw.line(glow_surf, core_color, start_pos, end_pos, core_width)
            surface.blit(glow_surf, (0, 0))

        # Glowing spark at newest fingertip
        tip = self.points[-1]
        tip_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(tip_surf, (*self.glow_rgb, 180), (16, 16), 12)
        pygame.draw.circle(tip_surf, (255, 255, 255, 255), (16, 16), 5)
        surface.blit(tip_surf, (int(tip[0] - 16), int(tip[1] - 16)))
