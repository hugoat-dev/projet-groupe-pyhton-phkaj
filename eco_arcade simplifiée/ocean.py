import random
import pygame
from config import W, H, clamp, lerp_col, sprite
from ui import State

SURF_Y = 140
TRASH_KINDS = ["bottle", "can", "bag", "tire", "box"]
FISH_KINDS = ["orange", "blue", "purple"]


class OceanGame(State):
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 28)

        # backgrounds
        self.sky = pygame.Surface((W, SURF_Y))
        self.sky.fill((135, 200, 240))
        self.sea = pygame.Surface((W, H - SURF_Y))
        self.sea.fill((25, 85, 150))

        # sprites
        self.boat_img = sprite("boat")
        self.gr_img = sprite("grapple")

        # bateau
        self.boat_x = float(W // 2)
        self.boat_vx = 0.0

        # grappin
        self.gr_active = False
        self.gr_state = "idle"
        self.gr_y = float(SURF_Y)
        self.gr_caught = None

        # entités
        self.trash = []
        self.fish = []
        self.float_texts = []  # [x, y, texte, age, couleur]

        # stats
        self.score = 0
        self.lives = 10
        self.time_left = 75.0
        self.spawn_t = 0.0
        self.trash_limit = 3
        self.scale_t = 0.0

        for _ in range(2): self._spawn_trash()
        for _ in range(3): self._spawn_fish()

    def _spawn_trash(self):
        k = random.choice(TRASH_KINDS)
        y = random.uniform(SURF_Y + 50, H - 60)
        self.trash.append({"x": -50.0, "y": y, "vx": random.uniform(60, 100),
                           "img": sprite(f"trash_{k}")})

    def _spawn_fish(self):
        y = random.uniform(SURF_Y + 30, H - 50)
        self.fish.append({"x": W + 50.0, "y": y, "vx": -random.uniform(80, 130),
                          "img": sprite(f"fish_{random.choice(FISH_KINDS)}")})

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                from menu import MenuState
                self.game.go(MenuState(self.game))
            elif e.key == pygame.K_p:
                from end import PauseState
                self.game.push(PauseState(self.game, self))
            elif e.key == pygame.K_SPACE:
                if not self.gr_active:
                    self.gr_active = True
                    self.gr_state = "down"
                    self.gr_y = float(SURF_Y)
                    self.gr_caught = None
                elif self.gr_state == "down":
                    self.gr_state = "up"

    def update(self, dt):
        self.time_left -= dt
        self.scale_t += dt
        if self.scale_t >= 10.0:
            self.scale_t = 0.0
            self.trash_limit = int(self.trash_limit * 1.5)

        if self.time_left <= 0 or self.lives <= 0:
            from end import EndState
            self.game.go(EndState(self.game, "ocean", self.score,
                                  [("Déchets", self.score // 10)]))
            return

        # bateau
        keys = pygame.key.get_pressed()
        ax = (-1300 if (keys[pygame.K_LEFT] or keys[pygame.K_a]) else 0) + \
             (1300 if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) else 0)
        self.boat_vx = clamp(self.boat_vx * (1 - 7*dt) + ax*dt, -300, 300)
        self.boat_x = clamp(self.boat_x + self.boat_vx*dt, 60, W-60)

        # grappin
        gr_x = self.boat_x
        if self.gr_active:
            if self.gr_state == "down":
                self.gr_y += 260 * dt
                if self.gr_y >= H - 60: self.gr_state = "up"
                if self.gr_caught is None:
                    for t in self.trash:
                        if abs(gr_x - t["x"]) < 32 and abs(self.gr_y - t["y"]) < 32:
                            self.gr_caught = t
                            self.gr_state = "up"
                            break
                for f in self.fish:
                    if abs(gr_x - f["x"]) < 28 and abs(self.gr_y - f["y"]) < 22:
                        self.lives -= 1
                        self.gr_state = "up"
                        break
            else:
                self.gr_y -= 260 * dt
                if self.gr_caught:
                    self.gr_caught["x"] = gr_x
                    self.gr_caught["y"] = self.gr_y + 22
                if self.gr_y <= SURF_Y:
                    if self.gr_caught:
                        if self.gr_caught in self.trash: self.trash.remove(self.gr_caught)
                        self.score += 10
                        self.float_texts.append([gr_x, SURF_Y - 20, "+10", 0.0, (70, 210, 140)])
                        self.gr_caught = None
                    self.gr_active = False
                    self.gr_state = "idle"

        for t in self.trash[:]:
            t["x"] += t["vx"] * dt
            if t["x"] > W + 60: self.trash.remove(t)
        for f in self.fish[:]:
            f["x"] += f["vx"] * dt
            if f["x"] < -60: self.fish.remove(f)

        self.spawn_t += dt
        if self.spawn_t >= 1.5:
            self.spawn_t = 0.0
            if len(self.trash) < self.trash_limit: self._spawn_trash()
            if len(self.fish) < 6: self._spawn_fish()

        for ft in self.float_texts[:]:
            ft[1] -= 45 * dt
            ft[3] += dt
            if ft[3] > 1.0: self.float_texts.remove(ft)

    def draw(self, screen):
        screen.blit(self.sky, (0, 0))
        screen.blit(self.sea, (0, SURF_Y))
        pygame.draw.line(screen, (190, 235, 255), (0, SURF_Y), (W, SURF_Y), 3)

        for f in self.fish:
            screen.blit(f["img"], (int(f["x"]-24), int(f["y"]-16)))
        for t in self.trash:
            screen.blit(t["img"], (int(t["x"]-27), int(t["y"]-27)))

        if self.gr_active:
            gx, gy = int(self.boat_x), int(self.gr_y)
            pygame.draw.line(screen, (110, 110, 125), (gx, SURF_Y + 10), (gx, gy), 2)
            screen.blit(self.gr_img, (gx-17, gy-17))

        screen.blit(self.boat_img, (int(self.boat_x-48), 30))

        for ft in self.float_texts:
            a = int(255 * (1 - ft[3]))
            s = self.font.render(ft[2], True, ft[4])
            s.set_alpha(a)
            screen.blit(s, (int(ft[0]-s.get_width()//2), int(ft[1])))

        # HUD
        pygame.draw.rect(screen, (255, 255, 255), (0, 0, W, 28))
        screen.blit(self.font.render(f"Score: {self.score}", True, (20,20,20)), (10, 4))
        screen.blit(self.font.render(f"Vies: {self.lives}", True, (200,50,50)), (W-130, 4))
        tpct = max(0, self.time_left / 75.0)
        pygame.draw.rect(screen, (200,200,210), (W//2-75, 7, 150, 14), border_radius=7)
        pygame.draw.rect(screen, lerp_col((255,60,60),(70,210,140),tpct),
                         (W//2-75, 7, int(150*tpct), 14), border_radius=7)
        screen.blit(self.font.render(f"{int(self.time_left)}s", True, (20,20,20)), (W//2+83, 4))
