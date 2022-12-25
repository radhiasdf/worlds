import os
from random import shuffle
from solitaire.changeColour import change_colour
from itertools import chain
import pygame as pg
import time

FPS = 60

SUITS = ['spades', 'clubs', 'hearts', 'diamonds']
VALUES = 14
PIXEL_SCALE = 3
CARD_SCALE = (17*PIXEL_SCALE, 23*PIXEL_SCALE)
PILE_SPACING = 1*PIXEL_SCALE
EXTRA_PILE_SPACING = 5*PIXEL_SCALE
CARD_SPACING = 8*PIXEL_SCALE
NUM_GROWING_PILES = 7

BOARD_SIZE = pg.Vector2(NUM_GROWING_PILES*(CARD_SCALE[0]+PILE_SPACING) + 2*(CARD_SCALE[0]+EXTRA_PILE_SPACING),
                        CARD_SPACING * VALUES + (CARD_SCALE[1] - CARD_SPACING))


# make it as independent of the game it is in as possible
class InSolitaire:
    def __init__(self, game_manager=None):
        self.gameManager = game_manager
        if game_manager:
            self.win = game_manager.win
        else:
            pg.init()
            pg.display.set_caption('Solitaire')
            pg.display.set_icon(pg.image.load(os.path.join("solitaire", "assets", "card_back.png")))
            self.win = pg.display.set_mode((pg.display.Info().current_w * .7, pg.display.Info().current_h * .7))

        self.suitImgs = [pg.transform.scale(pg.image.load(os.path.join('solitaire', 'assets', f'{suit}.png')), CARD_SCALE) for suit in SUITS]
        self.valImgs = [pg.transform.scale(pg.image.load(os.path.join('solitaire', 'assets', f'black_{i}.png')), CARD_SCALE) for i in range(1, VALUES)]
        self.cardFrontImg = pg.transform.scale(pg.image.load(os.path.join('solitaire', 'assets', 'card.png')), CARD_SCALE)
        self.cardBackImg = pg.transform.scale(pg.image.load(os.path.join('solitaire', 'assets', 'card_back.png')), CARD_SCALE)
        self.cardBorderImg = pg.transform.scale(pg.image.load(os.path.join('solitaire', 'assets', 'border.png')), CARD_SCALE)
        self.cardOutlineImg = pg.transform.scale(pg.image.load(os.path.join('solitaire', 'assets', 'card_outline.png')), CARD_SCALE)

        self.numOpenedCards = 3

        # setting up piles
        self.stockPile = StockPile(StockPileOpened(self.numOpenedCards), self.numOpenedCards)

        for i in range(1, VALUES):
            for j in range(len(SUITS)):
                self.stockPile.array.append(Card(i, SUITS[j], [self.cardFrontImg, self.suitImgs[j]], self.cardBackImg,
                                                 val_img=self.valImgs[i - 1], outline_img=self.cardOutlineImg))
                if j > 10:
                    self.stockPile.array[-1].layeredFrontImgs.append(self.cardBorderImg)
        self.suitPiles = [SuitPile(suit, self.suitImgs[i], self.cardOutlineImg) for i, suit in enumerate(SUITS)]
        shuffle(self.stockPile.array)

        # dealing cards from stockpile to growing piles
        self.growingPiles = [GrowingPile() for _ in range(NUM_GROWING_PILES)]
        for i, pile in enumerate(self.growingPiles):
            for _ in range(i+1):
                pile.array.append(self.stockPile.array.pop())
            pile.array[-1].faceUp = True

        self.set_positions()
        if not game_manager:
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
                self.update(dt, events)
                self.draw(self.win)

    def update(self, dt, events):
        for e in events:
            if e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                if self.gameManager:
                    self.gameManager.state_stack.pop()
            if e.type == pg.MOUSEBUTTONDOWN:
                pos = pg.mouse.get_pos()

                for pile in chain([self.stockPile], self.growingPiles, self.suitPiles):
                    pile.mouse_input(pos)

            if e.type == pg.VIDEORESIZE:
                self.set_positions()

    def set_positions(self):
        self.board_pos = pg.Vector2((self.win.get_width() - BOARD_SIZE.x) / 2,
                                    (self.win.get_height() - BOARD_SIZE.y) / 2)

        self.stockPile.rect.topleft = self.board_pos
        self.stockPile.openedPile.rect.topleft = (self.board_pos.x, self.stockPile.rect.bottom + PILE_SPACING)
        self.stockPile.openedPile.position_clickable()

        for i, pile in enumerate(self.growingPiles):
            pile.rect.topleft = (self.stockPile.rect.right + EXTRA_PILE_SPACING + (CARD_SCALE[0]+PILE_SPACING)*i,
                                 self.board_pos.y)
        for i, pile in enumerate(self.suitPiles):
            pile.rect.topleft = (self.growingPiles[-1].rect.right + EXTRA_PILE_SPACING,
                                 self.board_pos.y + (CARD_SCALE[1]+PILE_SPACING)*i)

    def draw(self, win):
        win.fill('darkolivegreen3')
        self.stockPile.draw(win)
        for pile in self.growingPiles:
            pile.draw(win)
        for pile in self.suitPiles:
            pile.draw(win)

        pg.display.update()


class Card:
    def __init__(self, value, suit, layered_front_imgs, back_img, face_up=False, val_img=None, outline_img=None):
        self.value = value
        self.suit = suit
        self.layeredFrontImgs = layered_front_imgs
        self.valImg = val_img
        self.backImg = back_img
        self.outlineImg = outline_img
        self.faceUp = face_up

        if self.suit in ('hearts', 'diamonds'):
            self.valImg = change_colour(self.valImg, 'red', special_flags=pg.BLEND_ADD)

    def draw(self, win, pos=(0, 0)):

        if self.faceUp:
            for img in self.layeredFrontImgs:
                win.blit(img, pos)
            if self.valImg:
                win.blit(self.valImg, pos)
        else:
            win.blit(self.backImg, pos)
        if self.outlineImg:
            win.blit(self.outlineImg, pos)


class Pile:
    def __init__(self, array=None, pos=(0, 0)):
        # to generalise stacks and queues
        if array is None:
            array = []
        self.array = array
        pass

        # would be the default (for stock and suit piles)
        self.rect = pg.rect.Rect(pos[0], pos[1], CARD_SCALE[0], CARD_SCALE[1])

    def mouse_input(self, pos):
        pass

    def draw(self, win):
        try:
            self.array[-1].draw(win, (self.rect.x, self.rect.y))
        except IndexError:
            pass


class StockPile(Pile):

    def __init__(self, opened_pile, num_opened_cards, outline_img=None):
        super().__init__()
        self.outlineImg = outline_img
        self.openedPile = opened_pile
        self.numOpenedCards = num_opened_cards

    def mouse_input(self, pos):
        if self.rect.collidepoint(pos):
            if len(self.array) == 0:
                for _ in range(len(self.openedPile.array)):
                    self.array.append(self.openedPile.array.pop(0))
                    self.array[-1].faceUp = False
                return
            for _ in range(self.numOpenedCards):
                try:
                    self.openedPile.array.append(self.array.pop(0))
                    self.openedPile.array[-1].faceUp = True
                except IndexError:
                    pass
        else:
            self.openedPile.mouse_input(pos)

    def draw(self, win):
        try:
            self.array[-1].draw(win, self.rect.topleft)
        except IndexError:
            if self.outlineImg:
                win.blit(self.outlineImg, self.rect.topleft)
        self.openedPile.draw(win)


class StockPileOpened(Pile):

    def __init__(self, num_visible_cards):
        super().__init__()
        self.numVisibleCards = num_visible_cards
        self.clickable = pg.rect.Rect(0, 0, CARD_SCALE[0], CARD_SCALE[1])

    def position_clickable(self):
        # because only the bottom card can be dragged/clicked theres another rect for it
        self.clickable.topleft = (self.rect.x, self.rect.y + CARD_SPACING*(self.numVisibleCards-1))
    def mouse_input(self, pos):
        if self.clickable.collidepoint(pos):
            pass


    def draw(self, win):
        try:
            for i in range(self.numVisibleCards):
                self.array[-(self.numVisibleCards-i)].draw(win, (self.rect.x, self.rect.y + i*CARD_SPACING))
        except IndexError: pass


class GrowingPile(Pile):

    def __init__(self):
        super().__init__()

    def draw(self, win):
        for i, card in enumerate(self.array):
            card.draw(win, (self.rect.x, self.rect.y + i*CARD_SPACING))


class SuitPile(Pile):

    def __init__(self, suit, suit_img, outline_img):
        super().__init__()
        self.suit = suit
        self.suitImg = suit_img
        self.outlineImg = outline_img

    def draw(self, win):
        for img in (self.suitImg, self.outlineImg):
            win.blit(img, self.rect.topleft)
        try:
            self.array[-1].draw(win)
        except IndexError:
            pass



