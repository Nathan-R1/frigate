from abc import ABC, abstractmethod
import random

from utils import (
    D6_HIT_THRESHOLD, TORPEDO_DEPLOY_RANGE, TORPEDO_ATTACK_RANGE,
    TORPEDO_DAMAGE, TORPEDO_ATTACKS,
    hex_distance, firing_arc_los, is_hit,
)
from objects import Ship, Asteroid, TorpedoDeployable


class Action(ABC):
    def __init__(self, name, energy_cost=0):
        self.name = name
        self.energy_cost = energy_cost

    @abstractmethod
    def execute(self, actor, game):
        pass


class Accelerate(Action):
    def __init__(self):
        super().__init__("Accelerate", 2)

    def execute(self, actor, game):
        actor.ship.speed += 1
        return True


class Decelerate(Action):
    def __init__(self):
        super().__init__("Decelerate", 2)

    def execute(self, actor, game):
        actor.ship.speed = max(0, actor.ship.speed - 1)
        return True


class NullMove(Action):
    def __init__(self):
        super().__init__("Null", 0)

    def execute(self, actor, game):
        return True


class PD(Action):
    def __init__(self, target_q, target_r, arc_direction):
        super().__init__("PD", 1)
        self.range_val = 1
        self.num_attacks = 3
        self.damage = 2
        self.target_q = target_q
        self.target_r = target_r
        self.arc_direction = arc_direction

    def execute(self, actor, game):
        ship = actor.ship

        if not ship.firing_arcs[self.arc_direction]:
            game.log(f"  {actor.name} PD: arc not enabled")
            return False

        uses = ship.uses_left.get("PD", 1)
        if uses <= 0:
            game.log(f"  {actor.name} PD: no uses left this turn")
            return False

        dist = hex_distance(
            (ship.tile.q, ship.tile.r), (self.target_q, self.target_r)
        )
        if dist > self.range_val:
            game.log(f"  {actor.name} PD: target out of range")
            return False

        if not firing_arc_los(
            ship.tile, self.arc_direction, self.range_val,
            self.target_q, self.target_r, game.board,
        ):
            game.log(f"  {actor.name} PD: no line of sight")
            return False

        target_tile = game.board.get_tile(self.target_q, self.target_r)
        targets = [o for o in target_tile.content if isinstance(o, Ship)]
        if not targets:
            return False

        hits = 0
        for _ in range(self.num_attacks):
            if is_hit():
                targets[0].take_damage(self.damage)
                hits += 1

        total_dmg = hits * self.damage
        game.log(
            f"  {actor.name} PD: {hits}/{self.num_attacks} hits, "
            f"{total_dmg} total damage"
        )
        ship.energy -= self.energy_cost
        ship.uses_left["PD"] = uses - 1
        return True


class Cannons(Action):
    def __init__(self, target_q, target_r, arc_direction):
        super().__init__("Cannons", 1)
        self.range_val = 4
        self.num_attacks = 2
        self.damage = 2
        self.target_q = target_q
        self.target_r = target_r
        self.arc_direction = arc_direction

    def execute(self, actor, game):
        ship = actor.ship

        if not ship.firing_arcs[self.arc_direction]:
            game.log(f"  {actor.name} Cannons: arc not enabled")
            return False

        uses = ship.uses_left.get("Cannons", 1)
        if uses <= 0:
            game.log(f"  {actor.name} Cannons: no uses left this turn")
            return False

        dist = hex_distance(
            (ship.tile.q, ship.tile.r), (self.target_q, self.target_r)
        )
        if dist > self.range_val:
            game.log(f"  {actor.name} Cannons: target out of range")
            return False

        if not firing_arc_los(
            ship.tile, self.arc_direction, self.range_val,
            self.target_q, self.target_r, game.board,
        ):
            game.log(f"  {actor.name} Cannons: no line of sight")
            return False

        target_tile = game.board.get_tile(self.target_q, self.target_r)
        targets = [o for o in target_tile.content if isinstance(o, Ship)]
        if not targets:
            return False

        hits = 0
        for _ in range(self.num_attacks):
            if is_hit():
                targets[0].take_damage(self.damage)
                hits += 1

        total_dmg = hits * self.damage
        game.log(
            f"  {actor.name} Cannons: {hits}/{self.num_attacks} hits, "
            f"{total_dmg} total damage"
        )
        ship.energy -= self.energy_cost
        ship.uses_left["Cannons"] = uses - 1
        return True


class TorpedoDeploy(Action):
    def __init__(self, target_q, target_r):
        super().__init__("Torpedo Deploy", 1)
        self.target_q = target_q
        self.target_r = target_r

    def execute(self, actor, game):
        ship = actor.ship

        uses = ship.uses_left.get("Torpedo Deploy", 1)
        if uses <= 0:
            game.log(f"  {actor.name} Torpedo Deploy: no uses left this turn")
            return False

        dist = hex_distance(
            (ship.tile.q, ship.tile.r), (self.target_q, self.target_r)
        )
        if dist > TORPEDO_DEPLOY_RANGE:
            return False

        tile = game.board.get_tile(self.target_q, self.target_r)
        if not tile:
            return False

        torpedo = TorpedoDeployable(tile, actor)
        tile.place(torpedo)
        actor.deployables.append(torpedo)
        from utils import coord_to_string
        game.log(
            f"  {actor.name} deployed torpedo at "
            f"{coord_to_string(self.target_q, self.target_r)}"
        )
        ship.energy -= self.energy_cost
        ship.uses_left["Torpedo Deploy"] = uses - 1
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
            game.log(
                f"  {actor.name} torpedo at "
                f"{coord_to_string(self.torpedo.tile.q, self.torpedo.tile.r)} "
                f"self-destructed"
            )
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
            game.log(
                f"  {actor.name} Torpedo: {hits}/{self.torpedo.attacks} hits, "
                f"{total_dmg} total damage"
            )

            game.board.remove_object(self.torpedo)
            if self.torpedo in actor.deployables:
                actor.deployables.remove(self.torpedo)
            return True

        return False


class NullAction(Action):
    def __init__(self):
        super().__init__("End Turn", 0)

    def execute(self, actor, game):
        return True
