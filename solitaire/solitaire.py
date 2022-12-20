import pygame
import os


class InSolitaire:
    def __init__(self):
        self.suitImgs = [pygame.image.load(os.path.join('assets', f'{name}.png')) for name in ('spades', 'clubs', 'hearts', 'diamonds')]
        self.numImgs = [[pygame.image.load(os.path.join('assets', f'{colour}_{name}.png')) for name in range(1, 14)] for colour in ('black', 'red')]

    def update(self, dt, events):
        pass
