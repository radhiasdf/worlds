from solitaire.images import change_colour
import pygame as pg
from solitaire.constants import CARD_SCALE, CARD_SPACING, VALUES
import random
from solitaire.actions import StockPileClick


class Card:
    def __init__(self, value, suit, layered_front_imgs, back_img, face_up=False, val_img=None, outline_img=None, pos=(0, 0)):
        self.value = value
        self.suit = suit
        self.layeredFrontImgs = layered_front_imgs
        self.valImg = val_img
        self.backImg = back_img
        self.outlineImg = outline_img
        self.faceUp = face_up
        self.pos = pos

        if self.suit in ('hearts', 'diamonds'):
            if val_img:
                self.valImg = change_colour(self.valImg, 'red', special_flags=pg.BLEND_ADD)
            self.colour = 'red'
        else:
            self.colour = 'black'

    def draw(self, win, position=None):

        if position is None:
            pos = self.pos
        else:
            pos = position

        if self.faceUp:
            for img in self.layeredFrontImgs:
                win.blit(img, pos)
            if self.valImg:
                win.blit(self.valImg, pos)
        else:
            win.blit(self.backImg, pos)
        if self.outlineImg:
            win.blit(self.outlineImg, pos)

    def set_win_animation(self, pos):
        a_magnitude = 10
        random_direction = random.choice([random.randint(-5, -1), random.randint(1, 5)])

        self.pos = [pos[0], pos[1]]
        if self.suit == 'spades':
            self.acceleration = [0, a_magnitude]
            self.velocity = [random_direction, 0]
        elif self.suit == 'clubs':
            self.acceleration = [0, -a_magnitude]
            self.velocity = [random_direction, 0]
        elif self.suit == 'hearts':
            self.acceleration = [a_magnitude, 0]
            self.velocity = [0, random_direction]
        elif self.suit == 'diamonds':
            self.acceleration = [-a_magnitude, 0]
            self.velocity = [0, random_direction]

    def update_win_animation(self, dt, win):
        self.velocity[0] += self.acceleration[0] * dt
        self.velocity[1] += self.acceleration[1] * dt
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

        if self.pos[0] < 0 or self.pos[0] > win.get_width() - self.backImg.get_width():
            if self.pos[0] < 0:
                self.pos[0] = 0
            if self.pos[0] > win.get_width() - self.backImg.get_width():
                self.pos[0] = win.get_width() - self.backImg.get_width()
            self.velocity[0] = -self.velocity[0]
        if self.pos[1] < 0 or self.pos[1] > win.get_height() - self.backImg.get_height():
            if self.pos[1] < 0:
                self.pos[1] = 0
            if self.pos[1] > win.get_height() - self.backImg.get_height():
                self.pos[1] = win.get_height() - self.backImg.get_height()
            self.velocity[1] = -self.velocity[1]


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

    def grab_cards(self, pos):
        # must return array of cards to be iterated in inhand pile
        if self.clickRect.collidepoint(pos):
            try:
                return [self.array.pop()]
            except IndexError:
                pass

    def check_accepted(self, pos, pile):
        pass

    def check_card_under(self):
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

    def __init__(self, opened_pile, num_opened_cards, action_manager, reload_img=None):
        super().__init__()
        self.reloadImg = reload_img
        self.openedPile = opened_pile
        self.numOpenedCards = num_opened_cards
        self.actionManager = action_manager  # sorry this is not consistent with where the stack is managed because the
        # cards dont get passed through the game manager

    def grab_cards(self, pos):
        # reloading all cards back face down
        if len(self.array) == 0:
            for _ in range(len(self.openedPile.array)):
                self.array.append(self.openedPile.array.pop())
                self.array[-1].faceUp = False
            self.actionManager.add_action(StockPileClick(self.openedPile, self, len(self.array), face_up=False))
            return []
        # opening one/three cards at a time
        num_cards = 0
        for _ in range(self.numOpenedCards):
            try:
                self.openedPile.array.append(self.array.pop())
                self.openedPile.array[-1].faceUp = True
                num_cards += 1
            except IndexError:
                pass
        self.actionManager.add_action(StockPileClick(self, self.openedPile, num_cards, face_up=True))
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

    def grab_cards(self, pos):
        self.mousedown = True
        if self.clickRect.collidepoint(pos):
            try:
                return [self.array.pop()]
            except IndexError:
                pass

    def check_accepted(self, pos, pile):
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

    def grab_cards(self, pos):
        if len(self.array) == 0:
            # there was an error where if i returned a string it would later dynamically be treated as a card object
            return
        grabbed = []
        if self.clickRect.bottom - pos[1] < CARD_SCALE[1]:
            num_grabbed = 1
        else:
            num_grabbed = (self.clickRect.bottom - CARD_SCALE[1] - pos[1])//CARD_SPACING + 2
        for _ in range(num_grabbed):
            # i use insert instead of 2 stacks because the inhand array is directly rendered
            try:
                grabbed.insert(0, self.array.pop())
            except IndexError:
                pass  # no idea why this happened  # update: actually might be something to do with the misaligned clickrect that was not reset
        return grabbed

    def check_accepted(self, pos, pile):
        if len(pile.array) == 0:
            return 'empty'
        if len(self.array) > 0:
            if pile.array[0].colour != self.array[-1].colour and pile.array[0].value == self.array[-1].value-1:
                return 'accepted'
        elif pile.array[0].value == VALUES:
            return 'accepted'

    def check_card_under(self):
        try:
            if not self.array[-1].faceUp:
                self.array[-1].faceUp = True
                self.set_click_rect()
                return True
            else:
                self.set_click_rect()
                return False
        except IndexError:
            return False


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

    def check_accepted(self, pos, pile):
        if len(pile.array) == 1 and pile.array[0].suit == self.suit:
            try:
                if pile.array[0].value == self.array[-1].value+1:
                    return 'accepted'
            except:
                if pile.array[0].value == 1:
                    return 'accepted'
