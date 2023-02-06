import random
from constants import CHUNK_SIZE


class Tile:
    def __init__(self, relative_location, index, rotation=0):
        self.x, self.y = relative_location
        self.id = index
        self.rotation = rotation


def generate_chunk():
    chunk = {}
    for x in range(CHUNK_SIZE):
        for y in range(CHUNK_SIZE):
            chunk[(x, y)] = Tile((x, y), random.choice([0, 0, 0, 0, 1]))
    return chunk




