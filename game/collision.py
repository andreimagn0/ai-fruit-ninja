import pygame

def blade_crosses_fruit(
        prev_x,
        prev_y,
        current_x,
        current_y,
        fruit_x,
        fruit_y,
        fruit_radius
):
    # Starting and ending points of the blade movement
    start = pygame.Vector2(prev_x, prev_y)
    end = pygame.Vector2(current_x, current_y)

    # Center of the fruit
    fruit_center = pygame.Vector2(fruit_x, fruit_y)

    # The line traveled by the blade
    blade_path = end - start

    # If the blade did not move, just check whether
    # the point itself is inside the fruit
    if blade_path.length_squared() == 0:
        return fruit_center.distance_to(start) <= fruit_radius

    # Find the point along the blade path that is
    # closest to the center of the fruit
    t = (fruit_center - start).dot(blade_path) / blade_path.length_squared()

    # Keep t between 0 and 1 so we only check
    # the actual blade movement segment
    t = max(0, min(1, t))

    closest_point = start + blade_path * t

    # If that closest point is inside the fruit,
    # then the blade crossed the fruit
    distance = fruit_center.distance_to(closest_point)

    return distance <= fruit_radius