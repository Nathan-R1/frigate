# Frigate — Hex Space Combat

A 2D turn-based space combat game played on a hexagonal grid. Two ships — you and an AI opponent — navigate through space, manage shields and energy, plan their movement several turns in advance, and attack using directional weapon arcs.

## Quick Start

```bash
python3 main.py
```

Requires Python 3.10+.

Standard library only — no additional packages are required.

---

# How to Play

Combat is turn-based. Each **round consists of a single turn**.

On your turn, your ship automatically resolves its planned movement before you take actions. You then perform any actions available to your ship before ending your turn.

Once your turn ends, the enemy takes its turn.

---

# Turn Structure

Each turn has two phases:

1. **Start of Turn** — energy, movement, turning, and future movement are resolved.
2. **Action Phase** — take any available actions, then end your turn.

## Start of Turn

At the beginning of your turn, resolve the following steps in order.

### 1. Recharge Energy

Your ship regains energy according to its recharge rules, up to its `Max Energy`.

### 2. Apply Future Move 1

Your current `Future Move 1` is applied.

A Future Move modifies your ship's movement state, such as changing its speed.

### 3. Turning

After updating your speed:

> If `Speed <= Navigation`, you may turn up to your ship's `Turning` total.

Turning changes the direction your ship is facing.

You may turn through one or more hex directions, up to the maximum allowed by your `Turning` stat.

### 4. Travel

Your ship now travels in the direction it is currently facing.

It moves a number of hexes equal to its new `Speed`.

### 5. Cycle Future Moves

After movement resolves, your planned moves advance:

```text
Future Move 1 ← Future Move 2
Future Move 2 ← Future Move 3
Future Move 3 ← New Move
```

Your old `Future Move 1` has now been resolved.

### 6. Set a New Future Move 3

Choose a new `Future Move 3`.

This means that movement is always planned **three turns in advance**.

At any given time, your ship has:

- `Future Move 1` — resolves on the next turn.
- `Future Move 2` — resolves after that.
- `Future Move 3` — resolves after that.

You can only choose the new third move when the queue cycles.

---

# Action Phase

After the automatic start-of-turn sequence has finished, you may take actions.

You may take **any number of actions available to your ship**, provided you meet that action's requirements.

Actions may have different rules regarding:

- Energy cost
- Range
- Line of Sight
- Available firing arcs
- Usage limits
- Other resource requirements

Generally:

- Actions cost Energy to perform.
- Actions can only be used once per round.

However, individual actions may override either of these rules.

Some actions may:

- Cost no Energy.
- Be usable multiple times per round.
- Have special restrictions or requirements.

When you are finished taking actions, end your turn.

The enemy then begins its turn.

---

# Ship Statistics

Each ship has the following statistics.

| Stat | Description |
|---|---|
| `Hull HP` | The ship's current hull integrity. |
| `Max Hull` | The maximum amount of Hull HP the ship can have. |
| `Shield HP` | The ship's current shield strength. |
| `Max Shield` | The maximum amount of Shield HP the ship can have. |
| `Energy` | The ship's currently available energy. |
| `Max Energy` | The maximum amount of energy the ship can store. |
| `Storage` | The ship's available storage capacity. |
| `Scan Range` | The maximum range at which the ship can scan. |
| `Turning` | The maximum number of hex directions the ship may turn when turning is allowed. |
| `Speed` | The ship's current speed. |
| `Future Move 1` | The movement change that will resolve on the next turn. |
| `Future Move 2` | The movement change that will resolve after Future Move 1. |
| `Future Move 3` | The movement change that will resolve after Future Move 2. |

A ship also has a current **facing direction**, which determines both its movement direction and the orientation of its firing arcs.

---

# Firing Arcs

Each ship has an array of six firing arcs.

Each arc corresponds to one of the six directions surrounding a hex.

Each arc has a value of either:

```text
true
```

or:

```text
false
```

A value of `true` means that the arc is available for firing.

A value of `false` means that weapons cannot fire through that arc.

When attacking, a weapon must have an available firing arc that can establish Line of Sight to the target.

---

# Line of Sight

A weapon's Line of Sight is determined by its:

- **Firing Arc**
- **Range**

Each firing arc has a **primary direction**.

To determine whether a target is within Line of Sight, construct the weapon's firing area using the following process.

## Step 1: Project the Primary Line

Starting from the ship, project a straight line in the firing arc's primary direction.

The line extends a number of hexes equal to the weapon's `Range`.

## Step 2: Extend Adjacent Directions

From **each hex on the primary line**, extend Line of Sight outward in the two hex directions immediately adjacent to the primary direction.

Each adjacent line may extend up to the weapon's `Range`.

## Step 3: Determine Valid Targets

All hexes reached by this process are within the weapon's Line of Sight.

The resulting area forms a wedge extending outward from the selected firing arc.

A hex is a valid target if it lies within this resulting Line of Sight area.

---

## Example — Front Arc, Range 4

Project a straight line:

```text
Ship → → → →
```

The line extends four hexes directly in front of the ship.

From every hex on that line, extend up to four hexes outward in each of the two directions immediately adjacent to the forward direction.

The resulting wedge-shaped area is the weapon's Line of Sight.

---

## Example — Front Arc, Range 2

Project a line two hexes directly in front of the ship.

From each hex on that line, extend up to two hexes in each of the two directions adjacent to the forward direction.

All hexes reached form the weapon's Line of Sight area.

---

## Example — Side Arc, Range 3

Project a line three hexes directly outward from the selected side of the ship.

From every hex on that line, extend up to three hexes in each of the two directions immediately adjacent to that side-facing direction.

All reached hexes are valid targets for that firing arc.

---

# Combat

Weapons and other combat actions may have their own:

- Energy costs
- Range
- Damage
- Dice rolls
- Firing arc requirements
- Usage limits
- Special effects

To attack a target:

1. Select an available weapon or combat action.
2. Select a valid firing arc, if required.
3. The firing arc must be enabled.
4. The target must be within the weapon's Line of Sight.
5. Resolve the weapon's attack according to its individual rules.

---

# Movement Planning

Movement is not chosen immediately before the ship moves.

Instead, you maintain a rolling queue of three planned Future Moves.

For example:

```text
Turn 1:

Future Move 1: Accelerate
Future Move 2: Turn
Future Move 3: Decelerate
```

At the beginning of the turn:

```text
Accelerate resolves.
```

The queue then becomes:

```text
Future Move 1: Turn
Future Move 2: Decelerate
Future Move 3: [Choose New Move]
```

You then choose a new Future Move 3.

This means you must continually plan your ship's movement **three turns ahead**, while adapting to changes in combat.

---

# Win Condition

Destroy the enemy ship by reducing its Hull HP to `0`.

Shields may absorb damage according to the relevant combat rules, but once a ship's Hull HP reaches `0`, that ship is destroyed.

The remaining ship wins the battle.

---

# Board

The game is played on a hexagonal grid.

The board uses **axial coordinates**.

The playable area is defined by `HEX_RADIUS = 5`, giving valid coordinate values:

```text
q = -5 to 5
r = -5 to 5
```

Coordinates are written as `q,r`, for example:

```text
5,0
-2,3
0,-4
```

Enter target coordinates using this same `q,r` format.

The board may contain:

| Emoji | Meaning |
|---|---|
| Symbol | Meaning |
|---|---|
| →, ↗, ↖, ←, ↙, ↘ | Ship facing in that direction |
| 🪨 | Asteroid |
| 💫 | Torpedo / Deployable |
| `.` | Empty space |

Ships are displayed on the board using directional arrows to show their current facing. The 🚢 ship icon may be used in the status display, but it is not used as the ship's board position.

Terrain, obstacles, deployables, and other objects may affect movement, scanning, Line of Sight, or combat according to their individual rules.

---

# Controls

Controls depend on the currently available action or prompt.

Typical inputs include:

- Movement or Future Move selections.
- Action selections numbered `1`–`4`.
- Press **Enter** with no input to select `Null` when available.
- Target coordinates in `q,r` format, such as `5,0`.
- Firing arc selections where required.
- `q` or `Ctrl+C` to quit.
