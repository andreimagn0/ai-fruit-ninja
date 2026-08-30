import pygame
import random

from vision.hand_tracker import LiveHandTracker
from game.fruit import Fruit
from game.collision import blade_crosses_fruit


# GAME SETTINGS
WIDTH = 1280
HEIGHT = 720
FPS = 60
MIN_SLICE_VELOCITY = 0.8
GAME_DURATION = 30.0


def create_random_fruit():
    x = random.randint(200, WIDTH - 200)
    y = HEIGHT + 50

    vx = random.randint(-200, 200)
    vy = random.randint(-900, -700)

    return Fruit(
        x=x,
        y=y,
        radius=50,
        vx=vx,
        vy=vy,
    )


# SETUP
pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Fruit Ninja")

clock = pygame.time.Clock()
font = pygame.font.Font(None, 48)

tracker = LiveHandTracker()
tracker.start()

fruit = create_random_fruit()
score = 0
time_remaining = GAME_DURATION

running = True

try:
    while running:
        dt = clock.tick(FPS) / 1000.0

        # EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    fruit = create_random_fruit()
                    score = 0
                    time_remaining = GAME_DURATION

        # GET LIVE HAND TRACKING STATE
        blade, camera_frame = tracker.get_blade_state()

        # Convert normalized BladeState coordinates to game pixels
        blade_x = int(blade.x * WIDTH)
        blade_y = int(blade.y * HEIGHT)

        prev_blade_x = int(blade.prev_x * WIDTH)
        prev_blade_y = int(blade.prev_y * HEIGHT)

        # Update timer
        time_remaining = max(0, time_remaining - dt)

        # Update fruit physics
        fruit.update(dt)

        # COLLISION
        if (
            time_remaining > 0
            and blade.visible
            and blade.velocity >= MIN_SLICE_VELOCITY
            and not fruit.sliced
        ):
            if blade_crosses_fruit(
                prev_blade_x,
                prev_blade_y,
                blade_x,
                blade_y,
                fruit.x,
                fruit.y,
                fruit.radius,
            ):
                fruit.sliced = True
                score += 100

        # Replace fruit once sliced or offscreen
        if fruit.sliced:
            fruit = create_random_fruit()
        elif fruit.is_offscreen(HEIGHT):
            fruit = create_random_fruit()

        # DRAWING
        screen.fill((30, 30, 30))

        score_text = font.render(
            f"Score: {score}",
            True,
            (255, 255, 255),
        )

        timer_text = font.render(
            f"Time: {time_remaining:.1f}",
            True,
            (255, 255, 255),
        )

        timer_rect = timer_text.get_rect(
            topright=(WIDTH - 20, 20)
        )

        screen.blit(score_text, (20, 20))
        screen.blit(timer_text, timer_rect)

        fruit.draw(screen)

        # Display game over screen
        if time_remaining <= 0:
            game_over_text = font.render(
                "TIME'S UP!",
                True,
                (255, 255, 255),
            )

            game_over_rect = game_over_text.get_rect(
                center=(WIDTH // 2, HEIGHT // 2)
            )

            screen.blit(game_over_text, game_over_rect)

        # Only draw blade when CV currently sees motion
        if blade.visible:
            pygame.draw.circle(
                screen,
                (255, 255, 255),
                (blade_x, blade_y),
                10,
            )

            # Debug slash line between previous and current position
            pygame.draw.line(
                screen,
                (200, 200, 200),
                (prev_blade_x, prev_blade_y),
                (blade_x, blade_y),
                4,
            )

        # Temporary debug telemetry
        debug_text = font.render(
            f"Visible: {blade.visible}  "
            f"Vel: {blade.velocity:.2f}  "
            f"Threshold: {MIN_SLICE_VELOCITY:.2f}",
            True,
            (255, 255, 255),
        )

        screen.blit(debug_text, (20, 70))

        pygame.display.flip()

finally:
    tracker.stop()
    pygame.quit()