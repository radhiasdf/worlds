import pygame as pg
import time
from player import Player
from chunk import *
import shelve
import os
from constants import *
import shadows
CHUNK_PIXELS = TILE_ZOOM * CHUNK_SIZE
import solitaire.solitaire


class GameManager:
    def __init__(self):
        pg.init()
        pg.display.set_caption('Twuga')
        pg.display.set_icon(pg.image.load(os.path.join("assets", "tiles", "grass3.png")))
        self.win = pg.display.set_mode((pg.display.Info().current_w * .7, pg.display.Info().current_h * .7))

        self.state_stack = [MainMenu(self)]

        run = True
        prev_time = time.time()
        while run:
            pg.time.Clock().tick(FPS)
            dt = time.time() - prev_time  # delta time
            prev_time = time.time()

            events = pg.event.get()
            for e in events:
                if e.type == pg.QUIT:
                    run = False

            self.state_stack[-1].update(dt, events)
            self.state_stack[-1].draw(self.win)
            print([state.__class__.__name__ for state in self.state_stack])
        pg.quit()


class State:
    def __init__(self, game_manager):
        self.gameManager = game_manager

    def update(self, dt, events):
        pass

    def draw(self, win):
        pass


class MainMenu(State):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.lobby = InWorld(game_manager, 'lobby_world')

    def update(self, dt, events):

        for e in events:
            if e.type == pg.KEYDOWN and e.key == pg.K_SPACE:
                self.gameManager.state_stack.append(InWorld(self.gameManager, "world_1"))

        self.lobby.update(dt, events)

    def draw(self, win):
        self.lobby.draw(win)


class InWorld(State):
    def __init__(self, game_manager, world_name_id):
        super().__init__(game_manager)
        self.player = Player((game_manager.win.get_width() / 2, game_manager.win.get_height() / 2), game_manager)

        self.world_file = shelve.open(os.path.join("saves", world_name_id))
        try:
            self.mapData = self.world_file['map_data']
        except KeyError:
            self.mapData = {}
        self.tileImgs = {i: pg.image.load(os.path.join('assets', 'tiles', TILES[i])) for i in TILES}
        self.set_tile_scale()

        self.cameraLocation = pg.Vector2(0, 0)  # is in pixels

    def update(self, dt, events):
        for e in events:
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    self.gameManager.state_stack.append(InWorldPauseMenu(self.gameManager))

        self.playerInfo = self.player.update(dt, self.cameraLocation, events)
        self.cameraLocation = self.playerInfo['cameraLocation']
        self.playerCoords = (self.cameraLocation + self.player.rect.midbottom)/TILE_ZOOM
        print(self.playerCoords)

    def handle_mouse_down(self):
        pass
        """buttons = pg.mouse.get_pressed()
            if buttons[0]:
                x = int(location.x / CHUNK_PIXELS)
                y = int(location.y / CHUNK_PIXELS)
            self.mapData[(x, y)][0].id = self.player.inHand['tileID']  """

    def save_and_quit(self):
        self.world_file['map_data'] = self.mapData
        self.gameManager.state_stack.pop()

    def draw(self, win):
        win.fill('darkolivegreen3')
        self.draw_map(win, self.cameraLocation)
        self.player.draw(win)
        pg.display.update()

    def draw_map(self, win, location):  # location is in pixels
        # how many chunks are on screen
        cols_onscreen = int(pg.display.Info().current_w / CHUNK_PIXELS)
        rows_onscreen = int(pg.display.Info().current_h / CHUNK_PIXELS)
        # which chunk coordinates is on top left of screen
        chunk_x, chunk_y = int(location.x / CHUNK_PIXELS), int(location.y / CHUNK_PIXELS)

        for x in range(chunk_x - RENDER_DISTANCE, chunk_x + cols_onscreen + RENDER_DISTANCE + 1):
            for y in range(chunk_y - RENDER_DISTANCE, chunk_y + rows_onscreen + RENDER_DISTANCE + 1):
                try:
                    for tile in self.mapData[(x, y)]:
                        pos_x = x * CHUNK_PIXELS + tile.x * TILE_ZOOM - location.x
                        pos_y = y * CHUNK_PIXELS + tile.y * TILE_ZOOM - location.y
                        try:
                            if tile.id == 0:
                                continue
                            img = self.tileImgs[tile.id]
                        except KeyError:
                            img = self.tileImgs[-1]
                        if SHADOWS_ON:
                            shadows.draw_shadow(img, win, (pos_x, pos_y), pos_y + img.get_height() - 2)
                        win.blit(img, (pos_x, pos_y))
                except KeyError:
                    self.mapData[(x, y)] = generate_chunk()

    def set_tile_scale(self):
        self.tileImgs = {i: pg.transform.scale(self.tileImgs[i], (
            TILE_ZOOM, int(TILE_ZOOM * (self.tileImgs[i].get_height() / self.tileImgs[i].get_width())))).convert_alpha()
                         for
                         i in self.tileImgs}


class InWorldPauseMenu(State):
    def __init__(self, game_manager):
        super().__init__(game_manager)

    def update(self, dt, events):
        for e in events:
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    self.gameManager.state_stack.pop()
                elif e.key == pg.K_o:
                    self.gameManager.state_stack.pop()
                    self.gameManager.state_stack[-1].save_and_quit()

    def draw(self, win):
        win.fill('yellow')
        pg.display.update()


#run = GameManager()
pg.init()
solitaire.solitaire.InSolitaire()