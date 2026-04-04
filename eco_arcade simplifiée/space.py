import random
import pygame
from config import W, H, clamp, lerp_col, sprite
from ui import State


class SpaceGame(State):
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 28)

        # fond étoilé statique
        self.bg = pygame.Surface((W, H))
        self.bg.fill((8, 10, 18))
        for _ in range(180):
            x, y = random.randint(0, W), random.randint(0, H)
            r = random.choice([1, 1, 1, 2])
            c = random.randint(180, 255)
            pygame.draw.circle(self.bg, (c, c, c), (x, y), r)

        self.ship_img = sprite("ship")
        self.laser_img = sprite("laser")

        self.ship_x = float(W // 2)
        self.vx = 0.0

        self.lasers = []
        self.cool = 0.0
        self.energy = 100.0

        self.debris = []
        self.float_texts = []

        self.score = 0
        self.lives = 3
        self.time_left = 60.0
        self.diff = 0.0
        self.spawn_t = 0.0

    def _spawn_debris(self):
        sz = random.choices(["small", "medium", "large"], weights=[0.6, 0.3, 0.1])[0]
        hp = {"small": 1, "medium": 2, "large": 3}[sz]
        self.debris.append({
            "sz": sz, "hp": hp, "max_hp": hp,
            "img": sprite(f"debris_{sz}"),
            "x": random.uniform(40, W-40), "y": -60.0,
            "vx": random.uniform(-15, 15),
            "vy": random.uniform(60, 110 + self.diff*2),
            "rot": random.uniform(0, 360), "rots": random.uniform(-60, 60)
        })

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                from menu import MenuState
                self.game.go(MenuState(self.game))
            elif e.key == pygame.K_p:
                from end import PauseState
                self.game.push(PauseState(self.game, self))
            elif e.key == pygame.K_SPACE and self.cool <= 0 and self.energy >= 12:
                self.energy -= 12
                self.cool = 0.2
                self.lasers.append([self.ship_x - 18, self.ship_y + 10])
                self.lasers.append([self.ship_x + 18, self.ship_y + 10])

    @property
    def ship_y(self): return H - 95

    def update(self, dt):
        self.time_left -= dt
        self.diff += dt

        if self.time_left <= 0 or self.lives <= 0:
            from end import EndState
            self.game.go(EndState(self.game, "space", self.score,
                                  [("Débris détruits", self.score)]))
            return

        keys = pygame.key.get_pressed()
        ax = (-1250 if (keys[pygame.K_LEFT] or keys[pygame.K_a]) else 0) + \
             (1250 if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) else 0)
        self.vx = clamp(self.vx * (1 - 10*dt) + ax*dt, -300, 300)
        self.ship_x = clamp(self.ship_x + self.vx*dt, 40, W-40)

        self.energy = min(100, self.energy + 28*dt)
        if self.cool > 0: self.cool -= dt

        for l in self.lasers[:]:
            l[1] -= 560 * dt
            if l[1] < -20: self.lasers.remove(l)

        ship_rect = pygame.Rect(self.ship_x-25, self.ship_y-20, 50, 60)
        for d in self.debris[:]:
            d["x"] += d["vx"] * dt
            d["y"] += d["vy"] * dt
            d["rot"] += d["rots"] * dt
            dr = pygame.Rect(0, 0, d["img"].get_width(), d["img"].get_height())
            dr.center = (int(d["x"]), int(d["y"]))
            hit = False
            for l in self.lasers[:]:
                if dr.collidepoint(int(l[0]), int(l[1])):
                    if l in self.lasers: self.lasers.remove(l)
                    d["hp"] -= 1
                    hit = True
                    if d["hp"] <= 0:
                        pts = {"small":1,"medium":2,"large":3}[d["sz"]]
                        self.score += pts
                        self.float_texts.append([d["x"], d["y"], f"+{pts}", 0.0, (255,220,60)])
                        if d in self.debris: self.debris.remove(d)
                    break
            if hit and d not in self.debris: continue
            if dr.colliderect(ship_rect):
                self.lives -= 1
                if d in self.debris: self.debris.remove(d)
            elif d["y"] > H + 50:
                if d in self.debris: self.debris.remove(d)

        self.spawn_t += dt
        if self.spawn_t >= max(0.4, 1.2 - self.diff*0.02):
            self.spawn_t = 0.0
            self._spawn_debris()

        for ft in self.float_texts[:]:
            ft[1] -= 45 * dt
            ft[3] += dt
            if ft[3] > 1.0: self.float_texts.remove(ft)

    def draw(self, screen):
        screen.blit(self.bg, (0, 0))

        for l in self.lasers:
            screen.blit(self.laser_img, (int(l[0]), int(l[1])))

        screen.blit(self.ship_img, (int(self.ship_x-28), self.ship_y-35))

        for d in self.debris:
            img = pygame.transform.rotate(d["img"], d["rot"])
            cx, cy = int(d["x"]), int(d["y"])
            screen.blit(img, img.get_rect(center=(cx, cy)))
            if d["max_hp"] > 1:
                bw = img.get_width()
                pct = d["hp"] / d["max_hp"]
                pygame.draw.rect(screen, (70,70,70), (cx-bw//2, cy-img.get_height()//2-10, bw, 5))
                pygame.draw.rect(screen, lerp_col((255,60,60),(70,210,140),pct),
                                 (cx-bw//2, cy-img.get_height()//2-10, int(bw*pct), 5))

        for ft in self.float_texts:
            a = int(255 * (1 - ft[3]))
            s = self.font.render(ft[2], True, ft[4])
            s.set_alpha(a)
            screen.blit(s, (int(ft[0]), int(ft[1])))

        # HUD — bande semi-transparente en haut
        hud = pygame.Surface((W, 38), pygame.SRCALPHA)
        hud.fill((0, 0, 0, 140))
        screen.blit(hud, (0, 0))

        # Score (gauche)
        score_lbl = self.font.render("SCORE", True, (120, 130, 160))
        score_val = pygame.font.Font(None, 36).render(str(self.score), True, (255, 255, 255))
        screen.blit(score_lbl, (12, 4))
        screen.blit(score_val, (12, 20))

        # Vies sous forme d'icônes ♥ (droite)
        heart_font = pygame.font.Font(None, 30)
        hearts = "♥ " * self.lives
        hx = W - 10 - heart_font.size(hearts.rstrip())[0]
        screen.blit(heart_font.render("VIES", True, (120, 130, 160)), (W - 68, 4))
        screen.blit(heart_font.render(hearts.rstrip(), True, (220, 70, 70)), (hx, 20))

        # Énergie (centre-gauche)
        pct = self.energy / 100.0
        screen.blit(self.font.render("NRJ", True, (180, 180, 200)), (W//2 - 108, 10))
        pygame.draw.rect(screen, (40, 40, 55), (W//2 - 80, 12, 160, 14), border_radius=7)
        ecol = (70, 210, 140) if pct > 0.3 else (220, 80, 80)
        pygame.draw.rect(screen, ecol, (W//2 - 80, 12, int(160 * pct), 14), border_radius=7)

        # Temps restant — barre verticale (bord droit)
        tpct = max(0, self.time_left / 60.0)
        pygame.draw.rect(screen, (40, 40, 55), (W - 22, 48, 12, H - 68), border_radius=6)
        fh = int((H - 68) * tpct)
        pygame.draw.rect(screen, lerp_col((255, 60, 60), (70, 210, 140), tpct),
                         (W - 22, 48 + (H - 68) - fh, 12, fh), border_radius=6)
        t_lbl = pygame.font.Font(None, 22).render(f"{int(self.time_left)}s", True, (180, 180, 200))
        screen.blit(t_lbl, (W - 26 - t_lbl.get_width() // 2, H - 52))
