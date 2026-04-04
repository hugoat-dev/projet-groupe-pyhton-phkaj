import sys
import pygame
from config import W, H, FPS, load_save
from menu import MenuState


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Eco Arcade — Édition Simplifiée")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.running = True
        self.data = load_save()
        self.state = None
        self._stack = []
        self.go(MenuState(self))

    def go(self, state):
        self._stack.clear()
        self.state = state

    def push(self, state):
        self._stack.append(self.state)
        self.state = state

    def pop(self):
        if self._stack:
            self.state = self._stack.pop()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.state:
                    self.state.handle(event)
            if self.state:
                if hasattr(self.state, 'update'):
                    self.state.update(dt)
                self.state.draw(self.screen)
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
