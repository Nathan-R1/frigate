import random


NEIGHBOR_OFFSETS = [
    (1, 0),    # 0 = E
    (1, -1),   # 1 = NE
    (0, -1),   # 2 = NW
    (-1, 0),   # 3 = W
    (-1, 1),   # 4 = SW
    (0, 1),    # 5 = SE
]

DIRECTION_NAMES = ["E", "NE", "NW", "W", "SW", "SE"]

ADJACENT_ARC_DIRECTIONS = [
    (1, 5),
    (0, 2),
    (1, 3),
    (2, 4),
    (3, 5),
    (4, 0),
]

HEX_RADIUS = 5

D6_HIT_THRESHOLD = 2
TORPEDO_DEPLOY_RANGE = 8
TORPEDO_ATTACK_RANGE = 8
TORPEDO_DAMAGE = 4
TORPEDO_ATTACKS = 1


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


def _walk_primary_line(q, r, direction, max_range, board=None):
    from objects import Asteroid
    dq, dr = NEIGHBOR_OFFSETS[direction]
    results = []
    cq, cr = q, r
    for _ in range(max_range):
        cq, cr = cq + dq, cr + dr
        if not is_valid_hex(cq, cr):
            break
        if board is not None:
            tile = board.get_tile(cq, cr)
            if tile and any(isinstance(o, Asteroid) for o in tile.content):
                break
        results.append((cq, cr))
    return results


def _extend_adjacent(q, r, primary_dir, max_range):
    adj_a, adj_b = ADJACENT_ARC_DIRECTIONS[primary_dir]
    daq, dar = NEIGHBOR_OFFSETS[adj_a]
    dbq, dbr = NEIGHBOR_OFFSETS[adj_b]
    results = set()
    for dist in range(1, max_range + 1):
        results.add((q + daq * dist, r + dar * dist))
        results.add((q + dbq * dist, r + dbr * dist))
    return results


def firing_arc_los(ship_tile, arc_direction, max_range, target_q, target_r, board):
    from objects import Asteroid
    primary_line = _walk_primary_line(
        ship_tile.q, ship_tile.r, arc_direction, max_range, board,
    )

    for pq, pr in primary_line:
        if pq == target_q and pr == target_r:
            return True

    for pq, pr in primary_line:
        adjacent = _extend_adjacent(pq, pr, arc_direction, max_range)
        if (target_q, target_r) in adjacent:
            line_hexes = hex_line_between((pq, pr), (target_q, target_r))
            blocked = False
            for lq, lr in line_hexes[1:-1]:
                tile = board.get_tile(lq, lr)
                if tile and any(isinstance(o, Asteroid) for o in tile.content):
                    blocked = True
                    break
            if not blocked:
                return True

    return False


def get_tiles_in_arc(ship_tile, arc_direction, max_range, board):
    from objects import Asteroid

    if arc_direction is None:
        tiles = set()
        for q, r in hex_coords():
            if hex_distance((ship_tile.q, ship_tile.r), (q, r)) <= max_range:
                tiles.add((q, r))
        return tiles

    primary_line = _walk_primary_line(
        ship_tile.q, ship_tile.r, arc_direction, max_range, board,
    )
    tiles = set()

    for pq, pr in primary_line:
        tiles.add((pq, pr))

    for pq, pr in primary_line:
        adjacent = _extend_adjacent(pq, pr, arc_direction, max_range)
        for aq, ar in adjacent:
            if (aq, ar) in tiles:
                continue
            line_hexes = hex_line_between((pq, pr), (aq, ar))
            blocked = False
            for lq, lr in line_hexes[1:-1]:
                tile = board.get_tile(lq, lr)
                if tile and any(isinstance(o, Asteroid) for o in tile.content):
                    blocked = True
                    break
            if not blocked:
                tiles.add((aq, ar))

    return tiles
