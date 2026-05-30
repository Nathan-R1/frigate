import random

NEIGHBOR_OFFSETS = [
    (1, 0),   # east
    (1, -1),  # northeast
    (0, -1),  # northwest
    (-1, 0),  # west
    (-1, 1),  # southwest
    (0, 1),   # southeast
]

DIRECTION_NAMES = ["E", "NE", "NW", "W", "SW", "SE"]

HEX_RADIUS = 5

MAX_ENERGY = 6
MAX_HEALTH = 10
D6_HIT_THRESHOLD = 2
TORPEDO_DEPLOY_RANGE = 1
AI_DESIRED_RANGE = 3


def hex_coords():
    for q in range(-HEX_RADIUS, HEX_RADIUS + 1):
        for r in range(-HEX_RADIUS, HEX_RADIUS + 1):
            if max(abs(q), abs(r), abs(q + r)) <= HEX_RADIUS:
                yield (q, r)


def is_valid_hex(q, r):
    return max(abs(q), abs(r), abs(q + r)) <= HEX_RADIUS


def hex_distance(a, b):
    return (abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[0] + a[1] - b[0] - b[1])) // 2


def coord_to_string(q, r):
    return f"{q},{r}"


def string_to_coord(s):
    s = s.strip().replace(" ", "")
    parts = s.split(",")
    if len(parts) != 2:
        raise ValueError(f"Invalid coordinate: {s}")
    return (int(parts[0]), int(parts[1]))


def roll_d6():
    return random.randint(1, 6)


def is_hit():
    return roll_d6() <= D6_HIT_THRESHOLD


def axial_to_cube(q, r):
    return (q, -q - r, r)


def cube_round(x, y, z):
    rx, ry, rz = round(x), round(y), round(z)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    return (rx, ry, rz)


def hex_line_between(a, b):
    ax, ay, az = axial_to_cube(*a)
    bx, by, bz = axial_to_cube(*b)
    dist = hex_distance(a, b)
    results = []
    for i in range(dist + 1):
        t = i / max(dist, 1)
        cx, cy, cz = cube_round(
            ax + (bx - ax) * t,
            ay + (by - ay) * t,
            az + (bz - az) * t,
        )
        results.append((cx, cz))
    return results


def has_line_of_sight(start_tile, end_tile, board):
    from objects import Asteroid
    line_hexes = hex_line_between(
        (start_tile.q, start_tile.r),
        (end_tile.q, end_tile.r),
    )
    for q, r in line_hexes[1:-1]:
        tile = board.get_tile(q, r)
        if tile and any(isinstance(o, Asteroid) for o in tile.content):
            return False
    return True


def roll_d6():
    return random.randint(1, 6)


def is_hit():
    return roll_d6() <= D6_HIT_THRESHOLD


def axial_to_cube(q, r):
    return (q, -q - r, r)


def cube_round(x, y, z):
    rx, ry, rz = round(x), round(y), round(z)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    return (rx, ry, rz)


def hex_line_between(a, b):
    ax, ay, az = axial_to_cube(*a)
    bx, by, bz = axial_to_cube(*b)
    dist = hex_distance(a, b)
    results = []
    for i in range(dist + 1):
        t = i / max(dist, 1)
        cx, cy, cz = cube_round(
            ax + (bx - ax) * t,
            ay + (by - ay) * t,
            az + (bz - az) * t,
        )
        results.append((cx, cz))
    return results


def has_line_of_sight(start_tile, end_tile, board):
    from objects import Asteroid
    line_hexes = hex_line_between(
        (start_tile.q, start_tile.r),
        (end_tile.q, end_tile.r),
    )
    for q, r in line_hexes[1:-1]:
        tile = board.get_tile(q, r)
        if tile and any(isinstance(o, Asteroid) for o in tile.content):
            return False
    return True
