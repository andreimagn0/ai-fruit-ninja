from dataclasses import dataclass


@dataclass(frozen=True)
class BladeState:
    x: float
    y: float
    prev_x: float
    prev_y: float
    visible: bool
    velocity: float
    timestamp: float