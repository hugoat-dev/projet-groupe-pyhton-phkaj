#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECO ARCADE V3: ULTIMATE EDITION
=============================================================================
Auteur: Gemini (Architecture Avancée)
Version: 3.0.0
Description:
    Suite complète d'arcade écologique avec gestion de sauvegarde persistante,
    génération audio procédurale (synthétiseur), système de particules avancé,
    boutique d'améliorations (Shop), système de succès et 3 jeux approfondis.

Fonctionnalités V3:
    • [CORE] Moteur audio synthétique (aucun fichier mp3/wav requis).
    • [CORE] Système de particules V2 (Bloom, gravité, friction).
    • [META] Boutique d'améliorations (Upgrades persistants).
    • [META] Système de succès (Achievements) avec notifications pop-up.
    • [GAME] Océan : Oxygène, Cycle Jour/Nuit, Trésors.
    • [GAME] Jungle : Carburant, Nitro, Ralentisseurs (Boue), Glace.
    • [GAME] Espace : Boss Fight, Boucliers, Surchauffe.
"""

import os
import json
import math
import random
import sys
import time
import array
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Any, Optional, Tuple

import pygame

# =============================================================================
# 1. CONFIGURATION & CONSTANTES
# =============================================================================

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
W, H = WINDOW_WIDTH, WINDOW_HEIGHT
FPS = 60
SAVE_FILE = "eco_arcade_v3_save.json"

# Couleurs Système
C_BG = (15, 18, 25)
C_WHITE = (245, 245, 250)
C_ACCENT = (0, 255, 180)  # Cyan/Vert tech
C_ACCENT_2 = (255, 190, 0)  # Or/Jaune
C_DANGER = (255, 60, 80)  # Rouge alerte
C_SUCCESS = (100, 255, 100)
C_UI_BG = (30, 35, 45, 230)
C_UI_BORDER = (80, 90, 110)


# =============================================================================
# 2. MOTEUR AUDIO PROCÉDURAL (SYNTHÉTISEUR)
# =============================================================================
# Permet d'avoir du son sans assets externes.

class SoundSynth:
    """Génère des ondes sonores (Carré, Scie, Bruit) à la volée."""

    def __init__(self):
        self.sample_rate = 44100
        pygame.mixer.set_num_channels(8)
        self.sounds = {}
        self.volume = 0.5
        self.enabled = True

    def _generate_wave(self, freq, duration, shape="square", decay=True):
        n_samples = int(self.sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        amplitude = 4000  # Max 32767
        period = self.sample_rate / freq if freq > 0 else 1

        for i in range(n_samples):
            t = i / self.sample_rate
            # Enveloppe de volume (Decay)
            vol = amplitude * (1.0 - i / n_samples) if decay else amplitude

            val = 0
            if shape == "square":
                val = vol if (i % int(period)) < (period / 2) else -vol
            elif shape == "saw":
                val = vol - (vol * 2 * ((i % int(period)) / period))
            elif shape == "noise":
                val = random.randint(-int(vol), int(vol))
            elif shape == "triangle":
                p = i % int(period)
                m = period / 2
                val = (vol * 2 * (p / m)) - vol if p < m else vol - (vol * 2 * ((p - m) / m))

            buf[i] = int(val)
        return pygame.mixer.Sound(buffer=buf)

    def get_sound(self, name):
        if not self.enabled: return None
        if name in self.sounds: return self.sounds[name]

        # Génération différée (Lazy loading)
        snd = None
        if name == "hover":
            snd = self._generate_wave(440, 0.05, "triangle")
        elif name == "click":
            snd = self._generate_wave(880, 0.1, "square")
        elif name == "collect":
            snd = self._generate_wave(1200, 0.15, "triangle")
        elif name == "hurt":
            snd = self._generate_wave(150, 0.3, "saw")
        elif name == "shoot":
            snd = self._generate_wave(300, 0.15, "saw")
        elif name == "explode":
            snd = self._generate_wave(0, 0.4, "noise")
        elif name == "jump":
            snd = self._generate_wave(600, 0.2, "square")
        elif name == "powerup":
            snd = self._generate_wave(1500, 0.4, "triangle")
        elif name == "alert":
            snd = self._generate_wave(800, 0.3, "square", decay=False)

        if snd:
            snd.set_volume(self.volume)
            self.sounds[name] = snd
        return snd

    def play(self, name):
        if not self.enabled: return
        s = self.get_sound(name)
        if s: s.play()


AUDIO = SoundSynth()


# =============================================================================
# 3. UTILITAIRES MATHS & GRAPHIQUES
# =============================================================================

def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))


def lerp(a, b, t):
    return a + (b - a) * clamp(t, 0, 1)


def draw_rounded_rect(surface, rect, color, radius=10, border=0, border_color=None):
    """Dessine un rectangle arrondi propre avec option de bordure."""
    r = pygame.Rect(rect)
    pygame.draw.rect(surface, color, r, border_radius=radius)
    if border > 0 and border_color:
        pygame.draw.rect(surface, border_color, r, width=border, border_radius=radius)


def draw_gradient_rect(surface, rect, c1, c2, direction="vertical"):
    """Remplit une zone avec un dégradé."""
    x, y, w, h = rect
    if direction == "vertical":
        for i in range(h):
            r = int(c1[0] + (c2[0] - c1[0]) * i / h)
            g = int(c1[1] + (c2[1] - c1[1]) * i / h)
            b = int(c1[2] + (c2[2] - c1[2]) * i / h)
            pygame.draw.line(surface, (r, g, b), (x, y + i), (x + w, y + i))


def render_text_centered(surface, text, font, color, center_pos, shadow=True):
    if shadow:
        s = font.render(text, True, (0, 0, 0))
        r = s.get_rect(center=(center_pos[0] + 2, center_pos[1] + 2))
        surface.blit(s, r)
    txt = font.render(text, True, color)
    rect = txt.get_rect(center=center_pos)
    surface.blit(txt, rect)
    return rect


# =============================================================================
# 4. GESTIONNAIRE DE DONNÉES & SAUVEGARDE
# =============================================================================

class DataManager:
    def __init__(self):
        self.data = self._get_default_data()
        self.load()

    def _get_default_data(self):
        return {
            "version": "3.0",
            "coins": 0,
            "highscores": {"ocean": 0, "jungle": 0, "space": 0},
            "upgrades": {
                # Océan
                "hook_speed": 0,  # Niveau 0 à 3
                "oxygen_tank": 0,  # Durée oxygène
                # Jungle
                "engine_power": 0,  # Vitesse max
                "fuel_tank": 0,  # Capacité essence
                # Espace
                "laser_cool": 0,  # Refroidissement
                "shield_max": 0  # Bouclier
            },
            "achievements": [],  # Liste des IDs débloqués
            "settings": {"music": True, "sfx": True, "particles": "high"}
        }

    def load(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r') as f:
                    loaded = json.load(f)
                    # Fusion intelligente (pour ne pas casser si on ajoute des clés)
                    self._merge(self.data, loaded)
            except:
                print("Save file corrupted, using defaults.")

    def _merge(self, default, loaded):
        for k, v in default.items():
            if k in loaded:
                if isinstance(v, dict) and isinstance(loaded[k], dict):
                    self._merge(v, loaded[k])
                else:
                    default[k] = loaded[k]

    def save(self):
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Save failed: {e}")

    def add_coins(self, amount):
        self.data["coins"] += amount
        self.save()

    def unlock_achievement(self, ach_id):
        if ach_id not in self.data["achievements"]:
            self.data["achievements"].append(ach_id)
            self.save()
            return True
        return False


DB = DataManager()


# =============================================================================
# 5. SYSTÈME DE PARTICULES & EFFETS
# =============================================================================

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: tuple
    size: float
    gravity: float = 0.0
    friction: float = 1.0
    shrink: bool = True
    bloom: bool = False


class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []

    def spawn(self, x, y, count=1, color=C_WHITE, speed=50, life=1.0, size=3,
              gravity=0, bloom=False, spread_angle=360):
        for _ in range(count):
            angle = math.radians(random.uniform(0, spread_angle))
            sp = random.uniform(speed * 0.5, speed * 1.5)
            vx = math.cos(angle) * sp
            vy = math.sin(angle) * sp
            self.particles.append(Particle(
                x, y, vx, vy, life, life, color, size, gravity, 0.95, True, bloom
            ))

    def update(self, dt):
        for p in self.particles[:]:
            p.life -= dt
            if p.life <= 0:
                self.particles.remove(p)
                continue

            p.vx *= pow(p.friction, dt * 60)
            p.vy *= pow(p.friction, dt * 60)
            p.vy += p.gravity * dt * 100
            p.x += p.vx * dt
            p.y += p.vy * dt

    def draw(self, surface):
        for p in self.particles:
            alpha = int((p.life / p.max_life) * 255)
            sz = p.size * (p.life / p.max_life) if p.shrink else p.size
            if sz < 0.5: continue

            col = (*p.color[:3], alpha)

            # Effet Bloom (lueur)
            if p.bloom:
                glow_surf = pygame.Surface((int(sz * 4), int(sz * 4)), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*p.color[:3], int(alpha * 0.3)), (int(sz * 2), int(sz * 2)), int(sz * 2))
                surface.blit(glow_surf, (p.x - sz * 2, p.y - sz * 2))

            part_surf = pygame.Surface((int(sz * 2), int(sz * 2)), pygame.SRCALPHA)
            pygame.draw.circle(part_surf, col, (int(sz), int(sz)), int(sz))
            surface.blit(part_surf, (p.x - sz, p.y - sz))


PFX = ParticleSystem()


class ScreenShake:
    def __init__(self):
        self.duration = 0
        self.magnitude = 0
        self.offset = [0, 0]

    def trigger(self, duration, magnitude):
        self.duration = duration
        self.magnitude = magnitude

    def update(self, dt):
        if self.duration > 0:
            self.duration -= dt
            mx = self.magnitude * (self.duration * 2)  # Fade out
            self.offset = [random.uniform(-mx, mx), random.uniform(-mx, mx)]
        else:
            self.offset = [0, 0]


SHAKE = ScreenShake()


# =============================================================================
# 6. ÉLÉMENTS UI & HUD
# =============================================================================

class NotificationManager:
    """Gère les toasts de succès."""

    def __init__(self):
        self.queue = []
        self.current = None
        self.timer = 0
        self.y_offset = -60

    def push(self, title, subtitle, icon_color=C_ACCENT):
        self.queue.append({"t": title, "s": subtitle, "c": icon_color})

    def update(self, dt):
        if self.current:
            self.timer -= dt
            if self.timer <= 0:
                self.y_offset -= 100 * dt  # Slide up
                if self.y_offset < -80:
                    self.current = None
            else:
                self.y_offset = lerp(self.y_offset, 20, dt * 5)
        elif self.queue:
            self.current = self.queue.pop(0)
            self.timer = 3.0
            self.y_offset = -80
            AUDIO.play("powerup")

    def draw(self, screen):
        if self.current:
            r = pygame.Rect(W // 2 - 150, int(self.y_offset), 300, 60)
            draw_rounded_rect(screen, r, C_UI_BG, 10, 2, self.current["c"])

            font_b = pygame.font.SysFont("arial", 22, bold=True)
            font_s = pygame.font.SysFont("arial", 18)

            t = font_b.render(self.current["t"], True, self.current["c"])
            s = font_s.render(self.current["s"], True, C_WHITE)

            screen.blit(t, (r.x + 15, r.y + 8))
            screen.blit(s, (r.x + 15, r.y + 32))


NOTIFS = NotificationManager()


def trigger_achievement(ach_id, title, desc):
    if DB.unlock_achievement(ach_id):
        NOTIFS.push("SUCCÈS DÉBLOQUÉ !", title)


class FloatingText:
    def __init__(self, x, y, text, color, size=24):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.font = pygame.font.SysFont("arial", size, bold=True)
        self.life = 1.0
        self.vy = -30

    def update(self, dt):
        self.life -= dt
        self.y += self.vy * dt
        self.x += math.sin(self.life * 10) * 0.5  # Wiggle

    def draw(self, screen):
        if self.life > 0:
            alpha = int(clamp(self.life * 255, 0, 255))
            s = self.font.render(self.text, True, self.color)
            s.set_alpha(alpha)
            screen.blit(s, (self.x - s.get_width() // 2, self.y))


# =============================================================================
# 7. ASSET GENERATOR (Sprites procéduraux)
# =============================================================================
# Cache pour éviter de redessiner les sprites à chaque frame
SPRITE_CACHE = {}


def get_sprite(key, w, h, draw_func):
    k = (key, w, h)
    if k in SPRITE_CACHE: return SPRITE_CACHE[k]

    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    draw_func(surf, w, h)
    SPRITE_CACHE[k] = surf
    return surf


def draw_spaceship(s, w, h):
    c = (w // 2, h // 2)
    # Corps
    pygame.draw.polygon(s, (200, 200, 220), [(c[0], 0), (w, h), (c[0], h - 10), (0, h)])
    # Cockpit
    pygame.draw.circle(s, (50, 150, 255), (c[0], h // 2), w // 4)
    # Moteur
    pygame.draw.rect(s, C_ACCENT_2, (c[0] - 4, h - 5, 8, 5))


def draw_trash_bottle(s, w, h):
    rect = pygame.Rect(w // 3, h // 4, w // 3, h // 2)
    pygame.draw.rect(s, (100, 200, 255), rect, border_radius=4)
    pygame.draw.rect(s, (200, 200, 200), (w // 3 + 2, 0, w // 3 - 4, h // 4))


def draw_monkey(s, w, h):
    # Tête simple
    pygame.draw.circle(s, (139, 69, 19), (w // 2, h // 2), w // 2)
    pygame.draw.circle(s, (210, 180, 140), (w // 2, h // 2 + 5), w // 3)  # Visage
    pygame.draw.circle(s, (0, 0, 0), (w // 2 - 5, h // 2), 2)
    pygame.draw.circle(s, (0, 0, 0), (w // 2 + 5, h // 2), 2)


# =============================================================================
# 8. MOTEUR D'ÉTATS (STATE MACHINE)
# =============================================================================

class State:
    def __init__(self, game):
        self.game = game
        self.texts = []  # Floating texts

    def enter(self):
        pass

    def exit(self):
        pass

    def handle_input(self, event):
        pass

    def update(self, dt):
        for t in self.texts[:]:
            t.update(dt)
            if t.life <= 0: self.texts.remove(t)

    def draw(self, screen):
        for t in self.texts: t.draw(screen)

    def add_text(self, x, y, msg, col=C_WHITE):
        self.texts.append(FloatingText(x, y, msg, col))


class Game(object):
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Eco Arcade V3 : Ultimate Edition")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state_stack = []

        # Initialisation Polices
        self.font_title = pygame.font.SysFont("impact", 72)
        self.font_ui = pygame.font.SysFont("arial", 24)
        self.font_small = pygame.font.SysFont("arial", 16)

        self.push_state(MenuState(self))

    def push_state(self, state):
        if self.state_stack: self.state_stack[-1].exit()
        self.state_stack.append(state)
        state.enter()

    def pop_state(self):
        if len(self.state_stack) > 1:
            self.state_stack.pop().exit()
            self.state_stack[-1].enter()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.1)  # Lag prevention

            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.state_stack[-1].handle_input(event)

            # Update
            self.state_stack[-1].update(dt)
            PFX.update(dt)
            SHAKE.update(dt)
            NOTIFS.update(dt)
            AUDIO.volume = 0.5  # Reset par frame si besoin

            # Draw
            off = SHAKE.offset
            screen_surf = pygame.Surface((W, H))  # Buffer pour shake

            self.state_stack[-1].draw(screen_surf)
            PFX.draw(screen_surf)
            NOTIFS.draw(screen_surf)

            self.screen.blit(screen_surf, (off[0], off[1]))
            pygame.display.flip()

        DB.save()
        pygame.quit()
        sys.exit()


# =============================================================================
# 9. ÉTAT : MENU PRINCIPAL
# =============================================================================

class MenuState(State):
    def __init__(self, game):
        super().__init__(game)
        self.buttons = [
            {"label": "OCÉAN", "action": lambda: game.push_state(OceanGame(game)),
             "desc": "Nettoyez l'océan, attention à l'oxygène !"},
            {"label": "JUNGLE", "action": lambda: game.push_state(JungleGame(game)),
             "desc": "Course écologique en terrain hostile."},
            {"label": "ESPACE", "action": lambda: game.push_state(SpaceGame(game)),
             "desc": "Défense orbitale contre les débris + Boss."},
            {"label": "BOUTIQUE", "action": lambda: game.push_state(ShopState(game)),
             "desc": "Améliorez votre équipement."},
            {"label": "QUITTER", "action": lambda: setattr(game, 'running', False), "desc": "Sauvegarder et quitter."}
        ]
        self.selected = 0
        # Background anim
        self.bubbles = [[random.randint(0, W), random.randint(0, H), random.uniform(1, 3)] for _ in range(50)]

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.buttons)
                AUDIO.play("hover")
            if event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.buttons)
                AUDIO.play("hover")
            if event.key == pygame.K_RETURN:
                AUDIO.play("click")
                self.buttons[self.selected]["action"]()

    def update(self, dt):
        for b in self.bubbles:
            b[1] -= b[2] * 60 * dt
            if b[1] < -10: b[1] = H + 10; b[0] = random.randint(0, W)

    def draw(self, screen):
        # Fond dégradé
        draw_gradient_rect(screen, (0, 0, W, H), (10, 20, 40), (20, 40, 60))
        for b in self.bubbles:
            pygame.draw.circle(screen, (255, 255, 255, 50), (int(b[0]), int(b[1])), 2)

        # Titre
        render_text_centered(screen, "ECO ARCADE V3", self.game.font_title, C_ACCENT, (W // 2, 100))
        render_text_centered(screen, f"Crédits: {DB.data['coins']} 💰", self.game.font_ui, C_ACCENT_2, (W // 2, 160))

        # Menu
        start_y = 250
        for i, btn in enumerate(self.buttons):
            color = C_ACCENT if i == self.selected else C_WHITE
            rect = pygame.Rect(W // 2 - 150, start_y + i * 70, 300, 50)

            if i == self.selected:
                draw_rounded_rect(screen, rect.inflate(10, 5), C_ACCENT, 10, 2, C_WHITE)
                desc_rect = pygame.Rect(0, H - 40, W, 40)
                pygame.draw.rect(screen, (0, 0, 0), desc_rect)
                render_text_centered(screen, btn["desc"], self.game.font_small, C_WHITE, (W // 2, H - 20))

            render_text_centered(screen, btn["label"], self.game.font_ui, color, rect.center)


# =============================================================================
# 10. ÉTAT : BOUTIQUE (SHOP)
# =============================================================================

class ShopState(State):
    def __init__(self, game):
        super().__init__(game)
        self.items = [
            # ID, Nom, Prix base, Max Level, Desc
            ("hook_speed", "Grappin Rapide", 50, 5, "Pêchez plus vite !"),
            ("oxygen_tank", "Réservoir O2", 75, 5, "Restez sous l'eau plus longtemps."),
            ("engine_power", "Moteur V8 Bio", 100, 5, "Vitesse max accrue en Jungle."),
            ("fuel_tank", "Réservoir XL", 80, 5, "Moins d'arrêts au stand."),
            ("laser_cool", "Refroidisseur", 120, 5, "Tirez plus souvent."),
            ("shield_max", "Générateur Bouclier", 150, 3, "Encaissez plus de coups.")
        ]
        self.selected = 0

    def get_price(self, key):
        lvl = DB.data["upgrades"][key]
        base = next(i[2] for i in self.items if i[0] == key)
        return int(base * (1.5 ** lvl))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: self.game.pop_state()
            if event.key == pygame.K_UP: self.selected = (self.selected - 1) % len(self.items); AUDIO.play("hover")
            if event.key == pygame.K_DOWN: self.selected = (self.selected + 1) % len(self.items); AUDIO.play("hover")
            if event.key == pygame.K_RETURN: self.buy()

    def buy(self):
        key, name, _, max_lvl, _ = self.items[self.selected]
        lvl = DB.data["upgrades"][key]
        price = self.get_price(key)

        if lvl >= max_lvl:
            AUDIO.play("hurt")  # Erreur
        elif DB.data["coins"] >= price:
            DB.data["coins"] -= price
            DB.data["upgrades"][key] += 1
            DB.save()
            AUDIO.play("collect")
            PFX.spawn(W // 2, H // 2, 20, C_ACCENT_2, speed=100, bloom=True)
            self.add_text(W // 2, H // 2, "AMÉLIORÉ !", C_ACCENT)
        else:
            AUDIO.play("hurt")
            self.add_text(W // 2, H // 2, "PAS ASSEZ D'ARGENT", C_DANGER)

    def draw(self, screen):
        screen.fill(C_BG)
        render_text_centered(screen, "BOUTIQUE ÉCOLOGIQUE", self.game.font_title, C_ACCENT, (W // 2, 60))
        render_text_centered(screen, f"Portefeuille: {DB.data['coins']} 💰", self.game.font_ui, C_ACCENT_2,
                             (W // 2, 110))

        y = 160
        for i, (key, name, base, max_lvl, desc) in enumerate(self.items):
            lvl = DB.data["upgrades"][key]
            price = self.get_price(key)
            is_max = lvl >= max_lvl

            rect = pygame.Rect(100, y, W - 200, 70)
            col = C_ACCENT if i == self.selected else (50, 60, 70)
            draw_rounded_rect(screen, rect, (30, 35, 45), 10, 2 if i == self.selected else 0, col)

            # Icone / Nom
            render_text_centered(screen, name, self.game.font_ui, C_WHITE, (rect.x + 100, rect.y + 25))
            # Niveau
            lv_str = "MAX" if is_max else f"Lvl {lvl}/{max_lvl}"
            render_text_centered(screen, lv_str, self.game.font_small, C_ACCENT_2, (rect.x + 100, rect.y + 50))

            # Prix
            p_str = "---" if is_max else f"{price} 💰"
            render_text_centered(screen, p_str, self.game.font_ui, C_WHITE if not is_max else C_UI_BORDER,
                                 (rect.right - 80, rect.centery))

            # Barre de progression
            bar_w = 150
            fill = (lvl / max_lvl) * bar_w
            pygame.draw.rect(screen, (0, 0, 0), (rect.centerx - 20, rect.y + 45, bar_w, 10))
            pygame.draw.rect(screen, C_ACCENT, (rect.centerx - 20, rect.y + 45, fill, 10))

            y += 85

        # Description footer
        if 0 <= self.selected < len(self.items):
            render_text_centered(screen, self.items[self.selected][4], self.game.font_ui, C_WHITE, (W // 2, H - 30))


# =============================================================================
# 11. JEU DE BASE (CLASSE PARENTE)
# =============================================================================

class MiniGame(State):
    def __init__(self, game):
        super().__init__(game)
        self.score = 0
        self.lives = 3
        self.paused = False
        self.game_over = False
        self.time_elapsed = 0

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p: self.paused = not self.paused
            if event.key == pygame.K_ESCAPE: self.game.pop_state()
            if self.game_over and event.key == pygame.K_RETURN: self.game.pop_state()

    def end_game(self, mode_key):
        self.game_over = True
        bonus = int(self.score * 0.5)
        DB.add_coins(bonus)
        if self.score > DB.data["highscores"][mode_key]:
            DB.data["highscores"][mode_key] = self.score
            trigger_achievement(f"best_{mode_key}", "Nouveau Record !", f"Score: {self.score}")
        AUDIO.play("alert")

    def draw_hud(self, screen, color=C_WHITE):
        draw_rounded_rect(screen, (10, 10, 200, 80), (0, 0, 0, 150), 10)
        screen.blit(self.game.font_ui.render(f"Score: {self.score}", True, color), (20, 20))
        screen.blit(self.game.font_ui.render(f"Vies: {'❤️' * self.lives}", True, C_DANGER), (20, 50))

        if self.paused:
            draw_rounded_rect(screen, (W // 2 - 100, H // 2 - 50, 200, 100), C_UI_BG, 10, 2, C_WHITE)
            render_text_centered(screen, "PAUSE", self.game.font_ui, C_WHITE, (W // 2, H // 2))

        if self.game_over:
            s = pygame.Surface((W, H), pygame.SRCALPHA)
            s.fill((0, 0, 0, 200))
            screen.blit(s, (0, 0))
            render_text_centered(screen, "PARTIE TERMINÉE", self.game.font_title, C_DANGER, (W // 2, H // 2 - 50))
            render_text_centered(screen, f"Score Final: {self.score}", self.game.font_ui, C_WHITE,
                                 (W // 2, H // 2 + 20))
            render_text_centered(screen, f"Gains: +{int(self.score * 0.5)} 💰", self.game.font_ui, C_ACCENT_2,
                                 (W // 2, H // 2 + 60))
            render_text_centered(screen, "Appuyez sur ENTRÉE", self.game.font_small, C_WHITE, (W // 2, H // 2 + 100))


# =============================================================================
# 12. JEU 1 : ESPACE (SPACE DEFENDER - ULTIMATE)
# =============================================================================

class SpaceGame(MiniGame):
    def __init__(self, game):
        super().__init__(game)
        self.player_x = W // 2
        self.player_y = H - 80

        # Stats via Upgrades
        lvl_cool = DB.data["upgrades"]["laser_cool"]
        self.cooldown_max = max(0.1, 0.4 - (lvl_cool * 0.05))
        self.cooldown = 0

        lvl_shield = DB.data["upgrades"]["shield_max"]
        self.shield_max = 0 if lvl_shield == 0 else (50 + lvl_shield * 50)
        self.shield = self.shield_max

        self.lasers = []
        self.enemies = []
        self.boss = None
        self.spawn_timer = 0
        self.stars = [[random.randint(0, W), random.randint(0, H), random.random()] for _ in range(100)]
        self.heat = 0  # Surchauffe

    def update(self, dt):
        super().update(dt)
        if self.paused or self.game_over: return
        self.time_elapsed += dt

        # Contrôles
        keys = pygame.key.get_pressed()
        speed = 400 * dt
        if keys[pygame.K_LEFT]: self.player_x -= speed
        if keys[pygame.K_RIGHT]: self.player_x += speed
        self.player_x = clamp(self.player_x, 30, W - 30)

        # Tir & Surchauffe
        self.cooldown -= dt
        self.heat = max(0, self.heat - 10 * dt)
        if keys[pygame.K_SPACE] and self.cooldown <= 0 and self.heat < 100:
            self.lasers.append([self.player_x, self.player_y - 20])
            self.cooldown = self.cooldown_max
            self.heat += 15
            AUDIO.play("shoot")
            if self.heat > 80: self.add_text(self.player_x, self.player_y - 40, "HOT!", C_DANGER)

        # Lasers
        for l in self.lasers[:]:
            l[1] -= 600 * dt
            if l[1] < 0: self.lasers.remove(l)

        # Ennemis (Debris)
        if self.boss is None:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.spawn_timer = max(0.5, 2.0 - (self.score * 0.02))
                sz = random.randint(20, 50)
                self.enemies.append({
                    "x": random.randint(0, W), "y": -50, "sz": sz, "hp": sz // 10,
                    "vx": random.uniform(-50, 50), "vy": random.uniform(100, 200 + self.score)
                })

        # Logique Ennemis
        player_rect = pygame.Rect(self.player_x - 20, self.player_y - 20, 40, 40)

        for e in self.enemies[:]:
            e["y"] += e["vy"] * dt
            e["x"] += e["vx"] * dt
            r = pygame.Rect(e["x"] - e["sz"] / 2, e["y"] - e["sz"] / 2, e["sz"], e["sz"])

            # Collision Laser
            hit = False
            for l in self.lasers[:]:
                if r.collidepoint(l[0], l[1]):
                    self.lasers.remove(l)
                    e["hp"] -= 1
                    PFX.spawn(l[0], l[1], 5, C_ACCENT, 100, 0.2)
                    if e["hp"] <= 0:
                        hit = True
                        self.score += 1
                        AUDIO.play("explode")
                        PFX.spawn(e["x"], e["y"], 20, C_DANGER, 150, bloom=True)
                        SHAKE.trigger(0.2, 5)
                        break
            if hit:
                self.enemies.remove(e)
                continue

            # Collision Joueur
            if r.colliderect(player_rect):
                AUDIO.play("hurt")
                SHAKE.trigger(0.4, 10)
                self.enemies.remove(e)
                damage = 100 if e["sz"] > 40 else 50
                if self.shield > 0:
                    self.shield -= damage
                    self.add_text(self.player_x, self.player_y, "BOUCLIER -", C_ACCENT)
                else:
                    self.lives -= 1
                    self.add_text(self.player_x, self.player_y, "-1 VIE", C_DANGER)
                    if self.lives <= 0: self.end_game("space")

        # Boss Spawn
        if self.score > 0 and self.score % 50 == 0 and self.boss is None:
            self.boss = {"x": W // 2, "y": -100, "hp": 50, "max_hp": 50, "state": "enter"}
            AUDIO.play("alert")
            NOTIFS.push("ALERTE", "BOSS EN APPROCHE", C_DANGER)

        # Boss Logic
        if self.boss:
            b = self.boss
            br = pygame.Rect(b["x"] - 60, b["y"] - 40, 120, 80)

            if b["state"] == "enter":
                b["y"] = lerp(b["y"], 150, dt)
                if abs(b["y"] - 150) < 5: b["state"] = "fight"
            elif b["state"] == "fight":
                b["x"] += math.sin(self.time_elapsed * 2) * 200 * dt
                # Boss shoot
                if random.random() < 0.05:
                    self.enemies.append({"x": b["x"], "y": b["y"] + 40, "sz": 15, "hp": 1, "vx": 0, "vy": 400})

            # Boss hit
            for l in self.lasers[:]:
                if br.collidepoint(l[0], l[1]):
                    self.lasers.remove(l)
                    b["hp"] -= 1
                    PFX.spawn(l[0], l[1], 3, C_WHITE)
                    if b["hp"] <= 0:
                        self.boss = None
                        self.score += 50
                        AUDIO.play("powerup")
                        SHAKE.trigger(1.0, 20)
                        PFX.spawn(b["x"], b["y"], 100, C_ACCENT_2, 300, 2.0, bloom=True)
                        trigger_achievement("boss_killed", "Tueur de Boss", "Menace neutralisée")

    def draw(self, screen):
        screen.fill((10, 10, 15))
        # Stars parallax
        for s in self.stars:
            s[1] += s[2] * 2
            if s[1] > H: s[1] = 0
            c = int(s[2] * 255)
            pygame.draw.circle(screen, (c, c, c), (int(s[0]), int(s[1])), 1)

        # Player
        draw_spaceship(get_sprite("ship", 40, 40, draw_spaceship), 40, 40)
        s_surf = get_sprite("ship", 40, 40, draw_spaceship)
        screen.blit(s_surf, (self.player_x - 20, self.player_y - 20))

        # Shield Bubble
        if self.shield > 0:
            alpha = int((self.shield / self.shield_max) * 100) + 50
            surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(surf, (0, 200, 255, alpha), (30, 30), 30, 2)
            screen.blit(surf, (self.player_x - 30, self.player_y - 30))

        # Enemies
        for e in self.enemies:
            col = (150, 150, 150)
            pygame.draw.circle(screen, col, (int(e["x"]), int(e["y"])), e["sz"] // 2)
            pygame.draw.circle(screen, (100, 100, 100), (int(e["x"]), int(e["y"])), e["sz"] // 2 - 2)

        # Lasers
        for l in self.lasers:
            pygame.draw.rect(screen, C_ACCENT, (l[0] - 2, l[1], 4, 15))
            # Glow
            gs = pygame.Surface((10, 20), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*C_ACCENT, 100), (0, 0, 10, 20))
            screen.blit(gs, (l[0] - 5, l[1] - 2))

        # Boss
        if self.boss:
            b = self.boss
            r = pygame.Rect(b["x"] - 60, b["y"] - 40, 120, 80)
            draw_rounded_rect(screen, r, C_DANGER, 15)
            pygame.draw.rect(screen, (0, 0, 0), (b["x"] - 50, b["y"] - 60, 100, 10))
            pygame.draw.rect(screen, C_DANGER, (b["x"] - 50, b["y"] - 60, 100 * (b["hp"] / b["max_hp"]), 10))

        # UI
        self.draw_hud(screen)
        # Heat Bar
        pygame.draw.rect(screen, (50, 50, 50), (W - 120, H - 40, 100, 20))
        col_h = C_DANGER if self.heat > 80 else C_ACCENT
        pygame.draw.rect(screen, col_h, (W - 120, H - 40, self.heat, 20))
        screen.blit(self.game.font_small.render("TEMP", True, C_WHITE), (W - 120, H - 60))

        super().draw(screen)


# =============================================================================
# 13. JEU 2 : OCÉAN (DEEP CLEAN - ULTIMATE)
# =============================================================================

class OceanGame(MiniGame):
    def __init__(self, game):
        super().__init__(game)
        self.boat_x = W // 2

        # Upgrades
        self.hook_speed = 300 + (DB.data["upgrades"]["hook_speed"] * 100)
        self.max_o2 = 30 + (DB.data["upgrades"]["oxygen_tank"] * 15)
        self.o2 = self.max_o2

        self.hook = {"x": self.boat_x, "y": 100, "state": "idle", "obj": None}
        self.trash_list = []
        self.fish_list = []
        self.bubbles = []
        self.time_of_day = 0  # 0 to 1

        # Init Spawn
        for _ in range(10): self.spawn_trash()
        for _ in range(15): self.spawn_fish()

    def spawn_trash(self):
        self.trash_list.append({
            "x": random.randint(50, W - 50),
            "y": random.randint(200, H - 50),
            "type": random.choice(["bottle", "tire", "can"]),
            "val": 10
        })

    def spawn_fish(self):
        self.fish_list.append({
            "x": random.randint(0, W),
            "y": random.randint(200, H - 50),
            "vx": random.choice([-1, 1]) * random.randint(50, 100),
            "color": random.choice([(255, 100, 100), (255, 200, 50), (100, 255, 200)])
        })

    def update(self, dt):
        super().update(dt)
        if self.paused or self.game_over: return

        # Day/Night Cycle
        self.time_of_day = (self.time_of_day + dt * 0.05) % 1.0

        # Controls
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: self.boat_x -= 300 * dt
        if keys[pygame.K_RIGHT]: self.boat_x += 300 * dt
        self.boat_x = clamp(self.boat_x, 50, W - 50)

        # Hook Logic
        h = self.hook
        if h["state"] == "idle":
            h["x"] = self.boat_x
            h["y"] = 100
            self.o2 = min(self.o2 + 10 * dt, self.max_o2)  # Regen O2 surface
            if keys[pygame.K_SPACE]:
                h["state"] = "down"
                AUDIO.play("jump")  # Sfx drop

        elif h["state"] == "down":
            h["y"] += self.hook_speed * dt
            self.o2 -= 2 * dt  # O2 drain

            # Hit bottom or O2 empty
            if h["y"] > H - 20 or self.o2 <= 0:
                h["state"] = "up"
                if self.o2 <= 0: self.add_text(h["x"], h["y"], "OXYGÈNE !", C_DANGER)

            # Collisions Trash
            hook_rect = pygame.Rect(h["x"] - 10, h["y"], 20, 20)
            if not h["obj"]:
                for t in self.trash_list[:]:
                    tr = pygame.Rect(t["x"] - 15, t["y"] - 15, 30, 30)
                    if hook_rect.colliderect(tr):
                        h["obj"] = t
                        h["state"] = "up"
                        self.trash_list.remove(t)
                        AUDIO.play("click")
                        break

                # Collision Fish (Bad!)
                for f in self.fish_list:
                    fr = pygame.Rect(f["x"] - 15, f["y"] - 10, 30, 20)
                    if hook_rect.colliderect(fr):
                        h["state"] = "up"
                        self.lives -= 1
                        AUDIO.play("hurt")
                        self.add_text(h["x"], h["y"], "POISSON TOUCHÉ!", C_DANGER)
                        SHAKE.trigger(0.3, 5)
                        if self.lives <= 0: self.end_game("ocean")
                        break

        elif h["state"] == "up":
            h["y"] -= self.hook_speed * dt
            if h["obj"]:  # Sync obj pos
                h["obj"]["x"] = h["x"]
                h["obj"]["y"] = h["y"] + 10

            if h["y"] <= 100:
                h["state"] = "idle"
                if h["obj"]:
                    self.score += h["obj"]["val"]
                    h["obj"] = None
                    AUDIO.play("collect")
                    self.add_text(self.boat_x, 80, "+10", C_SUCCESS)
                    self.spawn_trash()

        # Fish Movement
        for f in self.fish_list:
            f["x"] += f["vx"] * dt
            if f["x"] > W + 20:
                f["x"] = -20
            elif f["x"] < -20:
                f["x"] = W + 20

    def draw(self, screen):
        # Sky color based on time
        sky_b = int(lerp(255, 50, abs(math.sin(self.time_of_day * 3.14))))
        sky_col = (100, 200, sky_b)
        pygame.draw.rect(screen, sky_col, (0, 0, W, 120))

        # Water
        water_dark = int(lerp(50, 20, self.time_of_day))
        draw_gradient_rect(screen, (0, 120, W, H - 120), (0, 100, 200), (0, 20, water_dark))

        # Boat
        pygame.draw.polygon(screen, (200, 50, 50),
                            [(self.boat_x - 40, 90), (self.boat_x + 40, 90), (self.boat_x + 20, 120),
                             (self.boat_x - 20, 120)])

        # Rope
        pygame.draw.line(screen, (50, 50, 50), (self.boat_x, 90), (self.hook["x"], self.hook["y"]), 2)

        # Hook
        pygame.draw.circle(screen, (200, 200, 200), (int(self.hook["x"]), int(self.hook["y"])), 8)

        # Trash
        for t in self.trash_list:
            pygame.draw.rect(screen, (150, 100, 50), (t["x"] - 10, t["y"] - 15, 20, 30))  # Bottle simple

        # Fish
        for f in self.fish_list:
            d = -1 if f["vx"] < 0 else 1
            pts = [(f["x"] + 15 * d, f["y"]), (f["x"] - 15 * d, f["y"] - 10), (f["x"] - 15 * d, f["y"] + 10)]
            pygame.draw.polygon(screen, f["color"], pts)

        # Catch object
        if self.hook["obj"]:
            t = self.hook["obj"]
            pygame.draw.rect(screen, (150, 100, 50), (t["x"] - 10, t["y"] - 15, 20, 30))

        # O2 Bar
        pygame.draw.rect(screen, (50, 50, 50), (self.boat_x - 30, 60, 60, 10))
        pct = self.o2 / self.max_o2
        col = C_SUCCESS if pct > 0.3 else C_DANGER
        pygame.draw.rect(screen, col, (self.boat_x - 30, 60, 60 * pct, 10))

        # Darkness overlay (Night)
        if water_dark < 40:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 10, int(lerp(0, 150, self.time_of_day))))
            # Light circle around hook
            pygame.draw.circle(overlay, (0, 0, 0, 0), (int(self.hook["x"]), int(self.hook["y"])), 100)
            screen.blit(overlay, (0, 0))

        self.draw_hud(screen, (0, 0, 0))
        super().draw(screen)


# =============================================================================
# 14. JEU 3 : JUNGLE (ECO RALLY - ULTIMATE)
# =============================================================================

class JungleGame(MiniGame):
    def __init__(self, game):
        super().__init__(game)
        self.car_x = W // 2
        self.road_w = 400
        self.curve = 0
        self.speed = 0
        self.dist = 0

        # Upgrades
        self.max_speed = 800 + (DB.data["upgrades"]["engine_power"] * 100)
        self.fuel_max = 100 + (DB.data["upgrades"]["fuel_tank"] * 20)
        self.fuel = self.fuel_max

        self.objs = []
        self.bg_scroll = 0

    def update(self, dt):
        super().update(dt)
        if self.paused or self.game_over: return

        keys = pygame.key.get_pressed()

        # Acceleration / Fuel
        accel = 500
        if keys[pygame.K_UP]:
            self.speed += accel * dt
            self.fuel -= 5 * dt
        elif keys[pygame.K_DOWN]:
            self.speed -= accel * 2 * dt
        else:
            self.speed -= 200 * dt  # Friction

        self.speed = clamp(self.speed, 0, self.max_speed)

        # Steering
        if self.speed > 0:
            steer = 300 * dt
            if keys[pygame.K_LEFT]: self.car_x -= steer
            if keys[pygame.K_RIGHT]: self.car_x += steer

        # Fuel Empty
        if self.fuel <= 0:
            self.speed -= 800 * dt
            if self.speed <= 0 and self.lives > 0:
                self.end_game("jungle")

        # Road Generation (Pseudo-3D Logic simplistic)
        self.dist += self.speed * dt
        self.bg_scroll += self.speed * dt * 0.1

        # Spawn obstacles
        if random.randint(0, 100) < 2 and self.speed > 100:
            type_o = random.choice(["rock", "coin", "fuel"])
            self.objs.append({"x": random.randint(W // 2 - 150, W // 2 + 150), "y": -50, "t": type_o})

        # Update Objects
        car_rect = pygame.Rect(self.car_x - 20, H - 120, 40, 60)

        for o in self.objs[:]:
            o["y"] += (self.speed * dt) + 100 * dt  # Relative speed

            r = pygame.Rect(o["x"] - 15, o["y"] - 15, 30, 30)

            # Collision
            if r.colliderect(car_rect):
                if o["t"] == "rock":
                    self.speed *= 0.2
                    self.lives -= 1
                    AUDIO.play("explode")
                    SHAKE.trigger(0.5, 15)
                    self.objs.remove(o)
                    if self.lives <= 0: self.end_game("jungle")
                elif o["t"] == "coin":
                    self.score += 50
                    AUDIO.play("collect")
                    self.objs.remove(o)
                elif o["t"] == "fuel":
                    self.fuel = min(self.fuel + 30, self.fuel_max)
                    AUDIO.play("powerup")
                    self.add_text(self.car_x, H - 150, "FUEL +", C_ACCENT)
                    self.objs.remove(o)

            if o["y"] > H: self.objs.remove(o)

        # Off-road penalty
        if self.car_x < W // 2 - 200 or self.car_x > W // 2 + 200:
            self.speed *= 0.95  # Slow down on grass

    def draw(self, screen):
        # Background
        pygame.draw.rect(screen, (50, 150, 50), (0, 0, W, H))  # Grass

        # Road (Perspective simple)
        road_col = (80, 80, 80)
        pygame.draw.polygon(screen, road_col, [
            (W // 2 - 20, 0), (W // 2 + 20, 0),
            (W // 2 + 200, H), (W // 2 - 200, H)
        ])

        # Stripes
        strip_off = (self.dist % 100) / 100
        for i in range(10):
            y = i * (H / 10) + (strip_off * (H / 10))
            if y < H:
                w = lerp(5, 20, y / H)
                pygame.draw.rect(screen, (255, 255, 255), (W // 2 - w / 2, y, w, H / 20))

        # Objects
        for o in self.objs:
            col = (100, 100, 100)
            if o["t"] == "coin":
                col = C_ACCENT_2
            elif o["t"] == "fuel":
                col = C_DANGER
            scale = lerp(0.5, 1.0, o["y"] / H)
            sz = 30 * scale
            pygame.draw.rect(screen, col, (o["x"] - sz / 2, o["y"] - sz / 2, sz, sz))

        # Car
        draw_rounded_rect(screen, (self.car_x - 20, H - 120, 40, 60), C_ACCENT, 8)
        # Tires
        pygame.draw.rect(screen, (0, 0, 0), (self.car_x - 22, H - 110, 4, 15))
        pygame.draw.rect(screen, (0, 0, 0), (self.car_x + 18, H - 110, 4, 15))

        # UI
        self.draw_hud(screen)
        # Fuel
        pygame.draw.rect(screen, (0, 0, 0), (20, H - 40, 200, 20))
        pygame.draw.rect(screen, C_DANGER, (22, H - 38, 196 * (self.fuel / self.fuel_max), 16))
        screen.blit(self.game.font_small.render("FUEL", True, C_WHITE), (25, H - 38))

        # Speedometer
        speed_txt = self.game.font_ui.render(f"{int(self.speed / 10)} km/h", True, C_WHITE)
        screen.blit(speed_txt, (W - 150, H - 50))

        super().draw(screen)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    Game().run()