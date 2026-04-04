import math
import random

import pygame

from config import lerp, W, H
from graphics import rounded_rect_surf


class State:
    def __init__(self, game):
        self.game = game

    def enter(self, **kwargs): pass
    def exit(self): pass
    def handle_event(self, e): pass
    def update(self, dt): pass
    def draw(self, screen): pass


class Button:
    def __init__(self, rect, label, font):
        self.base_rect = pygame.Rect(rect)
        self.label = label
        self.font = font
        self.hover = False
        self.pulse = 0.0
        self.shimmer = random.uniform(0, math.tau)

    def update(self, dt, mouse_pos):
        self.hover = self.base_rect.collidepoint(mouse_pos)
        self.pulse = max(0.0, min(1.0, self.pulse + dt * (8 if self.hover else -12)))
        self.shimmer += dt * 2.5

    def draw(self, screen, pal, selected=False):
        t = max(self.pulse, 1.0 if selected else 0.0)
        grow = int(lerp(0, 12, t))
        rect = self.base_rect.inflate(grow, int(grow * 0.5))

        shadow = rounded_rect_surf((rect.w, rect.h), (0, 0, 0, 90), radius=14)
        screen.blit(shadow, (rect.x + 2, rect.y + 6))

        body_col = (*pal["accent"], 230) if t > 0 else (35, 40, 52, 210)
        border_col = pal["accent2"] if t > 0 else (200, 205, 215)
        body = rounded_rect_surf((rect.w, rect.h), body_col, radius=14, border=2, border_color=border_col)
        screen.blit(body, rect.topleft)

        if t > 0.05:
            glow_a = int(50 * t)
            glow = pygame.Surface((rect.w + 22, rect.h + 22), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*pal["accent2"], glow_a), glow.get_rect(), border_radius=20)
            screen.blit(glow, (rect.x - 11, rect.y - 11))

        if t > 0.1:
            sh_x = rect.x + int((math.sin(self.shimmer) * 0.5 + 0.5) * rect.w)
            sh_surf = pygame.Surface((60, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(sh_surf, (255, 255, 255, 30), sh_surf.get_rect(), border_radius=14)
            screen.blit(sh_surf, (sh_x - 30, rect.y))

        txt = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=rect.center))
