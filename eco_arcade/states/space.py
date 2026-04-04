import random

import pygame

from config import W, H, palette, clamp, lerp_col
from particles import FloatText, ScreenShake
from sprite_loader import load_sprite
from ui import State


class SpaceGameState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal = palette(game.data["settings"]["color_mode"])
        self.font = pygame.font.Font(None, 26)
        self.score_font = pygame.font.Font(None, 38)
        self.ship_img = load_sprite("ship")
        self.laser_img = load_sprite("laser")
        self.ship_x, self.ship_y = W * 0.5, H - 95
        self.vx, self.acc, self.drag, self.maxv = 0.0, 1250.0, 10.0, 300.0
        self.lasers, self.cool = [], 0.0
        self.energy, self.energy_max = 100.0, 100.0
        self.energy_regen, self.shot_cost = 28.0, 12.0
        self.debris, self.float_texts = [], []
        self.shake = ScreenShake()
        self.spawn_t, self.diff = 0.0, 0.0
        self.score, self.lives, self.time_left = 0, 3, 60.0
        self.stars_layers = [
            [{"x": random.uniform(0, W), "y": random.uniform(0, H), "r": 1,
              "sp": 20 + random.uniform(0, 10)} for _ in range(100)],
            [{"x": random.uniform(0, W), "y": random.uniform(0, H), "r": 1,
              "sp": 50 + random.uniform(0, 20)} for _ in range(60)],
            [{"x": random.uniform(0, W), "y": random.uniform(0, H), "r": 2,
              "sp": 90 + random.uniform(0, 30)} for _ in range(25)],
        ]

    def _spawn_debris(self):
        sz = random.choices(["small", "medium", "large"], weights=[0.6, 0.3, 0.1])[0]
        hp = {"small": 1, "medium": 2, "large": 3}[sz]
        self.debris.append({
            "sz": sz, "hp": hp, "max_hp": hp,
            "img": load_sprite(f"debris_{sz}"),
            "x": random.uniform(40, W - 40), "y": -65,
            "vx": random.uniform(-12, 12),
            "vy": random.uniform(55, 105 + self.diff * 2),
            "rot": random.uniform(0, 360), "rots": random.uniform(-65, 65)
        })

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p:
                from states.pause import PauseState
                self.game.push_state(PauseState(self.game, self))
            elif e.key == pygame.K_ESCAPE:
                from states.menu import MenuState
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
        self.shake.update(dt)

        if self.time_left <= 0 or self.lives <= 0:
            from states.pause import EndState
            self.game.transition_to(EndState(self.game, "space", self.score,
                [("Débris détruits", self.score), ("Vies restantes", self.lives)]))
            return

        for layer in self.stars_layers:
            for s in layer:
                s["y"] += s["sp"] * dt
                if s["y"] > H:
                    s["y"] = -5
                    s["x"] = random.uniform(0, W)

        keys = pygame.key.get_pressed()
        ax = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: ax -= self.acc
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: ax += self.acc
        self.vx += ax * dt
        self.vx -= self.vx * self.drag * dt
        self.vx = clamp(self.vx, -self.maxv, self.maxv)
        self.ship_x = clamp(self.ship_x + self.vx * dt, 40, W - 40)

        self.energy = min(self.energy_max, self.energy + self.energy_regen * dt)
        if self.cool > 0: self.cool -= dt
        for l in self.lasers[:]:
            l[1] -= 560 * dt
            if l[1] < -20: self.lasers.remove(l)

        ship_rect = pygame.Rect(self.ship_x - 25, self.ship_y - 20, 50, 60)
        for d in self.debris[:]:
            d["y"] += d["vy"] * dt
            d["x"] += d["vx"] * dt
            d["rot"] += d["rots"] * dt
            d_rect = pygame.Rect(0, 0, d["img"].get_width(), d["img"].get_height())
            d_rect.center = (int(d["x"]), int(d["y"]))

            hit = False
            for l in self.lasers[:]:
                if d_rect.collidepoint((int(l[0]), int(l[1]))):
                    if l in self.lasers: self.lasers.remove(l)
                    d["hp"] -= 1
                    hit = True
                    if d["hp"] <= 0:
                        pts = 1 if d["sz"] == "small" else 2 if d["sz"] == "medium" else 3
                        self.score += pts
                        self.float_texts.append(FloatText(d["x"], d["y"], f"+{pts}",
                                                          self.pal["accent2"], font=self.score_font))
                        if d in self.debris: self.debris.remove(d)
                        break
            if hit and d not in self.debris: continue
            if d_rect.colliderect(ship_rect):
                self.lives -= 1
                self.shake.shake(0.8)
                if d in self.debris: self.debris.remove(d)
            elif d["y"] > H + 50:
                if d in self.debris: self.debris.remove(d)

        self.spawn_t += dt
        if self.spawn_t >= max(0.38, 1.2 - self.diff * 0.02):
            self.spawn_t = 0.0
            self._spawn_debris()

        for ft in self.float_texts[:]: ft.update(dt)
        self.float_texts = [ft for ft in self.float_texts if not ft.dead()]

    def draw(self, screen):
        ox, oy = self.shake.offset()
        screen.fill((8, 10, 18))

        star_cols = [(200, 200, 200), (230, 230, 240), (255, 255, 255)]
        for li, layer in enumerate(self.stars_layers):
            col = star_cols[li]
            for s in layer:
                r = s["r"]
                pygame.draw.circle(screen, col, (int(s["x"] + ox), int(s["y"] + oy)), r)

        for l in self.lasers:
            screen.blit(self.laser_img, (int(l[0] + ox), int(l[1] + oy)))

        screen.blit(self.ship_img, (int(self.ship_x - 28 + ox), int(self.ship_y - 35 + oy)))

        for d in self.debris:
            img = pygame.transform.rotate(d["img"], d["rot"])
            cx, cy = int(d["x"] + ox), int(d["y"] + oy)
            screen.blit(img, img.get_rect(center=(cx, cy)))
            if d["max_hp"] > 1:
                bw = img.get_width()
                pct = d["hp"] / d["max_hp"]
                pygame.draw.rect(screen, (80, 80, 80),
                                 (cx - bw // 2, cy - img.get_height() // 2 - 10, bw, 5), border_radius=2)
                pygame.draw.rect(screen, lerp_col((255, 60, 60), (70, 210, 140), pct),
                                 (cx - bw // 2, cy - img.get_height() // 2 - 10, int(bw * pct), 5), border_radius=2)

        for ft in self.float_texts: ft.draw(screen)

        # HUD
        bar = pygame.Surface((W, 70), pygame.SRCALPHA)
        pygame.draw.rect(bar, (255, 255, 255, 25), bar.get_rect())
        screen.blit(bar, (0, 0))
        screen.blit(self.font.render(f"Score: {self.score}", True, (255, 255, 255)), (20, 18))
        screen.blit(self.font.render(f"Vie: {self.lives}", True, self.pal["danger"]), (W - 100, 18))

        pygame.draw.rect(screen, (45, 45, 55), (W // 2 - 105, 22, 210, 18), border_radius=9)
        pct = self.energy / self.energy_max
        ecol = self.pal["accent"] if pct > 0.3 else self.pal["danger"]
        pygame.draw.rect(screen, ecol, (W // 2 - 103, 24, int(206 * pct), 14), border_radius=7)
        screen.blit(self.font.render("NRJ", True, (200, 200, 210)), (W // 2 - 135, 20))

        tpct = self.time_left / 60.0
        pygame.draw.rect(screen, (45, 45, 55), (W - 30, 20, 14, H - 40), border_radius=7)
        fill_h = int((H - 40) * tpct)
        pygame.draw.rect(screen, lerp_col((255, 60, 60), (70, 210, 140), tpct),
                         (W - 30, 20 + (H - 40) - fill_h, 14, fill_h), border_radius=7)
