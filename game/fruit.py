import pygame

class Fruit:
    def __init__(
        self,
        x,
        y,
        radius=50,
        vx=0,
        vy=0,
        gravity=1000
    ):
        self.x = x
        self.y = y
        self.radius = radius

        self.vx = vx
        self.vy = vy
        self.gravity = gravity

        self.sliced = False

    def update(self, dt):
        if not self.sliced:
            # Gravity changes the vertical velocity
            self.vy += self.gravity * dt

            # Velocity changes the fruit's position
            self.x += self.vx * dt
            self.y += self.vy * dt

    def draw(self, screen):
        if not self.sliced:
            pygame.draw.circle(
                screen,
                (220, 50, 50),
                (int(self.x), int(self.y)),
                self.radius
            )

    def is_offscreen(self, screen_height):
        return self.y - self.radius > screen_height