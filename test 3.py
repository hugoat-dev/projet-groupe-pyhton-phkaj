#!/usr/bin/env python3
"""
Eco Arcade V2 - Version améliorée avec grappin, lasers et polish
Contrôles: Flèches/WASD, SPACE pour actions, ESC pour menu/pause
"""

import pygame
import random
import math
import json
import os
from enum import Enum

pygame.init()

# Constantes
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
DARK_BLUE = (20, 50, 150)
GREEN = (50, 200, 50)
DARK_GREEN = (20, 100, 20)
BROWN = (139, 69, 19)
GRAY = (100, 100, 100)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (150, 50, 200)
LIGHT_BLUE = (135, 206, 250)
DARK_GRAY = (50, 50, 50)
CYAN = (0, 255, 255)

# Cache sprites
SPRITE_CACHE = {}

# Système de sauvegarde
SAVE_FILE = "eco_arcade_save.json"

def load_save_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"ocean_best": 0, "jungle_best": 0, "space_best": 0,
            "settings": {"particle_intensity": "med", "color_mode": "normal"}}

def save_data(data):
    with open(SAVE_FILE, 'w') as f:
        json.dump(data, f)

GAME_DATA = load_save_data()

# Utilitaires
def draw_rounded_rect(surface, color, rect, radius=10, border=0, border_color=None):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, color, rect.inflate(-radius*2, 0))
    pygame.draw.rect(surface, color, rect.inflate(0, -radius*2))
    for pos in [(rect.left + radius, rect.top + radius),
                (rect.right - radius - 1, rect.top + radius),
                (rect.left + radius, rect.bottom - radius - 1),
                (rect.right - radius - 1, rect.bottom - radius - 1)]:
        pygame.draw.circle(surface, color, pos, radius)
    if border > 0 and border_color:
        pygame.draw.line(surface, border_color, (rect.left + radius, rect.top),
                        (rect.right - radius, rect.top), border)
        pygame.draw.line(surface, border_color, (rect.left + radius, rect.bottom - 1),
                        (rect.right - radius, rect.bottom - 1), border)
        pygame.draw.line(surface, border_color, (rect.left, rect.top + radius),
                        (rect.left, rect.bottom - radius), border)
        pygame.draw.line(surface, border_color, (rect.right - 1, rect.top + radius),
                        (rect.right - 1, rect.bottom - radius), border)
        for pos in [(rect.left + radius, rect.top + radius),
                    (rect.right - radius - 1, rect.top + radius),
                    (rect.left + radius, rect.bottom - radius - 1),
                    (rect.right - radius - 1, rect.bottom - radius - 1)]:
            pygame.draw.circle(surface, border_color, pos, radius, border)

def create_gradient(width, height, top_color, bottom_color):
    surf = pygame.Surface((width, height))
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        pygame.draw.line(surf, (r, g, b), (0, y), (width, y))
    return surf

# Sprites procéduraux
def create_trash_sprite(trash_type, size=30):
    key = f"trash_{trash_type}_{size}"
    if key in SPRITE_CACHE:
        return SPRITE_CACHE[key]

    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    if trash_type == "bottle":
        pygame.draw.rect(surf, (100, 150, 200), (size//3, size//5, size//3, size//2))
        pygame.draw.rect(surf, (80, 130, 180), (size//3+2, size//8, size//3-4, size//6))
        pygame.draw.circle(surf, (150, 200, 255), (size//2, size//3), size//8)
    elif trash_type == "can":
        pygame.draw.ellipse(surf, (180, 180, 190), (size//4, size//3, size//2, size//2))
        pygame.draw.rect(surf, (200, 200, 210), (size//4+2, size//3+5, size//2-4, 3))
    elif trash_type == "bag":
        points = [(size//2, size//5), (size*3//4, size//3), (size*2//3, size*3//4),
                  (size//3, size*3//4), (size//4, size//3)]
        pygame.draw.polygon(surf, (220, 220, 230, 150), points)
        pygame.draw.polygon(surf, (180, 180, 190), points, 2)
    elif trash_type == "tire":
        pygame.draw.circle(surf, (30, 30, 30), (size//2, size//2), size//3)
        pygame.draw.circle(surf, (50, 50, 50), (size//2, size//2), size//5)
    else:  # box
        pygame.draw.rect(surf, (139, 90, 43), (size//5, size//4, size*3//5, size//2))
        pygame.draw.line(surf, (100, 60, 20), (size//5, size//4), (size*4//5, size//4), 2)

    SPRITE_CACHE[key] = surf.convert_alpha()
    return SPRITE_CACHE[key]

def create_boat_sprite():
    if "boat" in SPRITE_CACHE:
        return SPRITE_CACHE["boat"]

    surf = pygame.Surface((70, 90), pygame.SRCALPHA)

    # Coque
    points = [(35, 10), (55, 35), (52, 70), (18, 70), (15, 35)]
    pygame.draw.polygon(surf, BLUE, points)
    pygame.draw.polygon(surf, DARK_BLUE, points, 3)

    # Cabine
    pygame.draw.rect(surf, WHITE, (25, 25, 20, 25))
    pygame.draw.rect(surf, DARK_BLUE, (25, 25, 20, 25), 2)
    pygame.draw.rect(surf, LIGHT_BLUE, (28, 30, 6, 6))
    pygame.draw.rect(surf, LIGHT_BLUE, (36, 30, 6, 6))

    # Pont
    pygame.draw.rect(surf, (200, 200, 200), (27, 15, 16, 10))

    # Grue/support pour grappin
    pygame.draw.rect(surf, GRAY, (33, 50, 4, 15))
    pygame.draw.circle(surf, YELLOW, (35, 65), 4)

    SPRITE_CACHE["boat"] = surf.convert_alpha()
    return SPRITE_CACHE["boat"]

def create_grapple_sprite():
    if "grapple" in SPRITE_CACHE:
        return SPRITE_CACHE["grapple"]

    surf = pygame.Surface((30, 30), pygame.SRCALPHA)

    # Crochet
    pygame.draw.circle(surf, (150, 150, 150), (15, 15), 8)
    pygame.draw.circle(surf, (100, 100, 100), (15, 15), 6, 2)

    # Griffes
    for angle in [0, 120, 240]:
        rad = math.radians(angle)
        x1 = 15 + 8 * math.cos(rad)
        y1 = 15 + 8 * math.sin(rad)
        x2 = 15 + 14 * math.cos(rad)
        y2 = 15 + 14 * math.sin(rad)
        pygame.draw.line(surf, (120, 120, 120), (x1, y1), (x2, y2), 3)

    SPRITE_CACHE["grapple"] = surf.convert_alpha()
    return SPRITE_CACHE["grapple"]

def create_fish_sprite(direction=1):
    key = f"fish_{direction}"
    if key in SPRITE_CACHE:
        return SPRITE_CACHE[key]

    surf = pygame.Surface((40, 28), pygame.SRCALPHA)

    pygame.draw.ellipse(surf, ORANGE, (6, 6, 26, 16))
    pygame.draw.ellipse(surf, (255, 140, 0), (6, 6, 26, 16), 2)

    if direction > 0:
        tail_points = [(32, 14), (38, 8), (38, 20)]
        eye_pos = (24, 12)
    else:
        tail_points = [(8, 14), (2, 8), (2, 20)]
        eye_pos = (16, 12)

    pygame.draw.polygon(surf, ORANGE, tail_points)
    pygame.draw.circle(surf, WHITE, eye_pos, 3)
    pygame.draw.circle(surf, BLACK, eye_pos, 2)

    SPRITE_CACHE[key] = surf.convert_alpha()
    return SPRITE_CACHE[key]

def create_car_sprite():
    if "car" in SPRITE_CACHE:
        return SPRITE_CACHE["car"]

    surf = pygame.Surface((90, 120), pygame.SRCALPHA)

    # Carrosserie
    pygame.draw.rect(surf, GREEN, (12, 30, 66, 80), border_radius=10)
    pygame.draw.rect(surf, DARK_GREEN, (12, 30, 66, 80), 3, border_radius=10)

    # Pare-brise
    pygame.draw.rect(surf, LIGHT_BLUE, (18, 45, 54, 22))
    pygame.draw.rect(surf, BLACK, (18, 45, 54, 22), 2)

    # BAC AVANT (zone de collecte)
    pygame.draw.rect(surf, (120, 120, 130), (15, 8, 60, 20), border_radius=5)
    pygame.draw.rect(surf, (80, 80, 90), (15, 8, 60, 20), 2, border_radius=5)
    pygame.draw.line(surf, (100, 100, 110), (20, 18), (70, 18), 2)

    # Roues
    for x in [20, 70]:
        for y in [35, 105]:
            pygame.draw.circle(surf, BLACK, (x, y), 9)
            pygame.draw.circle(surf, DARK_GRAY, (x, y), 6)

    # Phares
    pygame.draw.circle(surf, YELLOW, (25, 115), 4)
    pygame.draw.circle(surf, YELLOW, (65, 115), 4)

    SPRITE_CACHE["car"] = surf.convert_alpha()
    return SPRITE_CACHE["car"]

def create_monkey_sprite():
    if "monkey" in SPRITE_CACHE:
        return SPRITE_CACHE["monkey"]

    surf = pygame.Surface((45, 45), pygame.SRCALPHA)

    # Corps
    pygame.draw.circle(surf, BROWN, (22, 20), 16)

    # Oreilles
    pygame.draw.circle(surf, (160, 82, 45), (10, 14), 6)
    pygame.draw.circle(surf, (160, 82, 45), (34, 14), 6)

    # Visage
    pygame.draw.ellipse(surf, (210, 180, 140), (13, 18, 18, 16))

    # Yeux
    pygame.draw.circle(surf, WHITE, (18, 21), 3)
    pygame.draw.circle(surf, WHITE, (26, 21), 3)
    pygame.draw.circle(surf, BLACK, (18, 21), 2)
    pygame.draw.circle(surf, BLACK, (26, 21), 2)

    # Bouche
    pygame.draw.arc(surf, BLACK, (16, 26, 14, 8), 0, math.pi, 2)

    # Queue
    pygame.draw.line(surf, BROWN, (32, 32), (40, 42), 5)

    SPRITE_CACHE["monkey"] = surf.convert_alpha()
    return SPRITE_CACHE["monkey"]

def create_spaceship_sprite():
    if "spaceship" in SPRITE_CACHE:
        return SPRITE_CACHE["spaceship"]

    surf = pygame.Surface((50, 60), pygame.SRCALPHA)

    # Corps
    points = [(25, 5), (38, 40), (25, 35), (12, 40)]
    pygame.draw.polygon(surf, PURPLE, points)
    pygame.draw.polygon(surf, (100, 30, 150), points, 2)

    # Ailerons
    pygame.draw.polygon(surf, (120, 40, 180), [(12, 40), (5, 52), (12, 45)])
    pygame.draw.polygon(surf, (120, 40, 180), [(38, 40), (45, 52), (38, 45)])

    # Cockpit
    pygame.draw.ellipse(surf, (150, 200, 255), (18, 12, 14, 12))
    pygame.draw.ellipse(surf, WHITE, (20, 14, 10, 8))

    # Canons lasers
    pygame.draw.rect(surf, (200, 200, 220), (15, 35, 4, 8))
    pygame.draw.rect(surf, (200, 200, 220), (31, 35, 4, 8))

    SPRITE_CACHE["spaceship"] = surf.convert_alpha()
    return SPRITE_CACHE["spaceship"]

def create_laser_sprite():
    if "laser" in SPRITE_CACHE:
        return SPRITE_CACHE["laser"]

    surf = pygame.Surface((6, 20), pygame.SRCALPHA)
    pygame.draw.rect(surf, CYAN, (0, 0, 6, 20))
    pygame.draw.rect(surf, WHITE, (1, 0, 4, 20))

    SPRITE_CACHE["laser"] = surf.convert_alpha()
    return SPRITE_CACHE["laser"]

def create_debris_sprite(debris_type):
    key = f"debris_{debris_type}"
    if key in SPRITE_CACHE:
        return SPRITE_CACHE[key]

    if debris_type == "small":
        surf = pygame.Surface((25, 25), pygame.SRCALPHA)
        points = [(12, 2), (20, 8), (18, 18), (8, 20), (4, 10)]
        pygame.draw.polygon(surf, (120, 120, 130), points)
        pygame.draw.polygon(surf, (80, 80, 90), points, 2)
    elif debris_type == "medium":
        surf = pygame.Surface((35, 35), pygame.SRCALPHA)
        pygame.draw.rect(surf, (100, 100, 120), (5, 5, 25, 25))
        pygame.draw.line(surf, (150, 150, 170), (5, 5), (30, 30), 2)
        pygame.draw.line(surf, (150, 150, 170), (30, 5), (5, 30), 2)
    else:  # large
        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.circle(surf, (90, 90, 110), (25, 25), 22)
        pygame.draw.circle(surf, (60, 60, 80), (25, 25), 18)
        for i in range(4):
            angle = i * math.pi / 2
            x = 25 + 15 * math.cos(angle)
            y = 25 + 15 * math.sin(angle)
            pygame.draw.circle(surf, (70, 70, 90), (int(x), int(y)), 5)

    SPRITE_CACHE[key] = surf.convert_alpha()
    return SPRITE_CACHE[key]

# Particules
class Particle:
    def __init__(self, x, y, vx, vy, color, size, lifetime=None):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.age = 0

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.lifetime:
            self.age += dt

    def is_dead(self):
        return self.lifetime and self.age >= self.lifetime

    def draw(self, screen):
        if self.lifetime:
            alpha = int(255 * max(0, 1 - self.age / self.lifetime))
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color[:3], alpha), (self.size, self.size), self.size)
            screen.blit(s, (int(self.x - self.size), int(self.y - self.size)))
        else:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

class GameState(Enum):
    MENU = 1
    INSTRUCTIONS = 2
    SETTINGS = 3
    BOAT_GAME = 4
    JUNGLE_GAME = 5
    SPACE_GAME = 6
    GAME_OVER = 7

# Transition
class Transition:
    def __init__(self, duration=0.3):
        self.duration = duration
        self.timer = 0
        self.fading_out = False
        self.next_state = None

    def start_fade_out(self, next_state):
        self.fading_out = True
        self.next_state = next_state
        self.timer = 0

    def update(self, dt):
        if self.fading_out:
            self.timer += dt
            if self.timer >= self.duration:
                return self.next_state
        else:
            self.timer = min(self.timer + dt, self.duration)
        return None

    def get_alpha(self):
        if self.fading_out:
            return int(255 * (self.timer / self.duration))
        else:
            return int(255 * (1 - self.timer / self.duration))

    def draw(self, screen):
        alpha = self.get_alpha()
        if alpha > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, alpha))
            screen.blit(overlay, (0, 0))

# États
class MenuState:
    def __init__(self, game):
        self.game = game
        self.selected = 0
        self.options = ["Océan", "Jungle", "Espace", "Instructions", "Paramètres"]
        self.descriptions = [
            "Pêche des déchets avec un grappin",
            "Ramasse les déchets sur la route",
            "Détruis les débris spatiaux au laser",
            "Comment jouer",
            "Options du jeu"
        ]
        self.font_title = pygame.font.Font(None, 90)
        self.font_menu = pygame.font.Font(None, 40)
        self.font_help = pygame.font.Font(None, 22)
        self.mouse_hover = -1
        self.particles = []
        self.particle_timer = 0
        self.background = create_gradient(SCREEN_WIDTH, SCREEN_HEIGHT, (40, 160, 100), (20, 100, 60))

        self.button_rects = []
        button_width = 320
        button_height = 55
        start_y = 200
        for i in range(len(self.options)):
            rect = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, start_y + i * 70, button_width, button_height)
            self.button_rects.append(rect)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_DOWN, pygame.K_s]:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in [pygame.K_UP, pygame.K_w]:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self.launch_option(self.selected)
            elif event.key == pygame.K_ESCAPE:
                self.game.running = False
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_hover = -1
            for i, rect in enumerate(self.button_rects):
                if rect.collidepoint(event.pos):
                    self.mouse_hover = i
                    self.selected = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.mouse_hover != -1:
                self.launch_option(self.mouse_hover)

    def launch_option(self, index):
        if index == 0:
            self.game.transition.start_fade_out(GameState.BOAT_GAME)
        elif index == 1:
            self.game.transition.start_fade_out(GameState.JUNGLE_GAME)
        elif index == 2:
            self.game.transition.start_fade_out(GameState.SPACE_GAME)
        elif index == 3:
            self.game.transition.start_fade_out(GameState.INSTRUCTIONS)
        elif index == 4:
            self.game.transition.start_fade_out(GameState.SETTINGS)

    def update(self, dt):
        intensity = {"low": 0.5, "med": 0.3, "high": 0.15}
        spawn_rate = intensity.get(GAME_DATA["settings"]["particle_intensity"], 0.3)

        self.particle_timer += dt
        if self.particle_timer > spawn_rate:
            x = random.randint(0, SCREEN_WIDTH)
            y = -10
            vx = random.uniform(-15, 15)
            vy = random.uniform(25, 45)
            color = random.choice([(100, 200, 100), (80, 180, 80), (120, 220, 120)])
            self.particles.append(Particle(x, y, vx, vy, color, 4))
            self.particle_timer = 0

        for p in self.particles[:]:
            p.update(dt)
            if p.y > SCREEN_HEIGHT + 20:
                self.particles.remove(p)

    def draw(self, screen):
        screen.blit(self.background, (0, 0))

        for p in self.particles:
            p.draw(screen)

        # Titre avec glow
        title_text = "Eco Arcade"
        for offset in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
            shadow = self.font_title.render(title_text, True, (0, 0, 0, 100))
            screen.blit(shadow, (SCREEN_WIDTH//2 - shadow.get_width()//2 + offset[0], 70 + offset[1]))
        title = self.font_title.render(title_text, True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 70))

        subtitle = self.font_help.render("Version 2.0", True, YELLOW)
        screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 135))

        # Boutons
        for i, (option, rect) in enumerate(zip(self.options, self.button_rects)):
            is_selected = i == self.selected
            draw_rect = rect.copy()
            if is_selected:
                draw_rect.inflate_ip(8, 4)

            # Ombre
            shadow_rect = draw_rect.copy()
            shadow_rect.y += 3
            shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            draw_rounded_rect(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect(), radius=12)
            screen.blit(shadow_surf, shadow_rect)

            # Bouton
            color = (60, 200, 130) if is_selected else (45, 160, 100)
            border_color = YELLOW if is_selected else WHITE

            button_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
            draw_rounded_rect(button_surf, color, button_surf.get_rect(), radius=12, border=3, border_color=border_color)

            # Glow si sélectionné
            if is_selected:
                glow_surf = pygame.Surface((draw_rect.width + 10, draw_rect.height + 10), pygame.SRCALPHA)
                draw_rounded_rect(glow_surf, (255, 255, 0, 30), glow_surf.get_rect(), radius=15)
                screen.blit(glow_surf, (draw_rect.x - 5, draw_rect.y - 5))

            screen.blit(button_surf, draw_rect)

            text = self.font_menu.render(option, True, WHITE)
            screen.blit(text, text.get_rect(center=draw_rect.center))

        # Description
        desc_box = pygame.Rect(20, 520, 760, 65)
        desc_surf = pygame.Surface((desc_box.width, desc_box.height), pygame.SRCALPHA)
        draw_rounded_rect(desc_surf, (255, 255, 255, 200), desc_surf.get_rect(), radius=8)
        screen.blit(desc_surf, desc_box)

        desc_text = self.font_help.render(self.descriptions[self.selected], True, BLACK)
        screen.blit(desc_text, (desc_box.x + 10, desc_box.y + 10))

        controls = self.font_help.render("↑↓: Navigation | Entrée: Sélection | ESC: Quitter", True, WHITE)
        screen.blit(controls, (desc_box.x + 10, desc_box.y + 38))

class InstructionsState:
    def __init__(self, game):
        self.game = game
        self.font_title = pygame.font.Font(None, 54)
        self.font_text = pygame.font.Font(None, 24)
        self.background = create_gradient(SCREEN_WIDTH, SCREEN_HEIGHT, (20, 50, 100), (10, 30, 60))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.transition.start_fade_out(GameState.MENU)

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.blit(self.background, (0, 0))

        panel = pygame.Surface((720, 540), pygame.SRCALPHA)
        draw_rounded_rect(panel, (255, 255, 255, 240), panel.get_rect(), radius=15)
        screen.blit(panel, (40, 30))

        title = self.font_title.render("Instructions", True, DARK_BLUE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 45))

        instructions = [
            ("OCÉAN - Grappin", True),
            ("• WASD/Flèches: Déplacer le bateau", False),
            ("• SPACE: Lancer/descendre le grappin", False),
            ("• Le grappin attrape les déchets sous l'eau", False),
            ("• Évite les poissons (pénalité si touchés)", False),
            ("", False),
            ("JUNGLE - Voiture", True),
            ("• A/D ou ←→: Déplacer la voiture", False),
            ("• Le bac avant collecte les déchets", False),
            ("• Évite les singes (3 vies)", False),
            ("", False),
            ("ESPACE - Laser", True),
            ("• A/D ou ←→: Déplacer le vaisseau", False),
            ("• SPACE: Tirer des lasers", False),
            ("• Détruis les débris avant collision", False),
            ("• Petits=1HP, Moyens=2HP, Gros=3HP", False),
            ("", False),
            ("ESC: Retour menu | P: Pause", False)
        ]

        y = 100
        for line, is_title in instructions:
            if is_title:
                text = pygame.font.Font(None, 30).render(line, True, DARK_BLUE)
            else:
                text = self.font_text.render(line, True, BLACK)
            screen.blit(text, (70, y))
            y += 28

        back = self.font_text.render("Appuie sur ESC pour revenir", True, RED)
        screen.blit(back, (SCREEN_WIDTH//2 - back.get_width()//2, 560))

class SettingsState:
    def __init__(self, game):
        self.game = game
        self.font_title = pygame.font.Font(None, 54)
        self.font_text = pygame.font.Font(None, 28)
        self.background = create_gradient(SCREEN_WIDTH, SCREEN_HEIGHT, (40, 40, 50), (20, 20, 30))
        self.selected = 0
        self.options = ["particle_intensity", "color_mode"]
        self.values = {
            "particle_intensity": ["low", "med", "high"],
            "color_mode": ["normal", "deuteranopia"]
        }

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                save_data(GAME_DATA)
                self.game.transition.start_fade_out(GameState.MENU)
            elif event.key in [pygame.K_UP, pygame.K_w]:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d]:
                option = self.options[self.selected]
                current = GAME_DATA["settings"][option]
                values = self.values[option]
                idx = values.index(current)
                if event.key in [pygame.K_RIGHT, pygame.K_d]:
                    idx = (idx + 1) % len(values)
                else:
                    idx = (idx - 1) % len(values)
                GAME_DATA["settings"][option] = values[idx]

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.blit(self.background, (0, 0))

        panel = pygame.Surface((600, 400), pygame.SRCALPHA)
        draw_rounded_rect(panel, (255, 255, 255, 230), panel.get_rect(), radius=15)
        screen.blit(panel, (100, 100))

        title = self.font_title.render("Paramètres", True, DARK_BLUE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 120))

        y = 200
        labels = {"particle_intensity": "Particules", "color_mode": "Couleurs"}

        for i, option in enumerate(self.options):
            color = DARK_BLUE if i == self.selected else GRAY
            label = self.font_text.render(labels[option], True, color)
            screen.blit(label, (150, y))

            current = GAME_DATA["settings"][option]
            value_text = self.font_text.render(f"< {current} >", True, color)
            screen.blit(value_text, (450, y))

            y += 60

        help_text = self.font_text.render("←→: Changer | ESC: Retour", True, BLACK)
        screen.blit(help_text, (SCREEN_WIDTH//2 - help_text.get_width()//2, 450))

class BoatGameState:
    def __init__(self, game):
        self.game = game
        self.boat_x = SCREEN_WIDTH // 2 - 35
        self.boat_y = 80
        self.boat_vx = 0
        self.boat_speed = 180
        self.boat_sprite = create_boat_sprite()

        # Grappin
        self.grapple_active = False
        self.grapple_y = 0
        self.grapple_descending = True
        self.grapple_speed = 150
        self.grapple_max_depth = 400
        self.grapple_sprite = create_grapple_sprite()
        self.caught_trash = None

        self.trash_list = []
        self.fish_list = []
        self.trash_collected = 0
        self.fish_impacted = 0
        self.lives = 3
        self.timer = 70.0
        self.spawn_timer = 0
        self.paused = False
        self.game_over = False

        self.font = pygame.font.Font(None, 26)
        self.font_big = pygame.font.Font(None, 42)

        self.background_water = create_gradient(SCREEN_WIDTH, SCREEN_HEIGHT,
                                                (50, 150, 255), (20, 80, 180))

        # Spawn initial
        for _ in range(6):
            trash_type = random.choice(["bottle", "can", "bag", "tire", "box"])
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(200, SCREEN_HEIGHT - 50)
            self.trash_list.append({
                "x": x, "y": y, "type": trash_type, "sprite": create_trash_sprite(trash_type),
                "vx": random.uniform(-15, 15), "vy": random.uniform(-10, 10),
                "time": 0, "rotation": 0, "rotation_speed": random.uniform(-20, 20)
            })

        for _ in range(10):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(200, SCREEN_HEIGHT - 50)
            direction = random.choice([-1, 1])
            self.fish_list.append({
                "x": x, "y": y, "vx": direction * 40, "vy": random.uniform(-20, 20),
                "sprite": create_fish_sprite(direction), "time": 0
            })

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.transition.start_fade_out(GameState.MENU)
            elif event.key == pygame.K_p:
                self.paused = not self.paused
            elif event.key == pygame.K_SPACE and not self.grapple_active:
                self.grapple_active = True
                self.grapple_y = self.boat_y + 70
                self.grapple_descending = True
                self.caught_trash = None

    def update(self, dt):
        if self.paused or self.game_over:
            return

        self.timer -= dt
        if self.timer <= 0 or self.lives <= 0:
            self.game_over = True
            if self.trash_collected > GAME_DATA["ocean_best"]:
                GAME_DATA["ocean_best"] = self.trash_collected
                save_data(GAME_DATA)
            return

        # Déplacement bateau
        keys = pygame.key.get_pressed()
        target_vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            target_vx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            target_vx = 1

        # Inertie
        self.boat_vx += (target_vx - self.boat_vx) * 5 * dt
        self.boat_x += self.boat_vx * self.boat_speed * dt
        self.boat_x = max(0, min(SCREEN_WIDTH - 70, self.boat_x))

        # Grappin
        if self.grapple_active:
            grapple_x = self.boat_x + 35

            if self.grapple_descending:
                self.grapple_y += self.grapple_speed * dt

                # Check collision avec déchets
                if not self.caught_trash:
                    for trash in self.trash_list:
                        dist = math.sqrt((grapple_x - trash["x"])**2 + (self.grapple_y - trash["y"])**2)
                        if dist < 20:
                            self.caught_trash = trash
                            self.grapple_descending = False
                            break

                # Check collision avec poissons
                for fish in self.fish_list:
                    dist = math.sqrt((grapple_x - fish["x"])**2 + (self.grapple_y - fish["y"])**2)
                    if dist < 20:
                        self.lives -= 1
                        self.grapple_descending = False
                        break

                if self.grapple_y >= self.boat_y + self.grapple_max_depth:
                    self.grapple_descending = False
            else:
                # Remontée
                self.grapple_y -= self.grapple_speed * dt
                if self.caught_trash:
                    self.caught_trash["x"] = grapple_x
                    self.caught_trash["y"] = self.grapple_y + 15

                if self.grapple_y <= self.boat_y + 70:
                    self.grapple_active = False
                    if self.caught_trash:
                        self.trash_collected += 1
                        self.trash_list.remove(self.caught_trash)
                        self.caught_trash = None

        # Update trash
        for trash in self.trash_list:
            if trash != self.caught_trash:
                trash["x"] += trash["vx"] * dt
                trash["y"] += trash["vy"] * dt
                trash["time"] += dt
                trash["rotation"] += trash["rotation_speed"] * dt

                if trash["x"] < 0 or trash["x"] > SCREEN_WIDTH:
                    trash["vx"] *= -1
                if trash["y"] < 150 or trash["y"] > SCREEN_HEIGHT:
                    trash["vy"] *= -1

                trash["x"] = max(0, min(SCREEN_WIDTH, trash["x"]))
                trash["y"] = max(150, min(SCREEN_HEIGHT, trash["y"]))

                # Collision trash-poisson
                for fish in self.fish_list:
                    dist = math.sqrt((trash["x"] - fish["x"])**2 + (trash["y"] - fish["y"])**2)
                    if dist < 25:
                        self.fish_impacted += 1
                        if trash in self.trash_list:
                            self.trash_list.remove(trash)
                        break

        # Update poissons
        for fish in self.fish_list:
            fish["x"] += fish["vx"] * dt
            fish["y"] += fish["vy"] * dt
            fish["time"] += dt

            if fish["x"] < 0 or fish["x"] > SCREEN_WIDTH:
                fish["vx"] *= -1
                fish["sprite"] = create_fish_sprite(1 if fish["vx"] > 0 else -1)
            if fish["y"] < 150 or fish["y"] > SCREEN_HEIGHT:
                fish["vy"] *= -1

            fish["x"] = max(0, min(SCREEN_WIDTH, fish["x"]))
            fish["y"] = max(150, min(SCREEN_HEIGHT, fish["y"]))

        # Spawn
        self.spawn_timer += dt
        if self.spawn_timer > 2.5 and len(self.trash_list) < 8:
            trash_type = random.choice(["bottle", "can", "bag", "tire", "box"])
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(200, 350)
            self.trash_list.append({
                "x": x, "y": y, "type": trash_type, "sprite": create_trash_sprite(trash_type),
                "vx": random.uniform(-15, 15), "vy": random.uniform(-10, 10),
                "time": 0, "rotation": 0, "rotation_speed": random.uniform(-20, 20)
            })
            self.spawn_timer = 0

    def draw(self, screen):
        screen.blit(self.background_water, (0, 0))

        # Vagues animées
        wave_time = pygame.time.get_ticks() / 400
        for i in range(0, SCREEN_HEIGHT, 25):
            offset = int(math.sin(wave_time + i / 15) * 8)
            pygame.draw.line(screen, (30, 120, 220), (offset, i), (SCREEN_WIDTH + offset, i), 1)

        # Ligne surface eau
        pygame.draw.line(screen, (100, 200, 255), (0, 150), (SCREEN_WIDTH, 150), 3)

        # Zone sous l'eau (teinte plus sombre)
        underwater = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - 150), pygame.SRCALPHA)
        underwater.fill((0, 0, 50, 30))
        screen.blit(underwater, (0, 150))

        # Poissons
        for fish in self.fish_list:
            y_bob = math.sin(fish["time"] * 2) * 2
            screen.blit(fish["sprite"], (int(fish["x"] - 20), int(fish["y"] - 14 + y_bob)))

        # Déchets
        for trash in self.trash_list:
            y_bob = math.sin(trash["time"] * 1.5) * 3
            rotated = pygame.transform.rotate(trash["sprite"], trash["rotation"])
            rect = rotated.get_rect(center=(int(trash["x"]), int(trash["y"] + y_bob)))
            screen.blit(rotated, rect)

        # Câble grappin
        if self.grapple_active:
            grapple_x = self.boat_x + 35
            pygame.draw.line(screen, (80, 80, 80), (grapple_x, self.boat_y + 70),
                           (grapple_x, self.grapple_y), 3)
            screen.blit(self.grapple_sprite, (grapple_x - 15, self.grapple_y - 15))

        # Bateau
        screen.blit(self.boat_sprite, (int(self.boat_x), self.boat_y))

        # Reflet bateau
        reflect = pygame.transform.flip(self.boat_sprite, False, True)
        reflect.set_alpha(60)
        screen.blit(reflect, (int(self.boat_x), 150))

        # UI
        panel = pygame.Surface((SCREEN_WIDTH, 75), pygame.SRCALPHA)
        draw_rounded_rect(panel, (255, 255, 255, 220), panel.get_rect(), radius=0)
        screen.blit(panel, (0, 0))

        info1 = self.font.render(f"🗑️ Déchets: {self.trash_collected}", True, DARK_BLUE)
        screen.blit(info1, (15, 12))

        fish_color = RED if self.fish_impacted >= 5 else DARK_BLUE
        info2 = self.font.render(f"🐟 Impacts: {self.fish_impacted}", True, fish_color)
        screen.blit(info2, (15, 38))

        timer_color = RED if self.timer < 15 else DARK_BLUE
        timer_text = self.font.render(f"⏱️ {int(self.timer)}s", True, timer_color)
        screen.blit(timer_text, (SCREEN_WIDTH - 130, 12))

        lives_text = self.font.render(f"❤️ x{self.lives}", True, RED)
        screen.blit(lives_text, (SCREEN_WIDTH - 130, 38))

        hint = self.font.render("SPACE: Lancer grappin", True, YELLOW)
        screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 85))

        if self.paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            pause = self.font_big.render("PAUSE", True, WHITE)
            screen.blit(pause, (SCREEN_WIDTH//2 - pause.get_width()//2, SCREEN_HEIGHT//2))

        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            result = self.font_big.render(f"Score: {self.trash_collected}", True, YELLOW)
            screen.blit(result, (SCREEN_WIDTH//2 - result.get_width()//2, SCREEN_HEIGHT//2 - 40))

            best = self.font.render(f"Meilleur: {GAME_DATA['ocean_best']}", True, WHITE)
            screen.blit(best, (SCREEN_WIDTH//2 - best.get_width()//2, SCREEN_HEIGHT//2 + 10))

            esc = self.font.render("ESC: Menu", True, WHITE)
            screen.blit(esc, (SCREEN_WIDTH//2 - esc.get_width()//2, SCREEN_HEIGHT//2 + 50))

class JungleGameState:
    def __init__(self, game):
        self.game = game
        self.car_x = SCREEN_WIDTH // 2 - 45
        self.car_y = SCREEN_HEIGHT - 140
        self.car_speed = 220
        self.car_sprite = create_car_sprite()

        self.trash_list = []
        self.monkeys = []
        self.score = 0
        self.lives = 3
        self.timer = 70.0
        self.spawn_timer = 0
        self.difficulty = 0
        self.base_speed = 120
        self.road_offset = 0
        self.paused = False
        self.game_over = False
        self.invincible_timer = 0

        self.font = pygame.font.Font(None, 26)
        self.font_big = pygame.font.Font(None, 42)

        # Spawn initial
        for _ in range(3):
            trash_type = random.choice(["bottle", "can", "bag", "tire", "box"])
            x = random.randint(250, SCREEN_WIDTH - 250)
            y = random.randint(-150, -50)
            self.trash_list.append({
                "x": x, "y": y, "type": trash_type, "sprite": create_trash_sprite(trash_type, 28),
                "rotation": 0, "rotation_speed": random.uniform(-30, 30)
            })

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.transition.start_fade_out(GameState.MENU)
            elif event.key == pygame.K_p:
                self.paused = not self.paused

    def update(self, dt):
        if self.paused or self.game_over:
            return

        self.timer -= dt
        self.difficulty += dt * 0.8

        if self.timer <= 0 or self.lives <= 0:
            self.game_over = True
            if self.score > GAME_DATA["jungle_best"]:
                GAME_DATA["jungle_best"] = self.score
                save_data(GAME_DATA)
            return

        current_speed = self.base_speed + self.difficulty * 3

        if self.invincible_timer > 0:
            self.invincible_timer -= dt

        # Déplacement voiture
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.car_x -= self.car_speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.car_x += self.car_speed * dt

        self.car_x = max(200, min(SCREEN_WIDTH - 290, self.car_x))

        # Animation route
        self.road_offset += current_speed * dt
        if self.road_offset > 40:
            self.road_offset -= 40

        # Hitbox bac (avant de la voiture)
        bac_rect = pygame.Rect(self.car_x + 15, self.car_y + 8, 60, 20)

        # Update déchets
        for trash in self.trash_list[:]:
            trash["y"] += current_speed * dt
            trash["rotation"] += trash["rotation_speed"] * dt

            trash_rect = pygame.Rect(trash["x"] - 15, trash["y"] - 15, 30, 30)
            if bac_rect.colliderect(trash_rect):
                self.score += 1
                self.trash_list.remove(trash)
            elif trash["y"] > SCREEN_HEIGHT:
                self.trash_list.remove(trash)

        # Update singes
        car_rect = pygame.Rect(self.car_x + 12, self.car_y + 30, 66, 80)
        for monkey in self.monkeys[:]:
            monkey["y"] += current_speed * dt

            monkey_rect = pygame.Rect(monkey["x"] - 22, monkey["y"] - 22, 45, 45)
            if self.invincible_timer <= 0 and car_rect.colliderect(monkey_rect):
                self.lives -= 1
                self.invincible_timer = 1.5
                self.monkeys.remove(monkey)
            elif monkey["y"] > SCREEN_HEIGHT + 50:
                self.monkeys.remove(monkey)

        # Spawn
        self.spawn_timer += dt
        if self.spawn_timer > 1.2:
            if random.random() < 0.65:
                trash_type = random.choice(["bottle", "can", "bag", "tire", "box"])
                x = random.randint(250, SCREEN_WIDTH - 250)
                self.trash_list.append({
                    "x": x, "y": -30, "type": trash_type,
                    "sprite": create_trash_sprite(trash_type, 28),
                    "rotation": 0, "rotation_speed": random.uniform(-30, 30)
                })

            if random.random() < 0.35 + self.difficulty * 0.008:
                x = random.randint(250, SCREEN_WIDTH - 250)
                self.monkeys.append({"x": x, "y": -30, "sprite": create_monkey_sprite()})

            self.spawn_timer = 0

    def draw(self, screen):
        screen.fill(DARK_GREEN)

        # Forêt
        for x in range(0, SCREEN_WIDTH, 70):
            if x < 180 or x > SCREEN_WIDTH - 180:
                pygame.draw.circle(screen, (25, 70, 25), (x, random.randint(100, 500)), 35)

        # Route
        road_width = 420
        road_x = SCREEN_WIDTH // 2 - road_width // 2
        pygame.draw.rect(screen, (50, 50, 50), (road_x, 0, road_width, SCREEN_HEIGHT))

        # Lignes blanches
        for y in range(int(-self.road_offset), SCREEN_HEIGHT, 40):
            pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH//2 - 6, y, 12, 22))

        # Bords route
        pygame.draw.line(screen, WHITE, (road_x, 0), (road_x, SCREEN_HEIGHT), 4)
        pygame.draw.line(screen, WHITE, (road_x + road_width, 0), (road_x + road_width, SCREEN_HEIGHT), 4)

        # Déchets
        for trash in self.trash_list:
            rotated = pygame.transform.rotate(trash["sprite"], trash["rotation"])
            rect = rotated.get_rect(center=(int(trash["x"]), int(trash["y"])))
            screen.blit(rotated, rect)

        # Singes
        for monkey in self.monkeys:
            screen.blit(monkey["sprite"], (int(monkey["x"] - 22), int(monkey["y"] - 22)))

        # Voiture (clignotement si invincible)
        if self.invincible_timer <= 0 or int(self.invincible_timer * 10) % 2 == 0:
            screen.blit(self.car_sprite, (int(self.car_x), int(self.car_y)))

        # UI
        panel = pygame.Surface((SCREEN_WIDTH, 70), pygame.SRCALPHA)
        draw_rounded_rect(panel, (255, 255, 255, 220), panel.get_rect(), radius=0)
        screen.blit(panel, (0, 0))

        score_text = self.font.render(f"Score: {self.score}", True, DARK_GREEN)
        screen.blit(score_text, (15, 12))

        lives_text = self.font.render(f"❤️ x{self.lives}", True, RED)
        screen.blit(lives_text, (15, 40))

        timer_text = self.font.render(f"⏱️ {int(self.timer)}s", True, DARK_GREEN)
        screen.blit(timer_text, (SCREEN_WIDTH - 130, 12))

        hint = self.font.render("Ramasse avec le BAC !", True, YELLOW)
        screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 75))

        if self.paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            pause = self.font_big.render("PAUSE", True, WHITE)
            screen.blit(pause, (SCREEN_WIDTH//2 - pause.get_width()//2, SCREEN_HEIGHT//2))

        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            result = self.font_big.render(f"Score: {self.score}", True, YELLOW)
            screen.blit(result, (SCREEN_WIDTH//2 - result.get_width()//2, SCREEN_HEIGHT//2 - 40))

            best = self.font.render(f"Meilleur: {GAME_DATA['jungle_best']}", True, WHITE)
            screen.blit(best, (SCREEN_WIDTH//2 - best.get_width()//2, SCREEN_HEIGHT//2 + 10))

            esc = self.font.render("ESC: Menu", True, WHITE)
            screen.blit(esc, (SCREEN_WIDTH//2 - esc.get_width()//2, SCREEN_HEIGHT//2 + 50))

class SpaceGameState:
    def __init__(self, game):
        self.game = game
        self.ship_x = SCREEN_WIDTH // 2 - 25
        self.ship_y = SCREEN_HEIGHT - 100
        self.ship_speed = 250
        self.ship_sprite = create_spaceship_sprite()

        self.lasers = []
        self.laser_cooldown = 0
        self.laser_max_cooldown = 0.25
        self.laser_sprite = create_laser_sprite()

        self.debris_list = []
        self.particles = []
        self.score = 0
        self.combo = 0
        self.lives = 3
        self.timer = 60.0
        self.spawn_timer = 0
        self.difficulty = 0
        self.paused = False
        self.game_over = False

        self.font = pygame.font.Font(None, 26)
        self.font_big = pygame.font.Font(None, 42)

        self.stars = [(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT),
                      random.randint(1, 3), random.uniform(30, 80)) for _ in range(200)]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.transition.start_fade_out(GameState.MENU)
            elif event.key == pygame.K_p:
                self.paused = not self.paused

    def update(self, dt):
        if self.paused or self.game_over:
            return

        self.timer -= dt
        self.difficulty += dt * 1.5

        if self.timer <= 0 or self.lives <= 0:
            self.game_over = True
            if self.score > GAME_DATA["space_best"]:
                GAME_DATA["space_best"] = self.score
                save_data(GAME_DATA)
            return

        # Déplacement vaisseau
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.ship_x -= self.ship_speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.ship_x += self.ship_speed * dt

        self.ship_x = max(0, min(SCREEN_WIDTH - 50, self.ship_x))

        # Tir laser
        self.laser_cooldown -= dt
        if keys[pygame.K_SPACE] and self.laser_cooldown <= 0:
            self.lasers.append({"x": self.ship_x + 17, "y": self.ship_y})
            self.lasers.append({"x": self.ship_x + 33, "y": self.ship_y})
            self.laser_cooldown = self.laser_max_cooldown

        # Étoiles défilantes
        for star in self.stars:
            star[1] += star[3] * dt
            if star[1] > SCREEN_HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, SCREEN_WIDTH)

        # Update lasers
        for laser in self.lasers[:]:
            laser["y"] -= 400 * dt
            if laser["y"] < -20:
                self.lasers.remove(laser)

        # Update debris
        ship_rect = pygame.Rect(self.ship_x + 5, self.ship_y + 5, 40, 50)

        for debris in self.debris_list[:]:
            debris["y"] += debris["speed"] * dt

            debris_rect = pygame.Rect(debris["x"] - debris["size"]//2, debris["y"] - debris["size"]//2,
                                     debris["size"], debris["size"])

            # Collision laser-debris
            hit = False
            for laser in self.lasers[:]:
                laser_rect = pygame.Rect(laser["x"], laser["y"], 6, 20)
                if debris_rect.colliderect(laser_rect):
                    debris["hp"] -= 1
                    self.lasers.remove(laser)
                    hit = True

                    if debris["hp"] <= 0:
                        # Explosion
                        for _ in range(10):
                            vx = random.uniform(-80, 80)
                            vy = random.uniform(-80, 80)
                            self.particles.append(Particle(debris["x"], debris["y"], vx, vy,
                                                          ORANGE, 3, 0.5))

                        self.score += debris["points"]
                        self.combo += 1
                        self.debris_list.remove(debris)
                    break

            # Collision ship-debris
            if not hit and ship_rect.colliderect(debris_rect):
                self.lives -= 1
                self.combo = 0
                self.debris_list.remove(debris)
                # Explosion
                for _ in range(15):
                    vx = random.uniform(-100, 100)
                    vy = random.uniform(-100, 100)
                    self.particles.append(Particle(debris["x"], debris["y"], vx, vy,
                                                  RED, 4, 0.7))

            if debris["y"] > SCREEN_HEIGHT + 50:
                self.debris_list.remove(debris)

        # Update particules
        for p in self.particles[:]:
            p.update(dt)
            if p.is_dead():
                self.particles.remove(p)

        # Spawn debris
        self.spawn_timer += dt
        spawn_rate = max(0.5, 1.0 - self.difficulty * 0.02)

        if self.spawn_timer > spawn_rate:
            debris_type = random.choices(["small", "medium", "large"],
                                        weights=[0.5, 0.35, 0.15])[0]

            hp_map = {"small": 1, "medium": 2, "large": 3}
            points_map = {"small": 10, "medium": 25, "large": 50}
            size_map = {"small": 25, "medium": 35, "large": 50}
            speed_map = {"small": 100, "medium": 80, "large": 60}

            x = random.randint(30, SCREEN_WIDTH - 30)
            self.debris_list.append({
                "x": x, "y": -30, "type": debris_type,
                "sprite": create_debris_sprite(debris_type),
                "hp": hp_map[debris_type], "points": points_map[debris_type],
                "size": size_map[debris_type], "speed": speed_map[debris_type] + self.difficulty * 2,
                "rotation": 0, "rotation_speed": random.uniform(-100, 100)
            })
            self.spawn_timer = 0

    def draw(self, screen):
        screen.fill(BLACK)

        # Étoiles
        for star in self.stars:
            pygame.draw.circle(screen, WHITE, (int(star[0]), int(star[1])), star[2])

        # Particules
        for p in self.particles:
            p.draw(screen)

        # Debris
        for debris in self.debris_list:
            debris["rotation"] += debris["rotation_speed"] * 0.016
            rotated = pygame.transform.rotate(debris["sprite"], debris["rotation"])
            rect = rotated.get_rect(center=(int(debris["x"]), int(debris["y"])))
            screen.blit(rotated, rect)

            # HP bar
            if debris["hp"] > 1:
                bar_w = debris["size"]
                bar_x = debris["x"] - bar_w // 2
                bar_y = debris["y"] - debris["size"] // 2 - 8
                pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_w, 4))
                pygame.draw.rect(screen, GREEN, (bar_x, bar_y,
                                bar_w * debris["hp"] / (3 if debris["type"] == "large" else 2), 4))

        # Lasers
        for laser in self.lasers:
            screen.blit(self.laser_sprite, (laser["x"] - 3, laser["y"]))

        # Vaisseau
        screen.blit(self.ship_sprite, (int(self.ship_x), int(self.ship_y)))

        # UI
        panel = pygame.Surface((SCREEN_WIDTH, 70), pygame.SRCALPHA)
        draw_rounded_rect(panel, (50, 50, 50, 220), panel.get_rect(), radius=0)
        screen.blit(panel, (0, 0))

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (15, 12))

        if self.combo > 0:
            combo_text = self.font.render(f"Combo x{self.combo}!", True, YELLOW)
            screen.blit(combo_text, (15, 40))

        lives_text = self.font.render(f"❤️ x{self.lives}", True, RED)
        screen.blit(lives_text, (SCREEN_WIDTH - 130, 12))

        timer_text = self.font.render(f"⏱️ {int(self.timer)}s", True, WHITE)
        screen.blit(timer_text, (SCREEN_WIDTH - 130, 40))

        hint = self.font.render("SPACE: Tirer", True, CYAN)
        screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 75))

        if self.paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            pause = self.font_big.render("PAUSE", True, WHITE)
            screen.blit(pause, (SCREEN_WIDTH//2 - pause.get_width()//2, SCREEN_HEIGHT//2))

        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            result = self.font_big.render(f"Score: {self.score}", True, YELLOW)
            screen.blit(result, (SCREEN_WIDTH//2 - result.get_width()//2, SCREEN_HEIGHT//2 - 40))

            best = self.font.render(f"Meilleur: {GAME_DATA['space_best']}", True, WHITE)
            screen.blit(best, (SCREEN_WIDTH//2 - best.get_width()//2, SCREEN_HEIGHT//2 + 10))

            esc = self.font.render("ESC: Menu", True, WHITE)
            screen.blit(esc, (SCREEN_WIDTH//2 - esc.get_width()//2, SCREEN_HEIGHT//2 + 50))

# Gestionnaire
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Eco Arcade V2")
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_state = GameState.MENU
        self.transition = Transition()

        self.states = {
            GameState.MENU: MenuState(self),
            GameState.INSTRUCTIONS: InstructionsState(self),
            GameState.SETTINGS: SettingsState(self),
        }

    def change_state(self, new_state):
        self.current_state = new_state
        self.transition = Transition()

        if new_state == GameState.BOAT_GAME:
            self.states[GameState.BOAT_GAME] = BoatGameState(self)
        elif new_state == GameState.JUNGLE_GAME:
            self.states[GameState.JUNGLE_GAME] = JungleGameState(self)
        elif new_state == GameState.SPACE_GAME:
            self.states[GameState.SPACE_GAME] = SpaceGameState(self)
        elif new_state == GameState.MENU:
            self.states[GameState.MENU] = MenuState(self)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.states[self.current_state].handle_event(event)

            # Check transition
            next_state = self.transition.update(dt)
            if next_state:
                self.change_state(next_state)

            self.states[self.current_state].update(dt)
            self.states[self.current_state].draw(self.screen)
            self.transition.draw(self.screen)

            pygame.display.flip()

        pygame.quit()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
