# Frigate — Hex Space Combat

A 2D turn-based space combat game on a hexagonal grid. Two ships (you + AI) navigate, manage energy, and attack using dice-rolled actions.

## Quick Start

```bash
python3 main.py
```

Requires Python 3.10+ (standard library only — no pip install needed).

## How to Play

Each **round** has 3 turns. Each turn has 2 parts: a **pre-declared move** (changes speed/direction) and a **non-move action** (attack, deploy torpedo, or skip).

### 1. Declare Your Moves (start of round)

Before the round starts, declare 3 moves — one per turn. Pick from:

| Move | Energy | Effect |
|---|---|---|
| `Graviton+` | 2 | Accelerate +1 |
| `Graviton-` | 2 | Decelerate -1 (min 0) |
| `Turn CW` | 1 | Rotate direction clockwise |
| `Turn CCW` | 1 | Rotate direction counter-clockwise |
| `Null` | 0 | No change |

Your ship drifts `speed` hexes in `direction` each turn automatically.

### 2. Each Turn

1. **Move resolves** — your pre-declared move changes speed/direction
2. **Ships drift simultaneously** — your ship moves `speed` hexes in `direction`
3. **Conflict check** — if ships would swap, enter same hex, or enter an occupied hex, both stay put and take 3 crash damage
4. **Choose a non-move action:**

| Action | Energy | Range | Dice | Dmg | Description |
|---|---|---|---|---|---|
| `PD` (Point Defense) | 1 | 1 | 3 | 2 | Short-range rapid fire |
| `Cannons` | 1 | 4 | 2 | 2 | Medium-range direct fire |
| `Torpedo Deploy` | 1 | 8 | — | — | Deploy a torpedo at a target tile |
| `Command Torpedo` | 0 | — | — | — | Attack with or self-destruct your torpedo |
| `Null` | 0 | — | — | — | Skip |

### 3. Attack Resolution

- Each attack rolls **d6** — hit on **1-2** (33% chance)
- **Line of sight** required: asteroids block fire
- All attacks target a coordinate (e.g. `5g`)

### 4. Torpedo

Deploy a torpedo anywhere within range 8. On subsequent turns, you can command it to:
- **Attack** — fire at a target within range 8 (1 die, 4 dmg), then self-destruct
- **Destroy** — self-destruct immediately (no attack)

### 5. Energy

- Each action costs energy (accumulates during the round)
- At round end: if `energy_spent > max_energy(6)`, excess = direct hull damage
- Energy resets at the start of each round

### 6. Win Condition

Reduce the enemy ship to **0 HP** (starts at 10).

## Controls

- Move choices: enter `1`-`5` (see menu)
- Non-move action: enter `0`-`4` (see menu)
- Target coordinate: enter like `5g` (q + row letter, a-m)
- `q` or `Ctrl+C` at any prompt to quit

## Board

Hex grid with axial coordinates: q=`1`-`10`, r=`a`-`m`. Reference tiles like `7g` or `3b`.

| Emoji | Meaning |
|---|---|
| 🚢 | Ship |
| 🪨 | Asteroid (blocks movement + line of sight) |
| 💫 | Torpedo / Deployable |
| . | Empty space |
