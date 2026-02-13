#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================
Eco Arcade V2 - Jeu d'arcade écologique
===========================================

Description:
    Jeu éducatif avec 3 mini-jeux sur le thème de l'écologie :
    • Océan (Grappin) : Nettoyer l'océan sans blesser les poissons
    • Jungle (Voiture) : Collecter les déchets en évitant les singes
    • Espace (Lasers) : Détruire les débris spatiaux

Contrôles:
    • Flèches ou A/D : Déplacements
    • ESPACE : Action principale (grappin, tir)
    • P : Pause
    • ESC : Retour au menu
    • I : Instructions

Améliorations de cette version :
    ✓ Code mieux structuré et commenté
    ✓ Docstrings ajoutées
    ✓ Variables et fonctions renommées pour plus de clarté
    ✓ Constantes mieux organisées
    ✓ Meilleure séparation des responsabilités
    ✓ Performance optimisée

Auteur: Version refactorisée - Février 2026 — Menu + 3 mini-jeux (Océan grappin / Jungle voiture / Espace lasers)
Aucun asset externe: tout est dessiné procéduralement.
"""

import os
import json
import math
import random
from dataclasses import dataclass

import pygame


# -----------------------------
# =============================================================================
# CONFIGURATION GLOBALE
# =============================================================================
# -----------------------------
WINDOW_WIDTH, WINDOW_HEIGHT = 900, 600
FRAME_RATE = 60
SAVE_PATH = "eco_arcade_save.json"


def clamp(x, a, b):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


# -----------------------------
# =============================================================================
# GESTION DE LA SAUVEGARDE
# =============================================================================
# -----------------------------
def load_save():
    default = {
        "best": {"ocean": 0, "jungle": 0, "space": 0},
        "settings": {"particles": "med", "color_mode": "normal", "volume": 0.0},
    }
    if not os.path.exists(SAVE_PATH):
        return default
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge minimal
        for k in default:
            if k not in data:
                data[k] = default[k]
        for k in default["best"]:
            data["best"].setdefault(k, default["best"][k])
        for k in default["settings"]:
            data["settings"].setdefault(k, default["settings"][k])
        return data
    except Exception:
        return default


def save_now(data):
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# -----------------------------
# =============================================================================
# PALETTES DE COULEURS (avec support daltonisme)
# =============================================================================
# -----------------------------
def palette(color_mode: str):
    # simple alternative palette for better distinction (not perfect daltonism sim, but usable)
    if color_mode == "deuteranopia":
        return {
            "bg": (20, 25, 35),
            "panel": (245, 245, 245),
            "text": (20, 25, 35),
            "muted": (90, 95, 105),
            "accent": (0, 170, 255),     # cyan/blue
            "accent2": (255, 170, 0),    # orange
            "danger": (255, 80, 80),
            "ok": (0, 180, 255),
            "water_top": (130, 200, 255),
            "water_deep": (25, 75, 135),
            "jungle": (35, 95, 50),
        }
    return {
        "bg": (18, 22, 30),
        "panel": (245, 245, 245),
        "text": (18, 22, 30),
        "muted": (95, 100, 112),
        "accent": (70, 210, 140),      # green
        "accent2": (255, 220, 70),     # yellow
        "danger": (255, 70, 70),
        "ok": (70, 210, 140),
        "water_top": (145, 215, 255),
        "water_deep": (25, 85, 150),
        "jungle": (25, 105, 45),
    }


# -----------------------------
# =============================================================================
# UTILITAIRES GRAPHIQUES
# =============================================================================
# -----------------------------
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


# -----------------------------
# =============================================================================
# CACHE DE SPRITES (génération procédurale)
# =============================================================================
# -----------------------------
SPRITES = {}


def trash_sprite(kind: str, size=30):
    key = ("trash", kind, size)
    if key in SPRITES:
        return SPRITES[key]

    s = pygame.Surface((size, size), pygame.SRCALPHA)
    if kind == "bottle":
        pygame.draw.rect(s, (110, 165, 220), (size * 0.36, size * 0.18, size * 0.28, size * 0.58), border_radius=6)
        pygame.draw.rect(s, (85, 140, 200), (size * 0.40, size * 0.08, size * 0.20, size * 0.14), border_radius=4)
        pygame.draw.circle(s, (170, 220, 255, 120), (int(size * 0.50), int(size * 0.45)), int(size * 0.16))
    elif kind == "can":
        pygame.draw.ellipse(s, (195, 195, 210), (size * 0.25, size * 0.22, size * 0.50, size * 0.62))
        pygame.draw.ellipse(s, (160, 160, 175), (size * 0.28, size * 0.26, size * 0.44, size * 0.54), 2)
        pygame.draw.rect(s, (230, 230, 240), (size * 0.30, size * 0.44, size * 0.40, 3))
    elif kind == "bag":
        pts = [(size * 0.50, size * 0.10), (size * 0.80, size * 0.30), (size * 0.70, size * 0.85),
               (size * 0.30, size * 0.85), (size * 0.20, size * 0.30)]
        pygame.draw.polygon(s, (235, 235, 245, 140), pts)
        pygame.draw.polygon(s, (185, 185, 200, 210), pts, 2)
    elif kind == "tire":
        pygame.draw.circle(s, (25, 25, 30), (size // 2, size // 2), int(size * 0.34))
        pygame.draw.circle(s, (60, 60, 70), (size // 2, size // 2), int(size * 0.20))
        for a in range(0, 360, 45):
            r = math.radians(a)
            x1 = size // 2 + int(math.cos(r) * size * 0.20)
            y1 = size // 2 + int(math.sin(r) * size * 0.20)
            x2 = size // 2 + int(math.cos(r) * size * 0.30)
            y2 = size // 2 + int(math.sin(r) * size * 0.30)
            pygame.draw.line(s, (40, 40, 48), (x1, y1), (x2, y2), 2)
    else:  # "box"
        pygame.draw.rect(s, (150, 100, 55), (size * 0.18, size * 0.26, size * 0.64, size * 0.52), border_radius=4)
        pygame.draw.rect(s, (110, 70, 35), (size * 0.18, size * 0.26, size * 0.64, size * 0.52), 2, border_radius=4)
        pygame.draw.line(s, (110, 70, 35), (size * 0.18, size * 0.38), (size * 0.82, size * 0.38), 2)

    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]


def boat_sprite():
    key = ("boat",)
    if key in SPRITES:
        return SPRITES[key]
    s = pygame.Surface((96, 56), pygame.SRCALPHA)

    hull = [(10, 28), (16, 12), (48, 6), (80, 12), (86, 28), (80, 44), (48, 50), (16, 44)]
    pygame.draw.polygon(s, (65, 160, 255), hull)
    pygame.draw.polygon(s, (20, 60, 155), hull, 3)

    pygame.draw.rect(s, (245, 245, 250), (36, 18, 24, 22), border_radius=6)
    pygame.draw.rect(s, (20, 60, 155), (36, 18, 24, 22), 2, border_radius=6)
    pygame.draw.rect(s, (170, 220, 255), (40, 22, 7, 7), border_radius=2)
    pygame.draw.rect(s, (170, 220, 255), (49, 22, 7, 7), border_radius=2)

    # grapple mount (front center)
    pygame.draw.circle(s, (255, 220, 70), (48, 10), 4)
    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]


def grapple_sprite():
    key = ("grapple",)
    if key in SPRITES:
        return SPRITES[key]
    s = pygame.Surface((34, 34), pygame.SRCALPHA)
    pygame.draw.circle(s, (165, 165, 175), (17, 17), 9)
    pygame.draw.circle(s, (105, 105, 115), (17, 17), 7, 2)
    for a in (0, 120, 240):
        r = math.radians(a)
        x1 = 17 + 9 * math.cos(r)
        y1 = 17 + 9 * math.sin(r)
        x2 = 17 + 16 * math.cos(r)
        y2 = 17 + 16 * math.sin(r)
        pygame.draw.line(s, (130, 130, 140), (x1, y1), (x2, y2), 4)
    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]


def fish_sprite(direction=-1):
    key = ("fish", direction)
    if key in SPRITES:
        return SPRITES[key]
    s = pygame.Surface((44, 30), pygame.SRCALPHA)
    body = pygame.Rect(8, 7, 26, 16)
    pygame.draw.ellipse(s, (255, 165, 60), body)
    pygame.draw.ellipse(s, (230, 120, 35), body, 2)
    if direction < 0:
        tail = [(8, 15), (2, 9), (2, 21)]
        eye = (18, 13)
    else:
        tail = [(34, 15), (42, 9), (42, 21)]
        eye = (24, 13)
    pygame.draw.polygon(s, (255, 165, 60), tail)
    pygame.draw.circle(s, (255, 255, 255), eye, 3)
    pygame.draw.circle(s, (0, 0, 0), eye, 2)
    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]


def car_sprite():
    key = ("car",)
    if key in SPRITES:
        return SPRITES[key]
    s = pygame.Surface((120, 90), pygame.SRCALPHA)

    # main body
    pygame.draw.rect(s, (70, 210, 140), (12, 20, 96, 60), border_radius=14)
    pygame.draw.rect(s, (25, 105, 45), (12, 20, 96, 60), 3, border_radius=14)

    # windshield
    pygame.draw.rect(s, (160, 220, 255), (26, 33, 68, 18), border_radius=8)
    pygame.draw.rect(s, (0, 0, 0), (26, 33, 68, 18), 2, border_radius=8)

    # front bin (metal)
    pygame.draw.rect(s, (155, 160, 175), (20, 4, 80, 18), border_radius=6)
    pygame.draw.rect(s, (90, 95, 110), (20, 4, 80, 18), 2, border_radius=6)
    pygame.draw.line(s, (105, 110, 125), (26, 13), (94, 13), 2)

    # wheels
    for x in (28, 92):
        for y in (28, 76):
            pygame.draw.circle(s, (15, 15, 18), (x, y), 11)
            pygame.draw.circle(s, (55, 55, 65), (x, y), 7)

    # headlights
    pygame.draw.circle(s, (255, 220, 70), (34, 82), 4)
    pygame.draw.circle(s, (255, 220, 70), (86, 82), 4)

    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]


def monkey_sprite():
    key = ("monkey",)
    if key in SPRITES:
        return SPRITES[key]
    s = pygame.Surface((52, 52), pygame.SRCALPHA)
    pygame.draw.circle(s, (140, 85, 35), (26, 24), 18)
    pygame.draw.circle(s, (165, 110, 60), (14, 18), 7)
    pygame.draw.circle(s, (165, 110, 60), (38, 18), 7)
    pygame.draw.ellipse(s, (220, 190, 150), (16, 22, 20, 18))
    pygame.draw.circle(s, (255, 255, 255), (22, 26), 3)
    pygame.draw.circle(s, (255, 255, 255), (30, 26), 3)
    pygame.draw.circle(s, (0, 0, 0), (22, 26), 2)
    pygame.draw.circle(s, (0, 0, 0), (30, 26), 2)
    pygame.draw.arc(s, (0, 0, 0), (18, 30, 16, 10), 0, math.pi, 2)
    pygame.draw.line(s, (140, 85, 35), (34, 36), (48, 50), 6)  # tail
    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]


def ship_sprite():
    key = ("ship",)
    if key in SPRITES:
        return SPRITES[key]
    s = pygame.Surface((56, 70), pygame.SRCALPHA)
    pts = [(28, 6), (44, 44), (28, 38), (12, 44)]
    pygame.draw.polygon(s, (155, 70, 220), pts)
    pygame.draw.polygon(s, (95, 35, 150), pts, 2)
    pygame.draw.polygon(s, (130, 55, 200), [(12, 44), (5, 60), (14, 50)])
    pygame.draw.polygon(s, (130, 55, 200), [(44, 44), (51, 60), (42, 50)])
    pygame.draw.ellipse(s, (160, 220, 255), (20, 14, 16, 12))
    pygame.draw.ellipse(s, (245, 245, 255), (22, 16, 12, 8))
    pygame.draw.rect(s, (220, 220, 235), (18, 38, 5, 10), border_radius=2)
    pygame.draw.rect(s, (220, 220, 235), (33, 38, 5, 10), border_radius=2)
    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]


def laser_sprite():
    key = ("laser",)
    if key in SPRITES:
        return SPRITES[key]
    s = pygame.Surface((6, 22), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 255, 255), (0, 0, 6, 22))
    pygame.draw.rect(s, (255, 255, 255), (1, 0, 4, 22))
    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]


def debris_sprite(kind: str):
    key = ("debris", kind)
    if key in SPRITES:
        return SPRITES[key]
    if kind == "small":
        s = pygame.Surface((26, 26), pygame.SRCALPHA)
        pts = [(13, 2), (22, 9), (19, 21), (8, 23), (3, 11)]
        pygame.draw.polygon(s, (125, 125, 135), pts)
        pygame.draw.polygon(s, (75, 75, 85), pts, 2)
    elif kind == "medium":
        s = pygame.Surface((38, 38), pygame.SRCALPHA)
        pygame.draw.rect(s, (105, 105, 120), (6, 6, 26, 26), border_radius=5)
        pygame.draw.line(s, (160, 160, 175), (6, 6), (32, 32), 2)
        pygame.draw.line(s, (160, 160, 175), (32, 6), (6, 32), 2)
    else:
        s = pygame.Surface((54, 54), pygame.SRCALPHA)
        pygame.draw.circle(s, (95, 95, 115), (27, 27), 23)
        pygame.draw.circle(s, (65, 65, 85), (27, 27), 18)
        for a in (0, 90, 180, 270):
            r = math.radians(a)
            x = 27 + 15 * math.cos(r)
            y = 27 + 15 * math.sin(r)
            pygame.draw.circle(s, (75, 75, 95), (int(x), int(y)), 5)
    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]


# -----------------------------
# =============================================================================
# SYSTÈME DE PARTICULES (effets visuels légers)
# =============================================================================
# -----------------------------
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

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        # mild drag
        self.vx *= (1.0 - 0.9 * dt)
        self.vy *= (1.0 - 0.9 * dt)

    def dead(self):
        return self.age >= self.life

    def draw(self, screen):
        t = 1.0 - (self.age / max(1e-6, self.life))
        a = int(255 * clamp(t, 0.0, 1.0))
        r = max(1, int(self.size))
        surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.col[:3], a), (r + 1, r + 1), r)
        screen.blit(surf, (int(self.x - r), int(self.y - r)))


# -----------------------------
# =============================================================================
# SYSTÈME DE TRANSITION (fondus)
# =============================================================================
# -----------------------------
class Fade:
    def __init__(self, duration=0.28):
        self.duration = duration
        self.active = False
        self.t = 0.0
        self.phase = "out"  # out -> swap -> in
        self.on_swap = None

    def start(self, on_swap):
        self.active = True
        self.t = 0.0
        self.phase = "out"
        self.on_swap = on_swap

    def update(self, dt):
        if not self.active:
            return
        self.t += dt
        if self.phase == "out" and self.t >= self.duration:
            # do swap
            if self.on_swap:
                self.on_swap()
            self.phase = "in"
            self.t = 0.0
        elif self.phase == "in" and self.t >= self.duration:
            self.active = False
            self.on_swap = None

    def alpha(self):
        if not self.active:
            return 0
        u = clamp(self.t / self.duration, 0.0, 1.0)
        if self.phase == "out":
            return int(255 * u)
        return int(255 * (1.0 - u))

    def draw(self, screen):
        a = self.alpha()
        if a <= 0:
            return
        ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, a))
        screen.blit(ov, (0, 0))


# -----------------------------
# =============================================================================
# ARCHITECTURE DES ÉTATS (pattern State)
# =============================================================================
# -----------------------------
class State:
    def __init__(self, game):
        self.game = game

    def enter(self, **kwargs):
        pass

    def exit(self):
        pass

    def handle_event(self, e):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass


# -----------------------------
# =============================================================================
# COMPOSANTS UI (Boutons interactifs)
# =============================================================================
# -----------------------------
class Button:
    def __init__(self, rect, label, font):
        self.base_rect = pygame.Rect(rect)
        self.label = label
        self.font = font
        self.hover = False
        self.pulse = 0.0

    def update(self, dt, mouse_pos):
        self.hover = self.base_rect.collidepoint(mouse_pos)
        self.pulse = clamp(self.pulse + (dt * (7 if self.hover else -10)), 0.0, 1.0)

    def draw(self, screen, pal, selected=False):
        t = max(self.pulse, 1.0 if selected else 0.0)
        grow = int(lerp(0, 10, t))
        rect = self.base_rect.inflate(grow, int(grow * 0.6))

        # shadow
        shadow = rounded_rect_surf((rect.w, rect.h), (0, 0, 0, 80), radius=14)
        screen.blit(shadow, (rect.x, rect.y + 4))

        # body + border
        body_col = (pal["accent"][0], pal["accent"][1], pal["accent"][2], 240) if t > 0 else (40, 45, 58, 220)
        border_col = pal["accent2"] if t > 0 else (240, 240, 245)
        body = rounded_rect_surf((rect.w, rect.h), body_col, radius=14, border=3, border_color=border_col)
        screen.blit(body, rect.topleft)

        # glow
        if t > 0:
            glow = pygame.Surface((rect.w + 18, rect.h + 18), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*pal["accent2"], int(35 * t)), glow.get_rect(), border_radius=18)
            screen.blit(glow, (rect.x - 9, rect.y - 9))

        txt = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=rect.center))


# -----------------------------
# =============================================================================
# PARTICULES DE FOND DU MENU (animations thématiques)
# ============================================================================= (theme preview)
# -----------------------------
class MenuParticles:
    def __init__(self):
        self.items = []
        self.spawn_t = 0.0

    def clear(self):
        self.items.clear()

    def update(self, dt, mode, intensity):
        rate = {"low": 0.35, "med": 0.20, "high": 0.10}.get(intensity, 0.20)
        self.spawn_t += dt
        while self.spawn_t >= rate:
            self.spawn_t -= rate
            if mode == "ocean":
                x = random.uniform(0, WINDOW_WIDTH)
                y = WINDOW_HEIGHT + 10
                vx = random.uniform(-10, 10)
                vy = random.uniform(-55, -85)
                self.items.append(["bubble", x, y, vx, vy, random.uniform(0.8, 1.4), random.uniform(0.8, 1.4)])
            elif mode == "jungle":
                x = random.uniform(0, WINDOW_WIDTH)
                y = -12
                vx = random.uniform(-15, 15)
                vy = random.uniform(35, 60)
                self.items.append(["leaf", x, y, vx, vy, random.uniform(0.0, math.tau), random.uniform(0.8, 1.2)])
            else:  # space
                x = random.uniform(0, WINDOW_WIDTH)
                y = random.uniform(0, WINDOW_HEIGHT)
                sp = random.uniform(30, 110)
                self.items.append(["star", x, y, 0.0, sp, random.uniform(1.0, 2.5), 0.0])

        # update
        for it in self.items:
            kind = it[0]
            if kind == "bubble":
                it[1] += it[3] * dt
                it[2] += it[4] * dt
                it[2] += math.sin(pygame.time.get_ticks() / 500 + it[1] * 0.01) * 0.15
            elif kind == "leaf":
                it[1] += it[3] * dt
                it[2] += it[4] * dt
                it[5] += 1.2 * dt
                it[1] += math.sin(it[5]) * 12 * dt
            else:
                it[2] += it[4] * dt
                if it[2] > WINDOW_HEIGHT + 10:
                    it[2] = -10
                    it[1] = random.uniform(0, WINDOW_WIDTH)

        # cull
        self.items = [it for it in self.items if -60 < it[2] < WINDOW_HEIGHT + 60]

    def draw(self, screen, mode):
        if mode == "ocean":
            for it in self.items:
                if it[0] != "bubble":
                    continue
                _, x, y, *_ = it
                r = int(3 * it[5])
                pygame.draw.circle(screen, (220, 245, 255), (int(x), int(y)), r, 2)
        elif mode == "jungle":
            for it in self.items:
                if it[0] != "leaf":
                    continue
                _, x, y, *_ = it
                ang = it[5]
                sc = it[6]
                # simple leaf shape
                pts = []
                for k in range(6):
                    a = ang + k * (math.tau / 6)
                    rad = (8 if k % 2 == 0 else 4) * sc
                    pts.append((x + math.cos(a) * rad, y + math.sin(a) * rad))
                pygame.draw.polygon(screen, (110, 220, 140), pts)
                pygame.draw.polygon(screen, (40, 120, 70), pts, 2)
        else:
            for it in self.items:
                if it[0] != "star":
                    continue
                _, x, y, *_ = it
                r = int(it[5])
                pygame.draw.circle(screen, (245, 245, 255), (int(x), int(y)), r)


# -----------------------------
# =============================================================================
# ÉTAT : MENU PRINCIPAL
# =============================================================================
# -----------------------------
class MenuState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal = palette(game.data["settings"]["color_mode"])
        self.font_title = pygame.font.Font(None, 84)
        self.font_btn = pygame.font.Font(None, 38)
        self.font_small = pygame.font.Font(None, 22)

        self.bg_ocean = vertical_gradient((WINDOW_WIDTH, WINDOW_HEIGHT), (40, 160, 220), (15, 55, 120))
        self.bg_jungle = vertical_gradient((WINDOW_WIDTH, WINDOW_HEIGHT), (40, 170, 90), (18, 70, 45))
        self.bg_space = vertical_gradient((WINDOW_WIDTH, WINDOW_HEIGHT), (10, 12, 22), (28, 15, 45))

        self.selected = 0
        labels = ["Océan (Grappin)", "Jungle (Voiture)", "Espace (Lasers)", "Instructions", "Paramètres", "Quitter"]
        self.actions = ["ocean", "jungle", "space", "instructions", "settings", "quit"]
        self.buttons = []
        bw, bh = 360, 56
        sy = 190
        for i, lab in enumerate(labels):
            r = pygame.Rect(W // 2 - bw // 2, sy + i * 68, bw, bh)
            self.buttons.append(Button(r, lab, self.font_btn))

        self.particles = MenuParticles()

    def _preview_mode(self):
        if self.selected == 0:
            return "ocean"
        if self.selected == 1:
            return "jungle"
        if self.selected == 2:
            return "space"
        return "space"

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.buttons)
            elif e.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.buttons)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate(self.selected)
            elif e.key == pygame.K_i:
                self.game.transition_to(InstructionsState(self.game))
            elif e.key == pygame.K_ESCAPE:
                self.game.running = False
        elif e.type == pygame.MOUSEMOTION:
            for i, b in enumerate(self.buttons):
                if b.base_rect.collidepoint(e.pos):
                    self.selected = i
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, b in enumerate(self.buttons):
                if b.base_rect.collidepoint(e.pos):
                    self._activate(i)

    def _activate(self, idx):
        act = self.actions[idx]
        if act == "ocean":
            self.game.transition_to(OceanGameState(self.game))
        elif act == "jungle":
            self.game.transition_to(JungleGameState(self.game))
        elif act == "space":
            self.game.transition_to(SpaceGameState(self.game))
        elif act == "instructions":
            self.game.transition_to(InstructionsState(self.game))
        elif act == "settings":
            self.game.transition_to(SettingsState(self.game))
        else:
            self.game.running = False

    def update(self, dt):
        self.pal = palette(self.game.data["settings"]["color_mode"])
        mode = self._preview_mode()
        inten = self.game.data["settings"]["particles"]
        self.particles.update(dt, mode, inten)

        mp = pygame.mouse.get_pos()
        for i, b in enumerate(self.buttons):
            b.update(dt, mp)

    def draw(self, screen):
        mode = self._preview_mode()
        bg = self.bg_space if mode == "space" else self.bg_ocean if mode == "ocean" else self.bg_jungle
        screen.blit(bg, (0, 0))
        self.particles.draw(screen, mode)

        title = self.font_title.render("Eco Arcade", True, (255, 255, 255))
        shadow = self.font_title.render("Eco Arcade", True, (0, 0, 0))
        screen.blit(shadow, (W // 2 - shadow.get_width() // 2 + 2, 64))
        screen.blit(title, (W // 2 - title.get_width() // 2, 62))

        sub = self.font_small.render("V2 — plus fluide, plus beau, sans assets", True, self.pal["accent2"])
        screen.blit(sub, (W // 2 - sub.get_width() // 2, 132))

        for i, b in enumerate(self.buttons):
            b.draw(screen, self.pal, selected=(i == self.selected))

        # footer hint
        hint = self.font_small.render("↑↓/W-S: naviguer | Entrée: lancer | I: instructions | ESC: quitter", True, (240, 240, 245))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 30))


# -----------------------------
# =============================================================================
# ÉTAT : ÉCRAN D'INSTRUCTIONS
# =============================================================================
# -----------------------------
class InstructionsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.font_t = pygame.font.Font(None, 56)
        self.font = pygame.font.Font(None, 24)

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_i):
            self.game.transition_to(MenuState(self.game))

    def draw(self, screen):
        pal = palette(self.game.data["settings"]["color_mode"])
        screen.fill((20, 35, 60))

        panel = rounded_rect_surf((760, 520), (255, 255, 255, 235), radius=16, border=2, border_color=(0, 0, 0, 40))
        screen.blit(panel, (70, 40))

        t = self.font_t.render("Instructions", True, (15, 30, 55))
        screen.blit(t, (W // 2 - t.get_width() // 2, 60))

        lines = [
            ("OCÉAN — Grappin", True),
            ("• A/D ou ←→: déplacer le bateau (en haut).", False),
            ("• SPACE: lancer le grappin, il descend puis remonte.", False),
            ("• Déchets pêchés = +1. Poissons: jamais pêchables.", False),
            ("• Si grappin touche un poisson: -1 vie.", False),
            ("• Si un déchet touche un poisson: 'impact' (et peut faire perdre des vies).", False),
            ("", False),
            ("JUNGLE — Voiture + bac", True),
            ("• A/D ou ←→: déplacer la voiture (large, lente).", False),
            ("• Collecte uniquement avec le BAC à l'avant.", False),
            ("• Singe = obstacle: collision => -1 vie + invincibilité 1s.", False),
            ("", False),
            ("ESPACE — Lasers", True),
            ("• A/D ou ←→: gauche/droite uniquement.", False),
            ("• SPACE: tirer (énergie + cooldown).", False),
            ("• Débris: small(1), medium(2), large(3) PV.", False),
            ("", False),
            ("ESC / I: retour au menu", False),
        ]

        y = 130
        for txt, is_title in lines:
            if is_title:
                f = pygame.font.Font(None, 30)
                col = (15, 30, 55)
            else:
                f = self.font
                col = pal["text"]
            r = f.render(txt, True, col)
            screen.blit(r, (110, y))
            y += 28


# -----------------------------
# =============================================================================
# ÉTAT : PARAMÈTRES
# =============================================================================
# -----------------------------
class SettingsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.font_t = pygame.font.Font(None, 56)
        self.font = pygame.font.Font(None, 28)
        self.small = pygame.font.Font(None, 22)
        self.items = ["particles", "color_mode"]
        self.idx = 0

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                save_now(self.game.data)
                self.game.transition_to(MenuState(self.game))
            elif e.key in (pygame.K_UP, pygame.K_w):
                self.idx = (self.idx - 1) % len(self.items)
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.idx = (self.idx + 1) % len(self.items)
            elif e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                key = self.items[self.idx]
                if key == "particles":
                    vals = ["low", "med", "high"]
                else:
                    vals = ["normal", "deuteranopia"]
                cur = self.game.data["settings"][key]
                i = vals.index(cur)
                i = (i + (1 if e.key in (pygame.K_RIGHT, pygame.K_d) else -1)) % len(vals)
                self.game.data["settings"][key] = vals[i]

    def draw(self, screen):
        pal = palette(self.game.data["settings"]["color_mode"])
        screen.fill((25, 25, 32))
        panel = rounded_rect_surf((720, 420), (255, 255, 255, 235), radius=16, border=2, border_color=(0, 0, 0, 40))
        screen.blit(panel, (90, 90))

        t = self.font_t.render("Paramètres", True, (15, 30, 55))
        screen.blit(t, (W // 2 - t.get_width() // 2, 110))

        labels = {"particles": "Intensité particules", "color_mode": "Mode couleurs"}
        y = 200
        for i, key in enumerate(self.items):
            sel = (i == self.idx)
            col = (15, 30, 55) if sel else (90, 95, 105)
            name = self.font.render(labels[key], True, col)
            screen.blit(name, (140, y))

            val = str(self.game.data["settings"][key])
            v = self.font.render(f"<  {val}  >", True, col)
            screen.blit(v, (560, y))
            y += 70

        hint = self.small.render("←→: changer | ESC: retour", True, (20, 25, 35))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, 455))


# -----------------------------
# =============================================================================
# ÉTAT : PAUSE (overlay)
# =============================================================================
# -----------------------------
class PauseState(State):
    def __init__(self, game, under_state):
        super().__init__(game)
        self.under = under_state
        self.font = pygame.font.Font(None, 56)
        self.small = pygame.font.Font(None, 24)

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_p, pygame.K_ESCAPE):
                self.game.pop_state()  # return to game
            elif e.key == pygame.K_m:
                self.game.transition_to(MenuState(self.game))

    def update(self, dt):
        pass

    def draw(self, screen):
        self.under.draw(screen)
        ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        screen.blit(ov, (0, 0))

        panel = rounded_rect_surf((520, 220), (255, 255, 255, 235), radius=16)
        screen.blit(panel, (W // 2 - 260, WINDOW_HEIGHT // 2 - 110))

        t = self.font.render("PAUSE", True, (20, 25, 35))
        screen.blit(t, (W // 2 - t.get_width() // 2, WINDOW_HEIGHT // 2 - 80))

        h1 = self.small.render("P / ESC: reprendre", True, (20, 25, 35))
        h2 = self.small.render("M: menu", True, (20, 25, 35))
        screen.blit(h1, (W // 2 - h1.get_width() // 2, WINDOW_HEIGHT // 2 + 5))
        screen.blit(h2, (W // 2 - h2.get_width() // 2, WINDOW_HEIGHT // 2 + 34))


# -----------------------------
# =============================================================================
# ÉTAT : FIN DE PARTIE
# =============================================================================
# -----------------------------
class EndState(State):
    def __init__(self, game, mode, score, details):
        super().__init__(game)
        self.mode = mode
        self.score = score
        self.details = details
        self.font = pygame.font.Font(None, 64)
        self.small = pygame.font.Font(None, 26)

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.game.transition_to(MenuState(self.game))

    def draw(self, screen):
        pal = palette(self.game.data["settings"]["color_mode"])
        screen.fill((10, 12, 18))

        panel = rounded_rect_surf((720, 440), (255, 255, 255, 235), radius=18)
        screen.blit(panel, (90, 80))

        title = self.font.render("Fin de partie", True, (18, 22, 30))
        screen.blit(title, (W // 2 - title.get_width() // 2, 105))

        best = self.game.data["best"][self.mode]
        if self.score > best:
            self.game.data["best"][self.mode] = self.score
            save_now(self.game.data)
            best = self.score

        y = 210
        s1 = self.small.render(f"Mode: {self.mode.upper()}", True, pal["text"])
        s2 = self.small.render(f"Score: {self.score}", True, pal["text"])
        s3 = self.small.render(f"Meilleur: {best}", True, pal["text"])
        screen.blit(s1, (140, y)); y += 36
        screen.blit(s2, (140, y)); y += 36
        screen.blit(s3, (140, y)); y += 36

        y += 10
        for k, v in self.details:
            line = self.small.render(f"{k}: {v}", True, pal["muted"])
            screen.blit(line, (140, y))
            y += 30

        hint = self.small.render("ESC / Entrée: menu", True, pal["danger"])
        screen.blit(hint, (W // 2 - hint.get_width() // 2, 475))


# -----------------------------
# =============================================================================
# JEU 1 : OCÉAN (Nettoyage avec grappin)
# ============================================================================= (boat top + grapin vertical, fish/trash right->left)
# -----------------------------
class OceanGameState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal = palette(game.data["settings"]["color_mode"])
        self.font = pygame.font.Font(None, 26)
        self.big = pygame.font.Font(None, 44)

        self.surface_y = 120
        self.bg_water = vertical_gradient((WINDOW_WIDTH, WINDOW_HEIGHT), self.pal["water_top"], self.pal["water_deep"])

        # boat (top)
        self.boat_img = boat_sprite()
        self.boat_x = WINDOW_WIDTH * 0.5
        self.boat_vx = 0.0
        self.boat_y = 58
        self.boat_acc = 1300.0
        self.boat_drag = 7.5
        self.boat_max = 320.0

        # grapple
        self.gr_img = grapple_sprite()
        self.gr_active = False
        self.gr_y = self.boat_y + 40
        self.gr_state = "idle"  # idle/down/up
        self.gr_speed = 220.0
        self.gr_max_depth = WINDOW_HEIGHT - 85
        self.gr_caught = None

        # entities (right -> left)
        self.trash = []
        self.fish = []
        self.spawn_t = 0.0

        self.collected = 0
        self.impacts = 0
        self.lives = 3
        self.time_left = 75.0

        self.impact_threshold = 3  # every 3 impacts => lose 1 life
        self.next_impact_loss = self.impact_threshold
        self.flash_t = 0.0

        # particles (bubble splash / feedback)
        self.fx = []

        for _ in range(7):
            self._spawn_trash(x=W + random.uniform(0, 350))
        for _ in range(10):
            self._spawn_fish(x=W + random.uniform(0, 500))

    def _spawn_trash(self, x=None):
        kinds = ["bottle", "can", "bag", "tire", "box"]
        k = random.choice(kinds)
        y = random.uniform(self.surface_y + 35, WINDOW_HEIGHT - 55)
        vx = -random.uniform(45, 85)
        rot = random.uniform(-25, 25)
        x = WINDOW_WIDTH + 40 if x is None else x
        self.trash.append({
            "k": k, "x": x, "y": y, "vx": vx, "t": random.uniform(0, 10),
            "rot": random.uniform(0, 360), "rots": rot,
            "img": trash_sprite(k, 30),
        })

    def _spawn_fish(self, x=None):
        y = random.uniform(self.surface_y + 30, WINDOW_HEIGHT - 50)
        vx = -random.uniform(70, 120)
        x = WINDOW_WIDTH + 40 if x is None else x
        self.fish.append({
            "x": x, "y": y, "vx": vx, "t": random.uniform(0, 10),
            "img": fish_sprite(direction=-1)
        })

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p:
                self.game.push_state(PauseState(self.game, self))
            elif e.key == pygame.K_ESCAPE:
                self.game.transition_to(MenuState(self.game))
            elif e.key == pygame.K_SPACE and not self.gr_active:
                self.gr_active = True
                self.gr_state = "down"
                self.gr_y = self.boat_y + 40
                self.gr_caught = None

    def update(self, dt):
        self.pal = palette(self.game.data["settings"]["color_mode"])
        self.time_left -= dt
        if self.flash_t > 0:
            self.flash_t -= dt

        if self.time_left <= 0 or self.lives <= 0:
            score = max(0, self.collected * 10 - self.impacts * 3)
            details = [("Déchets récupérés", self.collected), ("Poissons impactés", self.impacts)]
            self.game.transition_to(EndState(self.game, "ocean", score, details))
            return

        # boat movement (smooth with inertia)
        keys = pygame.key.get_pressed()
        ax = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            ax -= self.boat_acc
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            ax += self.boat_acc

        self.boat_vx += ax * dt
        self.boat_vx -= self.boat_vx * self.boat_drag * dt
        self.boat_vx = clamp(self.boat_vx, -self.boat_max, self.boat_max)
        self.boat_x += self.boat_vx * dt
        self.boat_x = clamp(self.boat_x, 70, W - 70)

        # grapple anchor
        gr_x = self.boat_x  # vertical cable from boat
        if self.gr_active:
            if self.gr_state == "down":
                self.gr_y += self.gr_speed * dt
                if self.gr_y >= self.gr_max_depth:
                    self.gr_state = "up"

                # collision with trash (only if not already caught)
                if self.gr_caught is None:
                    for t in self.trash:
                        dx = (gr_x - t["x"])
                        dy = (self.gr_y - t["y"])
                        if dx * dx + dy * dy < (26 * 26):
                            self.gr_caught = t
                            self.gr_state = "up"
                            # splash
                            for _ in range(8):
                                self.fx.append(Particle(gr_x, self.gr_y, random.uniform(-35, 35),
                                                        random.uniform(-60, -20), 0.45, 0.0,
                                                        "bubble", random.uniform(2, 4), (220, 245, 255)))
                            break

                # collision with fish => penalty (no capture)
                for f in self.fish:
                    dx = (gr_x - f["x"])
                    dy = (self.gr_y - f["y"])
                    if dx * dx + dy * dy < (24 * 24):
                        self.lives -= 1
                        self.flash_t = 0.45
                        self.gr_state = "up"
                        for _ in range(10):
                            self.fx.append(Particle(gr_x, self.gr_y, random.uniform(-60, 60),
                                                    random.uniform(-30, 30), 0.55, 0.0,
                                                    "hit", random.uniform(2, 4), self.pal["danger"]))
                        break

            elif self.gr_state == "up":
                self.gr_y -= self.gr_speed * dt
                if self.gr_caught is not None:
                    self.gr_caught["x"] = gr_x
                    self.gr_caught["y"] = self.gr_y + 16
                    self.gr_caught["rot"] *= (1.0 - 5.0 * dt)

                if self.gr_y <= self.boat_y + 40:
                    self.gr_active = False
                    self.gr_state = "idle"
                    if self.gr_caught is not None:
                        if self.gr_caught in self.trash:
                            self.trash.remove(self.gr_caught)
                        self.collected += 1
                        for _ in range(10):
                            self.fx.append(Particle(gr_x, self.surface_y + 10, random.uniform(-60, 60),
                                                    random.uniform(-90, -35), 0.55, 0.0,
                                                    "pop", random.uniform(2, 4), self.pal["accent2"]))
                        self.gr_caught = None

        # move trash + fish (right -> left)
        for t in self.trash[:]:
            if t is self.gr_caught:
                continue
            t["x"] += t["vx"] * dt
            t["t"] += dt
            t["rot"] += t["rots"] * dt
            if t["x"] < -80:
                self.trash.remove(t)
                continue

            # trash-fish impact
            for f in self.fish:
                dx = t["x"] - f["x"]
                dy = t["y"] - f["y"]
                if dx * dx + dy * dy < (30 * 30):
                    self.impacts += 1
                    if t in self.trash:
                        self.trash.remove(t)
                    for _ in range(10):
                        self.fx.append(Particle(f["x"], f["y"], random.uniform(-70, 70),
                                                random.uniform(-70, 40), 0.60, 0.0,
                                                "impact", random.uniform(2, 4), (255, 150, 60)))
                    break

        for f in self.fish[:]:
            f["x"] += f["vx"] * dt
            f["t"] += dt
            if f["x"] < -80:
                self.fish.remove(f)

        # lose life by impact thresholds (every 3 impacts)
        if self.impacts >= self.next_impact_loss:
            self.lives -= 1
            self.flash_t = 0.55
            self.next_impact_loss += self.impact_threshold

        # spawn
        self.spawn_t += dt
        if self.spawn_t >= 1.25:
            self.spawn_t = 0.0
            if len(self.trash) < 9:
                self._spawn_trash()
            if len(self.fish) < 12:
                self._spawn_fish()

        # fx
        for p in self.fx[:]:
            p.update(dt)
            if p.dead():
                self.fx.remove(p)

    def draw(self, screen):
        screen.blit(self.bg_water, (0, 0))

        # sky band
        pygame.draw.rect(screen, (170, 225, 255), (0, 0, WINDOW_WIDTH, self.surface_y))
        pygame.draw.line(screen, (60, 140, 220), (0, self.surface_y), (WINDOW_WIDTH, self.surface_y), 4)

        # waves
        tt = pygame.time.get_ticks() / 280
        for x in range(0, WINDOW_WIDTH, 26):
            y = self.surface_y - 2 + int(math.sin(tt + x * 0.05) * 4)
            pygame.draw.line(screen, (245, 245, 255), (x, y), (x + 14, y), 2)

        # fish (under water)
        for f in self.fish:
            bob = math.sin(f["t"] * 2.2) * 3
            screen.blit(f["img"], (int(f["x"] - 22), int(f["y"] - 15 + bob)))

        # trash (under water)
        for t in self.trash:
            bob = math.sin(t["t"] * 1.6) * 2
            img = pygame.transform.rotate(t["img"], t["rot"])
            r = img.get_rect(center=(int(t["x"]), int(t["y"] + bob)))
            screen.blit(img, r)

        # depth tint around hook (readability)
        if self.gr_active:
            gr_x = self.boat_x
            s = pygame.Surface((180, 180), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 0, 0, 35), (90, 90), 88)
            screen.blit(s, (int(gr_x - 90), int(self.gr_y - 90)))

        # cable + hook
        if self.gr_active:
            gr_x = int(self.boat_x)
            pygame.draw.line(screen, (90, 90, 95), (gr_x, self.boat_y + 40), (gr_x, int(self.gr_y)), 3)
            screen.blit(self.gr_img, (gr_x - 17, int(self.gr_y) - 17))

        # boat + subtle reflection
        bx = int(self.boat_x - self.boat_img.get_width() // 2)
        by = int(self.boat_y - self.boat_img.get_height() // 2)
        screen.blit(self.boat_img, (bx, by))
        # tiny reflection in water
        ref = pygame.transform.flip(self.boat_img, False, True)
        ref.set_alpha(50)
        screen.blit(ref, (bx, self.surface_y + 10))

        # fx
        for p in self.fx:
            p.draw(screen)

        # UI top bar
        bar = pygame.Surface((WINDOW_WIDTH, 72), pygame.SRCALPHA)
        pygame.draw.rect(bar, (255, 255, 255, 220), bar.get_rect())
        screen.blit(bar, (0, 0))

        c1 = self.pal["text"]
        c2 = self.pal["danger"] if self.flash_t > 0 else self.pal["text"]
        t1 = self.font.render(f"🗑️ Déchets récupérés: {self.collected}", True, c1)
        t2 = self.font.render(f"🐟 Poissons impactés: {self.impacts} (−1 vie tous les {self.impact_threshold})", True, c1)
        t3 = self.font.render(f"❤️ x{self.lives}", True, c2)
        t4 = self.font.render(f"⏱️ {int(self.time_left)}s", True, c1)
        screen.blit(t1, (14, 10))
        screen.blit(t2, (14, 38))
        screen.blit(t3, (W - 120, 10))
        screen.blit(t4, (W - 120, 38))

        hint = self.font.render("A/D: bateau | SPACE: grappin | P: pause | ESC: menu", True, self.pal["accent2"])
        screen.blit(hint, (W // 2 - hint.get_width() // 2, self.surface_y - 28))


# -----------------------------
# =============================================================================
# JEU 2 : JUNGLE (Collecte en voiture)
# ============================================================================= (large slow car + front bin)
# -----------------------------
class JungleGameState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal = palette(game.data["settings"]["color_mode"])
        self.font = pygame.font.Font(None, 26)
        self.big = pygame.font.Font(None, 44)

        self.bg = vertical_gradient((WINDOW_WIDTH, WINDOW_HEIGHT), (40, 120, 65), (20, 70, 40))
        self.road_w = int(W * 0.52)
        self.road_x = WINDOW_WIDTH // 2 - self.road_w // 2
        self.scroll = 0.0

        self.car_img = car_sprite()
        self.car_x = WINDOW_WIDTH * 0.5
        self.car_vx = 0.0
        self.car_y = WINDOW_HEIGHT - 120
        self.acc = 1100.0
        self.drag = 9.0
        self.maxv = 280.0

        self.trash = []
        self.monkeys = []
        self.spawn_t = 0.0
        self.diff = 0.0

        self.score = 0
        self.lives = 3
        self.time_left = 70.0

        self.inv_t = 0.0
        self.knock_v = 0.0

        for _ in range(4):
            self._spawn_trash(y=random.uniform(-250, -40))

    def _spawn_trash(self, y=None):
        k = random.choice(["bottle", "can", "bag", "tire", "box"])
        x = random.uniform(self.road_x + 60, self.road_x + self.road_w - 60)
        y = -40 if y is None else y
        self.trash.append({
            "k": k, "x": x, "y": y,
            "rot": random.uniform(0, 360), "rots": random.uniform(-45, 45),
            "img": trash_sprite(k, 28)
        })

    def _spawn_monkey(self):
        x = random.uniform(self.road_x + 70, self.road_x + self.road_w - 70)
        self.monkeys.append({"x": x, "y": -50, "t": random.uniform(0, 10), "img": monkey_sprite()})

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p:
                self.game.push_state(PauseState(self.game, self))
            elif e.key == pygame.K_ESCAPE:
                self.game.transition_to(MenuState(self.game))

    def update(self, dt):
        self.pal = palette(self.game.data["settings"]["color_mode"])
        self.time_left -= dt
        if self.inv_t > 0:
            self.inv_t -= dt

        if self.time_left <= 0 or self.lives <= 0:
            score = self.score
            details = [("Déchets collectés", self.score), ("Vies restantes", self.lives)]
            self.game.transition_to(EndState(self.game, "jungle", score, details))
            return

        self.diff += dt
        speed = 140.0 + self.diff * 2.0  # slow scrolling

        # car movement (smooth)
        keys = pygame.key.get_pressed()
        ax = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            ax -= self.acc
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            ax += self.acc

        self.car_vx += ax * dt
        self.car_vx -= self.car_vx * self.drag * dt
        self.car_vx = clamp(self.car_vx, -self.maxv, self.maxv)

        # knockback from monkey hit
        if abs(self.knock_v) > 1:
            self.car_vx += self.knock_v
            self.knock_v *= (1.0 - 7.0 * dt)

        self.car_x += self.car_vx * dt
        self.car_x = clamp(self.car_x, self.road_x + 70, self.road_x + self.road_w - 70)

        # scrolling road
        self.scroll = (self.scroll + speed * dt) % 50

        # bin hitbox (front top of car sprite)
        car_rect = pygame.Rect(0, 0, self.car_img.get_width(), self.car_img.get_height())
        car_rect.center = (int(self.car_x), int(self.car_y))
        bin_rect = pygame.Rect(car_rect.left + 20, car_rect.top + 2, car_rect.width - 40, 20)

        # update trash
        for t in self.trash[:]:
            t["y"] += speed * dt
            t["rot"] += t["rots"] * dt
            tr = pygame.Rect(0, 0, 28, 28)
            tr.center = (int(t["x"]), int(t["y"]))
            if bin_rect.colliderect(tr):
                self.score += 1
                self.trash.remove(t)
            elif t["y"] > WINDOW_HEIGHT + 60:
                self.trash.remove(t)

        # update monkeys
        for m in self.monkeys[:]:
            m["y"] += (speed * 1.05) * dt
            m["t"] += dt
            mr = pygame.Rect(0, 0, 46, 46)
            mr.center = (int(m["x"]), int(m["y"]))
            body = car_rect.inflate(-20, -18)

            if self.inv_t <= 0 and body.colliderect(mr):
                self.lives -= 1
                self.inv_t = 1.0
                self.knock_v = (140 if (self.car_x < m["x"]) else -140)
                self.monkeys.remove(m)
            elif m["y"] > WINDOW_HEIGHT + 70:
                self.monkeys.remove(m)

        # spawn pacing (always playable)
        self.spawn_t += dt
        spawn_rate = max(0.55, 1.05 - self.diff * 0.01)
        if self.spawn_t >= spawn_rate:
            self.spawn_t = 0.0
            if random.random() < 0.72 and len(self.trash) < 10:
                self._spawn_trash()
            if random.random() < (0.25 + self.diff * 0.002) and len(self.monkeys) < 7:
                self._spawn_monkey()

    def draw(self, screen):
        screen.blit(self.bg, (0, 0))

        # stylized jungle on sides
        for x in range(0, WINDOW_WIDTH, 90):
            if x < self.road_x - 30 or x > self.road_x + self.road_w + 30:
                pygame.draw.circle(screen, (25, 60, 25), (x, 140), 52)
                pygame.draw.rect(screen, (60, 40, 20), (x - 6, 140, 12, 140), border_radius=6)
                pygame.draw.line(screen, (35, 90, 55), (x, 170), (x + 35, 200), 4)

        # road
        pygame.draw.rect(screen, (45, 45, 52), (self.road_x, 0, self.road_w, WINDOW_HEIGHT))
        pygame.draw.line(screen, (240, 240, 245), (self.road_x, 0), (self.road_x, WINDOW_HEIGHT), 4)
        pygame.draw.line(screen, (240, 240, 245), (self.road_x + self.road_w, 0), (self.road_x + self.road_w, WINDOW_HEIGHT), 4)
        for y in range(int(-self.scroll), WINDOW_HEIGHT, 50):
            pygame.draw.rect(screen, (240, 240, 245), (W // 2 - 6, y, 12, 28), border_radius=4)

        # trash
        for t in self.trash:
            img = pygame.transform.rotate(t["img"], t["rot"])
            r = img.get_rect(center=(int(t["x"]), int(t["y"])))
            screen.blit(img, r)

        # monkeys
        for m in self.monkeys:
            bob = math.sin(m["t"] * 6) * 2
            screen.blit(m["img"], (int(m["x"] - 26), int(m["y"] - 26 + bob)))

        # car (blink if invincible)
        car_pos = (int(self.car_x - self.car_img.get_width() // 2), int(self.car_y - self.car_img.get_height() // 2))
        if self.inv_t <= 0 or (int(self.inv_t * 12) % 2 == 0):
            screen.blit(self.car_img, car_pos)

        # UI bar
        bar = pygame.Surface((WINDOW_WIDTH, 68), pygame.SRCALPHA)
        pygame.draw.rect(bar, (255, 255, 255, 220), bar.get_rect())
        screen.blit(bar, (0, 0))

        t1 = self.font.render(f"🗑️ Score: {self.score}", True, self.pal["text"])
        t2 = self.font.render(f"❤️ x{self.lives}", True, self.pal["danger"])
        t3 = self.font.render(f"⏱️ {int(self.time_left)}s", True, self.pal["text"])
        screen.blit(t1, (14, 10))
        screen.blit(t2, (W - 120, 10))
        screen.blit(t3, (W - 120, 38))

        hint = self.font.render("Collecte UNIQUEMENT avec le bac avant | P: pause | ESC: menu", True, self.pal["accent2"])
        screen.blit(hint, (W // 2 - hint.get_width() // 2, 74))


# -----------------------------
# =============================================================================
# JEU 3 : ESPACE (Destruction de débris)
# ============================================================================= (left/right only + lasers + energy)
# -----------------------------
class SpaceGameState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal = palette(game.data["settings"]["color_mode"])
        self.font = pygame.font.Font(None, 26)

        self.ship_img = ship_sprite()
        self.ship_x = WINDOW_WIDTH * 0.5
        self.ship_y = WINDOW_HEIGHT - 95
        self.vx = 0.0
        self.acc = 1250.0
        self.drag = 10.0
        self.maxv = 300.0

        self.laser_img = laser_sprite()
        self.lasers = []
        self.cool = 0.0

        self.energy = 100.0
        self.energy_max = 100.0
        self.energy_regen = 28.0
        self.shot_cost = 12.0

        self.debris = []
        self.fx = []
        self.spawn_t = 0.0
        self.diff = 0.0

        self.score = 0
        self.combo = 0
        self.lives = 3
        self.time_left = 60.0

        # FIX du bug: étoiles en LISTES mutables, pas tuples
        self.stars = []
        for _ in range(220):
            self.stars.append([random.uniform(0, WINDOW_WIDTH), random.uniform(0, WINDOW_HEIGHT), random.uniform(
