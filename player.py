import pygame as pg
import os
import shadows
from constants import TILE_ZOOM
sprite_size = TILE_ZOOM*2
from solitaire.solitaire import InSolitaire


class Player:
    def __init__(self, pos, game):
        self.game = game  # is putting the game instance in a bunch of other instances bad

        self.imgsWalkingFront = [pg.image.load(os.path.join("assets", "pixil-gif-drawing-tamarin-20221217", f"sprite_{i}.png")) for i in range(4)]
        for i, img in enumerate(self.imgsWalkingFront):
            self.imgsWalkingFront[i] = pg.transform.scale(img, (sprite_size, sprite_size)).convert_alpha()

        self.currentAnimationImgs = self.imgsWalkingFront
        self.rect = self.currentAnimationImgs[0].get_rect(center=pos)
        self.direction = pg.math.Vector2()
        self.speed = 150
        self.animationSpeed = 7
        self.frameIndex = 0
        self.img = self.currentAnimationImgs[int(self.frameIndex)]

    def input(self, events):
        keys = pg.key.get_pressed()  # does this slow down code
        print(len(keys))
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
                    self.game.state_stack.append(InSolitaire(game_manager=self.game))

                """if e.key in (pg.K_UP,pg.K_w):
                    """

    def update(self, dt, camera_location, events):
        self.input(events)
        camera_location += self.direction * int(self.speed * dt) # there was a bug where going down and right were slower than up and left; i suspect the rounding to rect.center was floor, causing -1.7 --> 2 and 1.7 --> 1

        if self.direction != (0, 0):
            self.frameIndex += self.animationSpeed * dt
        if self.frameIndex > len(self.currentAnimationImgs):
            self.frameIndex = 0
        self.img = self.currentAnimationImgs[int(self.frameIndex)]

        return camera_location

    def draw(self, win):

        shadows.draw_shadow(self.img, win, self.rect.topleft, self.rect.bottom-6)
        win.blit(self.img, (self.rect.x, self.rect.y))

