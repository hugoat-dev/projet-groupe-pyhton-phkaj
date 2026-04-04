import pygame


class State:
    _under = None
    def handle(self, e): pass
    def update(self, dt): pass
    def draw(self, screen): pass


class Button:
    def __init__(self, rect, label, font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font = font

    def draw(self, screen, selected=False):
        col = (70, 200, 120) if selected else (40, 45, 58)
        pygame.draw.rect(screen, col, self.rect, border_radius=10)
        pygame.draw.rect(screen, (180, 185, 195), self.rect, 2, border_radius=10)
        txt = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def hit(self, pos):
        return self.rect.collidepoint(pos)
