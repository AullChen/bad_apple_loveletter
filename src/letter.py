import sys
import json
import math
import pygame
import numpy as np
from pygame.locals import *
from pygame import gfxdraw
from dataclasses import dataclass, field

# 初始化配置
pygame.init()
pygame.mixer.init()
info = pygame.display.Info()
SCREEN_SIZE = (info.current_w, info.current_h)
FONT = pygame.font.SysFont('simhei', 40)


@dataclass
class PhaseControl:
    """程序阶段状态机"""
    current_phase: int = 0
    phase_times: tuple = (5, 10, 20, 3)  # Increased poetry display time
    transition_alpha: int = 0
    poem_displayed: bool = False
    surprise_message_alpha: int = 0
    poem_lines: list = field(default_factory=list)  # 修改这里
    line_alpha: list = field(default_factory=list)  # 修改这里
    line_positions: list = field(default_factory=list)  # 修改这里


class HeartbeatGenerator:
    """动态心跳音效系统"""

    def __init__(self):
        self.base_freq = 55
        self.samples = 44100
        self.current_sound = None

    def generate(self, intensity, volume):
        """根据情感强度生成心跳"""
        t = np.linspace(0, 0.6, int(self.samples*0.6))
        wave = (np.sin(2*np.pi*self.base_freq*t) *
                np.exp(-5*t) *
                np.clip(np.sin(8*np.pi*t), 0, 1))

        # 转换为立体声（二维数组）
        stereo_wave = np.column_stack((wave, wave))  # 双声道相同数据
        stereo_wave = (stereo_wave * 32767 * intensity *
                       volume).astype(np.int16)

        return pygame.sndarray.make_sound(stereo_wave)


class LoveParticle(pygame.sprite.Sprite):
    """量子纠缠粒子精灵"""

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
        """带阻尼的平滑运动"""
        direction = self.target - self.pos
        distance = np.linalg.norm(direction)
        if distance > 5:
            self.pos += (direction / distance) * self.speed * dt * 60
        self.rect.center = self.pos
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color,
                           (self.size//2, self.size//2), self.size//2)


class PoetryAnimator:
    """动态诗歌渲染器"""

    def __init__(self, poems):
        self.poems = poems
        self.poem_lines = []
        self.line_alpha = []
        self.line_positions = []

    def generate_poem(self):
        """生成完整的诗歌并初始化显示"""
        self.poem_lines = self.poems
        self.line_alpha = [0] * len(self.poem_lines)  # 每行的透明度
        self.line_positions = [SCREEN_SIZE[1] + 40 *
                               i for i in range(len(self.poem_lines))]  # 位置初始化

    def render_text(self, surface, heartbeat_intensity, phase):
        """带心跳律动的文字动画，模仿电影结尾滚动效果"""

        if len(self.poem_lines) == 0:
            self.generate_poem()

        # 动态显示每一行的诗句
        for i, line in enumerate(self.poem_lines):
            if self.line_alpha[i] < 255:
                self.line_alpha[i] = min(
                    255, self.line_alpha[i] + heartbeat_intensity * 5)

            # 滚动显示诗句
            line_surf = FONT.render(line, True, (255, 105, 180))
            line_rect = line_surf.get_rect(
                center=(SCREEN_SIZE[0] // 2, self.line_positions[i]))

            # 增加字体的阴影效果
            shadow_surf = FONT.render(line, True, (50, 50, 50))
            shadow_rect = shadow_surf.get_rect(
                center=(line_rect.centerx + 2, line_rect.centery + 2))
            surface.blit(shadow_surf, shadow_rect)

            # 绘制带有渐变效果的诗句
            line_surf.set_alpha(self.line_alpha[i])
            surface.blit(line_surf, line_rect)

            # 更新行位置，模拟滚动效果
            # Once it’s visible, scroll it upwards
            if self.line_positions[i] > 40:
                self.line_positions[i] -= 1.5  # Scroll speed



class HeartRenderer:
    """实时动态心形渲染器"""

    def __init__(self):
        self.vertices = self._generate_heart_shape()
        self.scale = 0.1
        self.rotation = 0

    def _generate_heart_shape(self):
        """生成心形顶点数据"""
        t = np.linspace(0, 2*np.pi, 100)
        x = 16*np.sin(t)**3
        y = 13*np.cos(t) - 5*np.cos(2*t) - 2*np.cos(3*t) - np.cos(4*t)
        return np.column_stack((x, y))

    def update(self, dt):
        """动态缩放和旋转"""
        self.scale = 0.5 + 0.1 * math.sin(pygame.time.get_ticks()/500)
        self.rotation = pygame.time.get_ticks()/1000

    def draw(self, surface, alpha=255):
        """应用仿射变换绘制"""
        center = np.array(SCREEN_SIZE)//2
        scaled = self.vertices * self.scale * 15
        rotated = scaled @ [[math.cos(self.rotation), -math.sin(self.rotation)],
                            [math.sin(self.rotation), math.cos(self.rotation)]]
        points = (rotated + center).astype(int)

        # 使用抗锯齿绘制心形
        pygame.gfxdraw.filled_polygon(surface, points, (255, 105, 180, alpha))
        pygame.gfxdraw.aapolygon(surface, points, (255, 105, 180, alpha))


def start():
    screen = pygame.display.set_mode(SCREEN_SIZE, FULLSCREEN)
    clock = pygame.time.Clock()

    # 初始化各子系统
    particles = pygame.sprite.Group()
    phase = PhaseControl()
    heart = HeartRenderer()
    poetry = PoetryAnimator(
        json.load(open('../assets/tech_love.json', encoding='utf-8'))['qubits'])
    hb_gen = HeartbeatGenerator()
    last_hb = 0

    # 预生成粒子系统
    for _ in range(500):  # 增加粒子数量
        particles.add(LoveParticle(np.array(SCREEN_SIZE) //
                      2, size=np.random.randint(8, 15)))

    # 主循环
    while True:
        dt = clock.tick(60)/1000
        current_time = pygame.time.get_ticks()

        # 事件处理
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                #pygame.quit()
                #sys.exit()
                return

        # 状态机更新
        if phase.current_phase == 0:
            # 心跳生长阶段
            heartbeat_intensity = min(1, current_time/2000)
            volume = 0.5 + 0.5 * np.sin(current_time / 1000)  # 音量根据时间起伏
            if current_time - last_hb > 600:
                hb_gen.generate(heartbeat_intensity, volume).play()
                last_hb = current_time

            if current_time > phase.phase_times[0]*1000:
                phase.current_phase += 1

        elif phase.current_phase == 1:
            # 粒子聚集阶段
            particles.update(dt)
            if current_time > sum(phase.phase_times[:2])*1000:
                phase.current_phase += 1

        elif phase.current_phase == 2:
            # 诗歌展示阶段
            phase.transition_alpha = min(255, phase.transition_alpha+3)
            if current_time > sum(phase.phase_times[:3])*1000:
                phase.current_phase += 1

        else:
            # 白色淡出阶段
            phase.transition_alpha = min(255, phase.transition_alpha+2)
            phase.surprise_message_alpha = min(
                255, phase.surprise_message_alpha+1)
            if current_time > sum(phase.phase_times)*1000:
                pygame.quit()
                sys.exit()

        # 画面渲染
        screen.fill((30, 30, 30))

        if phase.current_phase < 3:
            particles.draw(screen)
            heart.update(dt)
            heart.draw(screen, phase.transition_alpha)

            if phase.current_phase >= 1:
                poetry.render_text(screen, heartbeat_intensity, phase)

        # 白色淡出层
        if phase.transition_alpha > 0:
            fade_surf = pygame.Surface(SCREEN_SIZE)
            fade_surf.fill((255, 255, 255))
            fade_surf.set_alpha(phase.transition_alpha)
            screen.blit(fade_surf, (0, 0))

        pygame.display.flip()


if __name__ == "__main__":
    start()
