from utils import NEIGHBOR_OFFSETS, hex_coords, is_valid_hex


class Tile:
    def __init__(self, q, r):
        self.q = q
        self.r = r
        self.content = []

    def get_adj(self):
        result = []
        for dq, dr in NEIGHBOR_OFFSETS:
            nq, nr = self.q + dq, self.r + dr
            if is_valid_hex(nq, nr):
                result.append((nq, nr))
        return result

    def get_xy_coord(self):
        x = self.q * 1.5
        y = self.r * 1.732 + (self.q % 2) * 0.866
        return (x, y)

    def get_content(self):
        return self.content

    def is_occupied(self):
        return len(self.content) > 0

    def place(self, obj):
        self.content.append(obj)
        obj.tile = self

    def remove(self, obj):
        if obj in self.content:
            self.content.remove(obj)


class Board:
    def __init__(self):
        self.tiles = {}
        for q, r in hex_coords():
            self.tiles[(q, r)] = Tile(q, r)

    def get_tile(self, q, r):
        return self.tiles.get((q, r))

    def is_valid(self, q, r):
        return (q, r) in self.tiles

    def place_object(self, obj, q, r):
        tile = self.get_tile(q, r)
        if tile:
            tile.place(obj)

    def remove_object(self, obj):
        if obj.tile:
            obj.tile.remove(obj)
            obj.tile = None

    def get_all_objects(self):
        objects = []
        for tile in self.tiles.values():
            objects.extend(tile.content)
        return objects

    def get_objects_of_type(self, cls):
        return [o for o in self.get_all_objects() if isinstance(o, cls)]
