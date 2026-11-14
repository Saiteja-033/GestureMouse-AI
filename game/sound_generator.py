"""
GestureMouse AI - Procedural Arcade Sound Generator
Synthesizes crisp, responsive sound effects for slices, splats, combos, and bomb explosions
using pygame.mixer and numpy. Operates with zero external audio file dependencies.
"""

import math
import numpy as np
import pygame


class SoundManager:
    """
    Manages procedural sound effects for Fruit Ninja gameplay.
    """

    def __init__(self):
        self.enabled = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.sample_rate = 44100
            self.sounds = {
                "slice": self._create_slice_sound(),
                "splat": self._create_splat_sound(),
                "combo": self._create_combo_sound(),
                "bomb": self._create_bomb_sound(),
                "start": self._create_start_sound(),
                "gameover": self._create_gameover_sound(),
            }
            self.enabled = True
        except Exception as e:
            print(f"[SoundManager] Audio initialization note: {e}")
            self.sounds = {}

    def play(self, sound_name: str):
        """Play a cached sound effect if audio is available."""
        if self.enabled and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception:
                pass

    def _create_slice_sound(self) -> pygame.mixer.Sound:
        """Sharp whoosh / blade cut sound (frequency sweep + white noise)."""
        duration = 0.14
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        
        # Fast descending sine whoosh with noise
        freq = np.linspace(2400, 450, num_samples)
        sine_wave = np.sin(2 * np.pi * freq * t)
        noise = (np.random.rand(num_samples) - 0.5) * 0.4
        
        envelope = np.exp(-t * 22)
        audio = (sine_wave + noise) * envelope
        return self._numpy_to_sound(audio, volume=0.5)

    def _create_splat_sound(self) -> pygame.mixer.Sound:
        """Juicy fruit squish / impact sound."""
        duration = 0.20
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)

        freq = np.linspace(350, 90, num_samples)
        sine = np.sin(2 * np.pi * freq * t)
        noise = (np.random.rand(num_samples) - 0.5) * 0.7
        envelope = np.exp(-t * 18)
        audio = (sine * 0.6 + noise * 0.4) * envelope
        return self._numpy_to_sound(audio, volume=0.6)

    def _create_combo_sound(self) -> pygame.mixer.Sound:
        """Upbeat dual-tone chime for multi-fruit combos."""
        duration = 0.35
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)

        # Chime notes: C6 (1046 Hz) and G6 (1568 Hz)
        t1 = t[: num_samples // 2]
        t2 = t[num_samples // 2 :]
        tone1 = np.sin(2 * np.pi * 1046 * t1) * np.exp(-t1 * 14)
        tone2 = np.sin(2 * np.pi * 1568 * t2) * np.exp(-t2 * 10)
        audio = np.concatenate([tone1, tone2])
        return self._numpy_to_sound(audio, volume=0.7)

    def _create_bomb_sound(self) -> pygame.mixer.Sound:
        """Heavy bass explosion sound with low rumble."""
        duration = 0.85
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)

        freq = np.linspace(140, 25, num_samples)
        bass = np.sin(2 * np.pi * freq * t)
        noise = (np.random.rand(num_samples) - 0.5) * 1.0
        envelope = np.exp(-t * 5.0)
        audio = (bass * 0.5 + noise * 0.5) * envelope
        return self._numpy_to_sound(audio, volume=0.85)

    def _create_start_sound(self) -> pygame.mixer.Sound:
        """Rising arcade fanfare chord."""
        duration = 0.45
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        chord = (
            np.sin(2 * np.pi * 523 * t)
            + np.sin(2 * np.pi * 659 * t)
            + np.sin(2 * np.pi * 784 * t)
        ) / 3.0
        envelope = np.exp(-t * 6.0)
        audio = chord * envelope
        return self._numpy_to_sound(audio, volume=0.6)

    def _create_gameover_sound(self) -> pygame.mixer.Sound:
        """Descending game over tritone."""
        duration = 0.70
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        freq = np.linspace(440, 110, num_samples)
        audio = np.sin(2 * np.pi * freq * t) * np.exp(-t * 4.0)
        return self._numpy_to_sound(audio, volume=0.7)

    def _numpy_to_sound(self, audio_arr: np.ndarray, volume: float = 0.5) -> pygame.mixer.Sound:
        """Converts float numpy audio array into a stereo 16-bit pygame Sound."""
        audio_arr = np.clip(audio_arr * volume, -1.0, 1.0)
        int16_arr = (audio_arr * 32767).astype(np.int16)
        stereo = np.column_stack((int16_arr, int16_arr))
        return pygame.sndarray.make_sound(stereo)
