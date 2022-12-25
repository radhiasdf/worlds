import pygame as pg
import time
from player import Player
from world import World
import shelve
import os
from constants import FPS
user_data = shelve.open("user_data")


class GameManager:
    def __init__(self):
        pg.init()
        pg.display.set_caption('Twuga')
        pg.display.set_icon(pg.image.load(os.path.join("assets", "grass3.png")))
        self.win = pg.display.set_mode((pg.display.Info().current_w*.7, pg.display.Info().current_h*.7))

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

        try:
            user_data['world'] = self.state_stack[-1].world.mapData
        except AttributeError:
            print('arrribute error')
        user_data.close()
        pg.quit()


class MainMenu:
    def __init__(self, game):
        self.game = game

        bookImg = pg.image.load(os.path.join("assets", "pain in the ass book.png"))
        playButtonImg = pg.image.load(os.path.join("assets", "play.png"))
        self.guiImgs = [bookImg, playButtonImg]
        for i, img in enumerate(self.guiImgs):
            self.guiImgs[i] = pg.transform.scale(img, (img.get_width() * 3, img.get_height() * 3))

    def update(self, dt, events):

        for e in events:
            if e.type == pg.KEYDOWN and e.key == pg.K_SPACE:
                self.game.state_stack.append(InGame(self.game, World(user_data['world'])))

    def draw(self, win):
        win.fill('white')
        for i in range(0, 2):
            win.blit(self.guiImgs[i], ((win.get_width() - self.guiImgs[i].get_width())/2, (win.get_height() - self.guiImgs[i].get_height())/2))
        pg.display.update()


class InGame:
    def __init__(self, game, world_data):
        self.game = game
        self.player = Player((game.win.get_width()/2, game.win.get_height()/2), self.game)
        self.world = world_data

        self.cameraLocation = pg.Vector2(0, 0)  # is in pixels

    def update(self, dt, events):
        for e in events:
            if e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                self.game.state_stack.append(PauseMenu(self.game))

        self.cameraLocation = self.player.update(dt, self.cameraLocation, events)

    def draw(self, win):
        win.fill('darkolivegreen3')
        self.world.draw(win, self.cameraLocation)
        self.player.draw(win)
        pg.display.update()


class PauseMenu:
    def __init__(self, game):
        self.game = game
        pass

    def update(self, dt, events):
        for e in events:
            if e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                self.game.state_stack.pop()

    def draw(self, win):
        win.fill('yellow')
        pg.display.update()


game = GameManager()
