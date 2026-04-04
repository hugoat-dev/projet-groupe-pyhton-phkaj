import math

import pygame

from config import W, H, palette
from graphics import rounded_rect_surf, draw_glow
from ui import State


class PauseState(State):
    def __init__(self, game, under_state):
        super().__init__(game)
        self.under = under_state
        self.font = pygame.font.Font(None, 58)
        self.small = pygame.font.Font(None, 26)

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_p, pygame.K_ESCAPE):
                self.game.pop_state()
            elif e.key == pygame.K_m:
                from states.menu import MenuState
                self.game.transition_to(MenuState(self.game))

    def draw(self, screen):
        self.under.draw(screen)
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 165))
        screen.blit(ov, (0, 0))
        panel = rounded_rect_surf((540, 240), (255, 255, 255, 238), radius=18)
        screen.blit(panel, (W // 2 - 270, H // 2 - 120))
        t = self.font.render("PAUSE", True, (18, 22, 30))
        screen.blit(t, (W // 2 - t.get_width() // 2, H // 2 - 90))
        for i, txt in enumerate(["P / ESC : reprendre", "M : menu principal"]):
            r = self.small.render(txt, True, (18, 22, 30))
            screen.blit(r, (W // 2 - r.get_width() // 2, H // 2 + 15 + i * 34))


class EndState(State):
    def __init__(self, game, mode, score, details):
        super().__init__(game)
        self.mode = mode
        self.score = score
        self.details = details
        self.font = pygame.font.Font(None, 66)
        self.small = pygame.font.Font(None, 28)
        self.t = 0.0

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            from states.menu import MenuState
            self.game.transition_to(MenuState(self.game))

    def update(self, dt):
        self.t += dt

    def draw(self, screen):
        from config import save_now
        pal = palette(self.game.data["settings"]["color_mode"])
        screen.fill((8, 10, 16))
        for i in range(8):
            a = self.t * 0.5 + i * math.tau / 8
            x = W // 2 + int(math.cos(a) * 200)
            y = H // 2 + int(math.sin(a) * 120)
            draw_glow(screen, (x, y), 40, pal["accent"], 25)

        panel = rounded_rect_surf((740, 440), (255, 255, 255, 238), radius=20)
        screen.blit(panel, (80, 80))
        best = self.game.data["best"][self.mode]
        new_record = self.score > best
        if new_record:
            self.game.data["best"][self.mode] = self.score
            save_now(self.game.data)
            best = self.score

        title = self.font.render("Fin de partie", True, (15, 22, 38))
        screen.blit(title, (W // 2 - title.get_width() // 2, 100))

        if new_record:
            rec = pygame.font.Font(None, 34).render("★ NOUVEAU RECORD ★", True, (255, 200, 40))
            screen.blit(rec, (W // 2 - rec.get_width() // 2, 158))

        y = 220 if new_record else 200
        rows = [("Mode", self.mode.upper()), ("Score", str(self.score)), ("Meilleur", str(best))]
        for k, v in rows + list(self.details):
            col = pal["accent2"] if k == "Score" else pal["text"]
            r = self.small.render(f"{k} : {v}", True, col)
            screen.blit(r, (140, y))
            y += 36

        hint = pygame.font.Font(None, 24).render("ESC / Entrée : menu", True, pal["danger"])
        screen.blit(hint, (W // 2 - hint.get_width() // 2, 480))

