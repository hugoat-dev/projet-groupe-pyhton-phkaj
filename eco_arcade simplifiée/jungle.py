import random
import pygame
from config import W, H, clamp, lerp_col, sprite
from ui import State

ROAD_W = int(W * 0.50)
ROAD_X = W // 2 - ROAD_W // 2
TRASH_KINDS = ["bottle", "can", "bag", "tire", "box"]


class JungleGame(State):
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 28)

        # background statique
        self.bg = pygame.Surface((W, H))
        self.bg.fill((35, 120, 45))
        pygame.draw.rect(self.bg, (42, 42, 52), (ROAD_X, 0, ROAD_W, H))
        pygame.draw.rect(self.bg, (210, 170, 20), (ROAD_X, 0, 8, H))
        pygame.draw.rect(self.bg, (210, 170, 20), (ROAD_X + ROAD_W - 8, 0, 8, H))

        self.car_img = sprite("car")
        self.monkey_img = sprite("monkey")
        self.car_x = float(W // 2)
        self.car_vx = 0.0

        self.trash = []
        self.monkeys = []
        self.float_texts = []

        self.score = 0
        self.lives = 3
        self.time_left = 70.0
        self.diff = 0.0
        self.scroll = 0.0
        self.spawn_t = 0.0
        self.inv_t = 0.0

        for _ in range(3): self._spawn_trash(y=random.uniform(-300, -40))

    def _spawn_trash(self, y=None):
        k = random.choice(TRASH_KINDS)
        x = random.uniform(ROAD_X + 60, ROAD_X + ROAD_W - 60)
        self.trash.append({"x": x, "y": float(-40 if y is None else y),
                           "rot": random.uniform(0, 360), "rots": random.uniform(-40, 40),
                           "img": sprite(f"trash_{k}")})

    def _spawn_monkey(self):
        x = random.uniform(ROAD_X + 70, ROAD_X + ROAD_W - 70)
        self.monkeys.append({"x": x, "y": -50.0, "img": self.monkey_img})

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                from menu import MenuState
                self.game.go(MenuState(self.game))
            elif e.key == pygame.K_p:
                from end import PauseState
                self.game.push(PauseState(self.game, self))

    def update(self, dt):
        self.time_left -= dt
        self.diff += dt
        if self.inv_t > 0: self.inv_t -= dt

        if self.time_left <= 0 or self.lives <= 0:
            from end import EndState
            self.game.go(EndState(self.game, "jungle", self.score,
                                  [("Vies restantes", self.lives)]))
            return

        speed = 150.0 + self.diff * 2.5
        self.scroll = (self.scroll + speed * dt) % 60

        keys = pygame.key.get_pressed()
        ax = (-2200 if (keys[pygame.K_LEFT] or keys[pygame.K_a]) else 0) + \
             (2200 if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) else 0)
        self.car_vx = clamp(self.car_vx * (1 - 9*dt) + ax*dt, -560, 560)
        self.car_x = clamp(self.car_x + self.car_vx*dt, ROAD_X+100, ROAD_X+ROAD_W-100)

        car_rect = pygame.Rect(0, 0, 180, 135)
        car_rect.center = (int(self.car_x), H - 120)
        bin_rect = pygame.Rect(car_rect.left+30, car_rect.top+2, car_rect.width-60, 28)

        for t in self.trash[:]:
            t["y"] += speed * dt
            t["rot"] += t["rots"] * dt
            tr = pygame.Rect(0, 0, 52, 52)
            tr.center = (int(t["x"]), int(t["y"]))
            if bin_rect.colliderect(tr):
                self.score += 1
                self.float_texts.append([t["x"], t["y"]-20, "+1", 0.0, (70,210,140)])
                self.trash.remove(t)
            elif t["y"] > H + 60:
                self.trash.remove(t)

        for m in self.monkeys[:]:
            m["y"] += (speed * 1.1) * dt
            mr = pygame.Rect(0, 0, 50, 50)
            mr.center = (int(m["x"]), int(m["y"]))
            if self.inv_t <= 0 and car_rect.inflate(-20, -18).colliderect(mr):
                self.lives -= 1
                self.inv_t = 1.2
                self.monkeys.remove(m)
            elif m["y"] > H + 60:
                self.monkeys.remove(m)

        self.spawn_t += dt
        if self.spawn_t >= max(0.6, 1.1 - self.diff*0.01):
            self.spawn_t = 0.0
            if random.random() < 0.7 and len(self.trash) < 9: self._spawn_trash()
            if random.random() < 0.3 and len(self.monkeys) < 6: self._spawn_monkey()

        for ft in self.float_texts[:]:
            ft[1] -= 45 * dt
            ft[3] += dt
            if ft[3] > 1.0: self.float_texts.remove(ft)

    def draw(self, screen):
        screen.blit(self.bg, (0, 0))

        # tirets centraux
        for y in range(int(-self.scroll), H, 60):
            pygame.draw.rect(screen, (230, 230, 240), (W//2-5, y, 10, 32), border_radius=3)

        for t in self.trash:
            img = pygame.transform.rotate(t["img"], t["rot"])
            screen.blit(img, img.get_rect(center=(int(t["x"]), int(t["y"]))))
        for m in self.monkeys:
            screen.blit(m["img"], (int(m["x"]-27), int(m["y"]-28)))

        # voiture (clignotement si invincible)
        if self.inv_t <= 0 or int(self.inv_t * 12) % 2 == 0:
            screen.blit(self.car_img, (int(self.car_x-90), H-120-67))

        for ft in self.float_texts:
            a = int(255 * (1 - ft[3]))
            s = self.font.render(ft[2], True, ft[4])
            s.set_alpha(a)
            screen.blit(s, (int(ft[0]), int(ft[1])))

        # HUD
        pygame.draw.rect(screen, (255, 255, 255), (0, 0, W, 28))
        screen.blit(self.font.render(f"Score: {self.score}", True, (20,20,20)), (10, 4))
        screen.blit(self.font.render(f"Vies: {self.lives}", True, (200,50,50)), (W-130, 4))
        tpct = max(0, self.time_left / 70.0)
        pygame.draw.rect(screen, (200,200,210), (W//2-75, 7, 150, 14), border_radius=7)
        pygame.draw.rect(screen, lerp_col((255,60,60),(70,210,140),tpct),
                         (W//2-75, 7, int(150*tpct), 14), border_radius=7)
        screen.blit(self.font.render(f"{int(self.time_left)}s", True, (20,20,20)), (W//2+83, 4))
