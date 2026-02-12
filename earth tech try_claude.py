#!/usr/bin/env python3
"""
Eco Arcade - 3 mini-jeux écologiques avec Pygame
Contrôles: Flèches/WASD pour bouger, ESC pour menu, P pour pause, I pour instructions
"""

import pygame
import random
import math
from enum import Enum

# Initialisation Pygame
pygame.init()

# Constantes
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
DARK_BLUE = (20, 50, 150)
GREEN = (50, 200, 50)
DARK_GREEN = (20, 100, 20)
BROWN = (139, 69, 19)
GRAY = (100, 100, 100)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (150, 50, 200)

class GameState(Enum):
    MENU = 1
    INSTRUCTIONS = 2
    BOAT_GAME = 3
    JUNGLE_GAME = 4
    SPACE_GAME = 5
    GAME_OVER = 6

# Classes de base
class Player:
    def __init__(self, x, y, width, height, color, speed):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.speed = speed
        self.lives = 3

    def move(self, dx, dy, dt):
        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        self.y = max(0, min(SCREEN_HEIGHT - self.height, self.y))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.get_rect())

class Trash:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 15
        self.vx = random.uniform(-20, 20)
        self.vy = random.uniform(-20, 20)
        self.collected = False

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.x <= 0 or self.x >= SCREEN_WIDTH:
            self.vx *= -1
        if self.y <= 0 or self.y >= SCREEN_HEIGHT:
            self.vy *= -1

        self.x = max(0, min(SCREEN_WIDTH, self.x))
        self.y = max(0, min(SCREEN_HEIGHT, self.y))

    def get_rect(self):
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)

    def draw(self, screen):
        pygame.draw.rect(screen, GRAY, self.get_rect())
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), 3)

class Fish:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 20
        self.vx = random.choice([-50, 50])
        self.vy = random.uniform(-30, 30)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.x <= 0 or self.x >= SCREEN_WIDTH:
            self.vx *= -1
        if self.y <= 0 or self.y >= SCREEN_HEIGHT:
            self.vy *= -1

        self.x = max(0, min(SCREEN_WIDTH, self.x))
        self.y = max(0, min(SCREEN_HEIGHT, self.y))

    def get_rect(self):
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)

    def draw(self, screen):
        # Corps du poisson
        pygame.draw.ellipse(screen, ORANGE, self.get_rect())
        # Queue
        tail_dir = -1 if self.vx > 0 else 1
        tail_x = int(self.x + tail_dir * self.size//2)
        pygame.draw.polygon(screen, ORANGE, [
            (tail_x, int(self.y)),
            (tail_x + tail_dir * 10, int(self.y - 8)),
            (tail_x + tail_dir * 10, int(self.y + 8))
        ])

class Monkey:
    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.size = 25
        self.speed = speed

    def update(self, dt):
        self.y += self.speed * dt

    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT + 50

    def get_rect(self):
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)

    def draw(self, screen):
        # Corps du singe
        pygame.draw.circle(screen, BROWN, (int(self.x), int(self.y)), self.size//2)
        # Yeux
        pygame.draw.circle(screen, BLACK, (int(self.x - 5), int(self.y - 3)), 3)
        pygame.draw.circle(screen, BLACK, (int(self.x + 5), int(self.y - 3)), 3)

class Debris:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(15, 25)
        self.vx = random.uniform(-80, 80)
        self.vy = random.uniform(-80, 80)
        self.rotation = random.uniform(0, 360)
        self.collected = False

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += 100 * dt

    def is_off_screen(self):
        return (self.x < -50 or self.x > SCREEN_WIDTH + 50 or
                self.y < -50 or self.y > SCREEN_HEIGHT + 50)

    def get_rect(self):
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)

    def draw(self, screen):
        # Débris spatial (polygone irrégulier)
        angle = math.radians(self.rotation)
        points = []
        for i in range(6):
            r = self.size // 2 if i % 2 == 0 else self.size // 3
            theta = angle + i * math.pi / 3
            px = self.x + r * math.cos(theta)
            py = self.y + r * math.sin(theta)
            points.append((int(px), int(py)))
        pygame.draw.polygon(screen, GRAY, points)
        pygame.draw.polygon(screen, BLACK, points, 2)

# États du jeu
class MenuState:
    def __init__(self, game):
        self.game = game
        self.selected = 0
        self.options = ["Océan", "Jungle", "Espace"]
        self.font_title = pygame.font.Font(None, 74)
        self.font_menu = pygame.font.Font(None, 48)
        self.font_help = pygame.font.Font(None, 24)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_DOWN, pygame.K_s]:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in [pygame.K_UP, pygame.K_w]:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                if self.selected == 0:
                    self.game.change_state(GameState.BOAT_GAME)
                elif self.selected == 1:
                    self.game.change_state(GameState.JUNGLE_GAME)
                elif self.selected == 2:
                    self.game.change_state(GameState.SPACE_GAME)
            elif event.key == pygame.K_i:
                self.game.change_state(GameState.INSTRUCTIONS)

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(GREEN)

        # Titre
        title = self.font_title.render("Eco Arcade", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))

        # Options
        for i, option in enumerate(self.options):
            color = YELLOW if i == self.selected else WHITE
            text = self.font_menu.render(option, True, color)
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 220 + i * 70))

        # Aide
        help_texts = [
            "Flèches/WASD: Déplacements",
            "ESC: Retour au menu",
            "P: Pause",
            "I: Instructions",
            "Entrée: Sélectionner"
        ]
        y = 480
        for text_str in help_texts:
            text = self.font_help.render(text_str, True, WHITE)
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, y))
            y += 25

class InstructionsState:
    def __init__(self, game):
        self.game = game
        self.font_title = pygame.font.Font(None, 48)
        self.font_text = pygame.font.Font(None, 24)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_i:
                self.game.change_state(GameState.MENU)

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(DARK_BLUE)

        title = self.font_title.render("Instructions", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))

        instructions = [
            "OCÉAN:",
            "- Pilote le bateau (bleu) et ramasse les déchets (gris)",
            "- Évite les poissons (orange) : les toucher = pénalité",
            "- Si un déchet touche un poisson, +1 poisson impacté",
            "- Perdu si 10 poissons impactés ou temps écoulé",
            "",
            "JUNGLE:",
            "- Conduis la voiture (verte) sur la route",
            "- Ramasse les déchets, évite les singes (marron)",
            "- 3 vies : collision avec singe = -1 vie",
            "- Difficulté augmente avec le temps",
            "",
            "ESPACE:",
            "- Pilote le vaisseau (violet) avec un filet (jaune) derrière",
            "- Capture les débris avec le filet (pas le vaisseau!)",
            "- Le vaisseau ne doit PAS toucher les débris = -1 vie",
            "- 3 vies, survie pendant 60 secondes",
            "",
            "Appuie sur ESC pour revenir au menu"
        ]

        y = 100
        for line in instructions:
            text = self.font_text.render(line, True, WHITE)
            screen.blit(text, (50, y))
            y += 28

class BoatGameState:
    def __init__(self, game):
        self.game = game
        self.player = Player(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 40, 60, BLUE, 150)
        self.trash_list = []
        self.fish_list = []
        self.trash_collected = 0
        self.fish_impacted = 0
        self.timer = 60.0
        self.spawn_timer = 0
        self.paused = False
        self.game_over = False
        self.font = pygame.font.Font(None, 32)

        # Spawn initial
        for _ in range(5):
            self.trash_list.append(Trash(random.randint(50, SCREEN_WIDTH-50),
                                         random.randint(50, SCREEN_HEIGHT-50)))
        for _ in range(8):
            self.fish_list.append(Fish(random.randint(50, SCREEN_WIDTH-50),
                                       random.randint(50, SCREEN_HEIGHT-50)))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameState.MENU)
            elif event.key == pygame.K_p:
                self.paused = not self.paused

    def update(self, dt):
        if self.paused or self.game_over:
            return

        self.timer -= dt
        if self.timer <= 0 or self.fish_impacted >= 10:
            self.game_over = True
            return

        # Déplacement joueur
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        if dx != 0 or dy != 0:
            norm = math.sqrt(dx*dx + dy*dy)
            self.player.move(dx/norm, dy/norm, dt)

        # Update trash
        for trash in self.trash_list[:]:
            trash.update(dt)

            # Collision avec joueur
            if not trash.collected and self.player.get_rect().colliderect(trash.get_rect()):
                trash.collected = True
                self.trash_collected += 1
                self.trash_list.remove(trash)
                continue

            # Collision trash-poisson
            for fish in self.fish_list:
                if not trash.collected and trash.get_rect().colliderect(fish.get_rect()):
                    trash.collected = True
                    self.fish_impacted += 1
                    self.trash_list.remove(trash)
                    break

        # Update poissons
        for fish in self.fish_list:
            fish.update(dt)

            # Pénalité si joueur touche poisson
            if self.player.get_rect().colliderect(fish.get_rect()):
                self.trash_collected = max(0, self.trash_collected - 1)

        # Spawn nouveaux déchets
        self.spawn_timer += dt
        if self.spawn_timer > 2.0 and len(self.trash_list) < 10:
            self.trash_list.append(Trash(random.randint(50, SCREEN_WIDTH-50),
                                         random.randint(50, SCREEN_HEIGHT-50)))
            self.spawn_timer = 0

    def draw(self, screen):
        screen.fill(BLUE)

        # Vagues
        for i in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(screen, DARK_BLUE, (0, i), (SCREEN_WIDTH, i), 2)

        # Dessiner entités
        for fish in self.fish_list:
            fish.draw(screen)
        for trash in self.trash_list:
            trash.draw(screen)
        self.player.draw(screen)

        # UI
        info = self.font.render(f"Déchets: {self.trash_collected}  Poissons impactés: {self.fish_impacted}/10  Temps: {int(self.timer)}s", True, WHITE)
        screen.blit(info, (10, 10))

        instruction = self.font.render("Ramasse les déchets ! Évite les poissons !", True, YELLOW)
        screen.blit(instruction, (SCREEN_WIDTH//2 - instruction.get_width()//2, 50))

        if self.paused:
            pause_text = self.font.render("PAUSE", True, RED)
            screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2))

        if self.game_over:
            go_text = self.font.render(f"Terminé ! Score: {self.trash_collected} déchets", True, YELLOW)
            screen.blit(go_text, (SCREEN_WIDTH//2 - go_text.get_width()//2, SCREEN_HEIGHT//2))
            esc_text = self.font.render("ESC pour menu", True, WHITE)
            screen.blit(esc_text, (SCREEN_WIDTH//2 - esc_text.get_width()//2, SCREEN_HEIGHT//2 + 40))

class JungleGameState:
    def __init__(self, game):
        self.game = game
        self.player = Player(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100, 50, 70, GREEN, 200)
        self.trash_list = []
        self.monkeys = []
        self.score = 0
        self.timer = 60.0
        self.spawn_timer = 0
        self.difficulty_timer = 0
        self.base_speed = 100
        self.paused = False
        self.game_over = False
        self.font = pygame.font.Font(None, 32)

        # Spawn initial
        for _ in range(3):
            self.trash_list.append(Trash(random.randint(50, SCREEN_WIDTH-50),
                                         random.randint(-200, -50)))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameState.MENU)
            elif event.key == pygame.K_p:
                self.paused = not self.paused

    def update(self, dt):
        if self.paused or self.game_over:
            return

        self.timer -= dt
        if self.timer <= 0 or self.player.lives <= 0:
            self.game_over = True
            return

        # Augmenter difficulté
        self.difficulty_timer += dt
        current_speed = self.base_speed + (self.difficulty_timer * 5)

        # Déplacement joueur (gauche-droite seulement)
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        if dx != 0:
            self.player.move(dx, 0, dt)

        # Update déchets
        for trash in self.trash_list[:]:
            trash.y += current_speed * dt

            if self.player.get_rect().colliderect(trash.get_rect()):
                self.score += 1
                self.trash_list.remove(trash)
            elif trash.y > SCREEN_HEIGHT:
                self.trash_list.remove(trash)

        # Update singes
        for monkey in self.monkeys[:]:
            monkey.update(dt)

            if self.player.get_rect().colliderect(monkey.get_rect()):
                self.player.lives -= 1
                self.monkeys.remove(monkey)
            elif monkey.is_off_screen():
                self.monkeys.remove(monkey)

        # Spawn
        self.spawn_timer += dt
        if self.spawn_timer > 1.5:
            if random.random() < 0.6:
                self.trash_list.append(Trash(random.randint(50, SCREEN_WIDTH-50), -30))
            if random.random() < 0.4 + self.difficulty_timer * 0.01:
                self.monkeys.append(Monkey(random.randint(50, SCREEN_WIDTH-50), -30, current_speed))
            self.spawn_timer = 0

    def draw(self, screen):
        screen.fill(DARK_GREEN)

        # Route
        road_width = 400
        road_x = SCREEN_WIDTH//2 - road_width//2
        pygame.draw.rect(screen, GRAY, (road_x, 0, road_width, SCREEN_HEIGHT))
        # Lignes blanches
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH//2 - 5, y, 10, 20))

        # Entités
        for trash in self.trash_list:
            trash.draw(screen)
        for monkey in self.monkeys:
            monkey.draw(screen)
        self.player.draw(screen)

        # UI
        info = self.font.render(f"Score: {self.score}  Vies: {self.player.lives}  Temps: {int(self.timer)}s", True, WHITE)
        screen.blit(info, (10, 10))

        instruction = self.font.render("Ramasse les déchets ! Évite les singes !", True, YELLOW)
        screen.blit(instruction, (SCREEN_WIDTH//2 - instruction.get_width()//2, 50))

        if self.paused:
            pause_text = self.font.render("PAUSE", True, RED)
            screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2))

        if self.game_over:
            go_text = self.font.render(f"Terminé ! Score final: {self.score}", True, YELLOW)
            screen.blit(go_text, (SCREEN_WIDTH//2 - go_text.get_width()//2, SCREEN_HEIGHT//2))
            esc_text = self.font.render("ESC pour menu", True, WHITE)
            screen.blit(esc_text, (SCREEN_WIDTH//2 - esc_text.get_width()//2, SCREEN_HEIGHT//2 + 40))

class SpaceGameState:
    def __init__(self, game):
        self.game = game
        self.player = Player(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 30, 40, PURPLE, 180)
        self.net_offset_x = 0
        self.net_offset_y = 50
        self.net_width = 60
        self.net_height = 40
        self.debris_list = []
        self.score = 0
        self.timer = 60.0
        self.spawn_timer = 0
        self.paused = False
        self.game_over = False
        self.font = pygame.font.Font(None, 32)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameState.MENU)
            elif event.key == pygame.K_p:
                self.paused = not self.paused

    def get_net_rect(self):
        return pygame.Rect(
            self.player.x + self.player.width//2 - self.net_width//2 + self.net_offset_x,
            self.player.y + self.player.height + self.net_offset_y,
            self.net_width,
            self.net_height
        )

    def update(self, dt):
        if self.paused or self.game_over:
            return

        self.timer -= dt
        if self.timer <= 0 or self.player.lives <= 0:
            self.game_over = True
            return

        # Déplacement joueur
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        if dx != 0 or dy != 0:
            norm = math.sqrt(dx*dx + dy*dy)
            self.player.move(dx/norm, dy/norm, dt)

        # Update débris
        net_rect = self.get_net_rect()
        for debris in self.debris_list[:]:
            debris.update(dt)

            # Collision avec filet = capture
            if not debris.collected and net_rect.colliderect(debris.get_rect()):
                debris.collected = True
                self.score += 1
                self.debris_list.remove(debris)
                continue

            # Collision avec vaisseau = perte vie
            if not debris.collected and self.player.get_rect().colliderect(debris.get_rect()):
                self.player.lives -= 1
                self.debris_list.remove(debris)
                continue

            if debris.is_off_screen():
                self.debris_list.remove(debris)

        # Spawn débris
        self.spawn_timer += dt
        if self.spawn_timer > 0.8:
            edge = random.choice(['top', 'bottom', 'left', 'right'])
            if edge == 'top':
                x, y = random.randint(0, SCREEN_WIDTH), -30
            elif edge == 'bottom':
                x, y = random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + 30
            elif edge == 'left':
                x, y = -30, random.randint(0, SCREEN_HEIGHT)
            else:
                x, y = SCREEN_WIDTH + 30, random.randint(0, SCREEN_HEIGHT)

            self.debris_list.append(Debris(x, y))
            self.spawn_timer = 0

    def draw(self, screen):
        screen.fill(BLACK)

        # Étoiles
        for _ in range(100):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            pygame.draw.circle(screen, WHITE, (x, y), 1)

        # Filet (derrière le vaisseau)
        net_rect = self.get_net_rect()
        pygame.draw.rect(screen, YELLOW, net_rect, 3)
        pygame.draw.line(screen, YELLOW,
                        (self.player.x + self.player.width//2, self.player.y + self.player.height),
                        (net_rect.centerx, net_rect.top), 2)

        # Débris
        for debris in self.debris_list:
            debris.draw(screen)

        # Vaisseau
        self.player.draw(screen)
        # Fenêtre vaisseau
        pygame.draw.circle(screen, YELLOW,
                          (int(self.player.x + self.player.width//2),
                           int(self.player.y + self.player.height//2)), 5)

        # UI
        info = self.font.render(f"Score: {self.score}  Vies: {self.player.lives}  Temps: {int(self.timer)}s", True, WHITE)
        screen.blit(info, (10, 10))

        instruction = self.font.render("Capture avec le filet ! Ne touche pas les débris !", True, YELLOW)
        screen.blit(instruction, (SCREEN_WIDTH//2 - instruction.get_width()//2, 50))

        if self.paused:
            pause_text = self.font.render("PAUSE", True, RED)
            screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2))

        if self.game_over:
            go_text = self.font.render(f"Terminé ! Score final: {self.score}", True, YELLOW)
            screen.blit(go_text, (SCREEN_WIDTH//2 - go_text.get_width()//2, SCREEN_HEIGHT//2))
            esc_text = self.font.render("ESC pour menu", True, WHITE)
            screen.blit(esc_text, (SCREEN_WIDTH//2 - esc_text.get_width()//2, SCREEN_HEIGHT//2 + 40))

# Gestionnaire principal
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Eco Arcade")
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_state = GameState.MENU
        self.states = {
            GameState.MENU: MenuState(self),
            GameState.INSTRUCTIONS: InstructionsState(self),
        }

    def change_state(self, new_state):
        self.current_state = new_state
        if new_state == GameState.BOAT_GAME:
            self.states[GameState.BOAT_GAME] = BoatGameState(self)
        elif new_state == GameState.JUNGLE_GAME:
            self.states[GameState.JUNGLE_GAME] = JungleGameState(self)
        elif new_state == GameState.SPACE_GAME:
            self.states[GameState.SPACE_GAME] = SpaceGameState(self)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.states[self.current_state].handle_event(event)

            self.states[self.current_state].update(dt)
            self.states[self.current_state].draw(self.screen)

            pygame.display.flip()

        pygame.quit()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()