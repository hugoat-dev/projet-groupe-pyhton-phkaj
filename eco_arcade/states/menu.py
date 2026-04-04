import math

import pygame

from config import W, H, palette
from graphics import vertical_gradient, rounded_rect_surf
from particles import MenuParticles, FadeTransition
from ui import State, Button


class MenuState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal = palette(game.data["settings"]["color_mode"])
        self.font_title = pygame.font.Font(None, 90)
        self.font_btn = pygame.font.Font(None, 38)
        self.font_small = pygame.font.Font(None, 22)
        self.bg_ocean = vertical_gradient((W, H), (30, 140, 210), (12, 50, 115))
        self.bg_jungle = vertical_gradient((W, H), (35, 155, 80), (15, 65, 40))
        self.bg_space = vertical_gradient((W, H), (8, 10, 18), (22, 12, 38))
        self.selected = 0
        labels = ["Océan (Grappin)", "Jungle (Voiture)", "Espace (Lasers)",
                  "Instructions", "Paramètres", "Quitter"]
        self.actions = ["ocean", "jungle", "space", "instructions", "settings", "quit"]
        self.buttons = []
        bw, bh = 360, 56
        sy = 190
        for i, lab in enumerate(labels):
            r = pygame.Rect(W // 2 - bw // 2, sy + i * 68, bw, bh)
            self.buttons.append(Button(r, lab, self.font_btn))
        self.particles = MenuParticles()
        self.title_t = 0.0
        self.fade = FadeTransition(0.4)
        self.fade.fading_out = False

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
        from states.ocean import OceanGameState
        from states.jungle import JungleGameState
        from states.space import SpaceGameState
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
        self.title_t += dt
        mode = self._preview_mode()
        self.particles.update(dt, mode, self.game.data["settings"]["particles"])
        mp = pygame.mouse.get_pos()
        for b in self.buttons: b.update(dt, mp)
        self.fade.update(dt)

    def draw(self, screen):
        mode = self._preview_mode()
        bg = self.bg_space if mode == "space" else self.bg_ocean if mode == "ocean" else self.bg_jungle
        screen.blit(bg, (0, 0))
        self.particles.draw(screen, mode)

        t = self.title_t
        title_str = "Eco Arcade"
        for i, ch in enumerate(title_str):
            wave_y = int(math.sin(t * 2.8 + i * 0.45) * 5)
            sh = self.font_title.render(ch, True, (0, 0, 0))
            tl = self.font_title.render(ch, True, (255, 255, 255))
            total_w = self.font_title.size(title_str)[0]
            char_x = W // 2 - total_w // 2 + self.font_title.size(title_str[:i])[0]
            screen.blit(sh, (char_x + 3, 62 + wave_y + 3))
            screen.blit(tl, (char_x, 62 + wave_y))

        sub = self.font_small.render("V2 Enhanced — images + multi-fichiers", True, self.pal["accent2"])
        screen.blit(sub, (W // 2 - sub.get_width() // 2, 140))

        for i, b in enumerate(self.buttons):
            b.draw(screen, self.pal, selected=(i == self.selected))

        hint = self.font_small.render("↑↓: naviguer | Entrée: lancer | I: instructions | ESC: quitter",
                                      True, (230, 235, 245))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 30))
        self.fade.draw(screen)


class InstructionsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.font_t = pygame.font.Font(None, 54)
        self.font = pygame.font.Font(None, 24)

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_i):
            self.game.transition_to(MenuState(self.game))

    def draw(self, screen):
        pal = palette(self.game.data["settings"]["color_mode"])
        screen.fill((18, 32, 55))
        panel = rounded_rect_surf((760, 520), (255, 255, 255, 230), radius=16, border=2, border_color=(0, 0, 0, 40))
        screen.blit(panel, (70, 40))
        t = self.font_t.render("Instructions", True, (15, 28, 52))
        screen.blit(t, (W // 2 - t.get_width() // 2, 58))
        lines = [
            ("OCÉAN — Grappin", True),
            ("• A/D ou ←→: déplacer le bateau.", False),
            ("• SPACE: lancer le grappin (descend puis remonte).", False),
            ("• Déchets pêchés = +10 pts. Poissons = -1 vie si touchés.", False),
            ("JUNGLE — Voiture", True),
            ("• A/D ou ←→: déplacer la voiture.", False),
            ("• Le bac en haut de la voiture collecte les déchets.", False),
            ("• Singe = obstacle: collision => -1 vie + invincibilité 1s.", False),
            ("ESPACE — Lasers", True),
            ("• A/D ou ←→: gauche/droite.", False),
            ("• SPACE: tirer (énergie + cooldown).", False),
            ("• Débris: small(1), medium(2), large(3) points.", False),
            ("", False),
            ("P: Pause | ESC / I: retour au menu", False),
        ]
        y = 128
        for txt, is_title in lines:
            f = pygame.font.Font(None, 30) if is_title else self.font
            col = (15, 28, 52) if is_title else pal["text"]
            r = f.render(txt, True, col)
            screen.blit(r, (110, y))
            y += 30


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
                from config import save_now
                save_now(self.game.data)
                self.game.transition_to(MenuState(self.game))
            elif e.key in (pygame.K_UP, pygame.K_w):
                self.idx = (self.idx - 1) % len(self.items)
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.idx = (self.idx + 1) % len(self.items)
            elif e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                key = self.items[self.idx]
                vals = ["low", "med", "high"] if key == "particles" else ["normal", "deuteranopia"]
                cur = self.game.data["settings"][key]
                i = vals.index(cur)
                i = (i + (1 if e.key in (pygame.K_RIGHT, pygame.K_d) else -1)) % len(vals)
                self.game.data["settings"][key] = vals[i]

    def draw(self, screen):
        screen.fill((22, 22, 30))
        panel = rounded_rect_surf((720, 420), (255, 255, 255, 230), radius=16, border=2, border_color=(0, 0, 0, 40))
        screen.blit(panel, (90, 90))
        t = self.font_t.render("Paramètres", True, (15, 28, 52))
        screen.blit(t, (W // 2 - t.get_width() // 2, 108))
        labels = {"particles": "Intensité particules", "color_mode": "Mode couleurs"}
        y = 200
        for i, key in enumerate(self.items):
            sel = (i == self.idx)
            col = (15, 28, 52) if sel else (90, 95, 108)
            screen.blit(self.font.render(labels[key], True, col), (140, y))
            val = str(self.game.data["settings"][key])
            screen.blit(self.font.render(f"<  {val}  >", True, col), (560, y))
            y += 70
        hint = self.small.render("←→: changer | ESC: retour", True, (20, 25, 35))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, 455))
