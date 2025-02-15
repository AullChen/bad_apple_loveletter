"""
    Love Letter Animation with Pygame
    This script implements a visual love letter animation using Pygame.
    It includes a heartbeat sound effect, particle effects, and scrolling poetry.
"""

import sys
import json
import math
import pygame
import numpy as np
from pygame.locals import *
from pygame import gfxdraw
from dataclasses import dataclass, field

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init()
info = pygame.display.Info()
SCREEN_SIZE = (info.current_w, info.current_h)
FONT = pygame.font.SysFont('simhei', 40)


@dataclass
class PhaseControl:
    """Program phase state machine"""
    current_phase: int = 0
    phase_times: tuple = (5, 10, 20, 3)  # Increased poetry display time
    transition_alpha: int = 0
    poem_displayed: bool = False
    surprise_message_alpha: int = 0
    poem_lines: list = field(default_factory=list)
    line_alpha: list = field(default_factory=list)
    line_positions: list = field(default_factory=list)


class HeartbeatGenerator:
    """Dynamic heartbeat sound effect system"""

    def __init__(self):
        self.base_freq = 55
        self.samples = 44100
        self.current_sound = None

    def generate(self, intensity, volume):
        """Generate heartbeat based on emotional intensity"""
        t = np.linspace(0, 0.6, int(self.samples*0.6))
        wave = (np.sin(2*np.pi*self.base_freq*t) *
                np.exp(-5*t) *
                np.clip(np.sin(8*np.pi*t), 0, 1))

        # Convert to stereo (two-channel same data)
        stereo_wave = np.column_stack((wave, wave))
        stereo_wave = (stereo_wave * 32767 * intensity *
                       volume).astype(np.int16)

        return pygame.sndarray.make_sound(stereo_wave)


class LoveParticle(pygame.sprite.Sprite):
    """Quantum entangled particle sprite"""

    def __init__(self, target_pos, size=5):
        super().__init__()
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.pos = np.array([np.random.uniform(0, SCREEN_SIZE[0]),
                             np.random.uniform(0, SCREEN_SIZE[1])], dtype=float)
        self.target = target_pos
        self.speed = np.random.uniform(2, 4)
        self.size = size
        hue = np.random.randint(0, 360)
        self.color = pygame.Color(0)
        self.color.hsva = (hue, 100, 100, 100)

    def update(self, dt):
        """Damped smooth movement"""
        direction = self.target - self.pos
        distance = np.linalg.norm(direction)
        if distance > 5:
            self.pos += (direction / distance) * self.speed * dt * 60
        self.rect.center = self.pos
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color,
                           (self.size//2, self.size//2), self.size//2)


class PoetryAnimator:
    """Dynamic poetry renderer"""

    def __init__(self, poems):
        self.poems = poems
        self.poem_lines = []
        self.line_alpha = []
        self.line_positions = []

    def generate_poem(self):
        """Generate complete poem and initialize display"""
        self.poem_lines = self.poems
        self.line_alpha = [0] * len(self.poem_lines)  # Alpha for each line
        self.line_positions = [SCREEN_SIZE[1] + 40 *
                               i for i in range(len(self.poem_lines))]  # Initialize positions

    def render_text(self, surface, heartbeat_intensity, phase):
        """Heartbeat rhythm text animation, mimicking movie ending scroll effect"""

        if len(self.poem_lines) == 0:
            self.generate_poem()

        # Dynamically display each line of the poem
        for i, line in enumerate(self.poem_lines):
            if self.line_alpha[i] < 255:
                self.line_alpha[i] = min(
                    255, self.line_alpha[i] + heartbeat_intensity * 5)

            # Scroll display of the poem
            line_surf = FONT.render(line, True, (255, 105, 180))
            line_rect = line_surf.get_rect(
                center=(SCREEN_SIZE[0] // 2, self.line_positions[i]))

            # Add shadow effect to the font
            shadow_surf = FONT.render(line, True, (50, 50, 50))
            shadow_rect = shadow_surf.get_rect(
                center=(line_rect.centerx + 2, line_rect.centery + 2))
            surface.blit(shadow_surf, shadow_rect)

            # Draw text with gradient effect
            line_surf.set_alpha(self.line_alpha[i])
            surface.blit(line_surf, line_rect)

            # Update line position, simulating scroll effect
            if self.line_positions[i] > 40:
                self.line_positions[i] -= 1.5  # Scroll speed


class HeartRenderer:
    """Real-time dynamic heart shape renderer"""

    def __init__(self):
        self.vertices = self._generate_heart_shape()
        self.scale = 0.1
        self.rotation = 0

    def _generate_heart_shape(self):
        """Generate heart shape vertices"""
        t = np.linspace(0, 2*np.pi, 100)
        x = 16*np.sin(t)**3
        y = 13*np.cos(t) - 5*np.cos(2*t) - 2*np.cos(3*t) - np.cos(4*t)
        return np.column_stack((x, y))

    def update(self, dt):
        """Dynamic scaling and rotation"""
        self.scale = 0.5 + 0.1 * math.sin(pygame.time.get_ticks()/500)
        self.rotation = pygame.time.get_ticks()/1000

    def draw(self, surface, alpha=255):
        """Apply affine transformation to draw"""
        center = np.array(SCREEN_SIZE)//2
        scaled = self.vertices * self.scale * 15
        rotated = scaled @ [[math.cos(self.rotation), -math.sin(self.rotation)],
                            [math.sin(self.rotation), math.cos(self.rotation)]]
        points = (rotated + center).astype(int)

        # Use anti-aliasing to draw heart
        pygame.gfxdraw.filled_polygon(surface, points, (255, 105, 180, alpha))
        pygame.gfxdraw.aapolygon(surface, points, (255, 105, 180, alpha))


def start():
    screen = pygame.display.set_mode(SCREEN_SIZE, FULLSCREEN)
    clock = pygame.time.Clock()

    # Initialize subsystems
    particles = pygame.sprite.Group()
    phase = PhaseControl()
    heart = HeartRenderer()
    poetry = PoetryAnimator(
        json.load(open('../assets/tech_love.json', encoding='utf-8'))['qubits'])
    hb_gen = HeartbeatGenerator()
    last_hb = 0

    # Pre-generate particle system
    for _ in range(500):  # Increase particle count
        particles.add(LoveParticle(np.array(SCREEN_SIZE) //
                      2, size=np.random.randint(8, 15)))

    # Main loop
    while True:
        dt = clock.tick(60)/1000
        current_time = pygame.time.get_ticks()

        # Event handling
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                return

        # State machine update
        if phase.current_phase == 0:
            # Heartbeat growth phase
            heartbeat_intensity = min(1, current_time/2000)
            # Volume varies with time
            volume = 0.5 + 0.5 * np.sin(current_time / 1000)
            if current_time - last_hb > 600:
                hb_gen.generate(heartbeat_intensity, volume).play()
                last_hb = current_time

            if current_time > phase.phase_times[0]*1000:
                phase.current_phase += 1

        elif phase.current_phase == 1:
            # Particle aggregation phase
            particles.update(dt)
            if current_time > sum(phase.phase_times[:2])*1000:
                phase.current_phase += 1

        elif phase.current_phase == 2:
            # Poetry display phase
            phase.transition_alpha = min(255, phase.transition_alpha+3)
            if current_time > sum(phase.phase_times[:3])*1000:
                phase.current_phase += 1

        else:
            # White fade-out phase
            phase.transition_alpha = min(255, phase.transition_alpha+2)
            phase.surprise_message_alpha = min(
                255, phase.surprise_message_alpha+1)
            if current_time > sum(phase.phase_times)*1000:
                pygame.quit()
                sys.exit()

        # Screen rendering
        screen.fill((30, 30, 30))

        if phase.current_phase < 3:
            particles.draw(screen)
            heart.update(dt)
            heart.draw(screen, phase.transition_alpha)

            if phase.current_phase >= 1:
                poetry.render_text(screen, heartbeat_intensity, phase)

        # White fade-out layer
        if phase.transition_alpha > 0:
            fade_surf = pygame.Surface(SCREEN_SIZE)
            fade_surf.fill((255, 255, 255))
            fade_surf.set_alpha(phase.transition_alpha)
            screen.blit(fade_surf, (0, 0))

        pygame.display.flip()


if __name__ == "__main__":
    start()
