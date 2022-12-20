import shadows
from constants import CHUNK_SIZE, TILE_ZOOM, RENDER_DISTANCE
import pygame as pg, os, random


class Tile:
    def __init__(self, relative_location, type):
        self.x, self.y = relative_location
        self.type = type


class World:
    def __init__(self, map_data):
        self.mapData = map_data
        img = pg.image.load(os.path.join("assets", "grass3.png"))
        self.grassImg = pg.transform.scale(img, (TILE_ZOOM, int(TILE_ZOOM * (img.get_height() / img.get_width())))).convert_alpha()

    def generate_chunk(self):
        chunk = []
        for x in range(CHUNK_SIZE):
            for y in range(CHUNK_SIZE):
                chunk.append(Tile((x, y), random.randint(0, 5)))
        return chunk

    def draw(self, win, location):  # location is in pixels
        img = self.grassImg
        rect = self.grassImg.get_rect()
        chunk_pixels = TILE_ZOOM*CHUNK_SIZE
        # how many chunks are on screen
        cols_onscreen = int(pg.display.Info().current_w/chunk_pixels)
        rows_onscreen = int(pg.display.Info().current_h/chunk_pixels)
        # which chunk is on top left of screen
        chunk_x, chunk_y = int(location.x/chunk_pixels), int(location.y/chunk_pixels)

        for x in range(chunk_x-RENDER_DISTANCE, chunk_x+cols_onscreen+RENDER_DISTANCE+1):
            for y in range(chunk_y-RENDER_DISTANCE, chunk_y+rows_onscreen+RENDER_DISTANCE+1):
                try:
                    for tile in self.mapData[(x, y)]:
                        if tile.type == 1:
                            pos_x = x*chunk_pixels + tile.x*TILE_ZOOM - location.x
                            pos_y = y*chunk_pixels + tile.y*TILE_ZOOM - location.y
                            shadows.draw_shadow(img, win, (pos_x, pos_y), pos_y+img.get_height()-2)
                            win.blit(img, (pos_x, pos_y))
                except KeyError:
                    self.mapData[(x, y)] = self.generate_chunk()
