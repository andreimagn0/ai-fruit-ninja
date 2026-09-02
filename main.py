import pygame
import random
import cv2
import numpy as np

from vision.hand_tracker import LiveHandTracker
from game.fruit import Fruit
from game.collision import blade_crosses_fruit
from game.effects import Particle, ScorePopup

from leaderboard.leaderboard import load_scores, add_score


# =========================================================
# GAME SETTINGS
# =========================================================

WIDTH = 1280
HEIGHT = 720
FPS = 60

MIN_SLICE_VELOCITY = 0.8
GAME_DURATION = 30.0

MIN_FRUIT_RADIUS = 35
MAX_FRUIT_RADIUS = 50

COUNTDOWN_DURATION = 3.5
GAME_OVER_DURATION = 4.0
NAME_TIMEOUT = 15.0
LEADERBOARD_DURATION = 6.0
MAX_NAME_LENGTH = 14

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
NAME = "NAME"
LEADERBOARD = "LEADERBOARD"


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def render_pip_overlay(
    surface,
    cv_frame,
    pip_width=240,
    margin=20,
):
    if cv_frame is None or cv_frame.size == 0:
        return

    frame_height, frame_width, _ = cv_frame.shape
    pip_height = int(pip_width * (frame_height / frame_width))

    small_frame = cv2.resize(
        cv_frame,
        (pip_width, pip_height),
        interpolation=cv2.INTER_NEAREST,
    )
    rgb_frame = cv2.cvtColor(
        small_frame,
        cv2.COLOR_BGR2RGB,
    )

    surf_array = np.transpose(rgb_frame, (1, 0, 2))
    pip_surface = pygame.surfarray.make_surface(surf_array)

    pip_x = WIDTH - pip_width - margin
    pip_y = HEIGHT - pip_height - margin

    pygame.draw.rect(
        surface,
        (0, 255, 0),
        (pip_x - 2, pip_y - 2, pip_width + 4, pip_height + 4),
        2,
    )
    surface.blit(pip_surface, (pip_x, pip_y))


def create_random_fruit():

    # Random radius
    radius = random.randint(
        MIN_FRUIT_RADIUS,
        MAX_FRUIT_RADIUS
    )

    x = random.randint(200, WIDTH - 200)
    y = HEIGHT + radius

    # Fruit on left launches toward center
    if x < WIDTH // 2:
        vx = random.randint(50, 400)

    # Fruit on right launches toward center
    else:
        vx = random.randint(-400, -50)

    # Launch velocity
    vy = random.randint(-1300, -850)

    return Fruit(
        x=x,
        y=y,
        radius=radius,
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

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED
)
pygame.display.set_caption("AI Fruit Ninja")

slice_sounds = [
    pygame.mixer.Sound("assets/sounds/bamboo-swipe-1.wav"),
    pygame.mixer.Sound("assets/sounds/bamboo-swipe-2.wav"),
    pygame.mixer.Sound("assets/sounds/bamboo-swipe-3.wav"),
    pygame.mixer.Sound("assets/sounds/bamboo-swipe-4.wav"),
]

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

particles = []
score_popups = []
blade_trail = []

score = 0
final_score = 0

time_remaining = GAME_DURATION
spawn_timer = 0.0

state = ATTRACT
state_elapsed = 0.0

player_name = ""

session_scores = load_scores()

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
                if event.key == pygame.K_ESCAPE:
                    running = False
                    continue


                # -----------------------------------------
                # ATTRACT input
                # -----------------------------------------

                elif state == ATTRACT:

                    if event.key == pygame.K_SPACE:
                        state = COUNTDOWN
                        state_elapsed = 0.0


                # -----------------------------------------
                # NAME input
                # -----------------------------------------

                elif state == NAME:

                    if event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]

                        # Reset inactivity timer
                        state_elapsed = 0.0


                    elif event.key == pygame.K_RETURN:

                        player_name = player_name.strip()

                        if len(player_name) > 0:

                            session_scores = add_score(
                                player_name,
                                final_score,
                            )

                            state = LEADERBOARD
                            state_elapsed = 0.0


                    elif len(player_name) < MAX_NAME_LENGTH:

                        # Allow letters
                        if event.unicode.isalpha():
                            player_name += event.unicode

                            state_elapsed = 0.0

                        # Allow a space, but not as the first character
                        # and not twice in a row
                        elif (
                            event.key == pygame.K_SPACE
                            and len(player_name) > 0
                            and not player_name.endswith(" ")
                        ):
                            player_name += " "

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

                particles = []
                score_popups = []
                blade_trail = []

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


            # Update blade trail
            if blade.visible:
                blade_trail.append(
                    (blade_x, blade_y)
                )

                # Only remember the most recent 12 positions
                blade_trail = blade_trail[-8:]

            else:
                blade_trail = []



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
                            random.choice(slice_sounds).play()

                            # Create slice particles
                            for _ in range(12):
                                particles.append(
                                    Particle(
                                        fruit.x,
                                        fruit.y,
                                    )
                                )

                            # Create floating +100 text
                            score_popups.append(
                                ScorePopup(
                                    fruit.x,
                                    fruit.y,
                                    "+100",
                                )
                            )


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

                # Update particles
                for particle in particles:
                    particle.update(dt)

                particles = [
                    particle
                    for particle in particles
                    if not particle.is_dead()
                ]


                # Update score popups
                for popup in score_popups:
                    popup.update(dt)

                score_popups = [
                    popup
                    for popup in score_popups
                    if not popup.is_dead()
                ]


        # =================================================
        # OTHER STATE TRANSITIONS
        # =================================================

        if state == GAME_OVER:

            if state_elapsed >= GAME_OVER_DURATION:

                player_name = ""

                state = NAME
                state_elapsed = 0.0


        elif state == NAME:

            if state_elapsed >= NAME_TIMEOUT:

                player_name = ""

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

            # Draw particles
            for particle in particles:
                particle.draw(screen)

            # Draw floating score popups
            for popup in score_popups:
                popup.draw(
                    screen,
                    small_font,
                )


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

            # Draw blade trail
            if len(blade_trail) >= 2:

                for i in range(
                    1,
                    len(blade_trail)
                ):

                    start = blade_trail[i - 1]
                    end = blade_trail[i]

                    # Trail gets thicker near the fingertip
                    width = max(
                        2,
                        int(
                            8 * i / len(blade_trail)
                        )
                    )

                    pygame.draw.line(
                        screen,
                        (220, 220, 220),
                        start,
                        end,
                        width,
                    )

            # Draw blade fingertip
            if blade.visible:

                pygame.draw.circle(
                    screen,
                    (255, 255, 255),
                    (blade_x, blade_y),
                    10,
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
        # NAME
        # ---------------------------------------------

        elif state == NAME:

            draw_centered_text(
                screen,
                "ENTER YOUR NAME",
                title_font,
                220,
            )

            draw_centered_text(
                screen,
                f"Score: {final_score}",
                font,
                330,
            )

            display_name = player_name + "_"

            draw_centered_text(
                screen,
                display_name,
                title_font,
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

        render_pip_overlay(screen, camera_frame, pip_width=240)
        pygame.display.flip()


# =========================================================
# CLEANUP
# =========================================================

finally:
    tracker.stop()
    pygame.quit()