from utils import (
    hex_distance, NEIGHBOR_OFFSETS, firing_arc_los,
    TORPEDO_DEPLOY_RANGE, TORPEDO_ATTACK_RANGE,
)
from objects import Ship, TorpedoDeployable
from actions import (
    Accelerate, Decelerate, NullMove,
    PD, Cannons, TorpedoDeploy, CommandTorpedo, NullAction,
)

AI_DESIRED_RANGE = 3


class Player:
    def __init__(self, name, ship, is_human=False):
        self.name = name
        self.ship = ship
        self.is_human = is_human
        self.deployables = []

    def direction_toward(self, from_coord, to_coord):
        best_dir = 0
        best_dist = 999
        for i, (dq, dr) in enumerate(NEIGHBOR_OFFSETS):
            nq = from_coord[0] + dq
            nr = from_coord[1] + dr
            d = hex_distance((nq, nr), to_coord)
            if d < best_dist:
                best_dist = d
                best_dir = i
        return best_dir

    def direction_away(self, from_coord, to_coord):
        return (self.direction_toward(from_coord, to_coord) + 3) % 6

    def choose_future_move(self, game):
        enemy = None
        for p in game.players:
            if p != self and p.ship.is_alive():
                enemy = p
                break
        if not enemy:
            return NullMove()

        my_pos = (self.ship.tile.q, self.ship.tile.r)
        enemy_pos = (enemy.ship.tile.q, enemy.ship.tile.r)
        dist = hex_distance(my_pos, enemy_pos)
        target_dir = self.direction_toward(my_pos, enemy_pos)
        away_dir = self.direction_away(my_pos, enemy_pos)

        if dist > AI_DESIRED_RANGE:
            if self.ship.direction != target_dir:
                diff = (target_dir - self.ship.direction) % 6
                if diff <= 3 and self.ship.turning > 0 and self.ship.speed <= self.ship.navigation:
                    return NullMove()
                else:
                    return Accelerate()
            else:
                return Accelerate()
        elif dist < AI_DESIRED_RANGE:
            if self.ship.direction != away_dir:
                diff = (away_dir - self.ship.direction) % 6
                if diff <= 3 and self.ship.turning > 0 and self.ship.speed <= self.ship.navigation:
                    return NullMove()
                else:
                    return Accelerate()
            else:
                return Accelerate()
        else:
            return NullMove()

    def choose_non_move_action(self, game):
        if not self.ship.is_alive():
            return NullAction()

        enemy = None
        for p in game.players:
            if p != self and p.ship.is_alive():
                enemy = p
                break
        if not enemy:
            return NullAction()

        ship = self.ship
        my_tile = ship.tile
        enemy_tile = enemy.ship.tile
        enemy_pos = (enemy_tile.q, enemy_tile.r)
        dist = hex_distance((my_tile.q, my_tile.r), enemy_pos)

        for torp in self.deployables:
            if isinstance(torp, TorpedoDeployable) and torp.tile:
                torp_dist = hex_distance(
                    (torp.tile.q, torp.tile.r), enemy_pos
                )
                if torp_dist <= TORPEDO_ATTACK_RANGE:
                    return CommandTorpedo(torp, "Attack", enemy_tile.q, enemy_tile.r)

        if ship.energy >= 1 and ship.uses_left.get("Cannons", 1) > 0:
            for arc_dir in range(6):
                if not ship.firing_arcs[arc_dir]:
                    continue
                if dist <= 4 and firing_arc_los(
                    my_tile, arc_dir, 4, enemy_tile.q, enemy_tile.r, game.board,
                ):
                    return Cannons(enemy_tile.q, enemy_tile.r, arc_dir)

        if ship.energy >= 1 and ship.uses_left.get("PD", 1) > 0:
            for arc_dir in range(6):
                if not ship.firing_arcs[arc_dir]:
                    continue
                if dist <= 1 and firing_arc_los(
                    my_tile, arc_dir, 1, enemy_tile.q, enemy_tile.r, game.board,
                ):
                    return PD(enemy_tile.q, enemy_tile.r, arc_dir)

        if ship.energy >= 1 and ship.uses_left.get("Torpedo Deploy", 1) > 0:
            if dist <= TORPEDO_DEPLOY_RANGE:
                return TorpedoDeploy(enemy_tile.q, enemy_tile.r)

        return NullAction()
