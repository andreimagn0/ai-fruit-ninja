import pygame

class Fruit:
    def __init__(self, x, y, radius=50):
        self.x = x
        self.y = y
        self.radius = radius
        self.sliced = False

    def draw(self, screen):
        if not self.sliced:
            pygame.draw.circle(
                screen,
                (220, 50, 50),
                (self.x, self.y),
                self.radius
            )