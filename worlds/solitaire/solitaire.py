import os
import random
from random import shuffle
from itertools import chain
import pygame as pg
from solitaire.cards_and_piles import Card, Pile, StockPile, StockPileOpened, GrowingPile, SuitPile
from solitaire.constants import VALUES, SUITS, CARD_SCALE, CARD_SPACING, NUM_GROWING_PILES, RANDOM_POP, \
    PILE_SPACING, EXTRA_PILE_SPACING, BOARD_SIZE, AUTO_WIN, PIXEL_SCALE
from solitaire.actions import ActionManager, CardAction


# make it as independent of the game it is in as possible
class InSolitaire:
    def __init__(self, game_manager=None):
        self.gameManager = game_manager
        if game_manager:
            self.win = game_manager.win
        else:
            pg.init()
            pg.display.set_caption('Solitaire')
            pg.display.set_icon(pg.image.load(os.path.join('solitaire', "assets", "card_back.png")))
            self.win = pg.display.set_mode((800, 500))

        self.images = load_images(os.path.join('solitaire', 'assets'))
        self.resetButton = Dropdown(img=self.images['reset_button'], pos=(PILE_SPACING, PILE_SPACING))
        self.resetButton.options.append(Button(img=self.images['easy'], pos=(self.resetButton.rect.x, self.resetButton.rect.bottom + PILE_SPACING)))
        self.resetButton.options.append(Button(img=self.images['hard'], pos=(self.resetButton.options[-1].rect.x, self.resetButton.options[-1].rect.bottom + PILE_SPACING)))

        self.reset(1)

    def reset(self, num_opened_cards):
        self.actionManager = ActionManager()

        # setting up piles
        self.stockPile = StockPile(StockPileOpened(num_opened_cards), num_opened_cards, self.actionManager,
                                   reload_img=self.images['card_reload'])

        for i in range(VALUES):
            for j in range(len(SUITS)):
                self.stockPile.array.append(
                    Card(i + 1, SUITS[j], [self.images['card'], self.images[SUITS[j]]], self.images['card_back'],
                         val_img=self.images[f'black_{i+1}'], outline_img=self.images['card_outline']))
                if j > 10:
                    self.stockPile.array[-1].layeredFrontImgs.append(self.images['border'])
        self.suitPiles = [SuitPile(suit, self.images[suit], self.images['card_outline']) for suit in SUITS]
        self.inHand = Pile()

        # dealing cards from stockpile to growing piles
        shuffle(self.stockPile.array)
        self.growingPiles = [GrowingPile() for _ in range(NUM_GROWING_PILES)]
        for i, pile in enumerate(self.growingPiles):
            for _ in range(i + 1):
                pile.array.append(self.stockPile.array.pop())
            pile.array[-1].faceUp = True

        self.set_positions()
        self.mousedown = False
        self.sourcePile = None
        self.won = False
        self.popTimer = 0
        if AUTO_WIN:
            for j in range(len(self.suitPiles)):
                for i in range(VALUES):
                    self.suitPiles[j].array.append(
                        Card(i + 1, SUITS[j], [self.images['card'], self.images[SUITS[j]]], self.images['card_back'],
                             val_img=self.images[f'black_{i+1}'], outline_img=self.images['card_outline'], face_up=True))
            self.won = True
        self.animatedCards = []

    def update(self, dt, events):

        for e in events:
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    if self.gameManager:
                        self.gameManager.state_stack.pop()
                elif pg.key.get_mods() & pg.KMOD_LCTRL:
                    if e.key == pg.K_z:
                        if pg.key.get_mods() & pg.KMOD_LSHIFT:
                            self.actionManager.do('redo')
                        else:
                            self.actionManager.do('undo')
                    elif e.key == pg.K_y:
                        self.actionManager.do('redo')
            if e.type == pg.MOUSEBUTTONDOWN:
                pos = pg.mouse.get_pos()
                if not self.won:
                    self.handle_mouse_down_piles(pos)
                self.handle_buttons(pos)
            if e.type == pg.MOUSEBUTTONUP:
                self.handle_mouse_up()
            if e.type == pg.VIDEORESIZE:
                self.set_positions()

        if self.won:
            self.popTimer -= dt
            if self.popTimer < 0:
                self.popTimer = random.uniform(RANDOM_POP[0], RANDOM_POP[1])
                pile = self.suitPiles[random.randint(0, len(SUITS)-1)]
                try:
                    card = pile.array.pop()
                    card.set_win_animation(pile.rect.topleft)
                    self.animatedCards.append(card)
                except IndexError: pass

            for card in self.animatedCards:
                card.update_win_animation(dt, self.win)

    def handle_mouse_down_piles(self, pos):
        self.mousedown = True
        for pile in chain([self.stockPile, self.stockPile.openedPile], self.growingPiles, self.suitPiles):
            if pile.clickRect.collidepoint(pos):
                self.sourcePile = pile
                # different piles have different rules and return arrays (that can be empty)
                cards = pile.grab_cards(pos)
                if cards is not None:
                    for card in cards:
                        self.inHand.array.append(card)
                    self.inHand.rect.update(self.sourcePile.clickRect)
                    if self.sourcePile in self.growingPiles:
                        self.dragging_pos = (self.sourcePile.rect.x - pos[0], self.sourcePile.rect.y + len(self.sourcePile.array)*CARD_SPACING - pos[1])
                    else:
                        self.dragging_pos = (self.sourcePile.clickRect.x - pos[0], self.sourcePile.clickRect.y - pos[1])

    def handle_mouse_up(self):
        self.mousedown = False
        pos = pg.mouse.get_pos()

        for pile in chain(self.growingPiles, self.suitPiles):
            if pile.acceptRect.collidepoint(pos) and pile != self.sourcePile:
                if pile.check_accepted(pos, self.inHand) == 'accepted':
                    num_cards = len(self.inHand.array)
                    for _ in range(num_cards):
                        pile.array.append(self.inHand.array.pop(0))
                    new_card_is_opened = self.sourcePile.check_card_under()
                    self.actionManager.add_action(CardAction(self.sourcePile, pile, num_cards, new_card_is_opened=new_card_is_opened))
                    pile.set_click_rect()
                    if pile in self.suitPiles:
                        self.check_won()
                    return
        for _ in range(len(self.inHand.array)):
            self.sourcePile.array.append(self.inHand.array.pop(0))

    def check_won(self):
        for pile in self.suitPiles:
            if len(pile.array) != VALUES:
                return
        self.won = True

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
            pile.acceptRect.update(pile.acceptRect.x, 0, self.win.get_width() - pile.acceptRect.x, self.win.get_height())

    def handle_buttons(self, pos):
        if self.resetButton.rect.collidepoint(pos):
            self.resetButton.open ^= True

        if self.resetButton.open:
            if self.resetButton.options[0].rect.collidepoint(pos):
                self.reset(1)
            elif self.resetButton.options[1].rect.collidepoint(pos):
                self.reset(3)

    def draw(self, window=None):
        if window is None:
            win = self.win
        else:
            win = window
        win.fill('bisque3')
        self.stockPile.draw(win)
        for pile in self.growingPiles:
            pile.draw_spaced(win)
        for pile in self.suitPiles:
            pile.draw(win)

        if self.mousedown:
            if len(self.inHand.array) > 0:
                self.inHand.rect.topleft = (pg.mouse.get_pos()[0] + self.dragging_pos[0], pg.mouse.get_pos()[1] + self.dragging_pos[1])
                self.inHand.draw_spaced(win)

        if self.won:
            for card in self.animatedCards:
                card.draw(win)

        self.resetButton.draw(win)

        pg.display.update()


class Button:
    def __init__(self, img=None, pos=(0, 0), width=50, height=50):
        self.img = img
        if img:
            width, height = img.get_width(), img.get_height()
        self.rect = pg.rect.Rect(pos[0], pos[1], width, height)

    def draw(self, win):
        if self.img:
            win.blit(self.img, self.rect.topleft)


class Dropdown(Button):
    def __init__(self, options=None, img=None, pos=(0, 0), width=50, height=50):
        super().__init__()
        if options is None:
            options = []
        self.options = options
        self.open = False
        self.img = img
        self.rect = pg.rect.Rect(pos[0], pos[1], width, height)

    def draw(self, win):
        if self.img:
            win.blit(self.img, self.rect.topleft)
        if self.open:
            for option in self.options:
                option.draw(win)


def load_images(path_to_directory):
    """Load images and return them as a dict."""
    image_dict = {}
    for filename in os.listdir(path_to_directory):
        if filename.endswith('.png'):
            path = os.path.join(path_to_directory, filename)
            key = filename[:-4]
            img = pg.image.load(path).convert_alpha()
            image_dict[key] = pg.transform.scale(img, (img.get_width()*PIXEL_SCALE, img.get_height()*PIXEL_SCALE))
    return image_dict
