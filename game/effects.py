import math
import random
import pygame

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        angle = random.uniform(0, math.tau)
        speed = random.uniform(100, 300)

        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        self.life = 0.5
        self.max_life = self.life

        self.radius = random.randint(3, 7)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Small amount of gravity
        self.vy += 300 * dt

        self.life -= dt

    def draw(self, screen):
        if self.life <= 0:
            return

        pygame.draw.circle(
            screen,
            (220, 50, 50),
            (int(self.x), int(self.y)),
            self.radius,
        )

    def is_dead(self):
        return self.life <= 0

class ScorePopup:
    def __init__(self, x, y, text="+100"):
        self.x = x
        self.y = y
        self.text = text

        self.life = 0.8
        self.max_life = self.life

    def update(self, dt):
        # Float upward
        self.y -= 70 * dt

        self.life -= dt

    def draw(self, screen, font):
        if self.life <= 0:
            return

        rendered_text = font.render(
            self.text,
            True,
            (255, 255, 255),
        )

        alpha = int(
            255 * (self.life / self.max_life)
        )

        rendered_text.set_alpha(alpha)

        rect = rendered_text.get_rect(
            center=(int(self.x), int(self.y))
        )

        screen.blit(rendered_text, rect)

    def is_dead(self):
        return self.life <= 0