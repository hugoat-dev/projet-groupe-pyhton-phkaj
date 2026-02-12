#!/usr/bin/env python3
"""
Eco Arcade - 3 mini-jeux écologiques avec Pygame (VERSION AMÉLIORÉE)
Contrôles: Flèches/WASD pour bouger, ESC pour menu, P pour pause, I pour instructions
"""

import pygame
import random
import math
from enum import Enum

# Initialisation Pygame
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
LIGHT_GREEN = (144, 238, 144)

# Cache des sprites pour éviter de les recréer
SPRITE_CACHE = {}

# ===== UTILITAIRES DE DESSIN =====

def draw_rounded_rect(surface, color, rect, radius=10, border=0, border_color=None):
    """Dessine un rectangle avec coins arrondis"""
    rect = pygame.Rect(rect)
    color = color[:3] if len(color) > 3 else color

    # Rectangle principal (sans coins)
    pygame.draw.rect(surface, color, rect.inflate(-radius*2, 0))
    pygame.draw.rect(surface, color, rect.inflate(0, -radius*2))

    # Coins arrondis
    for pos in [(rect.left + radius, rect.top + radius),
                (rect.right - radius - 1, rect.top + radius),
                (rect.left + radius, rect.bottom - radius - 1),
                (rect.right - radius - 1, rect.bottom - radius - 1)]:
        pygame.draw.circle(surface, color, pos, radius)

    # Bordure optionnelle
    if border > 0 and border_color:
        # Lignes horizontales
        pygame.draw.line(surface, border_color, (rect.left + radius, rect.top),
                        (rect.right - radius, rect.top), border)
        pygame.draw.line(surface, border_color, (rect.left + radius, rect.bottom - 1),
                        (rect.right - radius, rect.bottom - 1), border)
        # Lignes verticales
        pygame.draw.line(surface, border_color, (rect.left, rect.top + radius),
                        (rect.left, rect.bottom - radius), border)
        pygame.draw.line(surface, border_color, (rect.right - 1, rect.top + radius),
                        (rect.right - 1, rect.bottom - radius), border)
        # Coins
        for pos in [(rect.left + radius, rect.top + radius),
                    (rect.right - radius - 1, rect.top + radius),
                    (rect.left + radius, rect.bottom - radius - 1),
                    (rect.right - radius - 1, rect.bottom - radius - 1)]:
            pygame.draw.circle(surface, border_color, pos, radius, border)

def create_gradient_surface(width, height, top_color, bottom_color):
    """Crée une surface avec dégradé vertical"""
    surface = pygame.Surface((width, height))
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
    return surface

# ===== SPRITES PROCÉDURAUX CACHÉS =====

def create_trash_sprite(trash_type):
    """Crée un sprite de déchet selon le type"""
    if trash_type in SPRITE_CACHE:
        return SPRITE_CACHE[trash_type]

    size = 25
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    if trash_type == "bottle":
        # Bouteille plastique
        pygame.draw.rect(surf, (100, 150, 200), (8, 5, 10, 15))
        pygame.draw.rect(surf, (80, 130, 180), (9, 3, 8, 3))
        pygame.draw.circle(surf, (150, 200, 255), (13, 8), 2)

    elif trash_type == "can":
        # Canette
        pygame.draw.ellipse(surf, (180, 180, 190), (6, 8, 14, 12))
        pygame.draw.rect(surf, (200, 200, 210), (7, 10, 12, 2))
        pygame.draw.rect(surf, (160, 160, 170), (7, 15, 12, 2))

    elif trash_type == "bag":
        # Sac plastique
        points = [(13, 6), (18, 10), (16, 18), (10, 18), (8, 10)]
        pygame.draw.polygon(surf, (220, 220, 230, 150), points)
        pygame.draw.polygon(surf, (180, 180, 190), points, 2)

    elif trash_type == "tire":
        # Pneu
        pygame.draw.circle(surf, (30, 30, 30), (13, 13), 10)
        pygame.draw.circle(surf, (50, 50, 50), (13, 13), 6)
        pygame.draw.circle(surf, (30, 30, 30), (13, 13), 3)

    else:  # box
        # Carton
        pygame.draw.rect(surf, (139, 90, 43), (5, 6, 16, 14))
        pygame.draw.line(surf, (100, 60, 20), (5, 6), (21, 6), 2)
        pygame.draw.line(surf, (100, 60, 20), (5, 6), (5, 20), 2)

    SPRITE_CACHE[trash_type] = surf.convert_alpha()
    return SPRITE_CACHE[trash_type]

def create_boat_sprite():
    """Crée un sprite de bateau détaillé"""
    if "boat" in SPRITE_CACHE:
        return SPRITE_CACHE["boat"]

    surf = pygame.Surface((50, 70), pygame.SRCALPHA)

    # Coque (forme de bateau)
    points = [(25, 5), (40, 30), (38, 55), (12, 55), (10, 30)]
    pygame.draw.polygon(surf, BLUE, points)
    pygame.draw.polygon(surf, DARK_BLUE, points, 3)

    # Cabine
    pygame.draw.rect(surf, WHITE, (18, 20, 14, 18))
    pygame.draw.rect(surf, DARK_BLUE, (18, 20, 14, 18), 2)

    # Fenêtres
    pygame.draw.rect(surf, LIGHT_BLUE, (20, 24, 4, 4))
    pygame.draw.rect(surf, LIGHT_BLUE, (26, 24, 4, 4))

    # Pont avant
    pygame.draw.rect(surf, (200, 200, 200), (20, 10, 10, 8))

    SPRITE_CACHE["boat"] = surf.convert_alpha()
    return SPRITE_CACHE["boat"]

def create_net_sprite():
    """Crée un sprite de filet de pêche"""
    if "net" in SPRITE_CACHE:
        return SPRITE_CACHE["net"]

    surf = pygame.Surface((70, 50), pygame.SRCALPHA)

    # Filet semi-transparent
    pygame.draw.ellipse(surf, (255, 200, 0, 80), (0, 0, 70, 50))

    # Maillage du filet
    for i in range(0, 70, 10):
        pygame.draw.line(surf, (200, 150, 0, 120), (i, 0), (i, 50), 1)
    for i in range(0, 50, 10):
        pygame.draw.line(surf, (200, 150, 0, 120), (0, i), (70, i), 1)

    # Contour
    pygame.draw.ellipse(surf, (255, 180, 0), (0, 0, 70, 50), 3)

    SPRITE_CACHE["net"] = surf.convert_alpha()
    return SPRITE_CACHE["net"]

def create_fish_sprite(direction=1):
    """Crée un sprite de poisson plus détaillé"""
    key = f"fish_{direction}"
    if key in SPRITE_CACHE:
        return SPRITE_CACHE[key]

    surf = pygame.Surface((35, 25), pygame.SRCALPHA)

    # Corps
    pygame.draw.ellipse(surf, ORANGE, (5, 5, 22, 15))
    pygame.draw.ellipse(surf, (255, 140, 0), (5, 5, 22, 15), 2)

    # Queue
    if direction > 0:
        tail_points = [(27, 12), (32, 7), (32, 17)]
        eye_pos = (20, 10)
    else:
        tail_points = [(8, 12), (3, 7), (3, 17)]
        eye_pos = (15, 10)

    pygame.draw.polygon(surf, ORANGE, tail_points)
    pygame.draw.polygon(surf, (255, 140, 0), tail_points, 2)

    # Œil
    pygame.draw.circle(surf, WHITE, eye_pos, 3)
    pygame.draw.circle(surf, BLACK, eye_pos, 2)

    # Nageoires
    if direction > 0:
        pygame.draw.ellipse(surf, (255, 140, 0), (12, 18, 8, 4))
    else:
        pygame.draw.ellipse(surf, (255, 140, 0), (15, 18, 8, 4))

    SPRITE_CACHE[key] = surf.convert_alpha()
    return SPRITE_CACHE[key]

def create_car_sprite():
    """Crée un sprite de voiture plus détaillé"""
    if "car" in SPRITE_CACHE:
        return SPRITE_CACHE["car"]

    surf = pygame.Surface((55, 75), pygame.SRCALPHA)

    # Carrosserie
    pygame.draw.rect(surf, GREEN, (8, 20, 40, 50), border_radius=8)
    pygame.draw.rect(surf, DARK_GREEN, (8, 20, 40, 50), 3, border_radius=8)

    # Pare-brise
    pygame.draw.rect(surf, LIGHT_BLUE, (12, 28, 32, 15))
    pygame.draw.rect(surf, BLACK, (12, 28, 32, 15), 2)

    # Capot
    pygame.draw.rect(surf, (40, 180, 40), (10, 50, 36, 15))

    # Roues
    pygame.draw.circle(surf, BLACK, (15, 25), 6)
    pygame.draw.circle(surf, DARK_GRAY, (15, 25), 4)
    pygame.draw.circle(surf, BLACK, (41, 25), 6)
    pygame.draw.circle(surf, DARK_GRAY, (41, 25), 4)
    pygame.draw.circle(surf, BLACK, (15, 65), 6)
    pygame.draw.circle(surf, DARK_GRAY, (15, 65), 4)
    pygame.draw.circle(surf, BLACK, (41, 65), 6)
    pygame.draw.circle(surf, DARK_GRAY, (41, 65), 4)

    # Phares
    pygame.draw.circle(surf, YELLOW, (18, 70), 3)
    pygame.draw.circle(surf, YELLOW, (38, 70), 3)

    SPRITE_CACHE["car"] = surf.convert_alpha()
    return SPRITE_CACHE["car"]

def create_monkey_sprite():
    """Crée un sprite de singe plus reconnaissable"""
    if "monkey" in SPRITE_CACHE:
        return SPRITE_CACHE["monkey"]

    surf = pygame.Surface((40, 40), pygame.SRCALPHA)

    # Tête
    pygame.draw.circle(surf, BROWN, (20, 18), 14)

    # Oreilles
    pygame.draw.circle(surf, (160, 82, 45), (10, 12), 5)
    pygame.draw.circle(surf, (160, 82, 45), (30, 12), 5)

    # Visage (couleur chair)
    pygame.draw.ellipse(surf, (210, 180, 140), (12, 16, 16, 14))

    # Yeux
    pygame.draw.circle(surf, WHITE, (16, 18), 3)
    pygame.draw.circle(surf, WHITE, (24, 18), 3)
    pygame.draw.circle(surf, BLACK, (16, 18), 2)
    pygame.draw.circle(surf, BLACK, (24, 18), 2)

    # Bouche
    pygame.draw.arc(surf, BLACK, (14, 22, 12, 6), 0, math.pi, 2)

    # Queue
    pygame.draw.line(surf, BROWN, (30, 28), (36, 36), 4)

    SPRITE_CACHE["monkey"] = surf.convert_alpha()
    return SPRITE_CACHE["monkey"]

def create_spaceship_sprite():
    """Crée un sprite de vaisseau spatial stylé"""
    if "spaceship" in SPRITE_CACHE:
        return SPRITE_CACHE["spaceship"]

    surf = pygame.Surface((40, 50), pygame.SRCALPHA)

    # Corps principal
    points = [(20, 5), (30, 35), (20, 30), (10, 35)]
    pygame.draw.polygon(surf, PURPLE, points)
    pygame.draw.polygon(surf, (100, 30, 150), points, 2)

    # Ailerons
    pygame.draw.polygon(surf, (120, 40, 180), [(10, 35), (5, 45), (10, 40)])
    pygame.draw.polygon(surf, (120, 40, 180), [(30, 35), (35, 45), (30, 40)])

    # Cockpit
    pygame.draw.ellipse(surf, (150, 200, 255), (14, 10, 12, 10))
    pygame.draw.ellipse(surf, WHITE, (16, 12, 8, 6))

    # Réacteur
    pygame.draw.rect(surf, (255, 100, 100), (16, 30, 8, 4))

    SPRITE_CACHE["spaceship"] = surf.convert_alpha()
    return SPRITE_CACHE["spaceship"]

# ===== CLASSES DE BASE =====

class Particle:
    """Particule pour animations de fond"""
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
            alpha = int(255 * (1 - self.age / self.lifetime))
            color = (*self.color[:3], alpha)
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (self.size, self.size), self.size)
            screen.blit(s, (int(self.x - self.size), int(self.y - self.size)))
        else:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

class Player:
    def __init__(self, x, y, width, height, color, speed):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.speed = speed
        self.lives = 3
        self.sprite = None  # Sera défini par les states

    def move(self, dx, dy, dt):
        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        self.y = max(0, min(SCREEN_HEIGHT - self.height, self.y))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        if self.sprite:
            screen.blit(self.sprite, (int(self.x), int(self.y)))
        else:
            pygame.draw.rect(screen, self.color, self.get_rect())

class Trash:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 25
        self.vx = random.uniform(-20, 20)
        self.vy = random.uniform(-20, 20)
        self.collected = False
        self.bob_offset = random.uniform(0, math.pi * 2)  # Pour animation bobbing
        self.time = 0
        self.trash_type = random.choice(["bottle", "can", "bag", "tire", "box"])
        self.sprite = create_trash_sprite(self.trash_type)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-30, 30)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.time += dt
        self.rotation += self.rotation_speed * dt

        if self.x <= 0 or self.x >= SCREEN_WIDTH:
            self.vx *= -1
        if self.y <= 0 or self.y >= SCREEN_HEIGHT:
            self.vy *= -1

        self.x = max(0, min(SCREEN_WIDTH, self.x))
        self.y = max(0, min(SCREEN_HEIGHT, self.y))

    def get_rect(self):
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)

    def draw(self, screen, bobbing=False):
        y_offset = 0
        if bobbing:
            y_offset = math.sin(self.time * 2 + self.bob_offset) * 3

        # Rotation du sprite
        rotated = pygame.transform.rotate(self.sprite, self.rotation)
        rect = rotated.get_rect(center=(int(self.x), int(self.y + y_offset)))
        screen.blit(rotated, rect)

class Fish:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 35
        self.vx = random.choice([-50, 50])
        self.vy = random.uniform(-30, 30)
        self.time = 0
        self.bob_offset = random.uniform(0, math.pi * 2)
        self.sprite_right = create_fish_sprite(1)
        self.sprite_left = create_fish_sprite(-1)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.time += dt

        if self.x <= 0 or self.x >= SCREEN_WIDTH:
            self.vx *= -1
        if self.y <= 0 or self.y >= SCREEN_HEIGHT:
            self.vy *= -1

        self.x = max(0, min(SCREEN_WIDTH, self.x))
        self.y = max(0, min(SCREEN_HEIGHT, self.y))

    def get_rect(self):
        return pygame.Rect(self.x - self.size//2, self.y - 12, self.size, 25)

    def draw(self, screen):
        y_offset = math.sin(self.time * 3 + self.bob_offset) * 2
        sprite = self.sprite_right if self.vx > 0 else self.sprite_left
        screen.blit(sprite, (int(self.x - self.size//2), int(self.y - 12 + y_offset)))

class Monkey:
    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.size = 40
        self.speed = speed
        self.sprite = create_monkey_sprite()

    def update(self, dt):
        self.y += self.speed * dt

    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT + 50

    def get_rect(self):
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)

    def draw(self, screen):
        screen.blit(self.sprite, (int(self.x - self.size//2), int(self.y - self.size//2)))

class Debris:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(15, 25)
        self.vx = random.uniform(-80, 80)
        self.vy = random.uniform(-80, 80)
        self.rotation = random.uniform(0, 360)
        self.collected = False

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += 100 * dt

    def is_off_screen(self):
        return (self.x < -50 or self.x > SCREEN_WIDTH + 50 or
                self.y < -50 or self.y > SCREEN_HEIGHT + 50)

    def get_rect(self):
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)

    def draw(self, screen):
        angle = math.radians(self.rotation)
        points = []
        for i in range(6):
            r = self.size // 2 if i % 2 == 0 else self.size // 3
            theta = angle + i * math.pi / 3
            px = self.x + r * math.cos(theta)
            py = self.y + r * math.sin(theta)
            points.append((int(px), int(py)))
        pygame.draw.polygon(screen, (120, 120, 130), points)
        pygame.draw.polygon(screen, (80, 80, 90), points, 2)

class GameState(Enum):
    MENU = 1
    INSTRUCTIONS = 2
    BOAT_GAME = 3
    JUNGLE_GAME = 4
    SPACE_GAME = 5

# ===== ÉTATS DU JEU =====

class MenuState:
    def __init__(self, game):
        self.game = game
        self.selected = 0
        self.options = ["Océan", "Jungle", "Espace"]
        self.descriptions = [
            "Pilote un bateau et pêche les déchets avec ton filet",
            "Conduis sur la route et ramasse les déchets",
            "Capture les débris spatiaux avec ton vaisseau"
        ]
        self.font_title = pygame.font.Font(None, 80)
        self.font_menu = pygame.font.Font(None, 42)
        self.font_help = pygame.font.Font(None, 22)
        self.mouse_hover = -1

        # Particules de fond (bulles/feuilles/étoiles selon thème)
        self.particles = []
        self.particle_timer = 0

        # Pré-rendre le fond dégradé
        self.background = create_gradient_surface(SCREEN_WIDTH, SCREEN_HEIGHT,
                                                  (50, 180, 120), (30, 120, 80))

        # Positions des boutons
        self.button_rects = []
        button_width = 300
        button_height = 60
        start_y = 220
        for i in range(len(self.options)):
            rect = pygame.Rect(SCREEN_WIDTH//2 - button_width//2,
                             start_y + i * 85, button_width, button_height)
            self.button_rects.append(rect)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_DOWN, pygame.K_s]:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in [pygame.K_UP, pygame.K_w]:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self.launch_game(self.selected)
            elif event.key == pygame.K_i:
                self.game.change_state(GameState.INSTRUCTIONS)
            elif event.key == pygame.K_ESCAPE:
                self.game.running = False

        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            self.mouse_hover = -1
            for i, rect in enumerate(self.button_rects):
                if rect.collidepoint(mouse_pos):
                    self.mouse_hover = i
                    self.selected = i

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic gauche
                if self.mouse_hover != -1:
                    self.launch_game(self.mouse_hover)

    def launch_game(self, index):
        if index == 0:
            self.game.change_state(GameState.BOAT_GAME)
        elif index == 1:
            self.game.change_state(GameState.JUNGLE_GAME)
        elif index == 2:
            self.game.change_state(GameState.SPACE_GAME)

    def update(self, dt):
        # Animation des particules de fond
        self.particle_timer += dt
        if self.particle_timer > 0.3:
            # Créer des feuilles qui tombent
            x = random.randint(0, SCREEN_WIDTH)
            y = -10
            vx = random.uniform(-20, 20)
            vy = random.uniform(30, 60)
            color = random.choice([(100, 200, 100), (80, 180, 80), (120, 220, 120)])
            self.particles.append(Particle(x, y, vx, vy, color, 4))
            self.particle_timer = 0

        # Update particules
        for p in self.particles[:]:
            p.update(dt)
            if p.y > SCREEN_HEIGHT + 20:
                self.particles.remove(p)

    def draw(self, screen):
        # Fond dégradé
        screen.blit(self.background, (0, 0))

        # Particules
        for p in self.particles:
            p.draw(screen)

        # Titre avec ombre
        title_text = "Eco Arcade"
        # Ombre
        title_shadow = self.font_title.render(title_text, True, BLACK)
        screen.blit(title_shadow, (SCREEN_WIDTH//2 - title_shadow.get_width()//2 + 3, 83))
        # Titre principal
        title = self.font_title.render(title_text, True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))

        # Boutons
        for i, (option, rect) in enumerate(zip(self.options, self.button_rects)):
            # État du bouton
            is_selected = i == self.selected
            is_hover = i == self.mouse_hover

            # Effet zoom sur hover
            draw_rect = rect.copy()
            if is_hover or is_selected:
                draw_rect.inflate_ip(10, 5)

            # Ombre portée
            shadow_rect = draw_rect.copy()
            shadow_rect.y += 4
            shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            draw_rounded_rect(shadow_surf, (0, 0, 0, 60), shadow_surf.get_rect(), radius=15)
            screen.blit(shadow_surf, shadow_rect)

            # Bouton principal
            button_color = (70, 200, 140) if is_selected else (50, 170, 110)
            border_color = YELLOW if is_selected else WHITE

            button_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
            draw_rounded_rect(button_surf, button_color, button_surf.get_rect(),
                            radius=15, border=3, border_color=border_color)
            screen.blit(button_surf, draw_rect)

            # Texte du bouton
            text_color = WHITE
            text = self.font_menu.render(option, True, text_color)
            text_rect = text.get_rect(center=draw_rect.center)
            screen.blit(text, text_rect)

        # Zone d'aide à droite
        help_box_rect = pygame.Rect(500, 480, 280, 100)
        help_surf = pygame.Surface((help_box_rect.width, help_box_rect.height), pygame.SRCALPHA)
        draw_rounded_rect(help_surf, (255, 255, 255, 180), help_surf.get_rect(), radius=10)
        screen.blit(help_surf, help_box_rect)

        # Description du jeu sélectionné
        desc_text = self.font_help.render(self.descriptions[self.selected], True, BLACK)
        # Wrapper pour texte long
        words = self.descriptions[self.selected].split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if self.font_help.size(test_line)[0] <= help_box_rect.width - 20:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))

        y_offset = help_box_rect.y + 15
        for line in lines:
            line_surf = self.font_help.render(line, True, BLACK)
            screen.blit(line_surf, (help_box_rect.x + 10, y_offset))
            y_offset += 25

        # Contrôles en bas à gauche
        controls = ["↑↓ / Souris: Navigation", "Entrée / Clic: Sélection", "I: Instructions", "ESC: Quitter"]
        y = 480
        for ctrl in controls:
            text = self.font_help.render(ctrl, True, WHITE)
            # Ombre pour lisibilité
            shadow = self.font_help.render(ctrl, True, BLACK)
            screen.blit(shadow, (21, y + 1))
            screen.blit(text, (20, y))
            y += 25

class InstructionsState:
    def __init__(self, game):
        self.game = game
        self.font_title = pygame.font.Font(None, 52)
        self.font_text = pygame.font.Font(None, 24)
        self.background = create_gradient_surface(SCREEN_WIDTH, SCREEN_HEIGHT,
                                                  (20, 50, 100), (10, 30, 60))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_i:
                self.game.change_state(GameState.MENU)

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.blit(self.background, (0, 0))

        # Panel semi-transparent
        panel = pygame.Surface((700, 550), pygame.SRCALPHA)
        draw_rounded_rect(panel, (255, 255, 255, 230), panel.get_rect(), radius=15)
        screen.blit(panel, (50, 25))

        title = self.font_title.render("Instructions", True, DARK_BLUE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 40))

        instructions = [
            ("OCÉAN:", True),
            ("- Pilote le bateau (bleu) avec un filet de pêche devant", False),
            ("- Ramasse les déchets avec le FILET (pas le bateau)", False),
            ("- Évite les poissons: les toucher = pénalité", False),
            ("- Si un déchet touche un poisson: +1 poisson impacté", False),
            ("- Perdu si 10 poissons impactés ou 60 secondes", False),
            ("", False),
            ("JUNGLE:", True),
            ("- Conduis la voiture (verte) sur la route", False),
            ("- Ramasse les déchets, évite les singes", False),
            ("- 3 vies: collision avec singe = -1 vie", False),
            ("- Difficulté augmente avec le temps", False),
            ("", False),
            ("ESPACE:", True),
            ("- Pilote le vaisseau (violet) avec un filet jaune derrière", False),
            ("- Capture les débris avec le filet (pas le vaisseau!)", False),
            ("- Le vaisseau ne doit PAS toucher les débris = -1 vie", False),
            ("- 3 vies, survie pendant 60 secondes", False),
            ("", False),
            ("Contrôles: Flèches/WASD, P: Pause, ESC: Menu", False)
        ]

        y = 100
        for line, is_title in instructions:
            if is_title:
                text = self.font_text.render(line, True, DARK_BLUE)
                text = pygame.font.Font(None, 28).render(line, True, DARK_BLUE)
            else:
                text = self.font_text.render(line, True, BLACK)
            screen.blit(text, (80, y))
            y += 26

        # Indication retour
        back_text = self.font_text.render("Appuie sur ESC pour revenir au menu", True, RED)
        screen.blit(back_text, (SCREEN_WIDTH//2 - back_text.get_width()//2, 555))

class BoatGameState:
    """Jeu Océan avec système de filet de pêche"""
    def __init__(self, game):
        self.game = game
        self.player = Player(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 50, 70, BLUE, 150)
        self.player.sprite = create_boat_sprite()

        # FILET DE PÊCHE (devant le bateau)
        self.net_sprite = create_net_sprite()
        self.net_offset_x = 0
        self.net_offset_y = -55  # Devant le bateau (valeur négative)
        self.net_width = 70
        self.net_height = 50

        self.trash_list = []
        self.fish_list = []
        self.trash_collected = 0
        self.fish_impacted = 0
        self.timer = 60.0
        self.spawn_timer = 0
        self.paused = False
        self.game_over = False
        self.font = pygame.font.Font(None, 28)
        self.font_big = pygame.font.Font(None, 40)

        # Fond océan avec dégradé
        self.background = create_gradient_surface(SCREEN_WIDTH, SCREEN_HEIGHT,
                                                  (50, 150, 255), (20, 100, 200))

        # Spawn initial
        for _ in range(5):
            self.trash_list.append(Trash(random.randint(50, SCREEN_WIDTH-50),
                                         random.randint(50, SCREEN_HEIGHT-50)))
        for _ in range(8):
            self.fish_list.append(Fish(random.randint(50, SCREEN_WIDTH-50),
                                       random.randint(50, SCREEN_HEIGHT-50)))

    def get_net_rect(self):
        """Retourne le Rect de la zone de capture du filet"""
        return pygame.Rect(
            self.player.x + self.player.width//2 - self.net_width//2 + self.net_offset_x,
            self.player.y + self.net_offset_y,
            self.net_width,
            self.net_height
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameState.MENU)
            elif event.key == pygame.K_p:
                self.paused = not self.paused

    def update(self, dt):
        if self.paused or self.game_over:
            return

        self.timer -= dt
        if self.timer <= 0 or self.fish_impacted >= 10:
            self.game_over = True
            return

        # Déplacement joueur
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        if dx != 0 or dy != 0:
            norm = math.sqrt(dx*dx + dy*dy)
            self.player.move(dx/norm, dy/norm, dt)

        # Rect du filet pour collisions
        net_rect = self.get_net_rect()

        # Update trash
        for trash in self.trash_list[:]:
            trash.update(dt)

            # Collision FILET-déchet (capture)
            if not trash.collected and net_rect.colliderect(trash.get_rect()):
                trash.collected = True
                self.trash_collected += 1
                self.trash_list.remove(trash)
                continue

            # Collision trash-poisson
            for fish in self.fish_list:
                if not trash.collected and trash.get_rect().colliderect(fish.get_rect()):
                    trash.collected = True
                    self.fish_impacted += 1
                    self.trash_list.remove(trash)
                    break

        # Update poissons
        for fish in self.fish_list:
            fish.update(dt)

            # Pénalité si BATEAU touche poisson (jamais de collecte!)
            if self.player.get_rect().colliderect(fish.get_rect()):
                self.player.lives = max(0, self.player.lives - 0.5 * dt)  # Perte progressive

        # Spawn nouveaux déchets
        self.spawn_timer += dt
        if self.spawn_timer > 2.0 and len(self.trash_list) < 10:
            self.trash_list.append(Trash(random.randint(50, SCREEN_WIDTH-50),
                                         random.randint(50, SCREEN_HEIGHT-50)))
            self.spawn_timer = 0

    def draw(self, screen):
        # Fond océan
        screen.blit(self.background, (0, 0))

        # Vagues décoratives
        wave_time = pygame.time.get_ticks() / 500
        for i in range(0, SCREEN_HEIGHT, 30):
            offset = int(math.sin(wave_time + i / 20) * 10)
            pygame.draw.line(screen, (30, 120, 220, 100), (offset, i),
                           (SCREEN_WIDTH + offset, i), 2)

        # FILET (avant les entités pour être derrière)
        net_rect = self.get_net_rect()
        screen.blit(self.net_sprite, (net_rect.x, net_rect.y))
        # Ligne de connexion bateau-filet
        pygame.draw.line(screen, (200, 150, 0),
                        (self.player.x + self.player.width//2, self.player.y),
                        (net_rect.centerx, net_rect.bottom), 3)

        # Dessiner entités avec bobbing
        for fish in self.fish_list:
            fish.draw(screen)
        for trash in self.trash_list:
            trash.draw(screen, bobbing=True)

        # Bateau par-dessus
        self.player.draw(screen)

        # UI moderne
        # Panel supérieur
        panel = pygame.Surface((SCREEN_WIDTH, 80), pygame.SRCALPHA)
        draw_rounded_rect(panel, (255, 255, 255, 200), panel.get_rect(), radius=0)
        screen.blit(panel, (0, 0))

        # Compteurs
        info_y = 15
        trash_text = self.font.render(f"🗑️ Déchets pêchés: {self.trash_collected}", True, DARK_BLUE)
        screen.blit(trash_text, (20, info_y))

        fish_color = RED if self.fish_impacted >= 7 else DARK_BLUE
        fish_text = self.font.render(f"🐟 Poissons impactés: {self.fish_impacted}/10", True, fish_color)
        screen.blit(fish_text, (20, info_y + 25))

        # Timer
        timer_color = RED if self.timer < 10 else DARK_BLUE
        timer_text = self.font.render(f"⏱️ Temps: {int(self.timer)}s", True, timer_color)
        screen.blit(timer_text, (SCREEN_WIDTH - 180, info_y))

        # Vies (barre)
        lives_text = self.font.render(f"❤️ Vies:", True, DARK_BLUE)
        screen.blit(lives_text, (SCREEN_WIDTH - 180, info_y + 25))
        pygame.draw.rect(screen, RED, (SCREEN_WIDTH - 100, info_y + 30, self.player.lives * 30, 10))
        pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH - 100, info_y + 30, 90, 10), 2)

        # Instruction
        instruction = self.font.render("Pêche avec le FILET ! Évite les poissons !", True, YELLOW)
        shadow = self.font.render("Pêche avec le FILET ! Évite les poissons !", True, BLACK)
        screen.blit(shadow, (SCREEN_WIDTH//2 - instruction.get_width()//2 + 2, 87))
        screen.blit(instruction, (SCREEN_WIDTH//2 - instruction.get_width()//2, 85))

        if self.paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            pause_text = self.font_big.render("PAUSE", True, WHITE)
            screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2))

        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            go_text = self.font_big.render(f"Terminé ! Score: {self.trash_collected} déchets", True, YELLOW)
            screen.blit(go_text, (SCREEN_WIDTH//2 - go_text.get_width()//2, SCREEN_HEIGHT//2 - 20))
            esc_text = self.font.render("ESC pour menu", True, WHITE)
            screen.blit(esc_text, (SCREEN_WIDTH//2 - esc_text.get_width()//2, SCREEN_HEIGHT//2 + 30))

class JungleGameState:
    def __init__(self, game):
        self.game = game
        self.player = Player(SCREEN_WIDTH//2, SCREEN_HEIGHT - 120, 55, 75, GREEN, 200)
        self.player.sprite = create_car_sprite()
        self.trash_list = []
        self.monkeys = []
        self.score = 0
        self.timer = 60.0
        self.spawn_timer = 0
        self.difficulty_timer = 0
        self.base_speed = 100
        self.paused = False
        self.game_over = False
        self.font = pygame.font.Font(None, 28)
        self.font_big = pygame.font.Font(None, 40)
        self.road_offset = 0

        # Spawn initial
        for _ in range(3):
            self.trash_list.append(Trash(random.randint(50, SCREEN_WIDTH-50),
                                         random.randint(-200, -50)))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameState.MENU)
            elif event.key == pygame.K_p:
                self.paused = not self.paused

    def update(self, dt):
        if self.paused or self.game_over:
            return

        self.timer -= dt
        if self.timer <= 0 or self.player.lives <= 0:
            self.game_over = True
            return

        # Augmenter difficulté
        self.difficulty_timer += dt
        current_speed = self.base_speed + (self.difficulty_timer * 5)

        # Animation route
        self.road_offset += current_speed * dt
        if self.road_offset > 40:
            self.road_offset = 0

        # Déplacement joueur (gauche-droite seulement)
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        if dx != 0:
            self.player.move(dx, 0, dt)

        # Update déchets
        for trash in self.trash_list[:]:
            trash.y += current_speed * dt

            if self.player.get_rect().colliderect(trash.get_rect()):
                self.score += 1
                self.trash_list.remove(trash)
            elif trash.y > SCREEN_HEIGHT:
                self.trash_list.remove(trash)

        # Update singes
        for monkey in self.monkeys[:]:
            monkey.update(dt)

            if self.player.get_rect().colliderect(monkey.get_rect()):
                self.player.lives -= 1
                self.monkeys.remove(monkey)
            elif monkey.is_off_screen():
                self.monkeys.remove(monkey)

        # Spawn
        self.spawn_timer += dt
        if self.spawn_timer > 1.5:
            if random.random() < 0.6:
                self.trash_list.append(Trash(random.randint(200, SCREEN_WIDTH-200), -30))
            if random.random() < 0.4 + self.difficulty_timer * 0.01:
                self.monkeys.append(Monkey(random.randint(200, SCREEN_WIDTH-200), -30, current_speed))
            self.spawn_timer = 0

    def draw(self, screen):
        screen.fill(DARK_GREEN)

        # Forêt des deux côtés
        for x in range(0, SCREEN_WIDTH, 60):
            if x < 150 or x > SCREEN_WIDTH - 150:
                pygame.draw.circle(screen, (30, 80, 30), (x, random.randint(50, 550)), 40)

        # Route
        road_width = 400
        road_x = SCREEN_WIDTH//2 - road_width//2
        pygame.draw.rect(screen, (60, 60, 60), (road_x, 0, road_width, SCREEN_HEIGHT))

        # Lignes blanches animées
        for y in range(int(-self.road_offset), SCREEN_HEIGHT, 40):
            pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH//2 - 5, y, 10, 20))

        # Bords route
        pygame.draw.line(screen, WHITE, (road_x, 0), (road_x, SCREEN_HEIGHT), 3)
        pygame.draw.line(screen, WHITE, (road_x + road_width, 0), (road_x + road_width, SCREEN_HEIGHT), 3)

        # Entités
        for trash in self.trash_list:
            trash.draw(screen, bobbing=False)
        for monkey in self.monkeys:
            monkey.draw(screen)
        self.player.draw(screen)

        # UI
        panel = pygame.Surface((SCREEN_WIDTH, 70), pygame.SRCALPHA)
        draw_rounded_rect(panel, (255, 255, 255, 200), panel.get_rect(), radius=0)
        screen.blit(panel, (0, 0))

        score_text = self.font.render(f"Score: {self.score}", True, DARK_GREEN)
        screen.blit(score_text, (20, 15))

        lives_text = self.font.render(f"❤️ Vies: {self.player.lives}", True, RED)
        screen.blit(lives_text, (20, 40))

        timer_text = self.font.render(f"⏱️ {int(self.timer)}s", True, DARK_GREEN)
        screen.blit(timer_text, (SCREEN_WIDTH - 100, 15))

        instruction = self.font.render("Ramasse les déchets ! Évite les singes !", True, YELLOW)
        shadow = self.font.render("Ramasse les déchets ! Évite les singes !", True, BLACK)
        screen.blit(shadow, (SCREEN_WIDTH//2 - instruction.get_width()//2 + 2, 77))
        screen.blit(instruction, (SCREEN_WIDTH//2 - instruction.get_width()//2, 75))

        if self.paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            pause_text = self.font_big.render("PAUSE", True, WHITE)
            screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2))

        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            go_text = self.font_big.render(f"Terminé ! Score final: {self.score}", True, YELLOW)
            screen.blit(go_text, (SCREEN_WIDTH//2 - go_text.get_width()//2, SCREEN_HEIGHT//2 - 20))
            esc_text = self.font.render("ESC pour menu", True, WHITE)
            screen.blit(esc_text, (SCREEN_WIDTH//2 - esc_text.get_width()//2, SCREEN_HEIGHT//2 + 30))

class SpaceGameState:
    def __init__(self, game):
        self.game = game
        self.player = Player(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 40, 50, PURPLE, 180)
        self.player.sprite = create_spaceship_sprite()
        self.net_offset_x = 0
        self.net_offset_y = 55  # Derrière le vaisseau
        self.net_width = 60
        self.net_height = 40
        self.debris_list = []
        self.score = 0
        self.timer = 60.0
        self.spawn_timer = 0
        self.paused = False
        self.game_over = False
        self.font = pygame.font.Font(None, 28)
        self.font_big = pygame.font.Font(None, 40)
        self.stars = [(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT),
                       random.randint(1, 2)) for _ in range(150)]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameState.MENU)
            elif event.key == pygame.K_p:
                self.paused = not self.paused

    def get_net_rect(self):
        return pygame.Rect(
            self.player.x + self.player.width//2 - self.net_width//2 + self.net_offset_x,
            self.player.y + self.player.height + self.net_offset_y,
            self.net_width,
            self.net_height
        )

    def update(self, dt):
        if self.paused or self.game_over:
            return

        self.timer -= dt
        if self.timer <= 0 or self.player.lives <= 0:
            self.game_over = True
            return

        # Déplacement joueur
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        if dx != 0 or dy != 0:
            norm = math.sqrt(dx*dx + dy*dy)
            self.player.move(dx/norm, dy/norm, dt)

        # Update débris
        net_rect = self.get_net_rect()
        for debris in self.debris_list[:]:
            debris.update(dt)

            # Collision avec filet = capture
            if not debris.collected and net_rect.colliderect(debris.get_rect()):
                debris.collected = True
                self.score += 1
                self.debris_list.remove(debris)
                continue

            # Collision avec vaisseau = perte vie
            if not debris.collected and self.player.get_rect().colliderect(debris.get_rect()):
                self.player.lives -= 1
                self.debris_list.remove(debris)
                continue

            if debris.is_off_screen():
                self.debris_list.remove(debris)

        # Spawn débris
        self.spawn_timer += dt
        if self.spawn_timer > 0.8:
            edge = random.choice(['top', 'bottom', 'left', 'right'])
            if edge == 'top':
                x, y = random.randint(0, SCREEN_WIDTH), -30
            elif edge == 'bottom':
                x, y = random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + 30
            elif edge == 'left':
                x, y = -30, random.randint(0, SCREEN_HEIGHT)
            else:
                x, y = SCREEN_WIDTH + 30, random.randint(0, SCREEN_HEIGHT)

            self.debris_list.append(Debris(x, y))
            self.spawn_timer = 0

    def draw(self, screen):
        screen.fill(BLACK)

        # Étoiles fixes
        for x, y, size in self.stars:
            pygame.draw.circle(screen, WHITE, (x, y), size)

        # Filet (derrière le vaisseau)
        net_rect = self.get_net_rect()
        pygame.draw.rect(screen, (255, 200, 0, 120), net_rect)
        pygame.draw.rect(screen, YELLOW, net_rect, 3)
        pygame.draw.line(screen, YELLOW,
                        (self.player.x + self.player.width//2, self.player.y + self.player.height),
                        (net_rect.centerx, net_rect.top), 3)

        # Débris
        for debris in self.debris_list:
            debris.draw(screen)

        # Vaisseau
        self.player.draw(screen)

        # UI
        panel = pygame.Surface((SCREEN_WIDTH, 70), pygame.SRCALPHA)
        draw_rounded_rect(panel, (50, 50, 50, 200), panel.get_rect(), radius=0)
        screen.blit(panel, (0, 0))

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (20, 15))

        lives_text = self.font.render(f"❤️ Vies: {self.player.lives}", True, RED)
        screen.blit(lives_text, (20, 40))

        timer_text = self.font.render(f"⏱️ {int(self.timer)}s", True, WHITE)
        screen.blit(timer_text, (SCREEN_WIDTH - 100, 15))

        instruction = self.font.render("Capture avec le filet ! Ne touche pas les débris !", True, YELLOW)
        screen.blit(instruction, (SCREEN_WIDTH//2 - instruction.get_width()//2, 75))

        if self.paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            pause_text = self.font_big.render("PAUSE", True, WHITE)
            screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2))

        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            go_text = self.font_big.render(f"Terminé ! Score final: {self.score}", True, YELLOW)
            screen.blit(go_text, (SCREEN_WIDTH//2 - go_text.get_width()//2, SCREEN_HEIGHT//2 - 20))
            esc_text = self.font.render("ESC pour menu", True, WHITE)
            screen.blit(esc_text, (SCREEN_WIDTH//2 - esc_text.get_width()//2, SCREEN_HEIGHT//2 + 30))

# ===== GESTIONNAIRE PRINCIPAL =====

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Eco Arcade - Version Améliorée")
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_state = GameState.MENU
        self.states = {
            GameState.MENU: MenuState(self),
            GameState.INSTRUCTIONS: InstructionsState(self),
        }

    def change_state(self, new_state):
        self.current_state = new_state
        if new_state == GameState.BOAT_GAME:
            self.states[GameState.BOAT_GAME] = BoatGameState(self)
        elif new_state == GameState.JUNGLE_GAME:
            self.states[GameState.JUNGLE_GAME] = JungleGameState(self)
        elif new_state == GameState.SPACE_GAME:
            self.states[GameState.SPACE_GAME] = SpaceGameState(self)
        elif new_state == GameState.MENU:
            # Recréer le menu pour réinitialiser les particules
            self.states[GameState.MENU] = MenuState(self)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.states[self.current_state].handle_event(event)

            self.states[self.current_state].update(dt)
            self.states[self.current_state].draw(self.screen)

            pygame.display.flip()

        pygame.quit()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()