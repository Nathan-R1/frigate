from utils import Q_MIN, Q_MAX, R_MIN, R_MAX, DIRECTION_NAMES, MAX_HEALTH


def get_tile_emoji(tile):
    if not tile or not tile.content:
        return "."
    emojis = "".join(obj.emoji for obj in tile.content)
    return emojis


def tile_label(q, r):
    return f"{q}{chr(r + ord('a'))}"


def display_board(board, players=None):
    print()
    header = "          "
    for q in range(Q_MIN, Q_MAX + 1):
        header += f"  q{q:2d}  "
    print(header)

    for r in range(R_MIN, R_MAX + 1):
        offset = "     " if r % 2 == 0 else ""
        row = f"r={chr(r + ord('a'))}: {offset}"
        for q in range(Q_MIN, Q_MAX + 1):
            tile = board.get_tile(q, r)
            emoji = get_tile_emoji(tile)
            row += f"  {emoji}   "
        print(row)


def display_ship_status(player):
    ship = player.ship
    if not ship.is_alive():
        print(f"\U0001f6a2 {player.name}: DESTROYED")
        return

    hp_bar = _health_bar(ship.health, MAX_HEALTH)
    dir_name = DIRECTION_NAMES[ship.direction] if ship.direction < len(DIRECTION_NAMES) else "?"
    print(
        f"\U0001f6a2 {player.name}: {hp_bar} {ship.health}/{MAX_HEALTH} HP  "
        f"\u26a1 {ship.max_energy - ship.energy_spent}/{ship.max_energy}  "
        f"SPD:{ship.speed}  DIR:{dir_name}  "
        f"@{tile_label(ship.tile.q, ship.tile.r) if ship.tile else '?'}"
    )


def _health_bar(health, max_hp):
    bar_len = 10
    filled = max(0, health)
    filled_len = max(0, min(bar_len, filled * bar_len // max_hp))
    empty_len = bar_len - filled_len
    return "[" + "\u2588" * filled_len + "\u00b7" * empty_len + "]"
