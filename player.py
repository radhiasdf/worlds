import pygame as pg
import os
import shadows
from math import sqrt
from constants import TILE_ZOOM, MOUSE_REACH
from solitaire.solitaire import InSolitaire
SPRITE_SIZE = TILE_ZOOM * 2


class Player:
    def __init__(self, pos, game_manager):
        self.gameManager = game_manager  # is putting the game instance in a bunch of other instances bad

        self.imgsWalkingFront = [pg.image.load(os.path.join("assets", "pixil-gif-drawing-tamarin-20221217", f"sprite_{i}.png")) for i in range(4)]
        for i, img in enumerate(self.imgsWalkingFront):
            self.imgsWalkingFront[i] = pg.transform.scale(img, (SPRITE_SIZE, SPRITE_SIZE)).convert_alpha()

        self.currentAnimationImgs = self.imgsWalkingFront
        self.rect = self.currentAnimationImgs[0].get_rect(center=pos)
        self.direction = pg.math.Vector2()
        self.speed = 150
        self.animationSpeed = 7
        self.frameIndex = 0
        self.img = self.currentAnimationImgs[int(self.frameIndex)]

        self.inHand = {'tileID': 2, 'amount': 'infinite'}
        self.inReach = False
        self.mouseButtonDown = False

    def input(self, events):
        keys = pg.key.get_pressed()  # does this slow down code
        if keys[pg.K_UP] or keys[pg.K_w]:
            self.direction.y = -1
        elif keys[pg.K_DOWN] or keys[pg.K_s]:
            self.direction.y = 1
        else:
            self.direction.y = 0

        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.direction.x = 1
        elif keys[pg.K_LEFT] or keys[pg.K_a]:
            self.direction.x = -1
        else:
            self.direction.x = 0

        for e in events:
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_SPACE:
                    self.gameManager.state_stack.append(InSolitaire(game_manager=self.gameManager))
            elif e.type in (pg.MOUSEBUTTONDOWN, pg.MOUSEMOTION):
                self.check_reach()

    def update(self, dt, camera_location, events):
        self.input(events)
        camera_location += self.direction * int(self.speed * dt) # there was a bug where going down and right were slower than up and left; i suspect the rounding to rect.center was floor, causing -1.7 --> 2 and 1.7 --> 1

        if self.direction != (0, 0):
            self.frameIndex += self.animationSpeed * dt
        if self.frameIndex > len(self.currentAnimationImgs):
            self.frameIndex = 0
        self.img = self.currentAnimationImgs[int(self.frameIndex)]

        return {'cameraLocation': camera_location, 'inReach': self.inReach}

    def check_reach(self):
        pos = pg.mouse.get_pos()
        rect = self.rect.midbottom
        if sqrt((pos[0] - rect[0]) ** 2 + (pos[1] - rect[1]) ** 2) < MOUSE_REACH:
            self.inReach = True
        else:
            self.inReach = False

    def draw(self, win):
        shadows.draw_shadow(self.img, win, self.rect.topleft, self.rect.bottom-6)
        win.blit(self.img, (self.rect.x, self.rect.y))

