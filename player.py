from utils import (
    AI_DESIRED_RANGE, hex_distance, NEIGHBOR_OFFSETS, has_line_of_sight, TORPEDO_DEPLOY_RANGE,
)
from objects import Ship, TorpedoDeployable
from actions import (
    GravitonPlus, GravitonMinus, TurnCW, TurnCCW, NullMove,
    PD, Cannons, TorpedoDeploy, CommandTorpedo, NullAction,
)


class Player:
    def __init__(self, name, ship, is_human=False):
        self.name = name
        self.ship = ship
        self.is_human = is_human
        self.moves_queue = []
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

    def declare_moves(self, game):
        self.moves_queue = []
        enemy = None
        for p in game.players:
            if p != self and p.ship.is_alive():
                enemy = p
                break
        if not enemy:
            for _ in range(3):
                self.moves_queue.append(NullMove())
            return

        my_pos = (self.ship.tile.q, self.ship.tile.r)
        enemy_pos = (enemy.ship.tile.q, enemy.ship.tile.r)
        dist = hex_distance(my_pos, enemy_pos)
        target_dir = self.direction_toward(my_pos, enemy_pos)
        away_dir = self.direction_away(my_pos, enemy_pos)

        orig_dir = self.ship.direction
        orig_speed = self.ship.speed

        for _ in range(3):
            if dist > AI_DESIRED_RANGE:
                if self.ship.direction != target_dir:
                    diff = (target_dir - self.ship.direction) % 6
                    if diff <= 3:
                        if diff <= 2:
                            self.moves_queue.append(TurnCW())
                        else:
                            self.moves_queue.append(TurnCW())
                    else:
                        self.moves_queue.append(TurnCCW())
                else:
                    self.moves_queue.append(GravitonPlus())
            elif dist < AI_DESIRED_RANGE:
                if self.ship.direction != away_dir:
                    diff = (away_dir - self.ship.direction) % 6
                    if diff <= 3:
                        self.moves_queue.append(TurnCW())
                    else:
                        self.moves_queue.append(TurnCCW())
                else:
                    self.moves_queue.append(GravitonPlus())
            else:
                self.moves_queue.append(NullMove())

            if isinstance(self.moves_queue[-1], (TurnCW, TurnCCW)):
                if isinstance(self.moves_queue[-1], TurnCW):
                    self.ship.direction = (self.ship.direction + 1) % 6
                else:
                    self.ship.direction = (self.ship.direction - 1) % 6
                target_dir = self.direction_toward(
                    (self.ship.tile.q, self.ship.tile.r), enemy_pos
                )
                away_dir = self.direction_away(
                    (self.ship.tile.q, self.ship.tile.r), enemy_pos
                )
            elif isinstance(self.moves_queue[-1], GravitonPlus):
                self.ship.speed += 1

        self.ship.speed = orig_speed
        self.ship.direction = orig_dir

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

        my_tile = self.ship.tile
        enemy_tile = enemy.ship.tile
        dist = hex_distance(
            (my_tile.q, my_tile.r), (enemy_tile.q, enemy_tile.r)
        )
        has_los = has_line_of_sight(my_tile, enemy_tile, game.board)

        for torp in self.deployables:
            if isinstance(torp, TorpedoDeployable) and torp.tile:
                torp_dist = hex_distance(
                    (torp.tile.q, torp.tile.r), (enemy_tile.q, enemy_tile.r)
                )
                torp_los = has_line_of_sight(torp.tile, enemy_tile, game.board)
                if torp_dist <= torp.range and torp_los:
                    return CommandTorpedo(torp, "Attack", enemy_tile.q, enemy_tile.r)

        if dist <= 4 and has_los:
            return Cannons(enemy_tile.q, enemy_tile.r)

        if dist <= 1 and has_los:
            return PD(enemy_tile.q, enemy_tile.r)

        deploy_tile = None
        for dq in range(-TORPEDO_DEPLOY_RANGE, TORPEDO_DEPLOY_RANGE + 1):
            for dr in range(-TORPEDO_DEPLOY_RANGE, TORPEDO_DEPLOY_RANGE + 1):
                tq, tr = my_tile.q + dq, my_tile.r + dr
                if game.board.is_valid(tq, tr):
                    td = hex_distance((tq, tr), (enemy_tile.q, enemy_tile.r))
                    if td <= 8 and hex_distance((my_tile.q, my_tile.r), (tq, tr)) <= TORPEDO_DEPLOY_RANGE:
                        if deploy_tile is None or td < hex_distance(
                            (deploy_tile[0], deploy_tile[1]),
                            (enemy_tile.q, enemy_tile.r),
                        ):
                            deploy_tile = (tq, tr)

        if deploy_tile:
            return TorpedoDeploy(deploy_tile[0], deploy_tile[1])

        return NullAction()
