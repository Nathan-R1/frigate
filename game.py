import random

from utils import NEIGHBOR_OFFSETS, HEX_RADIUS, hex_coords, hex_distance, coord_to_string
from board import Board
from objects import Ship, Asteroid, Projectile, Deployable, TorpedoDeployable
from actions import (
    NullMove, NullAction, GravitonPlus, GravitonMinus, TurnCW, TurnCCW,
    PD, Cannons, TorpedoDeploy, CommandTorpedo,
)
from player import Player
from display import display_board, display_ship_status
import sys


class Game:
    def __init__(self, verbose=False):
        self.board = Board()
        self.players = []
        self.round_num = 0
        self.is_over = False
        self.verbose = verbose

    def setup(self):
        player_ship = Ship("Player", "\U0001f680")
        ai_ship = Ship("Enemy", "\U0001f6f8")
        ai_ship.direction = 3  # face W toward player

        self.board.place_object(player_ship, -HEX_RADIUS, 0)
        self.board.place_object(ai_ship, HEX_RADIUS, 0)

        human = Player("Player", player_ship, is_human=True)
        ai = Player("Enemy", ai_ship, is_human=False)
        self.players = [human, ai]

        self._scatter_asteroids(8)

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

    def run_round(self):
        self.round_num += 1
        print(f"\n{'='*60}")
        print(f"ROUND {self.round_num}")
        print(f"{'='*60}")

        # ── Declaration Phase ──
        for player in self.players:
            if not player.ship.is_alive():
                player.moves_queue = [NullMove(), NullMove(), NullMove()]
                continue
            if player.is_human:
                self._human_declare_moves(player)
            else:
                player.declare_moves(self)
            moves_str = ", ".join(m.name for m in player.moves_queue)
            if self.verbose and not player.is_human:
                from utils import AI_DESIRED_RANGE
                print(f"{player.name} moves: {moves_str}  (desired range: {AI_DESIRED_RANGE})")
            else:
                print(f"{player.name} moves: {moves_str}")

        # ── Turns ──
        for turn in range(3):
            if self.is_over:
                break
            self.run_turn(turn)

        # ── Settlement ──
        for player in self.players:
            if not player.ship.is_alive():
                continue
            excess = player.ship.energy_spent - player.ship.max_energy
            if excess > 0:
                player.ship.take_damage(excess)
                print(f"{player.name} pays {excess} overheat damage!")
            player.ship.energy_spent = 0

        self._check_winner()

    def run_turn(self, turn_index):
        print(f"\n--- Turn {turn_index + 1} ---")

        # 1. Move Resolution
        for player in self.players:
            if not player.ship.is_alive():
                continue
            if turn_index < len(player.moves_queue):
                move = player.moves_queue[turn_index]
                move.execute(player, self)

        # 2. Ship Movement (Concurrent)
        self._move_ships_concurrent()

        # 3. Projectile Movement
        self._move_projectiles()

        # Display after movement
        display_board(self.board, self.players)
        for player in self.players:
            display_ship_status(player)
        print()

        # 4. Action Phase
        actions = []
        for player in self.players:
            if not player.ship.is_alive():
                actions.append(NullAction())
                continue
            if player.is_human:
                action = self._human_choose_action(player)
            else:
                action = player.choose_non_move_action(self)
            actions.append(action)
            print(f"{player.name} action: {action.name}")

        for action, player in zip(actions, self.players):
            if not player.ship.is_alive():
                continue
            if not isinstance(action, NullAction):
                action.execute(player, self)

        self._check_projectile_collisions()

        display_board(self.board, self.players)
        for player in self.players:
            display_ship_status(player)

    def _move_ships_concurrent(self):
        alive_ships = [p.ship for p in self.players if p.ship.is_alive()]

        # Phase 1: Intended destinations
        for ship in alive_ships:
            current = ship.tile
            for _ in range(ship.speed):
                dq, dr = NEIGHBOR_OFFSETS[ship.direction]
                next_tile = self.board.get_tile(current.q + dq, current.r + dr)
                if not next_tile or any(isinstance(o, Asteroid) for o in next_tile.content):
                    break
                current = next_tile
            ship.intended_dest = current

        # Phase 2: Conflict resolution
        if len(alive_ships) == 2:
            a, b = alive_ships[0], alive_ships[1]
            oa, da = a.tile, a.intended_dest
            ob, db = b.tile, b.intended_dest

            if da == ob and db == oa:
                print("Collision: ships swap!")
                a.intended_dest = oa
                b.intended_dest = ob
                a.take_damage(3)
                b.take_damage(3)
            elif da == db:
                print("Collision: same hex!")
                a.intended_dest = oa
                b.intended_dest = ob
                a.take_damage(3)
                b.take_damage(3)
            elif da == ob and db != oa:
                print("Collision: ship enters occupied hex!")
                a.intended_dest = oa
                a.take_damage(3)
                b.take_damage(3)
            elif db == oa and da != ob:
                print("Collision: ship enters occupied hex!")
                b.intended_dest = ob
                a.take_damage(3)
                b.take_damage(3)

        # Execute movement
        for ship in alive_ships:
            if ship.intended_dest != ship.tile:
                ship.tile.remove(ship)
                ship.intended_dest.place(ship)
                ship.tile = ship.intended_dest

        for ship in alive_ships:
            if not ship.is_alive():
                print(f"{ship.name} has been destroyed!")
                self.is_over = True

    def _move_projectiles(self):
        projectiles = self.board.get_objects_of_type(Projectile)
        for proj in projectiles[:]:
            dq, dr = NEIGHBOR_OFFSETS[proj.direction]
            nq, nr = proj.tile.q + dq, proj.tile.r + dr
            next_tile = self.board.get_tile(nq, nr)
            if not next_tile:
                self.board.remove_object(proj)
                continue

            hit = False
            for obj in next_tile.content[:]:
                if isinstance(obj, Ship):
                    obj.take_damage(proj.damage)
                    self.board.remove_object(proj)
                    hit = True
                    break
                elif isinstance(obj, Asteroid):
                    self.board.remove_object(proj)
                    self.board.remove_object(obj)
                    hit = True
                    break
                elif isinstance(obj, Deployable):
                    self.board.remove_object(proj)
                    self.board.remove_object(obj)
                    if obj in getattr(obj, 'owner', None) and obj.owner:
                        if obj in obj.owner.deployables:
                            obj.owner.deployables.remove(obj)
                    hit = True
                    break

            if not hit:
                proj.tile.remove(proj)
                next_tile.place(proj)
                proj.tile = next_tile

    def _check_projectile_collisions(self):
        projectiles = self.board.get_objects_of_type(Projectile)
        for proj in projectiles[:]:
            for obj in proj.tile.content[:]:
                if obj is proj:
                    continue
                if isinstance(obj, Ship):
                    obj.take_damage(proj.damage)
                    self.board.remove_object(proj)
                    break
                elif isinstance(obj, Asteroid):
                    self.board.remove_object(proj)
                    self.board.remove_object(obj)
                    break
                elif isinstance(obj, Deployable):
                    self.board.remove_object(proj)
                    self.board.remove_object(obj)
                    if obj.owner and proj in obj.owner.deployables:
                        obj.owner.deployables.remove(obj)
                    break

    def _check_winner(self):
        for player in self.players:
            if not player.ship.is_alive():
                winner = [p for p in self.players if p.ship.is_alive()]
                if winner:
                    print(f"\n{winner[0].name} wins!")
                else:
                    print("\nDraw!")
                self.is_over = True
                return
        if all(not p.ship.is_alive() for p in self.players):
            print("\nDraw!")
            self.is_over = True

    def _input(self, prompt):
        try:
            s = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            s = "q"
        if s == "q":
            print("\nQuitting...")
            sys.exit(0)
        return s

    def _human_declare_moves(self, player):
        print(f"\n{player.name}: declare your 3 moves (enter empty for Null)")
        moves = []
        move_options = [
            ("1", "Graviton+ (accel, 2 energy)", GravitonPlus),
            ("2", "Graviton- (decel, 2 energy)", GravitonMinus),
            ("3", "Turn CW (1 energy)", TurnCW),
            ("4", "Turn CCW (1 energy)", TurnCCW),
        ]
        for i in range(3):
            print(f"  Move {i+1}:")
            for key, desc, _ in move_options:
                print(f"    {key}. {desc}")
            choice = self._input("  Choice: ")
            for key, _, cls in move_options:
                if choice == key:
                    moves.append(cls())
                    break
            else:
                moves.append(NullMove())
        player.moves_queue = moves

    def _human_choose_action(self, player):
        print(f"\n{player.name}: choose non-move action (enter empty for Null)")
        enemy = None
        for p in self.players:
            if p != player and p.ship.is_alive():
                enemy = p
                break

        options = [
            ("1", "PD (range 1, 3atk, 2dmg, 1 energy)"),
            ("2", "Cannons (range 4, 2atk, 2dmg, 1 energy)"),
            ("3", "Torpedo Deploy (range 1, 1 energy)"),
        ]

        if player.deployables:
            options.append(("4", "Command Torpedo (free)"))

        for key, desc in options:
            print(f"  {key}. {desc}")

        choice = self._input("  Choice: ")

        if choice == "":
            return NullAction()

        if choice == "1":
            target = self._get_target_in_range(player, 1, "PD")
            if target:
                return PD(target[0], target[1])
            return NullAction()

        if choice == "2":
            target = self._get_target_in_range(player, 4, "Cannons")
            if target:
                return Cannons(target[0], target[1])
            return NullAction()

        if choice == "3":
            target = self._get_target_in_range(player, 1, "Torpedo Deploy")
            if target:
                return TorpedoDeploy(target[0], target[1])
            return NullAction()

        if choice == "4" and player.deployables:
            torpedoes = [d for d in player.deployables if isinstance(d, TorpedoDeployable)]
            if torpedoes:
                print("  Torpedo options:")
                print("    1. Attack target")
                print("    2. Destroy (self-destruct)")
                sub = self._input("  Choice: ")
                if sub == "1":
                    target = self._get_target_in_range(player, 8, "Torpedo Attack", from_tile=torpedoes[0].tile)
                    if target:
                        return CommandTorpedo(torpedoes[0], "Attack", target[0], target[1])
                elif sub == "2":
                    return CommandTorpedo(torpedoes[0], "Destroy")

        return NullAction()

    def _get_target_in_range(self, player, max_range, action_name, from_tile=None):
        source = from_tile or player.ship.tile
        while True:
            s = self._input(f"  Target coordinate for {action_name} (max {max_range}, blank to skip): ")
            if s == "":
                return None
            try:
                from utils import string_to_coord
                q, r = string_to_coord(s)
            except ValueError:
                print(f"  Invalid coordinate")
                continue
            dist = hex_distance((source.q, source.r), (q, r))
            if dist > max_range:
                print(f"  Out of range ({dist} > {max_range})")
                continue
            return (q, r)


