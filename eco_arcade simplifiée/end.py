import pygame
from config import W, H, save_now
from ui import State


class PauseState(State):
    def __init__(self, game, under):
        self.game = game
        self._under = under
        self.font = pygame.font.Font(None, 64)
        self.small = pygame.font.Font(None, 28)

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_p, pygame.K_ESCAPE):
                self.game.pop()
            elif e.key == pygame.K_m:
                from menu import MenuState
                self.game.go(MenuState(self.game))

    def draw(self, screen):
        self._under.draw(screen)
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        screen.blit(ov, (0, 0))
        t = self.font.render("PAUSE", True, (255, 255, 255))
        screen.blit(t, (W//2 - t.get_width()//2, H//2 - 60))
        for i, txt in enumerate(["P / ESC : reprendre", "M : menu principal"]):
            r = self.small.render(txt, True, (200, 205, 215))
            screen.blit(r, (W//2 - r.get_width()//2, H//2 + 10 + i*36))


class EndState(State):
    def __init__(self, game, mode, score, details):
        self.game = game
        self.mode = mode
        self.score = score
        self.details = details
        self.font = pygame.font.Font(None, 64)
        self.small = pygame.font.Font(None, 30)
        best = game.data["best"].get(mode, 0)
        if score > best:
            game.data["best"][mode] = score
            save_now(game.data)
        self.best = game.data["best"][mode]

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
            from menu import MenuState
            self.game.go(MenuState(self.game))

    def draw(self, screen):
        screen.fill((12, 14, 20))
        t = self.font.render("Fin de partie", True, (255, 255, 255))
        screen.blit(t, (W//2 - t.get_width()//2, 80))
        y = 180
        rows = [("Mode", self.mode.upper()), ("Score", str(self.score)),
                ("Meilleur", str(self.best))] + list(self.details)
        for k, v in rows:
            col = (70, 210, 140) if k == "Score" else (210, 215, 225)
            r = self.small.render(f"{k} :  {v}", True, col)
            screen.blit(r, (W//2 - r.get_width()//2, y))
            y += 44
        if self.score >= self.best and self.score > 0:
            rec = pygame.font.Font(None, 36).render("★ NOUVEAU RECORD ★", True, (255, 210, 40))
            screen.blit(rec, (W//2 - rec.get_width()//2, y + 10))
        hint = self.small.render("ESC / Entrée : retour au menu", True, (100, 105, 115))
        screen.blit(hint, (W//2 - hint.get_width()//2, H - 50))
