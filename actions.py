from abc import ABC, abstractmethod
import random

from utils import D6_HIT_THRESHOLD, TORPEDO_DEPLOY_RANGE, hex_distance, has_line_of_sight, is_hit
from objects import Ship, Projectile, Asteroid, TorpedoDeployable


class Action(ABC):
    def __init__(self, name, energy_cost=0):
        self.name = name
        self.energy_cost = energy_cost

    @abstractmethod
    def execute(self, actor, game):
        pass


# ── Move Actions (pre-declared) ──

class GravitonPlus(Action):
    def __init__(self):
        super().__init__("Graviton+", 2)

    def execute(self, actor, game):
        actor.ship.speed += 1
        actor.ship.energy_spent += self.energy_cost
        return True


class GravitonMinus(Action):
    def __init__(self):
        super().__init__("Graviton-", 2)

    def execute(self, actor, game):
        actor.ship.speed = max(0, actor.ship.speed - 1)
        actor.ship.energy_spent += self.energy_cost
        return True


class TurnCW(Action):
    def __init__(self):
        super().__init__("Turn CW", 1)

    def execute(self, actor, game):
        actor.ship.direction = (actor.ship.direction - 1) % 6
        actor.ship.energy_spent += self.energy_cost
        return True


class TurnCCW(Action):
    def __init__(self):
        super().__init__("Turn CCW", 1)

    def execute(self, actor, game):
        actor.ship.direction = (actor.ship.direction + 1) % 6
        actor.ship.energy_spent += self.energy_cost
        return True


class NullMove(Action):
    def __init__(self):
        super().__init__("Null", 0)

    def execute(self, actor, game):
        return True


# ── Non-Move Actions ──

class PD(Action):
    def __init__(self, target_q, target_r):
        super().__init__("PD", 1)
        self.range_val = 1
        self.num_attacks = 3
        self.damage = 2
        self.target_q = target_q
        self.target_r = target_r

    def execute(self, actor, game):
        ship = actor.ship
        target_tile = game.board.get_tile(self.target_q, self.target_r)
        if not target_tile:
            return False

        dist = hex_distance((ship.tile.q, ship.tile.r), (self.target_q, self.target_r))
        if dist > self.range_val:
            game.log(f"  {actor.name} PD: target out of range")
            return False

        if not has_line_of_sight(ship.tile, target_tile, game.board):
            game.log(f"  {actor.name} PD: blocked by asteroid")
            return False

        targets = [o for o in target_tile.content if isinstance(o, Ship)]
        if not targets:
            return False

        hits = 0
        for _ in range(self.num_attacks):
            if is_hit():
                targets[0].take_damage(self.damage)
                hits += 1

        total_dmg = hits * self.damage
        game.log(f"  {actor.name} PD: {hits}/{self.num_attacks} hits, {total_dmg} total damage")
        ship.energy_spent += self.energy_cost
        return True


class Cannons(Action):
    def __init__(self, target_q, target_r):
        super().__init__("Cannons", 1)
        self.range_val = 4
        self.num_attacks = 2
        self.damage = 2
        self.target_q = target_q
        self.target_r = target_r

    def execute(self, actor, game):
        ship = actor.ship
        target_tile = game.board.get_tile(self.target_q, self.target_r)
        if not target_tile:
            return False

        dist = hex_distance((ship.tile.q, ship.tile.r), (self.target_q, self.target_r))
        if dist > self.range_val:
            game.log(f"  {actor.name} Cannons: target out of range")
            return False

        if not has_line_of_sight(ship.tile, target_tile, game.board):
            game.log(f"  {actor.name} Cannons: blocked by asteroid")
            return False

        targets = [o for o in target_tile.content if isinstance(o, Ship)]
        if not targets:
            return False

        hits = 0
        for _ in range(self.num_attacks):
            if is_hit():
                targets[0].take_damage(self.damage)
                hits += 1

        total_dmg = hits * self.damage
        game.log(f"  {actor.name} Cannons: {hits}/{self.num_attacks} hits, {total_dmg} total damage")
        ship.energy_spent += self.energy_cost
        return True


class TorpedoDeploy(Action):
    def __init__(self, target_q, target_r):
        super().__init__("Torpedo Deploy", 1)
        self.target_q = target_q
        self.target_r = target_r

    def execute(self, actor, game):
        ship = actor.ship
        dist = hex_distance((ship.tile.q, ship.tile.r), (self.target_q, self.target_r))
        if dist > TORPEDO_DEPLOY_RANGE:
            return False

        tile = game.board.get_tile(self.target_q, self.target_r)
        if not tile:
            return False

        torpedo = TorpedoDeployable(tile, actor)
        tile.place(torpedo)
        actor.deployables.append(torpedo)
        from utils import coord_to_string
        game.log(f"  {actor.name} deployed torpedo at {coord_to_string(self.target_q, self.target_r)}")
        ship.energy_spent += self.energy_cost
        return True


class CommandTorpedo(Action):
    def __init__(self, torpedo, sub_action, target_q=None, target_r=None):
        super().__init__("Command Torpedo", 0)
        self.torpedo = torpedo
        self.sub_action = sub_action
        self.target_q = target_q
        self.target_r = target_r

    def execute(self, actor, game):
        if self.sub_action == "Destroy":
            from utils import coord_to_string
            game.log(f"  {actor.name} torpedo at {coord_to_string(self.torpedo.tile.q, self.torpedo.tile.r)} self-destructed")
            game.board.remove_object(self.torpedo)
            if self.torpedo in actor.deployables:
                actor.deployables.remove(self.torpedo)
            return True

        if self.sub_action == "Attack":
            if self.target_q is None:
                return False
            target_tile = game.board.get_tile(self.target_q, self.target_r)
            if not target_tile:
                return False

            dist = hex_distance(
                (self.torpedo.tile.q, self.torpedo.tile.r),
                (self.target_q, self.target_r),
            )
            if dist > self.torpedo.range:
                return False

            if not has_line_of_sight(self.torpedo.tile, target_tile, game.board):
                game.log(f"  {actor.name} Torpedo: blocked by asteroid")
                game.board.remove_object(self.torpedo)
                if self.torpedo in actor.deployables:
                    actor.deployables.remove(self.torpedo)
                return False

            targets = [o for o in target_tile.content if isinstance(o, Ship)]
            if not targets:
                game.board.remove_object(self.torpedo)
                if self.torpedo in actor.deployables:
                    actor.deployables.remove(self.torpedo)
                return False

            hits = 0
            for _ in range(self.torpedo.attacks):
                if is_hit():
                    targets[0].take_damage(self.torpedo.damage)
                    hits += 1

            total_dmg = hits * self.torpedo.damage
            game.log(f"  {actor.name} Torpedo: {hits}/{self.torpedo.attacks} hits, {total_dmg} total damage")

            game.board.remove_object(self.torpedo)
            if self.torpedo in actor.deployables:
                actor.deployables.remove(self.torpedo)
            return True

        return False


class NullAction(Action):
    def __init__(self):
        super().__init__("Null", 0)

    def execute(self, actor, game):
        return True
