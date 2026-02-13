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

Commandes:
    • Flèches ou A/D : Déplacements
    • ESPACE : Action principale (grappin, tir)
    • P : Pause
    • ESC : Retour au menu
    • I : Instructions

Auteur: Refactorisé et Complété
"""

import os
import json
import math
import random
import sys
from dataclasses import dataclass

import pygame

# -----------------------------
# CONFIGURATION GLOBALE
# -----------------------------
WINDOW_WIDTH, WINDOW_HEIGHT = 900, 600
W, H = WINDOW_WIDTH, WINDOW_HEIGHT  # Alias pour faciliter la lecture
FRAME_RATE = 60
SAVE_PATH = "eco_arcade_save.json"


def clamp(x, a, b):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


# -----------------------------
# GESTION DE LA SAUVEGARDE
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
        # Merge minimal pour éviter les clés manquantes
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
# PALETTES DE COULEURS
# -----------------------------
def palette(color_mode: str):
    if color_mode == "deuteranopia":
        return {
            "bg": (20, 25, 35),
            "panel": (245, 245, 245),
            "text": (20, 25, 35),
            "muted": (90, 95, 105),
            "accent": (0, 170, 255),
            "accent2": (255, 170, 0),
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
        "accent": (70, 210, 140),
        "accent2": (255, 220, 70),
        "danger": (255, 70, 70),
        "ok": (70, 210, 140),
        "water_top": (145, 215, 255),
        "water_deep": (25, 85, 150),
        "jungle": (25, 105, 45),
    }


# -----------------------------
# UTILITAIRES GRAPHIQUES
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
# CACHE DE SPRITES (Génération procédurale)
# -----------------------------
SPRITES = {}


def trash_sprite(kind: str, size=30):
    key = ("trash", kind, size)
    if key in SPRITES: return SPRITES[key]

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
    if key in SPRITES: return SPRITES[key]
    s = pygame.Surface((96, 56), pygame.SRCALPHA)
    hull = [(10, 28), (16, 12), (48, 6), (80, 12), (86, 28), (80, 44), (48, 50), (16, 44)]
    pygame.draw.polygon(s, (65, 160, 255), hull)
    pygame.draw.polygon(s, (20, 60, 155), hull, 3)
    pygame.draw.rect(s, (245, 245, 250), (36, 18, 24, 22), border_radius=6)
    pygame.draw.rect(s, (20, 60, 155), (36, 18, 24, 22), 2, border_radius=6)
    pygame.draw.circle(s, (255, 220, 70), (48, 10), 4)
    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]


def grapple_sprite():
    key = ("grapple",)
    if key in SPRITES: return SPRITES[key]
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
    if key in SPRITES: return SPRITES[key]
    s = pygame.Surface((44, 30), pygame.SRCALPHA)
    body = pygame.Rect(8, 7, 26, 16)
    pygame.draw.ellipse(s, (255, 165, 60), body)
    pygame.draw.ellipse(s, (230, 120, 35), body, 2)
    tail = [(8, 15), (2, 9), (2, 21)] if direction < 0 else [(34, 15), (42, 9), (42, 21)]
    eye = (18, 13) if direction < 0 else (24, 13)
    pygame.draw.polygon(s, (255, 165, 60), tail)
    pygame.draw.circle(s, (255, 255, 255), eye, 3)
    pygame.draw.circle(s, (0, 0, 0), eye, 2)
    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]


def car_sprite():
    key = ("car",)
    if key in SPRITES: return SPRITES[key]
    s = pygame.Surface((120, 90), pygame.SRCALPHA)
    pygame.draw.rect(s, (70, 210, 140), (12, 20, 96, 60), border_radius=14)
    pygame.draw.rect(s, (25, 105, 45), (12, 20, 96, 60), 3, border_radius=14)
    pygame.draw.rect(s, (160, 220, 255), (26, 33, 68, 18), border_radius=8)
    pygame.draw.rect(s, (0, 0, 0), (26, 33, 68, 18), 2, border_radius=8)
    pygame.draw.rect(s, (155, 160, 175), (20, 4, 80, 18), border_radius=6)
    pygame.draw.rect(s, (90, 95, 110), (20, 4, 80, 18), 2, border_radius=6)
    pygame.draw.line(s, (105, 110, 125), (26, 13), (94, 13), 2)
    for x in (28, 92):
        for y in (28, 76):
            pygame.draw.circle(s, (15, 15, 18), (x, y), 11)
            pygame.draw.circle(s, (55, 55, 65), (x, y), 7)
    pygame.draw.circle(s, (255, 220, 70), (34, 82), 4)
    pygame.draw.circle(s, (255, 220, 70), (86, 82), 4)
    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]


def monkey_sprite():
    key = ("monkey",)
    if key in SPRITES: return SPRITES[key]
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
    pygame.draw.line(s, (140, 85, 35), (34, 36), (48, 50), 6)
    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]


def ship_sprite():
    key = ("ship",)
    if key in SPRITES: return SPRITES[key]
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
    if key in SPRITES: return SPRITES[key]
    s = pygame.Surface((6, 22), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 255, 255), (0, 0, 6, 22))
    pygame.draw.rect(s, (255, 255, 255), (1, 0, 4, 22))
    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]


def debris_sprite(kind: str):
    key = ("debris", kind)
    if key in SPRITES: return SPRITES[key]
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
# SYSTÈME DE PARTICULES
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
# ARCHITECTURE DES ÉTATS
# -----------------------------
class State:
    def __init__(self, game):
        self.game = game

    def enter(self, **kwargs): pass

    def exit(self): pass

    def handle_event(self, e): pass

    def update(self, dt): pass

    def draw(self, screen): pass


# -----------------------------
# COMPOSANTS UI
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

        shadow = rounded_rect_surf((rect.w, rect.h), (0, 0, 0, 80), radius=14)
        screen.blit(shadow, (rect.x, rect.y + 4))

        body_col = (pal["accent"][0], pal["accent"][1], pal["accent"][2], 240) if t > 0 else (40, 45, 58, 220)
        border_col = pal["accent2"] if t > 0 else (240, 240, 245)
        body = rounded_rect_surf((rect.w, rect.h), body_col, radius=14, border=3, border_color=border_col)
        screen.blit(body, rect.topleft)

        if t > 0:
            glow = pygame.Surface((rect.w + 18, rect.h + 18), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*pal["accent2"], int(35 * t)), glow.get_rect(), border_radius=18)
            screen.blit(glow, (rect.x - 9, rect.y - 9))

        txt = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=rect.center))


# -----------------------------
# PARTICULES DU MENU
# -----------------------------
class MenuParticles:
    def __init__(self):
        self.items = []
        self.spawn_t = 0.0

    def update(self, dt, mode, intensity):
        rate = {"low": 0.35, "med": 0.20, "high": 0.10}.get(intensity, 0.20)
        self.spawn_t += dt
        while self.spawn_t >= rate:
            self.spawn_t -= rate
            if mode == "ocean":
                x = random.uniform(0, W)
                y = H + 10
                vx = random.uniform(-10, 10)
                vy = random.uniform(-55, -85)
                self.items.append(["bubble", x, y, vx, vy, random.uniform(0.8, 1.4), random.uniform(0.8, 1.4)])
            elif mode == "jungle":
                x = random.uniform(0, W)
                y = -12
                vx = random.uniform(-15, 15)
                vy = random.uniform(35, 60)
                self.items.append(["leaf", x, y, vx, vy, random.uniform(0.0, math.tau), random.uniform(0.8, 1.2)])
            else:  # space
                x = random.uniform(0, W)
                y = random.uniform(0, H)
                sp = random.uniform(30, 110)
                self.items.append(["star", x, y, 0.0, sp, random.uniform(1.0, 2.5), 0.0])

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
                if it[2] > H + 10:
                    it[2] = -10
                    it[1] = random.uniform(0, W)

        self.items = [it for it in self.items if -60 < it[2] < H + 60]

    def draw(self, screen, mode):
        if mode == "ocean":
            for it in self.items:
                if it[0] != "bubble": continue
                _, x, y, *_ = it
                r = int(3 * it[5])
                pygame.draw.circle(screen, (220, 245, 255), (int(x), int(y)), r, 2)
        elif mode == "jungle":
            for it in self.items:
                if it[0] != "leaf": continue
                _, x, y, *_ = it
                ang = it[5]
                sc = it[6]
                pts = []
                for k in range(6):
                    a = ang + k * (math.tau / 6)
                    rad = (8 if k % 2 == 0 else 4) * sc
                    pts.append((x + math.cos(a) * rad, y + math.sin(a) * rad))
                pygame.draw.polygon(screen, (110, 220, 140), pts)
                pygame.draw.polygon(screen, (40, 120, 70), pts, 2)
        else:
            for it in self.items:
                if it[0] != "star": continue
                _, x, y, *_ = it
                r = int(it[5])
                pygame.draw.circle(screen, (245, 245, 255), (int(x), int(y)), r)


# -----------------------------
# ÉTATS DU JEU (MENU, INSTRUCTIONS, ETC)
# -----------------------------
class MenuState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal = palette(game.data["settings"]["color_mode"])
        self.font_title = pygame.font.Font(None, 84)
        self.font_btn = pygame.font.Font(None, 38)
        self.font_small = pygame.font.Font(None, 22)
        self.bg_ocean = vertical_gradient((W, H), (40, 160, 220), (15, 55, 120))
        self.bg_jungle = vertical_gradient((W, H), (40, 170, 90), (18, 70, 45))
        self.bg_space = vertical_gradient((W, H), (10, 12, 22), (28, 15, 45))
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
        if self.selected == 0: return "ocean"
        if self.selected == 1: return "jungle"
        if self.selected == 2: return "space"
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
                if b.base_rect.collidepoint(e.pos): self.selected = i
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, b in enumerate(self.buttons):
                if b.base_rect.collidepoint(e.pos): self._activate(i)

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
        for b in self.buttons: b.update(dt, mp)

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
        hint = self.font_small.render("↑↓/W-S: naviguer | Entrée: lancer | I: instructions | ESC: quitter", True,
                                      (240, 240, 245))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 30))


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


class PauseState(State):
    def __init__(self, game, under_state):
        super().__init__(game)
        self.under = under_state
        self.font = pygame.font.Font(None, 56)
        self.small = pygame.font.Font(None, 24)

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_p, pygame.K_ESCAPE):
                self.game.pop_state()
            elif e.key == pygame.K_m:
                self.game.transition_to(MenuState(self.game))

    def draw(self, screen):
        self.under.draw(screen)
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        screen.blit(ov, (0, 0))
        panel = rounded_rect_surf((520, 220), (255, 255, 255, 235), radius=16)
        screen.blit(panel, (W // 2 - 260, H // 2 - 110))
        t = self.font.render("PAUSE", True, (20, 25, 35))
        screen.blit(t, (W // 2 - t.get_width() // 2, H // 2 - 80))
        h1 = self.small.render("P / ESC: reprendre", True, (20, 25, 35))
        h2 = self.small.render("M: menu", True, (20, 25, 35))
        screen.blit(h1, (W // 2 - h1.get_width() // 2, H // 2 + 5))
        screen.blit(h2, (W // 2 - h2.get_width() // 2, H // 2 + 34))


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
        screen.blit(s1, (140, y));
        y += 36
        screen.blit(s2, (140, y));
        y += 36
        screen.blit(s3, (140, y));
        y += 36
        y += 10
        for k, v in self.details:
            line = self.small.render(f"{k}: {v}", True, pal["muted"])
            screen.blit(line, (140, y))
            y += 30
        hint = self.small.render("ESC / Entrée: menu", True, pal["danger"])
        screen.blit(hint, (W // 2 - hint.get_width() // 2, 475))


# -----------------------------
# JEU 1 : OCÉAN
# -----------------------------
class OceanGameState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal = palette(game.data["settings"]["color_mode"])
        self.font = pygame.font.Font(None, 26)
        self.surface_y = 120
        self.bg_water = vertical_gradient((W, H), self.pal["water_top"], self.pal["water_deep"])
        self.boat_img = boat_sprite()
        self.boat_x, self.boat_y = W * 0.5, 58
        self.boat_vx, self.boat_acc, self.boat_drag, self.boat_max = 0.0, 1300.0, 7.5, 320.0
        self.gr_img = grapple_sprite()
        self.gr_active, self.gr_state = False, "idle"
        self.gr_y = self.boat_y + 40
        self.gr_speed, self.gr_max_depth = 220.0, H - 85
        self.gr_caught = None
        self.trash, self.fish, self.fx = [], [], []
        self.spawn_t = 0.0
        self.collected, self.impacts, self.lives, self.time_left = 0, 0, 3, 75.0
        self.impact_threshold, self.next_impact_loss, self.flash_t = 3, 3, 0.0
        for _ in range(7): self._spawn_trash(x=W + random.uniform(0, 350))
        for _ in range(10): self._spawn_fish(x=W + random.uniform(0, 500))

    def _spawn_trash(self, x=None):
        kinds = ["bottle", "can", "bag", "tire", "box"]
        k = random.choice(kinds)
        y = random.uniform(self.surface_y + 35, H - 55)
        x = W + 40 if x is None else x
        self.trash.append({
            "k": k, "x": x, "y": y, "vx": -random.uniform(45, 85),
            "t": random.uniform(0, 10), "rot": random.uniform(0, 360),
            "rots": random.uniform(-25, 25), "img": trash_sprite(k, 30),
        })

    def _spawn_fish(self, x=None):
        y = random.uniform(self.surface_y + 30, H - 50)
        x = W + 40 if x is None else x
        self.fish.append({
            "x": x, "y": y, "vx": -random.uniform(70, 120),
            "t": random.uniform(0, 10), "img": fish_sprite(direction=-1)
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
        if self.flash_t > 0: self.flash_t -= dt
        if self.time_left <= 0 or self.lives <= 0:
            score = max(0, self.collected * 10 - self.impacts * 3)
            self.game.transition_to(EndState(self.game, "ocean", score, [("Déchets récupérés", self.collected),
                                                                         ("Poissons impactés", self.impacts)]))
            return

        keys = pygame.key.get_pressed()
        ax = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: ax -= self.boat_acc
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: ax += self.boat_acc
        self.boat_vx += ax * dt
        self.boat_vx -= self.boat_vx * self.boat_drag * dt
        self.boat_vx = clamp(self.boat_vx, -self.boat_max, self.boat_max)
        self.boat_x = clamp(self.boat_x + self.boat_vx * dt, 70, W - 70)

        gr_x = self.boat_x
        if self.gr_active:
            if self.gr_state == "down":
                self.gr_y += self.gr_speed * dt
                if self.gr_y >= self.gr_max_depth: self.gr_state = "up"
                if self.gr_caught is None:
                    for t in self.trash:
                        if (gr_x - t["x"]) ** 2 + (self.gr_y - t["y"]) ** 2 < 26 ** 2:
                            self.gr_caught = t
                            self.gr_state = "up"
                            break
                for f in self.fish:
                    if (gr_x - f["x"]) ** 2 + (self.gr_y - f["y"]) ** 2 < 24 ** 2:
                        self.lives -= 1
                        self.flash_t = 0.45
                        self.gr_state = "up"
                        break
            elif self.gr_state == "up":
                self.gr_y -= self.gr_speed * dt
                if self.gr_caught is not None:
                    self.gr_caught["x"], self.gr_caught["y"] = gr_x, self.gr_y + 16
                if self.gr_y <= self.boat_y + 40:
                    self.gr_active = False
                    self.gr_state = "idle"
                    if self.gr_caught is not None:
                        if self.gr_caught in self.trash: self.trash.remove(self.gr_caught)
                        self.collected += 1
                        self.gr_caught = None

        for t in self.trash[:]:
            if t is self.gr_caught: continue
            t["x"] += t["vx"] * dt
            t["t"] += dt
            t["rot"] += t["rots"] * dt
            if t["x"] < -80: self.trash.remove(t); continue
            for f in self.fish:
                if (t["x"] - f["x"]) ** 2 + (t["y"] - f["y"]) ** 2 < 30 ** 2:
                    self.impacts += 1
                    if t in self.trash: self.trash.remove(t)
                    break
        for f in self.fish[:]:
            f["x"] += f["vx"] * dt
            f["t"] += dt
            if f["x"] < -80: self.fish.remove(f)

        if self.impacts >= self.next_impact_loss:
            self.lives -= 1
            self.flash_t = 0.55
            self.next_impact_loss += self.impact_threshold

        self.spawn_t += dt
        if self.spawn_t >= 1.25:
            self.spawn_t = 0.0
            if len(self.trash) < 9: self._spawn_trash()
            if len(self.fish) < 12: self._spawn_fish()

    def draw(self, screen):
        screen.blit(self.bg_water, (0, 0))
        pygame.draw.rect(screen, (170, 225, 255), (0, 0, W, self.surface_y))
        pygame.draw.line(screen, (60, 140, 220), (0, self.surface_y), (W, self.surface_y), 4)
        for f in self.fish:
            screen.blit(f["img"], (int(f["x"] - 22), int(f["y"] - 15 + math.sin(f["t"] * 2.2) * 3)))
        for t in self.trash:
            img = pygame.transform.rotate(t["img"], t["rot"])
            screen.blit(img, img.get_rect(center=(int(t["x"]), int(t["y"] + math.sin(t["t"] * 1.6) * 2))))
        if self.gr_active:
            pygame.draw.line(screen, (90, 90, 95), (int(self.boat_x), self.boat_y + 40),
                             (int(self.boat_x), int(self.gr_y)), 3)
            screen.blit(self.gr_img, (int(self.boat_x) - 17, int(self.gr_y) - 17))
        screen.blit(self.boat_img, (int(self.boat_x - 48), int(self.boat_y - 28)))

        # UI
        bar = pygame.Surface((W, 72), pygame.SRCALPHA)
        pygame.draw.rect(bar, (255, 255, 255, 220), bar.get_rect())
        screen.blit(bar, (0, 0))
        c1, c2 = self.pal["text"], self.pal["danger"] if self.flash_t > 0 else self.pal["text"]
        screen.blit(self.font.render(f"🗑️ Déchets: {self.collected}", True, c1), (14, 10))
        screen.blit(self.font.render(f"🐟 Impacts: {self.impacts}", True, c1), (14, 38))
        screen.blit(self.font.render(f"❤️ x{self.lives}", True, c2), (W - 120, 10))
        screen.blit(self.font.render(f"⏱️ {int(self.time_left)}s", True, c1), (W - 120, 38))


# -----------------------------
# JEU 2 : JUNGLE
# -----------------------------
class JungleGameState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal = palette(game.data["settings"]["color_mode"])
        self.font = pygame.font.Font(None, 26)
        self.bg = vertical_gradient((W, H), (40, 120, 65), (20, 70, 40))
        self.road_w, self.road_x = int(W * 0.52), W // 2 - int(W * 0.52) // 2
        self.scroll = 0.0
        self.car_img = car_sprite()
        self.car_x, self.car_y = W * 0.5, H - 120
        self.car_vx, self.acc, self.drag, self.maxv = 0.0, 1100.0, 9.0, 280.0
        self.trash, self.monkeys = [], []
        self.spawn_t, self.diff = 0.0, 0.0
        self.score, self.lives, self.time_left = 0, 3, 70.0
        self.inv_t, self.knock_v = 0.0, 0.0
        for _ in range(4): self._spawn_trash(y=random.uniform(-250, -40))

    def _spawn_trash(self, y=None):
        k = random.choice(["bottle", "can", "bag", "tire", "box"])
        x = random.uniform(self.road_x + 60, self.road_x + self.road_w - 60)
        self.trash.append({"k": k, "x": x, "y": -40 if y is None else y, "rot": random.uniform(0, 360),
                           "rots": random.uniform(-45, 45), "img": trash_sprite(k, 28)})

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
        if self.inv_t > 0: self.inv_t -= dt
        if self.time_left <= 0 or self.lives <= 0:
            self.game.transition_to(EndState(self.game, "jungle", self.score,
                                             [("Déchets collectés", self.score), ("Vies restantes", self.lives)]))
            return

        self.diff += dt
        speed = 140.0 + self.diff * 2.0
        keys = pygame.key.get_pressed()
        ax = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: ax -= self.acc
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: ax += self.acc
        self.car_vx += ax * dt
        self.car_vx -= self.car_vx * self.drag * dt
        if abs(self.knock_v) > 1:
            self.car_vx += self.knock_v
            self.knock_v *= (1.0 - 7.0 * dt)
        self.car_x = clamp(self.car_x + self.car_vx * dt, self.road_x + 70, self.road_x + self.road_w - 70)
        self.scroll = (self.scroll + speed * dt) % 50

        car_rect = pygame.Rect(0, 0, 120, 90)
        car_rect.center = (int(self.car_x), int(self.car_y))
        bin_rect = pygame.Rect(car_rect.left + 20, car_rect.top + 2, car_rect.width - 40, 20)

        for t in self.trash[:]:
            t["y"] += speed * dt
            t["rot"] += t["rots"] * dt
            tr = pygame.Rect(0, 0, 28, 28)
            tr.center = (int(t["x"]), int(t["y"]))
            if bin_rect.colliderect(tr):
                self.score += 1
                self.trash.remove(t)
            elif t["y"] > H + 60:
                self.trash.remove(t)

        for m in self.monkeys[:]:
            m["y"] += (speed * 1.05) * dt
            m["t"] += dt
            mr = pygame.Rect(0, 0, 46, 46)
            mr.center = (int(m["x"]), int(m["y"]))
            if self.inv_t <= 0 and car_rect.inflate(-20, -18).colliderect(mr):
                self.lives -= 1
                self.inv_t = 1.0
                self.knock_v = (140 if (self.car_x < m["x"]) else -140)
                self.monkeys.remove(m)
            elif m["y"] > H + 70:
                self.monkeys.remove(m)

        self.spawn_t += dt
        if self.spawn_t >= max(0.55, 1.05 - self.diff * 0.01):
            self.spawn_t = 0.0
            if random.random() < 0.72 and len(self.trash) < 10: self._spawn_trash()
            if random.random() < (0.25 + self.diff * 0.002) and len(self.monkeys) < 7: self._spawn_monkey()

    def draw(self, screen):
        screen.blit(self.bg, (0, 0))
        for x in range(0, W, 90):
            if x < self.road_x - 30 or x > self.road_x + self.road_w + 30:
                pygame.draw.circle(screen, (25, 60, 25), (x, 140), 52)
        pygame.draw.rect(screen, (45, 45, 52), (self.road_x, 0, self.road_w, H))
        pygame.draw.line(screen, (240, 240, 245), (self.road_x, 0), (self.road_x, H), 4)
        pygame.draw.line(screen, (240, 240, 245), (self.road_x + self.road_w, 0), (self.road_x + self.road_w, H), 4)
        for y in range(int(-self.scroll), H, 50):
            pygame.draw.rect(screen, (240, 240, 245), (W // 2 - 6, y, 12, 28), border_radius=4)
        for t in self.trash:
            img = pygame.transform.rotate(t["img"], t["rot"])
            screen.blit(img, img.get_rect(center=(int(t["x"]), int(t["y"]))))
        for m in self.monkeys:
            screen.blit(m["img"], (int(m["x"] - 26), int(m["y"] - 26 + math.sin(m["t"] * 6) * 2)))
        if self.inv_t <= 0 or (int(self.inv_t * 12) % 2 == 0):
            screen.blit(self.car_img, (int(self.car_x - 60), int(self.car_y - 45)))

        # UI
        bar = pygame.Surface((W, 68), pygame.SRCALPHA)
        pygame.draw.rect(bar, (255, 255, 255, 220), bar.get_rect())
        screen.blit(bar, (0, 0))
        screen.blit(self.font.render(f"🗑️ Score: {self.score}", True, self.pal["text"]), (14, 10))
        screen.blit(self.font.render(f"❤️ x{self.lives}", True, self.pal["danger"]), (W - 120, 10))
        screen.blit(self.font.render(f"⏱️ {int(self.time_left)}s", True, self.pal["text"]), (W - 120, 38))


# -----------------------------
# JEU 3 : ESPACE
# -----------------------------
class SpaceGameState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal = palette(game.data["settings"]["color_mode"])
        self.font = pygame.font.Font(None, 26)
        self.ship_img = ship_sprite()
        self.ship_x, self.ship_y = W * 0.5, H - 95
        self.vx, self.acc, self.drag, self.maxv = 0.0, 1250.0, 10.0, 300.0
        self.laser_img = laser_sprite()
        self.lasers, self.cool = [], 0.0
        self.energy, self.energy_max, self.energy_regen, self.shot_cost = 100.0, 100.0, 28.0, 12.0
        self.debris, self.fx = [], []
        self.spawn_t, self.diff = 0.0, 0.0
        self.score, self.lives, self.time_left = 0, 3, 60.0
        self.stars = []
        for _ in range(220):
            self.stars.append([random.uniform(0, W), random.uniform(0, H), random.uniform(30, 100)])

    def _spawn_debris(self):
        sz = random.choices(["small", "medium", "large"], weights=[0.6, 0.3, 0.1])[0]
        hp = {"small": 1, "medium": 2, "large": 3}[sz]
        self.debris.append({
            "sz": sz, "hp": hp, "img": debris_sprite(sz),
            "x": random.uniform(40, W - 40), "y": -60,
            "vx": random.uniform(-10, 10), "vy": random.uniform(50, 100 + self.diff * 2),
            "rot": random.uniform(0, 360), "rots": random.uniform(-60, 60)
        })

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p:
                self.game.push_state(PauseState(self.game, self))
            elif e.key == pygame.K_ESCAPE:
                self.game.transition_to(MenuState(self.game))
            elif e.key == pygame.K_SPACE:
                if self.cool <= 0 and self.energy >= self.shot_cost:
                    self.energy -= self.shot_cost
                    self.cool = 0.18
                    self.lasers.append([self.ship_x - 18, self.ship_y + 10])
                    self.lasers.append([self.ship_x + 18, self.ship_y + 10])

    def update(self, dt):
        self.pal = palette(self.game.data["settings"]["color_mode"])
        self.time_left -= dt
        self.diff += dt
        if self.time_left <= 0 or self.lives <= 0:
            self.game.transition_to(EndState(self.game, "space", self.score,
                                             [("Débris détruits", self.score), ("Vies restantes", self.lives)]))
            return

        # Stars
        for s in self.stars:
            s[1] += s[2] * dt
            if s[1] > H:
                s[1] = -5
                s[0] = random.uniform(0, W)

        # Ship
        keys = pygame.key.get_pressed()
        ax = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: ax -= self.acc
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: ax += self.acc
        self.vx += ax * dt
        self.vx -= self.vx * self.drag * dt
        self.vx = clamp(self.vx, -self.maxv, self.maxv)
        self.ship_x = clamp(self.ship_x + self.vx * dt, 40, W - 40)

        # Energy & Laser
        self.energy = min(self.energy_max, self.energy + self.energy_regen * dt)
        if self.cool > 0: self.cool -= dt
        for l in self.lasers[:]:
            l[1] -= 550 * dt
            if l[1] < -20: self.lasers.remove(l)

        # Debris logic
        ship_rect = pygame.Rect(self.ship_x - 25, self.ship_y - 20, 50, 60)
        for d in self.debris[:]:
            d["y"] += d["vy"] * dt
            d["x"] += d["vx"] * dt
            d["rot"] += d["rots"] * dt
            d_rect = pygame.Rect(0, 0, d["img"].get_width(), d["img"].get_height())
            d_rect.center = (int(d["x"]), int(d["y"]))

            # Collision Laser -> Debris
            hit = False
            for l in self.lasers[:]:
                if d_rect.collidepoint((int(l[0]), int(l[1]))):
                    self.lasers.remove(l)
                    d["hp"] -= 1
                    hit = True
                    # Spark
                    for _ in range(3):
                        self.fx.append(
                            Particle(d["x"], d["y"], random.uniform(-40, 40), random.uniform(-40, 40), 0.3, 0.0,
                                     "spark", 2, self.pal["accent2"]))
                    if d["hp"] <= 0:
                        self.score += (1 if d["sz"] == "small" else 2 if d["sz"] == "medium" else 3)
                        self.debris.remove(d)
                        break
            if hit and d not in self.debris: continue

            # Collision Debris -> Ship
            if d_rect.colliderect(ship_rect):
                self.lives -= 1
                self.debris.remove(d)
                # Explosion
                for _ in range(12):
                    self.fx.append(
                        Particle(self.ship_x, self.ship_y, random.uniform(-80, 80), random.uniform(-80, 80), 0.6, 0.0,
                                 "boom", 3, self.pal["danger"]))
            elif d["y"] > H + 50:
                self.debris.remove(d)

        # Spawn
        self.spawn_t += dt
        if self.spawn_t >= max(0.4, 1.2 - self.diff * 0.02):
            self.spawn_t = 0.0
            self._spawn_debris()

        # Particles
        for p in self.fx[:]:
            p.update(dt)
            if p.dead(): self.fx.remove(p)

    def draw(self, screen):
        screen.fill((10, 12, 20))
        for s in self.stars:
            c = int(min(255, s[2] * 2))
            pygame.draw.circle(screen, (c, c, c), (int(s[0]), int(s[1])), 1)

        for l in self.lasers:
            screen.blit(self.laser_img, (int(l[0]), int(l[1])))

        screen.blit(self.ship_img, (int(self.ship_x - 28), int(self.ship_y - 35)))

        for d in self.debris:
            img = pygame.transform.rotate(d["img"], d["rot"])
            screen.blit(img, img.get_rect(center=(int(d["x"]), int(d["y"]))))

        for p in self.fx: p.draw(screen)

        # UI
        bar = pygame.Surface((W, 70), pygame.SRCALPHA)
        pygame.draw.rect(bar, (255, 255, 255, 30), bar.get_rect())
        screen.blit(bar, (0, 0))
        screen.blit(self.font.render(f"Score: {self.score}", True, (255, 255, 255)), (20, 20))
        screen.blit(self.font.render(f"❤️ x{self.lives}", True, self.pal["danger"]), (W - 100, 20))
        # Energy bar
        pygame.draw.rect(screen, (50, 50, 50), (W // 2 - 100, 25, 200, 16), border_radius=8)
        pct = self.energy / self.energy_max
        col = self.pal["accent"] if pct > 0.3 else self.pal["danger"]
        pygame.draw.rect(screen, col, (W // 2 - 98, 27, 196 * pct, 12), border_radius=6)


# -----------------------------
# CLASSE PRINCIPALE (GAME)
# -----------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Eco Arcade V2")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.data = load_save()

        # State stack
        self.state_stack = []
        self.transition_to(MenuState(self))

    def transition_to(self, state):
        self.state_stack = [state]
        state.enter()

    def push_state(self, state):
        self.state_stack.append(state)
        state.enter()

    def pop_state(self):
        if len(self.state_stack) > 1:
            s = self.state_stack.pop()
            s.exit()

    def run(self):
        while self.running:
            dt = self.clock.tick(FRAME_RATE) / 1000.0

            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.state_stack:
                    self.state_stack[-1].handle_event(event)

            # Update & Draw
            if self.state_stack:
                self.state_stack[-1].update(dt)
                self.state_stack[-1].draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# -----------------------------
# POINT D'ENTRÉE
# -----------------------------
if __name__ == "__main__":
    game = Game()
    game.run()