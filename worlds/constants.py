import pygame as pg
import os
TILE_ZOOM = 32
CHUNK_SIZE = 8
RENDER_DISTANCE = 1
FPS = 60

TILES = {-1: "missing_texture.png", 1: "grass3.png", 2: "plank_tile_tile.png"}
TILEIMGS = {i: pg.image.load(os.path.join('assets', 'tiles', TILES[i])) for i in TILES}

pg.font.init()
my_font = pg.font.SysFont('Comic Sans MS', 20)

SHADOWS_ON = False

MOUSE_REACH = 3 * TILE_ZOOM
