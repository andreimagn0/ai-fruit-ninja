import pygame

from vision.mouse_tracker import MouseTracker

# GAME SETTINGS
WIDTH = 1280
HEIGHT = 720
FPS = 60

# SETUP
pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Fruit Ninja")

clock = pygame.time.Clock()

mouse_tracker = MouseTracker(WIDTH, HEIGHT)

# Temporary fruit
fruit_x = WIDTH // 2
fruit_y = HEIGHT // 2
fruit_radius = 50

# GAME LOOP
running = True

while running:
    # Check for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Get the current fake BladeState
    blade = mouse_tracker.get_blade_state()

    # Convert normalized coordinates back into pixels
    blade_x = int(blade.x * WIDTH)
    blade_y = int(blade.y * HEIGHT)

    # Clear the screen
    screen.fill((30, 30, 30))

    # Draw temporary fruit
    pygame.draw.circle(
        screen,
        (220, 50, 50),
        (fruit_x, fruit_y),
        fruit_radius
    )

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