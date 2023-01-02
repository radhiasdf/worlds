class ActionManager:
    def __init__(self):
        self.undoStack = []
        self.redoStack = []

    def do(self, undo_redo):
        try:
            if undo_redo == 'redo':
                self.redoStack[-1].do('redo')
                self.undoStack.append(self.redoStack.pop())
            else:
                self.undoStack[-1].do('undo')
                self.redoStack.append(self.undoStack.pop())
        except IndexError:
            pass

    def add_action(self, action):
        self.undoStack.append(action)
        self.redoStack.clear()  # you cant go back to the future if youve changed something from the past


class CardAction:
    def __init__(self, taken_from, placed_to, num_cards, new_card_is_opened=False):
        self.pileTakenFrom = taken_from
        self.pilePlacedTo = placed_to
        self.numCards = num_cards
        self.new_card_opened = new_card_is_opened

    def do(self, undo_redo):
        temp = []
        if undo_redo == 'redo':  # basically do the exact same thing
            for _ in range(self.numCards):
                temp.append(self.pileTakenFrom.array.pop())
            if self.new_card_opened:
                self.pileTakenFrom.array[-1].faceUp = True
            for _ in range(self.numCards):
                self.pilePlacedTo.array.append(temp.pop())
        else:  # if undo, do the reverse
            for _ in range(self.numCards):
                temp.append(self.pilePlacedTo.array.pop())
            if self.new_card_opened:
                self.pileTakenFrom.array[-1].faceUp = False
            for _ in range(self.numCards):
                self.pileTakenFrom.array.append(temp.pop())

        for pile in (self.pileTakenFrom, self.pilePlacedTo):
            pile.set_click_rect()


class StockPileClick(CardAction):
    def __init__(self, taken_from, placed_to, num_cards, face_up=None):
        super().__init__(taken_from, placed_to, num_cards)
        self.faceUp = face_up

    def do(self, undo_redo):
        for _ in range(self.numCards):
            if undo_redo == 'redo':
                self.pilePlacedTo.array.append(self.pileTakenFrom.array.pop())
                if self.faceUp is not None:
                    self.pilePlacedTo.array[-1].faceUp = self.faceUp
            else:
                self.pileTakenFrom.array.append(self.pilePlacedTo.array.pop())
                if self.faceUp is not None:
                    self.pileTakenFrom.array[-1].faceUp = self.faceUp ^ True  # reverses it
