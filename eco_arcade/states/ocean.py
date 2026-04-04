import math
import random

import pygame

from config import W, H, palette, clamp, lerp_col
from graphics import vertical_gradient
from particles import Particle, FloatText, ScreenShake
from sprite_loader import load_sprite
from ui import State

_FISH_VARIANTS = ["orange", "blue", "purple"]  # jaune et rouge supprimés


class OceanGameState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal = palette(game.data["settings"]["color_mode"])
        self.font = pygame.font.Font(None, 26)
        self.score_font = pygame.font.Font(None, 36)
        self.surface_y = 125
        self.bg_deep = vertical_gradient((W, H), (60, 170, 230), (12, 50, 125))
        self.boat_img = load_sprite("boat")
        self.gr_img = load_sprite("grapple")
        self.boat_x, self.boat_y = W * 0.5, 60
        self.boat_vx = 0.0
        self.gr_active, self.gr_state = False, "idle"
        self.gr_y = self.boat_y + 44
        self.gr_speed = 225.0
        self.gr_max_depth = H - 85
        self.gr_caught = None
        self.trash, self.fish = [], []
        self.bubbles = []
        self.seaweeds = []
        self.splashes = []
        self.fx = []
        self.float_texts = []
        self.shake = ScreenShake()
        self.spawn_t = 0.0
        self.collected, self.impacts, self.lives, self.time_left = 0, 0, 10, 75.0
        self.impact_threshold, self.next_impact_loss, self.flash_t = 3, 3, 0.0
        self.wave_t = 0.0
        self.caustic_t = 0.0
        self.inv_frames = 0.0
        self.trash_limit = 3          # limite de déchets, augmente toutes les 10s
        self.trash_scale_t = 0.0      # timer pour la progression des déchets
        for _ in range(12):
            self.seaweeds.append({
                "x": random.uniform(0, W), "ph": random.uniform(0, math.tau),
                "h": random.uniform(25, 55),
                "col": random.choice([(40, 150, 80), (30, 120, 65), (55, 170, 90)])
            })
        for _ in range(2): self._spawn_trash(x=random.uniform(0, W))
        for _ in range(3): self._spawn_fish()
        for _ in range(20):
            self.bubbles.append({
                "x": random.uniform(0, W), "y": random.uniform(self.surface_y, H),
                "r": random.uniform(2, 6), "sp": random.uniform(18, 40), "ph": random.uniform(0, math.tau)
            })

    def _spawn_trash(self, x=None):
        k = random.choice(["bottle", "can", "bag", "tire", "box"])
        y = random.uniform(self.surface_y + 40, H - 55)
        self.trash.append({
            "k": k, "x": -40 if x is None else x, "y": y,
            "vx": random.uniform(48, 90),  # gauche → droite
            "t": random.uniform(0, 10),
            "rot": random.uniform(0, 360), "rots": random.uniform(-28, 28),
            "img": load_sprite(f"trash_{k}", (55, 55))
        })

    def _spawn_fish(self, x=None):
        y = random.uniform(self.surface_y + 35, H - 50)
        variant = random.choice(_FISH_VARIANTS)
        # poissons droite → gauche
        self.fish.append({
            "x": W + 40 if x is None else x, "y": y,
            "vx": -random.uniform(72, 125), "t": random.uniform(0, 10),
            "img": load_sprite(f"fish_{variant}"), "bob": random.uniform(0, math.tau)
        })

    def _splash(self, x, y):
        for _ in range(8):
            ang = random.uniform(-math.pi, 0)
            sp = random.uniform(40, 120)
            self.splashes.append(
                Particle(x, y, math.cos(ang) * sp, math.sin(ang) * sp, 0.4, 0, "splash", 3,
                         (190, 230, 255), gravity=180))

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p:
                from states.pause import PauseState
                self.game.push_state(PauseState(self.game, self))
            elif e.key == pygame.K_ESCAPE:
                from states.menu import MenuState
                self.game.transition_to(MenuState(self.game))
            elif e.key == pygame.K_SPACE:
                if not self.gr_active:
                    self.gr_active = True
                    self.gr_state = "down"
                    self.gr_y = self.boat_y + 44
                    self.gr_caught = None
                    self._splash(self.boat_x, self.surface_y)
                elif self.gr_state == "down":
                    self.gr_state = "up"  # rappui → remonte immédiatement

    def update(self, dt):
        self.pal = palette(self.game.data["settings"]["color_mode"])
        self.time_left -= dt
        self.wave_t += dt
        self.caustic_t += dt * 0.7
        if self.flash_t > 0: self.flash_t -= dt
        if self.inv_frames > 0: self.inv_frames -= dt
        self.shake.update(dt)

        if self.time_left <= 0 or self.lives <= 0:
            from states.pause import EndState
            score = max(0, self.collected * 10 - self.impacts * 3)
            self.game.transition_to(EndState(self.game, "ocean", score,
                [("Déchets récupérés", self.collected), ("Poissons impactés", self.impacts)]))
            return

        keys = pygame.key.get_pressed()
        ax = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: ax -= 1300.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: ax += 1300.0
        self.boat_vx += ax * dt
        self.boat_vx -= self.boat_vx * 7.5 * dt
        self.boat_vx = clamp(self.boat_vx, -320, 320)
        self.boat_x = clamp(self.boat_x + self.boat_vx * dt, 70, W - 70)

        gr_x = self.boat_x
        if self.gr_active:
            if self.gr_state == "down":
                self.gr_y += self.gr_speed * dt
                if self.gr_y >= self.gr_max_depth: self.gr_state = "up"
                if self.gr_caught is None:
                    for t in self.trash:
                        if (gr_x - t["x"]) ** 2 + (self.gr_y - t["y"]) ** 2 < 28 ** 2:
                            self.gr_caught = t
                            self.gr_state = "up"
                            break
                for f in self.fish:
                    if (gr_x - f["x"]) ** 2 + (self.gr_y - f["y"]) ** 2 < 26 ** 2:
                        self.lives -= 1
                        self.flash_t = 0.5
                        self.shake.shake(0.5)
                        self.gr_state = "up"
                        break
            elif self.gr_state == "up":
                self.gr_y -= self.gr_speed * dt
                if self.gr_caught:
                    self.gr_caught["x"] = gr_x
                    self.gr_caught["y"] = self.gr_y + 18
                if self.gr_y <= self.boat_y + 44:
                    self.gr_active = False
                    self.gr_state = "idle"
                    if self.gr_caught:
                        if self.gr_caught in self.trash: self.trash.remove(self.gr_caught)
                        self.collected += 1
                        self.float_texts.append(FloatText(gr_x, self.boat_y - 20, "+10",
                                                          self.pal["accent"], font=self.score_font))
                        for _ in range(10):
                            self.fx.append(Particle(gr_x, self.boat_y,
                                random.uniform(-60, 60), random.uniform(-80, -20),
                                0.5, 0, "collect", 3, self.pal["accent"], gravity=60))
                        self.gr_caught = None

        for t in self.trash[:]:
            if t is self.gr_caught: continue
            t["x"] += t["vx"] * dt
            t["t"] += dt
            t["rot"] += t["rots"] * dt
            if t["x"] > W + 80:  # sort à droite
                self.trash.remove(t)
                continue
            for f in self.fish:
                if (t["x"] - f["x"]) ** 2 + (t["y"] - f["y"]) ** 2 < 50 ** 2:  # hitbox agrandie
                    self.impacts += 1
                    if t in self.trash: self.trash.remove(t)
                    for _ in range(6):
                        self.fx.append(Particle(t["x"], t["y"],
                            random.uniform(-50, 50), random.uniform(-50, 50),
                            0.4, 0, "impact", 2, (255, 150, 50)))
                    break

        for f in self.fish[:]:
            f["x"] += f["vx"] * dt
            f["t"] += dt
            f["bob"] += dt * 2.2
            if f["x"] < -80: self.fish.remove(f)  # sortie à gauche

        if self.impacts >= self.next_impact_loss:
            self.lives -= 1
            self.flash_t = 0.6
            self.shake.shake(0.4)
            self.next_impact_loss += self.impact_threshold

        # progression des déchets : +50% toutes les 10s
        self.trash_scale_t += dt
        if self.trash_scale_t >= 10.0:
            self.trash_scale_t = 0.0
            self.trash_limit = int(self.trash_limit * 1.5)

        self.spawn_t += dt
        if self.spawn_t >= 1.25:
            self.spawn_t = 0.0
            if len(self.trash) < self.trash_limit: self._spawn_trash()
            if len(self.fish) < 6: self._spawn_fish()  # 1.5x plus de poissons

        for b in self.bubbles:
            b["y"] -= b["sp"] * dt
            b["x"] += math.sin(b["ph"] + self.wave_t * 1.2) * 14 * dt
            if b["y"] < self.surface_y:
                b["y"] = random.uniform(H - 100, H)
                b["x"] = random.uniform(0, W)

        for p in self.fx[:] + self.splashes[:]: p.update(dt)
        self.fx = [p for p in self.fx if not p.dead()]
        self.splashes = [p for p in self.splashes if not p.dead()]
        for ft in self.float_texts[:]: ft.update(dt)
        self.float_texts = [ft for ft in self.float_texts if not ft.dead()]

    def _draw_animated_water(self, screen):
        pts = [(0, H)]
        for x in range(0, W + 4, 4):
            y = self.surface_y + int(math.sin(x * 0.018 + self.wave_t * 2.2) * 5
                                     + math.sin(x * 0.035 + self.wave_t * 1.4) * 3)
            pts.append((x, y))
        pts.append((W, H))
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (60, 170, 230, 180), pts)
        screen.blit(surf, (0, 0))
        wave_pts = []
        for x in range(0, W + 2, 2):
            y = self.surface_y + int(math.sin(x * 0.018 + self.wave_t * 2.2) * 5
                                     + math.sin(x * 0.035 + self.wave_t * 1.4) * 3)
            wave_pts.append((x, y))
        if len(wave_pts) > 1:
            pygame.draw.lines(screen, (200, 240, 255), False, wave_pts, 3)

    def _draw_caustics(self, screen):
        for i in range(5):
            x = int((W / 5) * i + W / 10 + math.sin(self.caustic_t + i * 1.3) * 30)
            y = int(self.surface_y + 60 + math.cos(self.caustic_t * 0.8 + i * 0.9) * 25)
            size = int(20 + math.sin(self.caustic_t * 1.5 + i) * 8)
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (255, 255, 200, 18), (0, 0, size * 2, size * 2))
            screen.blit(s, (x - size, y - size))

    def draw(self, screen):
        ox, oy = self.shake.offset()

        screen.blit(self.bg_deep, (int(ox), int(oy)))
        pygame.draw.rect(screen, (160, 215, 255), (int(ox), int(oy), W, self.surface_y))

        wt = self.wave_t
        for sw in self.seaweeds:
            bx, by = int(sw["x"] + ox), H + int(oy)
            pts = []
            for i in range(9):
                t2 = i / 8
                sway = math.sin(wt * 1.8 + sw["ph"] + t2 * 3) * 10 * t2
                pts.append((bx + int(sway), by - int(sw["h"] * t2)))
            if len(pts) > 1:
                pygame.draw.lines(screen, sw["col"], False, pts, 3)

        self._draw_caustics(screen)
        self._draw_animated_water(screen)

        for b in self.bubbles:
            pygame.draw.circle(screen, (220, 248, 255), (int(b["x"] + ox), int(b["y"] + oy)), int(b["r"]), 1)

        for f in self.fish:
            bob = math.sin(f["bob"]) * 4
            screen.blit(f["img"], (int(f["x"] - 24 + ox), int(f["y"] - 16 + bob + oy)))

        for t in self.trash:
            img = pygame.transform.rotate(t["img"], t["rot"])
            bob = math.sin(t["t"] * 1.6) * 2
            screen.blit(img, img.get_rect(center=(int(t["x"] + ox), int(t["y"] + bob + oy))))

        if self.gr_active:
            gr_x, gr_y = int(self.boat_x + ox), int(self.gr_y + oy)
            by = int(self.boat_y + 44 + oy)
            pts = []
            for i in range(13):
                frac = i / 12
                cx = int(self.boat_x + ox) + int(math.sin(frac * math.pi + self.wave_t * 4) * 5 * (1 - frac))
                cy = by + int((gr_y - by) * frac)
                pts.append((cx, cy))
            if len(pts) > 1:
                pygame.draw.lines(screen, (100, 100, 112), False, pts, 2)
            screen.blit(self.gr_img, (gr_x - 17, gr_y - 17))

        for p in self.splashes + self.fx: p.draw(screen)
        screen.blit(self.boat_img, (int(self.boat_x - 48 + ox), int(self.boat_y - 28 + oy)))
        for ft in self.float_texts: ft.draw(screen)

        # HUD
        bar = pygame.Surface((W, 72), pygame.SRCALPHA)
        pygame.draw.rect(bar, (255, 255, 255, 215), bar.get_rect())
        screen.blit(bar, (0, 0))
        c1 = self.pal["text"]
        c2 = self.pal["danger"] if self.flash_t > 0 else self.pal["text"]
        tpct = self.time_left / 75.0
        pygame.draw.rect(screen, (220, 220, 225), (W // 2 - 100, 50, 200, 12), border_radius=6)
        pygame.draw.rect(screen, lerp_col((255, 60, 60), (70, 210, 140), tpct),
                         (W // 2 - 100, 50, int(200 * tpct), 12), border_radius=6)
        screen.blit(self.font.render(f"Déchets: {self.collected}", True, c1), (14, 10))
        screen.blit(self.font.render(f"Impacts: {self.impacts}", True, c1), (14, 38))
        screen.blit(self.font.render(f"Vie: {self.lives}", True, c2), (W - 120, 10))
        screen.blit(self.font.render(f"{int(self.time_left)}s", True, c1), (W - 80, 38))
