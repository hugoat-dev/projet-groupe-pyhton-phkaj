import pygame
from config import W, H
from ui import State, Button


class MenuState(State):
    def __init__(self, game):
        self.game = game
        self.font_title = pygame.font.Font(None, 88)
        self.font_btn = pygame.font.Font(None, 38)
        self.font_small = pygame.font.Font(None, 22)
        self.selected = 0
        labels = ["Océan", "Jungle", "Espace", "Instructions", "Quitter"]
        self.actions = ["ocean", "jungle", "space", "instructions", "quit"]
        bw, bh, sy = 320, 54, 210
        self.buttons = [Button((W//2 - bw//2, sy + i*68, bw, bh), lab, self.font_btn)
                        for i, lab in enumerate(labels)]
        self.bg = pygame.Surface((W, H))
        self.bg.fill((18, 22, 30))

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.buttons)
            elif e.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.buttons)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate(self.selected)
            elif e.key == pygame.K_ESCAPE:
                self.game.running = False
        elif e.type == pygame.MOUSEMOTION:
            for i, b in enumerate(self.buttons):
                if b.hit(e.pos): self.selected = i
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, b in enumerate(self.buttons):
                if b.hit(e.pos): self._activate(i)

    def _activate(self, idx):
        act = self.actions[idx]
        if act == "ocean":
            from ocean import OceanGame
            self.game.go(OceanGame(self.game))
        elif act == "jungle":
            from jungle import JungleGame
            self.game.go(JungleGame(self.game))
        elif act == "space":
            from space import SpaceGame
            self.game.go(SpaceGame(self.game))
        elif act == "instructions":
            self.game.go(InstructionsState(self.game))
        else:
            self.game.running = False

    def draw(self, screen):
        screen.blit(self.bg, (0, 0))
        title = self.font_title.render("Eco Arcade", True, (255, 255, 255))
        screen.blit(title, (W//2 - title.get_width()//2, 80))
        sub = self.font_small.render("Édition Simplifiée", True, (70, 210, 140))
        screen.blit(sub, (W//2 - sub.get_width()//2, 158))
        for i, b in enumerate(self.buttons):
            b.draw(screen, selected=(i == self.selected))
        hint = self.font_small.render("↑↓ ou souris pour naviguer — Entrée pour lancer",
                                      True, (120, 125, 140))
        screen.blit(hint, (W//2 - hint.get_width()//2, H - 28))


class InstructionsState(State):
    def __init__(self, game):
        self.game = game
        self.font_t = pygame.font.Font(None, 50)
        self.font = pygame.font.Font(None, 26)

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            self.game.go(MenuState(self.game))

    def draw(self, screen):
        screen.fill((18, 22, 30))
        t = self.font_t.render("Instructions", True, (255, 255, 255))
        screen.blit(t, (W//2 - t.get_width()//2, 40))
        lines = [
            ("OCÉAN", True),
            ("← → : déplacer le bateau", False),
            ("ESPACE : lancer/rappeler le grappin", False),
            ("Attraper les déchets = +10 pts | Toucher un poisson = -1 vie", False),
            ("JUNGLE", True),
            ("← → : déplacer la voiture", False),
            ("Le bac collecte les déchets | Éviter les singes", False),
            ("ESPACE", True),
            ("← → : déplacer le vaisseau", False),
            ("ESPACE : tirer | Détruire les débris pour marquer des points", False),
            ("", False),
            ("P : Pause | ESC : menu", False),
        ]
        y = 110
        for txt, bold in lines:
            col = (70, 210, 140) if bold else (210, 215, 225)
            f = pygame.font.Font(None, 30) if bold else self.font
            screen.blit(f.render(txt, True, col), (80, y))
            y += 36
        hint = self.font.render("Appuie sur n'importe quelle touche pour revenir", True, (100, 105, 115))
        screen.blit(hint, (W//2 - hint.get_width()//2, H - 40))
