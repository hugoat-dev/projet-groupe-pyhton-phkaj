import pygame
from config import lerp


def rounded_rect_surf(size, color, radius=12, border=0, border_color=(0, 0, 0, 0)):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    rect = surf.get_rect()
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border > 0:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=radius)
    return surf


def vertical_gradient(size, top_col, bot_col):
    surf = pygame.Surface(size)
    w, h = size
    for y in range(h):
        t = y / max(1, h - 1)
        c = (int(lerp(top_col[0], bot_col[0], t)),
             int(lerp(top_col[1], bot_col[1], t)),
             int(lerp(top_col[2], bot_col[2], t)))
        pygame.draw.line(surf, c, (0, y), (w, y))
    return surf.convert()


def draw_glow(surf, pos, radius, color, alpha=80):
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -4):
        a = int(alpha * (1 - r / radius) ** 2)
        pygame.draw.circle(glow, (*color[:3], a), (radius, radius), r)
    surf.blit(glow, (pos[0] - radius, pos[1] - radius), special_flags=pygame.BLEND_RGBA_ADD)
