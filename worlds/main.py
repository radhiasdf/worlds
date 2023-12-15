import pygame as pg
from player import Player
from chunk import *
import shelve
import os
from constants import *
import shadows
import asyncio
from bigObject import Baumhaus
from math import sqrt, floor

CHUNK_PIXELS = TILE_ZOOM * CHUNK_SIZE


class GameManager:
	def __init__(self):
		pg.init()
		pg.display.set_caption('Twuga')
		pg.display.set_icon(pg.image.load(os.path.join("assets", "tiles", "grass3.png")))
		self.win = pg.display.set_mode((896, 503))
		print(self.win.get_size())
		self.state_stack = [MainMenu(self, 'lobby_world')]

	def game_loop(self, events):
		tick = pg.time.Clock().tick(FPS)
		dt = tick / 1000
		# print(dt)

		try:
			self.state_stack[-1].update(dt, events)
			self.state_stack[-1].draw(self.win)
			print(self.state_stack[-1].world_name_id)
		except IndexError:
			print("out of the stack's index")
			pass


class State:
	def __init__(self, game_manager):
		self.gameManager = game_manager

	def update(self, dt, events):
		pass

	def draw(self, win):
		pass


class InWorld(State):
	def __init__(self, game_manager, world_name_id):
		super().__init__(game_manager)
		self.world_name_id = world_name_id
		self.player = Player((game_manager.win.get_width() / 2, game_manager.win.get_height() / 2), game_manager)

		self.world_file = shelve.open(os.path.join("saves", world_name_id))
		# opening the saved world
		try:
			self.chunksDict = self.world_file['map_data']
			self.playerCoords = self.world_file['player_coords']
		except KeyError:
			self.chunksDict = {}
			self.playerCoords = (0, 0)

		self.tileImgs = TILEIMGS
		self.set_tile_scale()

		self.cameraLocation = pg.Vector2(0, 0)  # is in pixels
		self.inReach = False

		self.baumhaus = Baumhaus((0, 0))

	def update(self, dt, events):
		for e in events:
			if e.type == pg.KEYDOWN:
				if e.key == pg.K_ESCAPE:
					self.gameManager.state_stack.append(InWorldPauseMenu(self.gameManager))
			if e.type == pg.MOUSEBUTTONDOWN:
				self.handle_mouse_down()
			elif e.type == pg.MOUSEWHEEL:
				self.player.changeInHand()

		self.playerInfo = self.player.update(dt, self.cameraLocation, events)
		self.cameraLocation = self.playerInfo['cameraLocation']
		self.playerCoords = (self.cameraLocation + self.player.rect.midbottom) / TILE_ZOOM

	def handle_mouse_down(self):
		buttons = pg.mouse.get_pressed()
		print(buttons[0])
		if buttons[0]:
			pos = (self.cameraLocation + pg.Vector2(pg.mouse.get_pos())) / TILE_ZOOM
			chunk = pos // CHUNK_SIZE
			print(f"chunk: {chunk}")
			tile = (floor(pos.x % CHUNK_SIZE), floor(pos.y % CHUNK_SIZE))
			print(f"tile: {tile}")
			self.chunksDict[(chunk.x, chunk.y)][(tile[0], tile[1])].id = self.player.inventory['tileID']

	def check_player_reach(self):
		pos = pg.mouse.get_pos()
		rect = self.player.rect.midbottom
		if sqrt((pos[0] - rect[0]) ** 2 + (pos[1] - rect[1]) ** 2) < MOUSE_REACH:
			self.inReach = True
		else:
			self.inReach = False

	def save_and_quit(self):
		self.world_file['map_data'] = self.chunksDict
		self.world_file['player_coords'] = self.playerCoords
		print(f'{self.__class__.__name__} saved')
		self.gameManager.state_stack.pop()

	def draw(self, win):
		win.fill('darkolivegreen3')
		self.draw_map(win, self.cameraLocation)
		win.blit(my_font.render(f'{self.playerCoords}', False, 'white'), (0, 0))
		self.baumhaus.draw(win, self.cameraLocation)
		self.player.draw(win)
		self.player.drawHotbar(win)
		pg.display.update()

	def draw_map(self, win, location):  # location is in pixels
		# how many chunks are on screen
		cols_onscreen = int(pg.display.Info().current_w / CHUNK_PIXELS)
		rows_onscreen = int(pg.display.Info().current_h / CHUNK_PIXELS)
		# which chunk coordinates is on top left of screen
		chunk_x, chunk_y = int(location.x / CHUNK_PIXELS), int(location.y / CHUNK_PIXELS)

		# loads the chunks on screen; the for loop iterates through certain chunk numbers in the chunks dictionary
		for x in range(chunk_x - RENDER_DISTANCE, chunk_x + cols_onscreen + RENDER_DISTANCE + 1):
			for y in range(chunk_y - RENDER_DISTANCE, chunk_y + rows_onscreen + RENDER_DISTANCE + 1):
				try:
					for tile in self.chunksDict[(x, y)].values():
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
					self.chunksDict[(x, y)] = generate_chunk()

	def set_tile_scale(self):
		self.tileImgs = {i: pg.transform.scale(self.tileImgs[i], (
			TILE_ZOOM, int(TILE_ZOOM * (self.tileImgs[i].get_height() / self.tileImgs[i].get_width())))).convert_alpha()
						 for i in self.tileImgs}


class MainMenu(InWorld):
	def __init__(self, game_manager, world_name_id):
		super().__init__(game_manager, world_name_id)
		# the lobby is like a glove of the InWorld state rn

	def update(self, dt, events):

		for e in events:
			if e.type == pg.KEYDOWN and e.key == pg.K_SPACE:
				self.gameManager.state_stack.append(InWorld(self.gameManager, "world_1"))
			if e.type == pg.MOUSEBUTTONDOWN:
				self.handle_mouse_down()
			if e.type == pg.QUIT:
				self.save_and_quit()

		self.playerInfo = self.player.update(dt, self.cameraLocation, events)
		self.cameraLocation = self.playerInfo['cameraLocation']
		self.playerCoords = (self.cameraLocation + self.player.rect.midbottom) / TILE_ZOOM
		# print(self.playerCoords)


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


async def main():
	game_manager = GameManager()
	run = True
	while run:
		events = pg.event.get()
		game_manager.game_loop(events)

		for e in events:
			if e.type == pg.QUIT:
				run = False
		#print([state.__class__.__name__ for state in game_manager.state_stack])

		await asyncio.sleep(0)


asyncio.run(main())
