import pygame
import random

from vision.hand_tracker import LiveHandTracker
from game.fruit import Fruit
from game.collision import blade_crosses_fruit


# =========================================================
# GAME SETTINGS
# =========================================================

WIDTH = 1280
HEIGHT = 720
FPS = 60

MIN_SLICE_VELOCITY = 0.8
GAME_DURATION = 30.0

COUNTDOWN_DURATION = 3.5
GAME_OVER_DURATION = 5.0
INITIALS_TIMEOUT = 15.0
LEADERBOARD_DURATION = 8.0

BASE_SPAWN_INTERVAL = 1.2
MIN_SPAWN_INTERVAL = 0.45
DIFFICULTY_RATE = 0.025
MAX_FRUITS = 5


# =========================================================
# GAME STATES
# =========================================================

ATTRACT = "ATTRACT"
COUNTDOWN = "COUNTDOWN"
PLAYING = "PLAYING"
GAME_OVER = "GAME_OVER"
INITIALS = "INITIALS"
LEADERBOARD = "LEADERBOARD"


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def create_random_fruit():
    x = random.randint(200, WIDTH - 200)
    y = HEIGHT + 50

    # Fruit on left launches toward center
    if x < WIDTH // 2:
        vx = random.randint(50, 250)

    # Fruit on right launches toward center
    else:
        vx = random.randint(-250, -50)

    vy = random.randint(-900, -700)

    return Fruit(
        x=x,
        y=y,
        radius=50,
        vx=vx,
        vy=vy,
    )


def draw_centered_text(
    screen,
    text,
    font,
    y,
    color=(255, 255, 255),
):
    rendered_text = font.render(
        text,
        True,
        color,
    )

    rect = rendered_text.get_rect(
        center=(WIDTH // 2, y)
    )

    screen.blit(rendered_text, rect)


# =========================================================
# SETUP
# =========================================================

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Fruit Ninja")

clock = pygame.time.Clock()

font = pygame.font.Font(None, 48)
title_font = pygame.font.Font(None, 90)
large_font = pygame.font.Font(None, 120)
small_font = pygame.font.Font(None, 36)

tracker = LiveHandTracker()
tracker.start()


# =========================================================
# INITIAL GAME DATA
# =========================================================

fruits = []

score = 0
final_score = 0

time_remaining = GAME_DURATION
spawn_timer = 0.0

state = ATTRACT
state_elapsed = 0.0

player_initials = ""

session_scores = []

running = True


# =========================================================
# MAIN GAME LOOP
# =========================================================

try:
    while running:

        dt = clock.tick(FPS) / 1000.0
        state_elapsed += dt


        # =================================================
        # EVENTS / KEYBOARD INPUT
        # =================================================

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                # -----------------------------------------
                # Developer reset
                # -----------------------------------------

                if event.key == pygame.K_r:
                    fruits = []

                    score = 0
                    final_score = 0

                    time_remaining = GAME_DURATION
                    spawn_timer = 0.0

                    player_initials = ""

                    state = ATTRACT
                    state_elapsed = 0.0


                # -----------------------------------------
                # ATTRACT input
                # -----------------------------------------

                elif state == ATTRACT:

                    if event.key == pygame.K_SPACE:
                        state = COUNTDOWN
                        state_elapsed = 0.0


                # -----------------------------------------
                # INITIALS input
                # -----------------------------------------

                elif state == INITIALS:

                    if event.key == pygame.K_BACKSPACE:
                        player_initials = player_initials[:-1]

                        # Reset inactivity timer
                        state_elapsed = 0.0


                    elif event.key == pygame.K_RETURN:

                        if len(player_initials) > 0:

                            session_scores.append({
                                "name": player_initials,
                                "score": final_score,
                            })

                            session_scores = sorted(
                                session_scores,
                                key=lambda entry: entry["score"],
                                reverse=True,
                            )[:10]

                            state = LEADERBOARD
                            state_elapsed = 0.0


                    elif (
                        event.unicode.isalnum()
                        and len(player_initials) < 3
                    ):
                        player_initials += event.unicode.upper()

                        # Reset inactivity timer
                        state_elapsed = 0.0


        # =================================================
        # STATE TRANSITIONS
        # =================================================

        # -----------------------------------------
        # COUNTDOWN → PLAYING
        # -----------------------------------------

        if state == COUNTDOWN:

            if state_elapsed >= COUNTDOWN_DURATION:

                fruits = []

                score = 0

                time_remaining = GAME_DURATION

                spawn_timer = 0.0

                state = PLAYING
                state_elapsed = 0.0


        # =================================================
        # HAND TRACKING
        # =================================================

        blade, camera_frame = tracker.get_blade_state()

        blade_x = int(blade.x * WIDTH)
        blade_y = int(blade.y * HEIGHT)

        prev_blade_x = int(blade.prev_x * WIDTH)
        prev_blade_y = int(blade.prev_y * HEIGHT)


        # =================================================
        # PLAYING STATE LOGIC
        # =================================================

        if state == PLAYING:

            # -----------------------------------------
            # Update timer
            # -----------------------------------------

            time_remaining = max(
                0,
                time_remaining - dt
            )


            # -----------------------------------------
            # Game finished
            # -----------------------------------------

            if time_remaining <= 0:

                final_score = score

                fruits = []

                state = GAME_OVER
                state_elapsed = 0.0


            # -----------------------------------------
            # Game is still active
            # -----------------------------------------

            else:

                # -------------------------------------
                # Spawn fruit
                # -------------------------------------

                spawn_timer -= dt

                if (
                    spawn_timer <= 0
                    and len(fruits) < MAX_FRUITS
                ):

                    fruits.append(
                        create_random_fruit()
                    )

                    elapsed_time = (
                        GAME_DURATION
                        - time_remaining
                    )

                    spawn_interval = max(
                        MIN_SPAWN_INTERVAL,
                        BASE_SPAWN_INTERVAL
                        - elapsed_time * DIFFICULTY_RATE
                    )

                    spawn_timer = spawn_interval


                # -------------------------------------
                # Update fruit physics
                # -------------------------------------

                for fruit in fruits:
                    fruit.update(dt)


                # -------------------------------------
                # Collision / slicing
                # -------------------------------------

                for fruit in fruits:

                    if (
                        blade.visible
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


                # -------------------------------------
                # Remove dead fruit
                # -------------------------------------

                fruits = [
                    fruit
                    for fruit in fruits
                    if (
                        not fruit.sliced
                        and not fruit.is_offscreen(HEIGHT)
                    )
                ]


        # =================================================
        # OTHER STATE TRANSITIONS
        # =================================================

        if state == GAME_OVER:

            if state_elapsed >= GAME_OVER_DURATION:

                player_initials = ""

                state = INITIALS
                state_elapsed = 0.0


        elif state == INITIALS:

            if state_elapsed >= INITIALS_TIMEOUT:

                player_initials = ""

                state = ATTRACT
                state_elapsed = 0.0


        elif state == LEADERBOARD:

            if state_elapsed >= LEADERBOARD_DURATION:

                state = ATTRACT
                state_elapsed = 0.0


        # =================================================
        # DRAWING
        # =================================================

        screen.fill((30, 30, 30))


        # ---------------------------------------------
        # ATTRACT
        # ---------------------------------------------

        if state == ATTRACT:

            draw_centered_text(
                screen,
                "AI FRUIT NINJA",
                title_font,
                180,
            )

            draw_centered_text(
                screen,
                "Slice fruit using your finger!",
                font,
                290,
            )

            draw_centered_text(
                screen,
                "30 SECOND CHALLENGE",
                font,
                360,
            )

            draw_centered_text(
                screen,
                "Press SPACE to play",
                font,
                470,
            )

            high_score = (
                session_scores[0]["score"]
                if session_scores
                else 0
            )

            draw_centered_text(
                screen,
                f"High Score: {high_score}",
                small_font,
                540,
            )


        # ---------------------------------------------
        # COUNTDOWN
        # ---------------------------------------------

        elif state == COUNTDOWN:

            if state_elapsed < 1:
                countdown_text = "3"

            elif state_elapsed < 2:
                countdown_text = "2"

            elif state_elapsed < 3:
                countdown_text = "1"

            else:
                countdown_text = "GO!"

            draw_centered_text(
                screen,
                countdown_text,
                large_font,
                HEIGHT // 2,
            )


        # ---------------------------------------------
        # PLAYING
        # ---------------------------------------------

        elif state == PLAYING:

            # Draw every fruit
            for fruit in fruits:
                fruit.draw(screen)


            # Score
            score_text = font.render(
                f"Score: {score}",
                True,
                (255, 255, 255),
            )

            screen.blit(
                score_text,
                (20, 20)
            )


            # Timer
            timer_text = font.render(
                f"Time: {time_remaining:.1f}",
                True,
                (255, 255, 255),
            )

            timer_rect = timer_text.get_rect(
                topright=(WIDTH - 20, 20)
            )

            screen.blit(
                timer_text,
                timer_rect
            )


            # Blade
            if blade.visible:

                pygame.draw.circle(
                    screen,
                    (255, 255, 255),
                    (blade_x, blade_y),
                    10,
                )

                pygame.draw.line(
                    screen,
                    (200, 200, 200),
                    (prev_blade_x, prev_blade_y),
                    (blade_x, blade_y),
                    4,
                )


            # Temporary debugging information
            debug_text = small_font.render(
                f"Visible: {blade.visible}  "
                f"Vel: {blade.velocity:.2f}  "
                f"Threshold: {MIN_SLICE_VELOCITY:.2f}",
                True,
                (255, 255, 255),
            )

            screen.blit(
                debug_text,
                (20, 70)
            )


        # ---------------------------------------------
        # GAME OVER
        # ---------------------------------------------

        elif state == GAME_OVER:

            draw_centered_text(
                screen,
                "GAME OVER",
                title_font,
                250,
            )

            draw_centered_text(
                screen,
                f"Final Score: {final_score}",
                font,
                370,
            )


        # ---------------------------------------------
        # INITIALS
        # ---------------------------------------------

        elif state == INITIALS:

            draw_centered_text(
                screen,
                "ENTER YOUR INITIALS",
                title_font,
                220,
            )

            draw_centered_text(
                screen,
                f"Score: {final_score}",
                font,
                330,
            )

            display_initials = player_initials

            while len(display_initials) < 3:
                display_initials += "_"

            draw_centered_text(
                screen,
                display_initials,
                large_font,
                450,
            )

            draw_centered_text(
                screen,
                "Press ENTER when finished",
                small_font,
                550,
            )


        # ---------------------------------------------
        # LEADERBOARD
        # ---------------------------------------------

        elif state == LEADERBOARD:

            draw_centered_text(
                screen,
                "LEADERBOARD",
                title_font,
                100,
            )

            y = 190

            for index, entry in enumerate(
                session_scores,
                start=1
            ):

                draw_centered_text(
                    screen,
                    f"{index}. "
                    f"{entry['name']} - "
                    f"{entry['score']}",
                    small_font,
                    y,
                )

                y += 45


        # =================================================
        # DISPLAY FINISHED FRAME
        # =================================================

        pygame.display.flip()


# =========================================================
# CLEANUP
# =========================================================

finally:
    tracker.stop()
    pygame.quit()