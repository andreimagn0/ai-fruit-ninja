import math
import time

import pygame

from shared.blade_state import BladeState

class MouseTracker:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        mouse_x, mouse_y = pygame.mouse.get_pos()

        self.prev_x = mouse_x / width
        self.prev_y = mouse_y / height
        self.prev_time = time.perf_counter()

    def get_blade_state(self):
        current_time = time.perf_counter()
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Convert pixel coordinates into normalized 0.0-1.0 coordinates
        x = mouse_x / self.width
        y = mouse_y / self.height

        # Determine how much time passed since the previous frame
        delta_time = current_time - self.prev_time

        if delta_time <= 0:
            delta_time = 0.000001

        # Calculate how far the mouse moved
        distance = math.hypot(
            x - self.prev_x,
            y - self.prev_y
        )

        velocity = distance / delta_time

        blade = BladeState(
            x=x,
            y=y,
            prev_x=self.prev_x,
            prev_y=self.prev_y,
            visible=True,
            velocity=velocity,
            timestamp=current_time
        )

        return blade