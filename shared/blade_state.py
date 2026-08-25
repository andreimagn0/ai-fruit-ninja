import time
from dataclasses import dataclass


@dataclass
class BladeState:
    x: float  # Normalized [0.0, 1.0]
    y: float  # Normalized [0.0, 1.0]
    prev_x: float
    prev_y: float
    velocity: float  # Normalized screen space / second
    visible: bool
    timestamp: float

    @classmethod
    def create(
        cls,
        x: float,
        y: float,
        prev_x: float,
        prev_y: float,
        visible: bool,
        prev_timestamp: float,
        is_reacquired: bool = False,
    ):
        now = time.perf_counter()

        # Force velocity to 0.0 on reacquisition or loss to avoid velocity spikes
        if is_reacquired or not visible:
            vel = 0.0
        else:
            dt = max(now - prev_timestamp, 1e-5)
            dx = x - prev_x
            dy = y - prev_y
            vel = (dx**2 + dy**2) ** 0.5 / dt

        return cls(
            x=x,
            y=y,
            prev_x=prev_x,
            prev_y=prev_y,
            velocity=vel,
            visible=visible,
            timestamp=now,
        )