# Frigate Game — Hex Space Combat

## Overview
A 2D turn-based space combat game played on a hexagonal grid. Two ships (player + AI) navigate, manage energy, and attack each other using dice-rolled actions. Rounds consist of 3 turns, each with a pre-declared move and an on-the-fly action.

---

## Coordinate System

- **Axial coordinates** `(q, r)` with pointy-top hexes
- Board bounds: `q ∈ [1, 10]`, `r ∈ [0, 12]` (0 = a, 12 = m) → 130 tiles
- String format: `"1a"` → `(1, 0)`, `"10m"` → `(10, 12)`

### Neighbor Offsets
```
NEIGHBOR_OFFSETS = [
    (1, 0),   # east
    (1, -1),  # northeast
    (0, -1),  # northwest
    (-1, 0),  # west
    (-1, 1),  # southwest
    (0, 1),   # southeast
]
```

### Hex Distance
```python
def hex_distance(a, b):
    return (abs(a[0]-b[0]) + abs(a[1]-b[1]) + abs(a[0]+a[1] - b[0]-b[1])) // 2
```

---

## File Structure

```
/workspace/frigate-test-client/
├── main.py       # Entry point: game init, human input, main loop
├── game.py       # Game class: setup, round/turn orchestration
├── board.py      # Tile + Board classes
├── objects.py    # Object (ABC), Ship, Asteroid, Projectile, Deployable, TorpedoDeployable
├── actions.py    # Action (ABC), all concrete move/attack/deploy actions
├── player.py     # Player class, human prompts, AI behavior
├── display.py    # Console rendering (hex board + status bars)
└── utils.py      # Constants, hex math, dice rolls, coord parsing
```

---

## Constants (`utils.py`)

```python
NEIGHBOR_OFFSETS = [(1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)]
Q_MIN, Q_MAX = 1, 10
R_MIN, R_MAX = 0, 12           # a=0 … m=12
MAX_ENERGY = 6
MAX_HEALTH = 10
D6_HIT_THRESHOLD = 2            # d6 ≤ 2 → hit (33%)
TORPEDO_DEPLOY_RANGE = 8
AI_DESIRED_RANGE = 3
```

---

## Classes

### `Tile` (`board.py`)
| Field/Method | Type/Returns | Description |
|---|---|---|---|
| `q`, `r` | `int` | Axial coordinates |
| `content` | `list[Object]` | Objects occupying this tile (empty list = unoccupied) |
| `get_adj()` | `list[tuple[int,int]]` | Valid neighbor coords within bounds |
| `get_xy_coord()` | `tuple[float,float]` | Pixel coords for display |
| `get_content()` | `list[Object]` | Returns the content list |
| `is_occupied()` | `bool` | True if content list is non-empty |
| `place(obj)` | `void` | Append object to content list |
| `remove(obj)` | `void` | Remove specific object from content list |

### `Board` (`board.py`)
| Method | Returns | Description |
|---|---|---|
| `get_tile(q, r)` | `Tile \| None` | Lookup by coord |
| `place_object(obj, q, r)` | `void` | Place object at tile |
| `remove_object(obj)` | `void` | Remove from board |
| `is_valid(q, r)` | `bool` | Within bounds |
| `get_all_objects()` | `list[Object]` | All objects on board |
| `get_objects_of_type(cls)` | `list[Object]` | Filtered by type |

### `Object` (`objects.py`) — ABC
| Field | Type | Default |
|---|---|---|
| `name` | `str` | — |
| `emoji` | `str` | — |
| `tile` | `Tile` | — |
| `speed` | `int` | 0 |
| `direction` | `int` (0-5) | 0 |
| `owner` | `Player \| None` | None |

### `Ship(Object)` (`objects.py`)
| Field | Default |
|---|---|
| `health` | 10 |
| `max_energy` | 6 |
| `energy_spent` | 0 (resets each round) |

| Method | Description |
|---|---|
| `take_damage(amount)` | Reduce health |
| `is_alive()` | `health > 0` |

### `Asteroid(Object)` (`objects.py`)
Static obstacle. Speed = 0. Blocks movement.

### `Projectile(Object)` (`objects.py`)
| Field | Description |
|---|---|
| `damage` | Damage on hit |
| `owner` | Who fired it |

| Method | Description |
|---|---|
| `advance()` | Move speed hexes in direction |
| `on_hit(target)` | Apply damage |

### `Deployable(Object)` (`objects.py`) — ABC
Player-owned deployable. `owner: Player`

### `TorpedoDeployable(Deployable)` (`objects.py`)
| Field | Value |
|---|---|
| `range` | 8 |
| `attacks` | 1 |
| `damage` | 4 |

On the player's turn, choosing `CommandTorpedo` as the non-move action lets the player pick one of two sub-actions for the torpedo:
- `Attack(target)` — fire at target within range 8 with LOS, then self-destruct
- `Destroy()` — self-destruct (no attack, no range needed)

Both sub-actions consume the torpedo (self-damage = all, torpedo removed from board).

---

## Actions (`actions.py`)

### `Action` (ABC)
| Field | Type |
|---|---|
| `name` | `str` |
| `energy_cost` | `int` |
| `execute(actor, game)` | `bool` |

### Move Actions (pre-declared, 3 per round)

| Class | Energy | Effect |
|---|---|---|
| `GravitonPlus` | 2 | `speed += 1` |
| `GravitonMinus` | 2 | `speed = max(0, speed-1)` |
| `TurnCW` | 1 | `direction = (dir+1) % 6` |
| `TurnCCW` | 1 | `direction = (dir-1) % 6` |
| `NullMove` | 0 | No change |

### Non-Move Actions (chosen on the fly, 1 per turn)

| Class | Energy | Range | Attacks | Dmg | Description |
|---|---|---|---|---|---|
| `PD` | 1 | 1 | 3 | 2 | Point defense |
| `Cannons` | 1 | 4 | 2 | 2 | Main cannons |
| `TorpedoDeploy` | 1 | 8 | — | — | Deploy torpedo at target tile |
| `CommandTorpedo` | 0 | — | — | — | Command owned torpedo: Attack(target≤8) or Destroy. Torpedo consumed either way. |
| `NullAction` | 0 | — | — | — | Skip bonus action |

### Attack Resolution
```python
# Step 1: Check line of sight — asteroids block fire
if not has_line_of_sight(attacker_tile, target_tile, board):
    return  # blocked by asteroid, attack fails

# Step 2: Roll attacks
for _ in range(num_attacks):
    if random.randint(1, 6) <= D6_HIT_THRESHOLD:  # 33%
        target.take_damage(damage)
```

### Line of Sight
All attacks require an unobstructed line between attacker and target. Asteroids are the only blocking objects (ships and deployables do not block).

```python
def has_line_of_sight(start_tile, end_tile, board):
    """Returns True if no asteroid lies on the hex line between start and end."""
    line_hexes = hex_line_between(
        (start_tile.q, start_tile.r),
        (end_tile.q, end_tile.r)
    )
    # Exclude the start and end tiles themselves
    for q, r in line_hexes[1:-1]:
        tile = board.get_tile(q, r)
        if tile and any(isinstance(o, Asteroid) for o in tile.content):
            return False
    return True
```

Hex line interpolation uses cube-coordinate rounding to find all hexes on the segment:

```python
def hex_line_between(a, b):
    """Returns list of (q,r) hexes from a to b inclusive."""
    # Convert axial (q,r) to cube (x,y,z): x=q, z=r, y=-x-z
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

    dist = hex_distance(a, b)
    ax, ay, az = axial_to_cube(*a)
    bx, by, bz = axial_to_cube(*b)
    results = []
    for i in range(dist + 1):
        t = i / max(dist, 1)
        cx, cy, cz = cube_round(
            ax + (bx - ax) * t,
            ay + (by - ay) * t,
            az + (bz - az) * t
        )
        results.append((cx, -cx - cz, cz))  # cube → axial
    return results
```

---

## Player (`player.py`)

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Display name |
| `ship` | `Ship` | Player's ship |
| `is_human` | `bool` | Human or AI |
| `moves_queue` | `list[Action]` | 3 pre-declared moves |
| `deployables` | `list[Deployable]` | Owned deployables on board |

### AI Logic

**Declare moves:**
```
for slot in 0..2:
    dist = hex_distance(ship.pos, enemy.pos)
    target_dir = direction_toward(enemy)
    
    if dist > desired_range and not facing(target_dir):
        turn toward enemy
    elif dist < desired_range and not facing(away_from_enemy):
        turn away from enemy
    elif dist > desired_range:
        GravitonPlus (accelerate toward)
    elif dist < desired_range:
        GravitonPlus (accelerate away)
    else:
        NullMove
```

**Choose non-move action:**
```
if has_torpedo and torpedo_in_range(enemy) and has_los(torpedo, enemy):
    CommandTorpedoAttack(enemy.pos)
elif distance <= 4 and has_los(my_ship, enemy):
    Cannons(enemy.pos)
elif distance <= 1 and has_los(my_ship, enemy):
    PD(enemy.pos)
elif can_deploy_torpedo(enemy):
    TorpedoDeploy(toward_enemy)
else:
    NullAction
```

If no weapon has line of sight, AI deploys a torpedo or skips (NullAction).

---

## Game Loop (`game.py`)

### Setup
1. Create Board (130 tiles)
2. Player ship at `(1, 6)`, AI ship at `(10, 6)`
3. Scatter 8 Asteroids on random unoccupied tiles
4. Display initial board

### Round Flow

```
ROUND START
│
├── 1. DECLARATION
│     Human: pick 3 moves from [Graviton+, Graviton-, TurnCW, TurnCCW, Null]
│     AI: auto-generates 3 moves via AI logic
│
├── 2. TURN 0
│     ├── 1. Move Resolution
│     │     a. Both pre-declared moves[N] resolve (speed/dir changes)
│     │
│     ├── 2. Ship Movement (Concurrent)
│     │     ├── Phase 1 — Calculate Intended Destinations
│     │     │     For each ship, step `speed` tiles in `direction` along a path,
│     │     │     stopping at asteroids or board edges (NOT at other ships).
│     │     │     Record `intended_dest` (the last reachable tile).
│     │     │
│     │     └── Phase 2 — Resolve Ship-Ship Conflicts
│     │           For each pair (A, B):
│     │           • Swap: A.dest == B.origin AND B.dest == A.origin
│     │               → both stay put, both take 3 crash damage
│     │           • Same hex: A.dest == B.dest (and that tile is empty)
│     │               → both stay put, both take 3 crash damage
│     │           • Enter occupied: A.dest == B.origin (B not leaving)
│     │               → A stays put, both take 3 crash damage
│     │           Check order: swap first, then same hex, then enter occupied.
│     │
│     ├── 3. Projectile Movement
│     │     a. All projectiles advance speed tiles in their direction
│     │     b. Collision: projectile↔ship = damage, projectile↔asteroid = both destroyed
│     │
│     └── 4. Action Phase
│           a. Human picks non-move action
│           b. AI picks non-move action
│           c. Both resolve simultaneously
│           d. Collision detection for new projectiles
│           e. Display board + status
│
├── 3. TURN 1 (same flow with moves[1])
│
├── 4. TURN 2 (same flow with moves[2])
│
└── 5. SETTLEMENT
      for each player:
          excess = energy_spent - max_energy
          if excess > 0: ship.take_damage(excess)
          energy_spent = 0
      check_winner()
```

### Concurrent Ship Movement

```python
# ── Phase 1: Intended Destinations ──
for ship in ships:
    current = ship.tile
    for _ in range(ship.speed):
        dq, dr = NEIGHBOR_OFFSETS[ship.direction]
        next_tile = board.get_tile(current.q + dq, current.r + dr)
        if not next_tile or any(isinstance(o, Asteroid) for o in next_tile.content):
            break
        current = next_tile
    ship.intended_dest = current

# ── Phase 2: Conflict Resolution ──
for each pair (ship_a, ship_b):
    origin_a, dest_a = ship_a.tile, ship_a.intended_dest
    origin_b, dest_b = ship_b.tile, ship_b.intended_dest

    if dest_a == origin_b and dest_b == origin_a:
        # SWAP — both stay, crash
        ship_a.intended_dest = origin_a
        ship_b.intended_dest = origin_b
        ship_a.take_damage(3); ship_b.take_damage(3)

    elif dest_a == dest_b:
        # SAME HEX — both stay, crash
        ship_a.intended_dest = origin_a
        ship_b.intended_dest = origin_b
        ship_a.take_damage(3); ship_b.take_damage(3)

    elif dest_a == origin_b and dest_b != origin_a:
        # ENTER OCCUPIED — A stays, crash
        ship_a.intended_dest = origin_a
        ship_a.take_damage(3); ship_b.take_damage(3)

    elif dest_b == origin_a and dest_a != origin_b:
        # symmetric: B tries to enter A's tile
        ship_b.intended_dest = origin_b
        ship_a.take_damage(3); ship_b.take_damage(3)

# ── Execute Movement ──
for ship in ships:
    if ship.intended_dest != ship.tile:
        ship.tile.remove(ship)
        ship.intended_dest.place(ship)
        ship.tile = ship.intended_dest
```

### Collision Cases
- **Projectile hits Ship**: projectile removed, ship takes damage
- **Projectile hits Asteroid**: both removed
- **Projectile hits Deployable**: projectile removed, deployable destroyed
- **Ship-ship crash** (swap / same hex / enter occupied): both ships stay at origin, both take 3 damage
- **Ship vs Asteroid**: handled in Phase 1 path calc — ship stops before asteroid, no additional damage

---

## Energy Accounting

```
Each action execution adds action.energy_cost to ship.energy_spent

End of round:
    excess = max(0, ship.energy_spent - ship.max_energy)   # max_energy = 6
    if excess > 0:
        ship.health -= excess
    ship.energy_spent = 0
```

Example: 3× Graviton+ (6 energy) + 3× Cannons (3 energy) = 9 energy → 3 self-damage

---

## Display (`display.py`)

### Board Rendering
Pointy-top hex grid with content emojis:

```
            1a 🚢      1b  .       1c  .
       2a  .       2b  .       2c 🪨
  3a  .       3b  .       3c  .
```

### Status Bars
```
🚢 Player  [████████··] 8/10 HP  ⚡ 4/6  SPD:2  DIR:E
🚢 Enemy   [████······] 4/10 HP  ⚡ 2/6  SPD:1  DIR:NE
```

---

## Win Condition
A ship reaches `health ≤ 0` → other player wins. Game ends immediately.

---

## Implementation Order

| Step | Files | Description |
|---|---|---|
| 1 | `utils.py` | Constants, hex math, dice, coord parsing |
| 2 | `board.py` | Tile + Board classes |
| 3 | `objects.py` | Object hierarchy (Ship, Asteroid, Projectile, Torpedo) |
| 4 | `actions.py` | All action classes |
| 5 | `player.py` | Player class + AI logic |
| 6 | `game.py` | Game orchestration (setup, round, turn, collisions) |
| 7 | `display.py` | Console rendering |
| 8 | `main.py` | Main loop, human input, wire everything |

---

## Edge Cases / Notes
- **Speed cap**: No explicit cap (speed can grow large, player must manage energy)
- **Direction 0-5**: Maps to `NEIGHBOR_OFFSETS` index
- **Multiple objects per tile**: Allowed — `Tile.content` is a list. Ships block other ships from moving into their tile, but deployables/projectiles can share a tile with other objects.
- **Projectile expiry**: Leave board bounds → removed automatically
- **Torpedo sub-actions**: Player picks Attack(target) or Destroy() when commanding. Attack requires valid target within torpedo's range and line of sight from torpedo to target.
- **Line of sight**: All attacks require unobstructed hex line between shooter and target. Asteroids are the only blocking terrain. Ships and deployables do not block LOS.
- **Simultaneous ship movement**: Intended destinations calculated in parallel, then Phase 2 resolves conflicts deterministically (swap → same hex → enter occupied). Crash damage applied to both ships immediately on conflict. Actions resolve in Phase 4 with no ordering advantage.
- **Edge tiles**: `get_adj()` only returns valid coords within bounds
