from abc import ABC


class Object(ABC):
    def __init__(self, name, emoji, tile=None):
        self.name = name
        self.emoji = emoji
        self.tile = tile
        self.speed = 0
        self.direction = 0
        self.owner = None


class Ship(Object):
    def __init__(self, name, emoji, tile=None):
        super().__init__(name, emoji, tile)
        self.hull = 10
        self.hull_max = 10
        self.shield = 5
        self.shield_max = 5
        self.energy = 6
        self.max_energy = 6
        self.storage = 10
        self.scan_range = 5
        self.navigation = 3
        self.turning = 2
        self.firing_arcs = [True] * 6
        self.future_moves = []
        self.uses_left = {}

    def recharge_energy(self):
        self.energy = self.max_energy

    def reset_uses(self):
        self.uses_left = {}

    def take_damage(self, amount):
        if self.shield > 0:
            absorbed = min(self.shield, amount)
            self.shield -= absorbed
            amount -= absorbed
        self.hull -= amount

    def is_alive(self):
        return self.hull > 0


class Asteroid(Object):
    def __init__(self, tile=None):
        super().__init__("Asteroid", "\U0001faa8", tile)
        self.speed = 0


class Deployable(Object):
    def __init__(self, name, emoji, tile, owner):
        super().__init__(name, emoji, tile)
        self.owner = owner


class TorpedoDeployable(Deployable):
    def __init__(self, tile, owner):
        super().__init__("Torpedo", "\U0001f4ab", tile, owner)
        self.range = 8
        self.attacks = 1
        self.damage = 4
