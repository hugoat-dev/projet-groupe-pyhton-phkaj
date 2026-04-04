import math
import random
from dataclasses import dataclass

import pygame

from config import clamp, W, H


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    age: float
    kind: str
    size: float
    col: tuple
    gravity: float = 0.0
    rot: float = 0.0
    rot_speed: float = 0.0

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.vx *= (1.0 - 0.8 * dt)
        self.vy *= (1.0 - 0.8 * dt)
        self.rot += self.rot_speed * dt

    def dead(self):
        return self.age >= self.life

    def draw(self, screen):
        t = 1.0 - (self.age / max(1e-6, self.life))
        a = int(255 * clamp(t, 0.0, 1.0))
        r = max(1, int(self.size * clamp(t, 0.1, 1.0)))
        surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.col[:3], a), (r + 1, r + 1), r)
        screen.blit(surf, (int(self.x - r), int(self.y - r)))


@dataclass
class FloatText:
    x: float
    y: float
    text: str
    col: tuple
    life: float = 1.2
    age: float = 0.0
    font: object = None

    def update(self, dt):
        self.age += dt
        self.y -= 55 * dt

    def dead(self):
        return self.age >= self.life

    def draw(self, screen):
        t = 1.0 - (self.age / max(1e-6, self.life))
        a = int(255 * min(1.0, t * 2))
        scale = 1.0 + 0.3 * (1.0 - t)
        txt = self.font.render(self.text, True, self.col)
        w, h = txt.get_width(), txt.get_height()
        big = pygame.transform.scale(txt, (int(w * scale), int(h * scale)))
        big.set_alpha(a)
        screen.blit(big, (int(self.x - big.get_width() // 2), int(self.y - big.get_height() // 2)))


class ScreenShake:
    def __init__(self):
        self.intensity = 0.0
        self.trauma = 0.0

    def shake(self, amount):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt):
        self.trauma = max(0.0, self.trauma - dt * 2.5)
        self.intensity = self.trauma ** 2

    def offset(self):
        if self.intensity < 0.001:
            return (0, 0)
        mx = 18 * self.intensity
        return (random.uniform(-mx, mx), random.uniform(-mx, mx))


class FadeTransition:
    def __init__(self, duration=0.35):
        self.duration = duration
        self.timer = 0.0
        self.fading_out = True
        self.done = False
        self.alpha = 0

    def update(self, dt):
        self.timer += dt
        t = min(1.0, self.timer / self.duration)
        if self.fading_out:
            self.alpha = int(255 * t)
            if self.timer >= self.duration:
                self.fading_out = False
                self.timer = 0.0
        else:
            self.alpha = int(255 * (1.0 - t))
            if self.timer >= self.duration:
                self.done = True

    def draw(self, screen):
        if self.alpha > 0:
            ov = pygame.Surface((W, H))
            ov.fill((0, 0, 0))
            ov.set_alpha(self.alpha)
            screen.blit(ov, (0, 0))


class MenuParticles:
    def __init__(self):
        self.items = []
        self.spawn_t = 0.0

    def update(self, dt, mode, intensity):
        rate = {"low": 0.35, "med": 0.18, "high": 0.08}.get(intensity, 0.18)
        self.spawn_t += dt
        while self.spawn_t >= rate:
            self.spawn_t -= rate
            if mode == "ocean":
                x = random.uniform(0, W)
                self.items.append(["bubble", x, H + 10, random.uniform(-12, 12),
                                   random.uniform(-60, -90), random.uniform(0.8, 1.6), random.uniform(0, 6)])
            elif mode == "jungle":
                x = random.uniform(0, W)
                self.items.append(["leaf", x, -14, random.uniform(-18, 18),
                                   random.uniform(40, 70), random.uniform(0, math.tau), random.uniform(0.8, 1.3)])
            else:
                self.items.append(["star", random.uniform(0, W), random.uniform(0, H),
                                   0, random.uniform(25, 120), random.uniform(1, 2.8), 0])
        for it in self.items:
            if it[0] == "bubble":
                it[1] += it[3] * dt
                it[2] += it[4] * dt
                it[1] += math.sin(pygame.time.get_ticks() / 500 + it[6]) * 0.2
            elif it[0] == "leaf":
                it[1] += it[3] * dt
                it[2] += it[4] * dt
                it[5] += 1.5 * dt
                it[1] += math.sin(it[5]) * 14 * dt
            else:
                it[2] += it[4] * dt
                if it[2] > H + 10:
                    it[2] = -10
                    it[1] = random.uniform(0, W)
        self.items = [it for it in self.items if -80 < it[2] < H + 80]

    def draw(self, screen, mode):
        if mode == "ocean":
            for it in self.items:
                if it[0] != "bubble": continue
                r = max(2, int(3 * it[5]))
                pygame.draw.circle(screen, (220, 248, 255), (int(it[1]), int(it[2])), r, 2)
        elif mode == "jungle":
            for it in self.items:
                if it[0] != "leaf": continue
                ang = it[5]
                sc = it[6]
                pts = [(it[1] + math.cos(ang + k * math.tau / 6) * ((9 if k % 2 == 0 else 5) * sc),
                        it[2] + math.sin(ang + k * math.tau / 6) * ((9 if k % 2 == 0 else 5) * sc))
                       for k in range(6)]
                pygame.draw.polygon(screen, (100, 215, 130), pts)
                pygame.draw.polygon(screen, (35, 115, 62), pts, 1)
        else:
            for it in self.items:
                if it[0] != "star": continue
                r = max(1, int(it[5]))
                pygame.draw.circle(screen, (248, 248, 255), (int(it[1]), int(it[2])), r)
