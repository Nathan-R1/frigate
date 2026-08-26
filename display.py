from utils import HEX_RADIUS, is_valid_hex, DIRECTION_NAMES

DIRECTION_ARROWS = ["\u2192", "\u2197", "\u2196", "\u2190", "\u2199", "\u2198"]
SCALE = 4

GREEN = "\033[32m"
RED = "\033[31m"
CYAN = "\033[36m"
RESET = "\033[0m"


def _bar(current, maximum, bar_len=10):
    filled = max(0, min(bar_len, current * bar_len // max(maximum, 1)))
    empty = bar_len - filled
    return "[" + "\u2588" * filled + "\u00b7" * empty + "]"


def get_tile_emoji(tile, players=None, color=True):
    if not tile or not tile.content:
        return "\u00b7"
    parts = []
    for obj in tile.content:
        from objects import Ship
        if isinstance(obj, Ship):
            arrow = DIRECTION_ARROWS[obj.direction]
            if players and color:
                if players[0].ship is obj:
                    parts.append(f"{GREEN}{arrow}{RESET}")
                elif len(players) > 1 and players[1].ship is obj:
                    parts.append(f"{RED}{arrow}{RESET}")
                else:
                    parts.append(arrow)
            else:
                parts.append(arrow)
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


def render_board(board, players=None, color=True):
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
            emoji = get_tile_emoji(tile, players, color) if tile else "\u00b7"
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

    hull_bar = _bar(ship.hull, ship.hull_max)
    shield_bar = _bar(ship.shield, ship.shield_max)
    dir_name = DIRECTION_NAMES[ship.direction] if ship.direction < len(DIRECTION_NAMES) else "?"

    future_str = "  ".join(m.name for m in ship.future_moves) if ship.future_moves else "---"

    return (
        f"{ship.emoji} {player.name}:"
        f"  HP {hull_bar} {ship.hull}/{ship.hull_max}"
        f"  SH {shield_bar} {ship.shield}/{ship.shield_max}"
        f"  \u26a1 {ship.energy}/{ship.max_energy}"
        f"  SPD:{ship.speed}  DIR:{dir_name}"
        f"  NAV:{ship.navigation}  TRN:{ship.turning}"
        f"  @{tile_label(ship.tile.q, ship.tile.r) if ship.tile else '?'}"
        f"\n      FM: [{future_str}]"
    )


def render_firing_arcs(ship):
    marks = []
    for i, enabled in enumerate(ship.firing_arcs):
        label = DIRECTION_NAMES[i]
        mark = f"{GREEN}\u2713{RESET}" if enabled else f"{RED}\u2717{RESET}"
        marks.append(f"{label}:{mark}")
    return "  ".join(marks)


def display_ship_status(player):
    print(render_ship_status(player))


def _health_bar(health, max_hp):
    return _bar(health, max_hp)
