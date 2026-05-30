from abc import ABC

from utils import MAX_HEALTH, MAX_ENERGY


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
        self.health = MAX_HEALTH
        self.max_energy = MAX_ENERGY
        self.energy_spent = 0

    def take_damage(self, amount):
        self.health -= amount

    def is_alive(self):
        return self.health > 0


class Asteroid(Object):
    def __init__(self, tile=None):
        super().__init__("Asteroid", "\U0001faa8", tile)
        self.speed = 0


class Projectile(Object):
    def __init__(self, name, emoji, tile, direction, damage, owner=None):
        super().__init__(name, emoji, tile)
        self.direction = direction
        self.speed = 1
        self.damage = damage
        self.owner = owner

    def advance(self):
        from utils import NEIGHBOR_OFFSETS
        dq, dr = NEIGHBOR_OFFSETS[self.direction]
        return self.tile.q + dq, self.tile.r + dr


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
