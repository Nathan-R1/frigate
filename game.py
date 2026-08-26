import random

from utils import (
    NEIGHBOR_OFFSETS, HEX_RADIUS, hex_coords, hex_distance,
    coord_to_string, string_to_coord, DIRECTION_NAMES,
)
from board import Board
from objects import Ship, Asteroid, Deployable, TorpedoDeployable
from actions import (
    NullMove, NullAction, Accelerate, Decelerate,
    PD, Cannons, TorpedoDeploy, CommandTorpedo,
)
from player import Player
from display import render_board, render_ship_status, render_firing_arcs, DIRECTION_ARROWS
from screen import Screen
import sys


class Game:
    def __init__(self, verbose=False, no_targeting=False):
        self.board = Board()
        self.players = []
        self.turn_num = 0
        self.is_over = False
        self.verbose = verbose
        self.no_targeting = no_targeting
        self.messages = []
        self.screen = Screen()

    def log(self, msg):
        self.messages.append(msg)

    def setup(self):
        player_ship = Ship("Player", "\U0001f680")
        ai_ship = Ship("Enemy", "\U0001f6f8")
        ai_ship.direction = 3

        self.board.place_object(player_ship, -HEX_RADIUS, 0)
        self.board.place_object(ai_ship, HEX_RADIUS, 0)

        human = Player("Player", player_ship, is_human=True)
        ai = Player("Enemy", ai_ship, is_human=False)
        self.players = [human, ai]

        self._scatter_asteroids(8)

    def pregame_phase(self):
        self.log("=== PREGAME: Set your Future Moves ===")
        for player in self.players:
            if player.is_human:
                self._human_pregame_moves(player)
            else:
                for _ in range(3):
                    fm = player.choose_future_move(self)
                    player.ship.future_moves.append(fm)

    def _human_pregame_moves(self, player):
        for i in range(3):
            saved = list(self.messages)
            self.log(f"{player.name}: set Future Move {i + 1}")
            self.log("  1. Accelerate (+1 speed, 2 energy)")
            self.log("  2. Decelerate (-1 speed, 2 energy)")
            self.log("  3. Null (no change)")
            self._render()
            choice = self._input("  Choice: ")
            self.messages = saved

            if choice == "1":
                player.ship.future_moves.append(Accelerate())
            elif choice == "2":
                player.ship.future_moves.append(Decelerate())
            else:
                player.ship.future_moves.append(NullMove())

    def _scatter_asteroids(self, count):
        all_hexes = list(hex_coords())
        random.shuffle(all_hexes)
        placed = 0
        for q, r in all_hexes:
            if placed >= count:
                break
            tile = self.board.get_tile(q, r)
            if tile and not tile.is_occupied():
                asteroid = Asteroid()
                tile.place(asteroid)
                placed += 1

    def _build_display(self, extra=None):
        lines = []
        lines.append("=" * 60)
        lines.append("FRIGATE \u2014 Hex Space Combat")
        lines.append("=" * 60)
        if self.turn_num > 0:
            lines.append(f"TURN {self.turn_num}")
        lines.append("")
        lines.extend(render_board(self.board, self.players))
        for p in self.players:
            lines.append(render_ship_status(p))
        lines.append("")
        if extra:
            lines.append(extra)
        msg_lines = self.messages[-8:]
        for msg in msg_lines:
            lines.append(msg if msg else "")
        return lines

    def _render(self, extra=None):
        self.screen.render(self._build_display(extra))

    def _input(self, prompt):
        s = self.screen.input(prompt)
        if s == "q":
            print("\nQuitting...")
            sys.exit(0)
        return s

    def run_turn(self):
        self.turn_num += 1
        self.messages = []

        self.log(f"--- Turn {self.turn_num} ---")

        for player in self.players:
            if not player.ship.is_alive():
                continue
            ship = player.ship
            ship.recharge_energy()
            ship.reset_uses()
            if ship.future_moves:
                move = ship.future_moves.pop(0)
                move.execute(player, self)
                self.log(f"{player.name} move: {move.name}")

        self._move_ships_concurrent()
        if self.is_over:
            return

        self._render()

        for player in self.players:
            if not player.ship.is_alive():
                continue
            ship = player.ship
            if ship.speed <= ship.navigation and ship.turning > 0:
                if player.is_human:
                    self._human_turning(player)
                else:
                    self._ai_turning(player)

        self._move_ships_concurrent()
        if self.is_over:
            return

        for player in self.players:
            if not player.ship.is_alive():
                continue
            if player.is_human:
                self._human_choose_future_move(player)
            else:
                new_move = player.choose_future_move(self)
                player.ship.future_moves.append(new_move)

        self._render()

        for player in self.players:
            if not player.ship.is_alive():
                continue
            if player.is_human:
                self._human_action_phase(player)
            else:
                self._ai_action_phase(player)

        if self.is_over:
            return

        self._check_winner()
        if not self.is_over:
            self._render()
            for p in self.players:
                if p.is_human and p.ship.is_alive():
                    self._input("  Press Enter for next turn...  ")
                    break

    def _human_turning(self, player):
        ship = player.ship
        self.log(f"{player.name}: choose turning (max {ship.turning} hexes, empty to skip)")
        for i in range(-ship.turning, ship.turning + 1):
            if i == 0:
                continue
            direction = "CW" if i > 0 else "CCW"
            self.log(f"  {i:+d}. Turn {direction} {abs(i)}")
        self._render()
        choice = self._input("  Turning: ")
        if choice == "":
            return
        try:
            amount = int(choice)
            if abs(amount) > ship.turning:
                self.log(f"  Invalid: max turning is {ship.turning}")
                return
            ship.direction = (ship.direction + amount) % 6
        except ValueError:
            pass

    def _ai_turning(self, player):
        ship = player.ship
        enemy = None
        for p in self.players:
            if p != player and p.ship.is_alive():
                enemy = p
                break
        if not enemy:
            return

        my_pos = (ship.tile.q, ship.tile.r)
        enemy_pos = (enemy.ship.tile.q, enemy.ship.tile.r)
        dist = hex_distance(my_pos, enemy_pos)
        target_dir = player.direction_toward(my_pos, enemy_pos)

        if dist > 3:
            diff = (target_dir - ship.direction) % 6
            if diff > 0 and diff <= ship.turning:
                ship.direction = (ship.direction + diff) % 6
            elif diff > ship.turning and diff <= 3:
                ship.direction = (ship.direction + ship.turning) % 6
            elif diff > 3:
                ccw_amount = min(6 - diff, ship.turning)
                ship.direction = (ship.direction - ccw_amount) % 6
        elif dist < 3:
            away_dir = (target_dir + 3) % 6
            diff = (away_dir - ship.direction) % 6
            if diff > 0 and diff <= ship.turning:
                ship.direction = (ship.direction + diff) % 6
            elif diff > ship.turning and diff <= 3:
                ship.direction = (ship.direction + ship.turning) % 6
            elif diff > 3:
                ccw_amount = min(6 - diff, ship.turning)
                ship.direction = (ship.direction - ccw_amount) % 6

    def _human_choose_future_move(self, player):
        saved = list(self.messages)
        self.log(f"{player.name}: choose new Future Move 3")
        self.log("  1. Accelerate (+1 speed, 2 energy)")
        self.log("  2. Decelerate (-1 speed, 2 energy)")
        self.log("  3. Null (no change)")
        self._render()
        choice = self._input("  Choice: ")
        self.messages = saved

        if choice == "1":
            player.ship.future_moves.append(Accelerate())
        elif choice == "2":
            player.ship.future_moves.append(Decelerate())
        else:
            player.ship.future_moves.append(NullMove())

    def _human_action_phase(self, player):
        while True:
            if self.is_over:
                return
            ship = player.ship
            self.log(f"{player.name}: choose action (energy: {ship.energy})")
            self.log("  1. PD (range 1, 3atk, 2dmg, 1 energy)")
            self.log("  2. Cannons (range 4, 2atk, 2dmg, 1 energy)")
            self.log("  3. Torpedo Deploy (range 8, 1 energy)")
            if player.deployables:
                torpedoes = [d for d in player.deployables if isinstance(d, TorpedoDeployable)]
                if torpedoes:
                    self.log("  4. Command Torpedo (free)")
            self.log("  0. End turn")
            self._render()
            choice = self._input("  Choice: ")

            saved = list(self.messages)
            self.messages = []

            if choice == "0" or choice == "":
                break

            if choice == "1":
                arc = self._select_arc(player, "PD")
                if arc is not None:
                    target = self._get_target_in_range(player, 1, "PD", arc)
                    if target:
                        PD(target[0], target[1], arc).execute(player, self)

            elif choice == "2":
                arc = self._select_arc(player, "Cannons")
                if arc is not None:
                    target = self._get_target_in_range(player, 4, "Cannons", arc)
                    if target:
                        Cannons(target[0], target[1], arc).execute(player, self)

            elif choice == "3":
                target = self._get_target_in_range(player, 8, "Torpedo Deploy", None)
                if target:
                    TorpedoDeploy(target[0], target[1]).execute(player, self)

            elif choice == "4" and player.deployables:
                torpedoes = [d for d in player.deployables if isinstance(d, TorpedoDeployable)]
                if torpedoes:
                    self.log("  Torpedo options:")
                    self.log("    1. Attack target")
                    self.log("    2. Destroy (self-destruct)")
                    self._render()
                    sub = self._input("  Choice: ")
                    self.messages = saved

                    if sub == "1":
                        target = self._get_target_in_range(
                            player, 8, "Torpedo Attack",
                            None, from_tile=torpedoes[0].tile,
                        )
                        if target:
                            CommandTorpedo(
                                torpedoes[0], "Attack", target[0], target[1]
                            ).execute(player, self)
                    elif sub == "2":
                        CommandTorpedo(torpedoes[0], "Destroy").execute(player, self)

            self._check_winner()
            if self.is_over:
                return

    def _ai_action_phase(self, player):
        for _ in range(3):
            if self.is_over:
                return
            action = player.choose_non_move_action(self)
            if isinstance(action, NullAction):
                break
            action.execute(player, self)
            self.log(f"{player.name} action: {action.name}")
            self._check_winner()
            if self.is_over:
                return

    def _select_arc(self, player, action_name):
        ship = player.ship
        enabled = [i for i in range(6) if ship.firing_arcs[i]]

        if not enabled:
            self.log("  No firing arcs enabled!")
            return None

        if len(enabled) == 1:
            return enabled[0]

        saved = list(self.messages)
        self.log(f"  Select firing arc for {action_name}:")
        for idx, arc_dir in enumerate(enabled):
            label = DIRECTION_NAMES[arc_dir]
            arrow = DIRECTION_ARROWS[arc_dir]
            self.log(f"    {idx + 1}. {label} ({arrow})")
        self._render()
        choice = self._input("  Arc: ")
        self.messages = saved

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(enabled):
                return enabled[idx]
        except ValueError:
            pass
        return None

    def _get_target_in_range(
        self, player, max_range, action_name, arc_direction, from_tile=None,
    ):
        source = from_tile or player.ship.tile
        if not self.no_targeting:
            from targeting import TargetSelector
            while True:
                selector = TargetSelector(
                    self.board, source.q, source.r, max_range, action_name,
                    self.players, arc_direction, player.ship.firing_arcs,
                    self.turn_num,
                )
                result = selector.select()
                if result is None:
                    return None
                return result

        while True:
            s = self._input(
                f"  Target for {action_name} (max {max_range}, blank to skip): "
            )
            if s == "":
                return None
            try:
                q, r = string_to_coord(s)
            except ValueError:
                self.log("  Invalid coordinate")
                continue
            dist = hex_distance((source.q, source.r), (q, r))
            if dist > max_range:
                self.log(f"  Out of range ({dist} > {max_range})")
                continue
            return (q, r)

    def _move_ships_concurrent(self):
        alive_ships = [p.ship for p in self.players if p.ship.is_alive()]

        for ship in alive_ships:
            current = ship.tile
            for _ in range(ship.speed):
                dq, dr = NEIGHBOR_OFFSETS[ship.direction]
                next_tile = self.board.get_tile(current.q + dq, current.r + dr)
                if not next_tile or any(
                    isinstance(o, Asteroid) for o in next_tile.content
                ):
                    break
                current = next_tile
            ship.intended_dest = current

        if len(alive_ships) == 2:
            a, b = alive_ships[0], alive_ships[1]
            oa, da = a.tile, a.intended_dest
            ob, db = b.tile, b.intended_dest

            if da == ob and db == oa:
                self.log("Collision: ships swap!")
                a.intended_dest = oa
                b.intended_dest = ob
                a.take_damage(3)
                b.take_damage(3)
            elif da == db:
                self.log("Collision: same hex!")
                a.intended_dest = oa
                b.intended_dest = ob
                a.take_damage(3)
                b.take_damage(3)
            elif da == ob and db != oa:
                self.log("Collision: ship enters occupied hex!")
                a.intended_dest = oa
                a.take_damage(3)
                b.take_damage(3)
            elif db == oa and da != ob:
                self.log("Collision: ship enters occupied hex!")
                b.intended_dest = ob
                a.take_damage(3)
                b.take_damage(3)

        for ship in alive_ships:
            if ship.intended_dest != ship.tile:
                ship.tile.remove(ship)
                ship.intended_dest.place(ship)
                ship.tile = ship.intended_dest

        for ship in alive_ships:
            if not ship.is_alive():
                self.log(f"{ship.name} has been destroyed!")
                self.is_over = True

    def _check_winner(self):
        alive = [p for p in self.players if p.ship.is_alive()]
        if len(alive) == 1:
            self.log(f"{alive[0].name} wins!")
            self.is_over = True
        elif all(not p.ship.is_alive() for p in self.players):
            self.log("Draw!")
            self.is_over = True
