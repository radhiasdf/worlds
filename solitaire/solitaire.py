import os
from random import shuffle
from solitaire.changeColour import change_colour
from itertools import chain
import pygame as pg
import time

FPS = 60

SUITS = ['spades', 'clubs', 'hearts', 'diamonds']
VALUES = 13
PIXEL_SCALE = 3
CARD_SCALE = (17*PIXEL_SCALE, 23*PIXEL_SCALE)
PILE_SPACING = 1*PIXEL_SCALE
EXTRA_PILE_SPACING = 5*PIXEL_SCALE
CARD_SPACING = 8*PIXEL_SCALE  # to show the numbers when theyre stacked face up
NUM_GROWING_PILES = 7

BOARD_SIZE = pg.Vector2(NUM_GROWING_PILES*(CARD_SCALE[0]+PILE_SPACING) + 2*(CARD_SCALE[0]+EXTRA_PILE_SPACING),
                        CARD_SCALE[1] + CARD_SPACING * (VALUES-1))


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

        self.suitImgs = [pg.transform.scale(pg.image.load(os.path.join('solitaire', 'assets', f'{suit}.png')), CARD_SCALE).convert_alpha() for suit in SUITS]
        self.valImgs = [pg.transform.scale(pg.image.load(os.path.join('solitaire', 'assets', f'black_{i+1}.png')), CARD_SCALE).convert_alpha() for i in range(VALUES)]
        self.cardFrontImg = pg.transform.scale(pg.image.load(os.path.join('solitaire', 'assets', 'card.png')), CARD_SCALE).convert_alpha()
        self.cardBackImg = pg.transform.scale(pg.image.load(os.path.join('solitaire', 'assets', 'card_back.png')), CARD_SCALE).convert_alpha()
        self.cardBorderImg = pg.transform.scale(pg.image.load(os.path.join('solitaire', 'assets', 'border.png')), CARD_SCALE).convert_alpha()
        self.cardOutlineImg = pg.transform.scale(pg.image.load(os.path.join('solitaire', 'assets', 'card_outline.png')), CARD_SCALE).convert_alpha()
        self.cardReloadImg = pg.transform.scale(pg.image.load(os.path.join('solitaire', 'assets', 'card_reload.png')), CARD_SCALE).convert_alpha()

        self.numOpenedCards = 1

        # setting up piles
        self.stockPile = StockPile(StockPileOpened(self.numOpenedCards), self.numOpenedCards, reload_img=self.cardReloadImg)

        for i in range(VALUES):
            for j in range(len(SUITS)):
                self.stockPile.array.append(Card(i+1, SUITS[j], [self.cardFrontImg, self.suitImgs[j]], self.cardBackImg,
                                                 val_img=self.valImgs[i], outline_img=self.cardOutlineImg))
                if j > 10:
                    self.stockPile.array[-1].layeredFrontImgs.append(self.cardBorderImg)
        self.suitPiles = [SuitPile(suit, self.suitImgs[i], self.cardOutlineImg) for i, suit in enumerate(SUITS)]
        self.inHand = Pile()

        # dealing cards from stockpile to growing piles
        shuffle(self.stockPile.array)
        self.growingPiles = [GrowingPile() for _ in range(NUM_GROWING_PILES)]
        for i, pile in enumerate(self.growingPiles):
            for _ in range(i+1):
                pile.array.append(self.stockPile.array.pop())
            pile.array[-1].faceUp = True

        self.set_positions()
        self.mousedown = False
        self.sourcePile = None

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
                self.handle_mouse_down()
            if e.type == pg.MOUSEBUTTONUP:
                self.handle_mouse_up()
            if e.type == pg.VIDEORESIZE:
                self.set_positions()

    def handle_mouse_down(self):
        self.mousedown = True
        pos = pg.mouse.get_pos()
        for pile in chain([self.stockPile, self.stockPile.openedPile], self.growingPiles, self.suitPiles):
            if pile.clickRect.collidepoint(pos):
                self.sourcePile = pile
                # different piles have different rules and return arrays (that can be empty)
                cards = pile.mouse_down_collide(pos)
                if cards is not None:
                    for card in cards: self.inHand.array.append(card)
                    self.inHand.rect.update(self.sourcePile.clickRect)
                    self.dragging_pos = (self.sourcePile.clickRect.x - pos[0], self.sourcePile.clickRect.y - pos[1])

    def handle_mouse_up(self):
        self.mousedown = False
        pos = pg.mouse.get_pos()

        for pile in chain(self.growingPiles, self.suitPiles):
            if pile.acceptRect.collidepoint(pos) and pile != self.sourcePile:
                if pile.mouse_up_collide(pos, self.inHand) == 'accepted':
                    for _ in range(len(self.inHand.array)):
                        pile.array.append(self.inHand.array.pop(0))
                    self.sourcePile.released_successfully()
                    pile.set_click_rect()
                    return
        for _ in range(len(self.inHand.array)):
            self.sourcePile.array.append(self.inHand.array.pop(0))

    def set_positions(self):
        self.board_pos = pg.Vector2((self.win.get_width() - BOARD_SIZE.x) / 2,
                                    (self.win.get_height() - BOARD_SIZE.y) / 2)

        self.stockPile.clickRect.topleft = self.stockPile.rect.topleft = self.board_pos
        self.stockPile.openedPile.rect.topleft = (self.board_pos.x, self.stockPile.rect.bottom + PILE_SPACING)
        self.stockPile.openedPile.set_click_rect()

        for i, pile in enumerate(self.growingPiles):
            pile.acceptRect.topleft = pile.rect.topleft = (self.stockPile.rect.right + EXTRA_PILE_SPACING + (CARD_SCALE[0] + PILE_SPACING) * i,
                                                           self.board_pos.y)
            pile.acceptRect.y, pile.acceptRect.h = 0, self.win.get_height()
            pile.set_click_rect()
        for i, pile in enumerate(self.suitPiles):
            pile.rect.topleft = pile.clickRect.topleft = pile.acceptRect.topleft = \
                (self.growingPiles[-1].rect.right + EXTRA_PILE_SPACING,
                 self.board_pos.y + (CARD_SCALE[1]+PILE_SPACING) * i)

    def draw(self, win):
        win.fill('darkolivegreen3')
        self.stockPile.draw(win)
        for pile in self.growingPiles:
            pile.draw_spaced(win)
            pg.draw.rect(win, 'red', pile.clickRect, PIXEL_SCALE)
        for pile in self.suitPiles:
            pile.draw(win)

        if self.mousedown:
            if len(self.inHand.array) > 0:

                self.inHand.rect.topleft = (pg.mouse.get_pos()[0] + self.dragging_pos[0], pg.mouse.get_pos()[1] + self.dragging_pos[1])
                self.inHand.draw_spaced(win)

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
            self.colour = 'red'
        else:
            self.colour = 'black'

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
        self.clickRect = pg.rect.Rect(pos[0], pos[1], CARD_SCALE[0], CARD_SCALE[1])
        self.acceptRect = pg.rect.Rect(pos[0], pos[1], CARD_SCALE[0], CARD_SCALE[1])

    def mouse_down_collide(self, pos):
        # must return array of cards to be iterated in inhand pile
        if self.clickRect.collidepoint(pos):
            try:
                return [self.array.pop()]
            except IndexError:
                pass

    def mouse_up_collide(self, pos, pile):
        pass

    def released_successfully(self):
        pass

    def set_click_rect(self):
        pass

    def draw(self, win):
        # the cards don't have a rect and are instead anchored to the piles' rects
        try:
            self.array[-1].draw(win, self.rect.topleft)
        except IndexError:
            pass

    def draw_spaced(self, win):
        for i, card in enumerate(self.array):
            card.draw(win, (self.rect.x, self.rect.y + i*CARD_SPACING))


class StockPile(Pile):

    def __init__(self, opened_pile, num_opened_cards, reload_img=None):
        super().__init__()
        self.reloadImg = reload_img
        self.openedPile = opened_pile
        self.numOpenedCards = num_opened_cards

    def mouse_down_collide(self, pos):
        # reloading all cards back face down
        if len(self.array) == 0:
            for _ in range(len(self.openedPile.array)):
                self.array.append(self.openedPile.array.pop(0))
                self.array[-1].faceUp = False
            return []
        # opening one/three cards at a time
        for _ in range(self.numOpenedCards):
            try:
                self.openedPile.array.append(self.array.pop(0))
                self.openedPile.array[-1].faceUp = True
            except IndexError:
                pass
        return []

    def draw(self, win):
        try:
            self.array[-1].draw(win, self.rect.topleft)
        except IndexError:
            if self.reloadImg:
                win.blit(self.reloadImg, self.rect.topleft)
        self.openedPile.draw(win)


class StockPileOpened(Pile):

    def __init__(self, num_visible_cards):
        super().__init__()
        self.numVisibleCards = num_visible_cards
        self.mousedown = False

    def set_click_rect(self):
        # because only the bottom card can be dragged/clicked theres another rect for it
        self.clickRect.topleft = (self.rect.x, self.rect.y + CARD_SPACING * (self.numVisibleCards - 1))

    def mouse_down_collide(self, pos):
        self.mousedown = True
        if self.clickRect.collidepoint(pos):
            try:
                return [self.array.pop()]
            except IndexError:
                pass

    def mouse_up_collide(self, pos, pile):
        self.mousedown = False

    def draw(self, win):
        for i in range(self.numVisibleCards):
            try:
                self.array[-(self.numVisibleCards-i)].draw(win, (self.rect.x, self.rect.y + i*CARD_SPACING))
            except IndexError: pass


class GrowingPile(Pile):

    def __init__(self):
        super().__init__()

    def set_click_rect(self):
        face_down_cards = 0
        for card in self.array:
            if not card.faceUp:
                face_down_cards += 1

        self.clickRect.update(self.rect.x, self.rect.y + face_down_cards*CARD_SPACING,
                              self.rect.w, CARD_SCALE[1] + (len(self.array)-face_down_cards-1)*CARD_SPACING)

    def mouse_down_collide(self, pos):
        if len(self.array) == 0:
            return 'empty'
        grabbed = []
        if self.clickRect.bottom-pos[1] < CARD_SCALE[1]:
            num_grabbed = 1
        else:
            num_grabbed = (self.clickRect.bottom-pos[1]-CARD_SCALE[1])//CARD_SPACING + 2
        for _ in range(num_grabbed):
            grabbed.insert(0, self.array.pop())
        return grabbed

    def mouse_up_collide(self, pos, pile):
        if len(pile.array) == 0:
            return 'empty'
        if len(self.array) > 0:
            if pile.array[0].colour != self.array[-1].colour and pile.array[0].value == self.array[-1].value-1:
                return 'accepted'
        elif pile.array[0].value == VALUES:
            return 'accepted'

    def released_successfully(self):
        try:
            self.array[-1].faceUp = True
        except IndexError:
            print('index error???')
        self.set_click_rect()


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
            self.array[-1].draw(win, self.rect.topleft)
        except IndexError:
            pass

    def mouse_up_collide(self, pos, pile):
        if len(pile.array) == 1 and pile.array[0].suit == self.suit:
            try:
                if pile.array[0].value == self.array[-1].value+1:
                    return 'accepted'
            except:
                if pile.array[0].value == 1:
                    return 'accepted'
