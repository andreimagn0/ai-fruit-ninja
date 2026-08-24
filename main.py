import pygame

from vision.mouse_tracker import MouseTracker
from game.fruit import Fruit
from game.collision import blade_crosses_fruit

# GAME SETTINGS
WIDTH = 1280
HEIGHT = 720
FPS = 60

# SETUP
pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Fruit Ninja")

clock = pygame.time.Clock()
font = pygame.font.Font(None, 48)

mouse_tracker = MouseTracker(WIDTH, HEIGHT)

fruit = Fruit(
    WIDTH // 2,
    HEIGHT // 2
    )

score = 0

# GAME LOOP
running = True

while running:
    # Check for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Simply for development testing purposes:
        # Press the R key to reset the fruit and score
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                fruit = Fruit(
                    WIDTH // 2,
                    HEIGHT // 2
                )
                score = 0

    # Get the current fake BladeState
    blade = mouse_tracker.get_blade_state()

    # Convert normalized coordinates back into pixels
    blade_x = int(blade.x * WIDTH)
    blade_y = int(blade.y * HEIGHT)

    prev_blade_x = int(blade.prev_x * WIDTH)
    prev_blade_y = int(blade.prev_y * HEIGHT)

    # Collision
    if not fruit.sliced:
        if blade_crosses_fruit(
            prev_blade_x,
            prev_blade_y,
            blade_x,
            blade_y,
            fruit.x,
            fruit.y,
            fruit.radius
        ):
            fruit.sliced = True
            score += 100

    # Drawing
    screen.fill((30, 30, 30))

    score_text = font.render(
        f"Score: {score}",
        True,
        (255, 255, 255)
    )

    screen.blit(
        score_text,
        (20, 20)
    )

    fruit.draw(screen)

    # Draw the blade position
    pygame.draw.circle(
        screen,
        (255, 255, 255),
        (blade_x, blade_y),
        10
    )

    # Show everything we drew
    pygame.display.flip()

    # Limit the game to 60 FPS
    clock.tick(FPS)

pygame.quit()