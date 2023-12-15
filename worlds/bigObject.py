import pygame as pg
import os
from constants import TILE_ZOOM


class BigObject:
	# so its gonna have a rect that will also act as a collidebox
	def __init__(self):
		self.collideBox = pg.Rect(0, 0, 0, 0)



class Baumhaus(BigObject):

	def __init__(self, coords):
		super(Baumhaus, self).__init__()
		self.img = pg.image.load(os.path.join("assets", "baumhaus.png"))
		self.img = pg.transform.scale(self.img, (self.img.get_width() * 2, self.img.get_height() * 2))
		self.collideBox = pg.Rect(coords[0], coords[1], self.img.get_width(), self.img.get_height())

	def draw(self, win, cameraCoords):
		win.blit(self.img, pg.Vector2(self.collideBox.topleft) - cameraCoords)
