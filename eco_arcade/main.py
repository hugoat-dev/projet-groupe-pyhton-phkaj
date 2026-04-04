import sys
import pygame
from config import W, H, FRAME_RATE, load_save
from states.menu import MenuState


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Eco Arcade V2 Enhanced")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.running = True
        self.data = load_save()
        self.state_stack = []
        self.transition_to(MenuState(self))

    def transition_to(self, state):
        self.state_stack = [state]
        state.enter()

    def push_state(self, state):
        self.state_stack.append(state)
        state.enter()

    def pop_state(self):
        if len(self.state_stack) > 1:
            s = self.state_stack.pop()
            s.exit()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FRAME_RATE) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.state_stack:
                    self.state_stack[-1].handle_event(event)
            if self.state_stack:
                self.state_stack[-1].update(dt)
                self.state_stack[-1].draw(self.screen)
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
