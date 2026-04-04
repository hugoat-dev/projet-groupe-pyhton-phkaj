import math
import random

import pygame

from config import W, H, palette, clamp, lerp_col
from graphics import vertical_gradient
from particles import Particle, FloatText, ScreenShake
from sprite_loader import load_sprite
from ui import State


class JungleGameState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal = palette(game.data["settings"]["color_mode"])
        self.font = pygame.font.Font(None, 26)
        self.score_font = pygame.font.Font(None, 36)
        self.bg_sky = vertical_gradient((W, H), (50, 170, 90), (18, 70, 42))
        self.parallax = [
            {"surf": self._make_treeline(W, H, 0.45, (18,80,38), (25,100,48), 80, 50),  "x": 0.0, "sp": 20},
            {"surf": self._make_treeline(W, H, 0.55, (28,110,52), (38,140,62), 60, 40), "x": 0.0, "sp": 50},
            {"surf": self._make_treeline(W, H, 0.68, (35,130,60), (50,165,75), 45, 30), "x": 0.0, "sp": 90},
        ]
        self.road_w = int(W * 0.52)
        self.road_x = W // 2 - self.road_w // 2
        self.scroll = 0.0
        self.car_img = load_sprite("car")
        self.monkey_img = load_sprite("monkey")
        self.car_x, self.car_y = W * 0.5, H - 120
        self.car_vx, self.acc, self.drag, self.maxv = 0.0, 2200.0, 9.0, 560.0
        self.trash, self.monkeys = [], []
        self.fx, self.float_texts = [], []
        self.shake = ScreenShake()
        self.spawn_t, self.diff = 0.0, 0.0
        self.score, self.lives, self.time_left = 0, 3, 70.0
        self.inv_t, self.knock_v = 0.0, 0.0
        for _ in range(4): self._spawn_trash(y=random.uniform(-250, -40))

    def _make_treeline(self, w, h, horizon_frac, col1, col2, tree_w, tree_h):
        surf = pygame.Surface((w * 2, h), pygame.SRCALPHA)
        horizon_y = int(h * horizon_frac)
        pygame.draw.rect(surf, col1, (0, horizon_y, w * 2, h - horizon_y))
        for x in range(0, w * 2, tree_w + random.randint(5, 20)):
            bh = random.randint(int(tree_h * 0.7), tree_h)
            bx = x + random.randint(-10, 10)
            pygame.draw.rect(surf, (80, 50, 25), (bx + tree_w // 2 - 4, horizon_y - bh + bh // 2, 8, bh // 2 + 20))
            for i in range(3):
                r = tree_w // 2 + i * 6
                cy = horizon_y - bh + i * bh // 4
                pygame.draw.circle(surf, col2, (bx + tree_w // 2, cy), r)
                pygame.draw.circle(surf, col1, (bx + tree_w // 2, cy), r, 2)
        return surf.convert_alpha()

    def _spawn_trash(self, y=None):
        k = random.choice(["bottle", "can", "bag", "tire", "box"])
        x = random.uniform(self.road_x + 60, self.road_x + self.road_w - 60)
        self.trash.append({
            "k": k, "x": x, "y": -40 if y is None else y,
            "rot": random.uniform(0, 360), "rots": random.uniform(-45, 45),
            "img": load_sprite(f"trash_{k}", (52, 52))
        })

    def _spawn_monkey(self):
        x = random.uniform(self.road_x + 70, self.road_x + self.road_w - 70)
        self.monkeys.append({"x": x, "y": -50, "t": random.uniform(0, 10), "img": self.monkey_img})

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p:
                from states.pause import PauseState
                self.game.push_state(PauseState(self.game, self))
            elif e.key == pygame.K_ESCAPE:
                from states.menu import MenuState
                self.game.transition_to(MenuState(self.game))

    def update(self, dt):
        self.pal = palette(self.game.data["settings"]["color_mode"])
        self.time_left -= dt
        if self.inv_t > 0: self.inv_t -= dt
        self.shake.update(dt)

        if self.time_left <= 0 or self.lives <= 0:
            from states.pause import EndState
            self.game.transition_to(EndState(self.game, "jungle", self.score,
                [("Déchets collectés", self.score), ("Vies restantes", self.lives)]))
            return

        self.diff += dt
        speed = 142.0 + self.diff * 2.0

        keys = pygame.key.get_pressed()
        ax = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: ax -= self.acc
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: ax += self.acc
        self.car_vx += ax * dt
        self.car_vx -= self.car_vx * self.drag * dt
        if abs(self.knock_v) > 1:
            self.car_vx += self.knock_v
            self.knock_v *= (1.0 - 7.0 * dt)
        self.car_x = clamp(self.car_x + self.car_vx * dt, self.road_x + 100, self.road_x + self.road_w - 100)
        self.scroll = (self.scroll + speed * dt) % 50

        for layer in self.parallax:
            layer["x"] = (layer["x"] - layer["sp"] * dt) % W

        car_rect = pygame.Rect(0, 0, 180, 135)
        car_rect.center = (int(self.car_x), int(self.car_y))
        bin_rect = pygame.Rect(car_rect.left + 30, car_rect.top + 2, car_rect.width - 60, 28)

        for t in self.trash[:]:
            t["y"] += speed * dt
            t["rot"] += t["rots"] * dt
            tr = pygame.Rect(0, 0, 52, 52)
            tr.center = (int(t["x"]), int(t["y"]))
            if bin_rect.colliderect(tr):
                self.score += 1
                self.float_texts.append(FloatText(t["x"], t["y"] - 20, "+1", self.pal["accent"], font=self.score_font))
                for _ in range(5):
                    self.fx.append(Particle(t["x"], t["y"], random.uniform(-40, 40), random.uniform(-50, -10),
                                            0.4, 0, "collect", 3, self.pal["accent"], gravity=50))
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
                self.shake.shake(0.6)
                self.knock_v = 145 if self.car_x < m["x"] else -145
                for _ in range(14):
                    self.fx.append(Particle(m["x"], m["y"], random.uniform(-70, 70), random.uniform(-70, 20),
                                            0.55, 0, "boom", 4, self.pal["danger"], gravity=80))
                self.monkeys.remove(m)
            elif m["y"] > H + 70:
                self.monkeys.remove(m)

        self.spawn_t += dt
        if self.spawn_t >= max(0.55, 1.05 - self.diff * 0.01):
            self.spawn_t = 0.0
            if random.random() < 0.72 and len(self.trash) < 10: self._spawn_trash()
            if random.random() < (0.25 + self.diff * 0.002) and len(self.monkeys) < 7: self._spawn_monkey()

        for p in self.fx[:]: p.update(dt)
        self.fx = [p for p in self.fx if not p.dead()]
        for ft in self.float_texts[:]: ft.update(dt)
        self.float_texts = [ft for ft in self.float_texts if not ft.dead()]

    def draw(self, screen):
        ox, oy = self.shake.offset()
        screen.blit(self.bg_sky, (int(ox), int(oy)))

        for layer in self.parallax:
            for rep in range(3):
                x = int(layer["x"] + ox - W + rep * W)
                screen.blit(layer["surf"], (x, int(oy)))

        # Route
        pygame.draw.rect(screen, (42, 42, 50), (int(self.road_x + ox), int(oy), self.road_w, H))

        # Bandes latérales jaunes (bord de route)
        for bx in [self.road_x, self.road_x + self.road_w - 8]:
            pygame.draw.rect(screen, (210, 170, 20), (int(bx + ox), 0, 8, H))

        # Lignes de bord blanches
        for bx in [self.road_x + 8, self.road_x + self.road_w - 10]:
            pygame.draw.line(screen, (255, 255, 255), (int(bx + ox), 0), (int(bx + ox), H), 2)

        # Tirets centraux qui défilent — espacement variable pour l'effet de perspective
        dash_h = 36
        gap = 50
        for y in range(int(-self.scroll % (dash_h + gap)), H + dash_h, dash_h + gap):
            # les tirets sont plus courts en haut (loin) et plus longs en bas (proche)
            t_persp = y / H
            w_dash = int(8 + t_persp * 6)
            h_dash = int(dash_h * (0.5 + t_persp * 0.8))
            pygame.draw.rect(screen, (240, 240, 245),
                             (int(W // 2 - w_dash // 2 + ox), int(y + oy), w_dash, h_dash),
                             border_radius=3)

        # Marquages latéraux qui défilent (chevrons de bord)
        for y in range(int(-self.scroll % 80), H + 40, 80):
            for bx, direction in [(self.road_x + 14, 1), (self.road_x + self.road_w - 22, -1)]:
                pts = [(int(bx + ox), int(y + oy)),
                       (int(bx + direction * 10 + ox), int(y + 18 + oy)),
                       (int(bx + ox), int(y + 36 + oy))]
                pygame.draw.lines(screen, (180, 180, 190), False, pts, 2)

        for t in self.trash:
            img = pygame.transform.rotate(t["img"], t["rot"])
            screen.blit(img, img.get_rect(center=(int(t["x"] + ox), int(t["y"] + oy))))

        for m in self.monkeys:
            bob = math.sin(m["t"] * 6) * 2
            screen.blit(m["img"], (int(m["x"] - 27 + ox), int(m["y"] - 27 + bob + oy)))

        for p in self.fx: p.draw(screen)

        if self.inv_t <= 0 or (int(self.inv_t * 14) % 2 == 0):
            screen.blit(self.car_img, (int(self.car_x - 90 + ox), int(self.car_y - 67 + oy)))

        for ft in self.float_texts: ft.draw(screen)

        # HUD
        bar = pygame.Surface((W, 68), pygame.SRCALPHA)
        pygame.draw.rect(bar, (255, 255, 255, 215), bar.get_rect())
        screen.blit(bar, (0, 0))
        screen.blit(self.font.render(f"Score: {self.score}", True, self.pal["text"]), (14, 10))
        screen.blit(self.font.render(f"Vie: {self.lives}", True, self.pal["danger"]), (W - 120, 10))
        tpct = self.time_left / 70.0
        pygame.draw.rect(screen, (220, 220, 225), (W // 2 - 100, 48, 200, 12), border_radius=6)
        pygame.draw.rect(screen, lerp_col((255, 60, 60), (70, 210, 140), tpct),
                         (W // 2 - 100, 48, int(200 * tpct), 12), border_radius=6)
        screen.blit(self.font.render(f"{int(self.time_left)}s", True, self.pal["text"]), (W // 2 + 108, 40))
