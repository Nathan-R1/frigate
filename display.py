from utils import HEX_RADIUS, is_valid_hex, DIRECTION_NAMES, MAX_HEALTH
from objects import Ship

DIRECTION_ARROWS = ["\u2192", "\u2197", "\u2196", "\u2190", "\u2199", "\u2198"]
SCALE = 4


def get_tile_emoji(tile):
    if not tile or not tile.content:
        return "\u00b7"
    parts = []
    for obj in tile.content:
        if isinstance(obj, Ship):
            parts.append(DIRECTION_ARROWS[obj.direction])
        else:
            parts.append(obj.emoji)
    return "\u200b".join(parts)


def tile_label(q, r):
    return f"{q},{r}"


def row_q_range(r):
    min_q = max(-HEX_RADIUS, -HEX_RADIUS - r)
    max_q = min(HEX_RADIUS, HEX_RADIUS - r)
    return min_q, max_q


def hex_to_pos(q, r):
    return (q + r / 2) * SCALE


def render_board(board, players=None):
    lines = []
    min_x = -HEX_RADIUS * SCALE
    max_x = HEX_RADIUS * SCALE
    width = max_x - min_x + 1
    offset_x = -min_x

    for r in range(-HEX_RADIUS, HEX_RADIUS + 1):
        min_q, max_q = row_q_range(r)
        line = [" "] * width
        for q in range(min_q, max_q + 1):
            x = hex_to_pos(q, r)
            ix = int(round(x)) + offset_x
            tile = board.get_tile(q, r)
            emoji = get_tile_emoji(tile) if tile else "\u00b7"
            if 0 <= ix < width:
                line[ix] = emoji
        lines.append("".join(line))
        lines.append("")
    return lines


def display_board(board, players=None):
    for line in render_board(board, players):
        print(line)


def render_ship_status(player):
    ship = player.ship
    if not ship.is_alive():
        return f"{ship.emoji} {player.name}: DESTROYED"

    hp_bar = _health_bar(ship.health, MAX_HEALTH)
    dir_name = DIRECTION_NAMES[ship.direction] if ship.direction < len(DIRECTION_NAMES) else "?"
    return (
        f"{ship.emoji} {player.name}: {hp_bar} {ship.health}/{MAX_HEALTH} HP  "
        f"\u26a1 {ship.max_energy - ship.energy_spent}/{ship.max_energy}  "
        f"SPD:{ship.speed}  DIR:{dir_name}  "
        f"@{tile_label(ship.tile.q, ship.tile.r) if ship.tile else '?'}"
    )


def display_ship_status(player):
    print(render_ship_status(player))


def _health_bar(health, max_hp):
    bar_len = 10
    filled = max(0, health)
    filled_len = max(0, min(bar_len, filled * bar_len // max_hp))
    empty_len = bar_len - filled_len
    return "[" + "\u2588" * filled_len + "\u00b7" * empty_len + "]"
