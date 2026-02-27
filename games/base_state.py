from aqt.qt import QTimer

class BaseState:

    def __init__(self, cards, cards_per_batch, on_batch_done, on_game_done, on_move):
        self.cards           = cards
        self.cards_per_batch = cards_per_batch
        self.on_batch_done   = on_batch_done
        self.on_game_done    = on_game_done
        self.on_move         = on_move

        self.card1        = None
        self.card2        = None
        self.input_locked = False
        self.batch_index  = 0
        self.pairs_up     = 0

    def load_batch(self):
        if self.batch_index >= len(self.cards):
            self.on_game_done()
            return

        batch             = self.cards[self.batch_index: self.batch_index + self.cards_per_batch]
        self.batch_index += len(batch)
        self.pairs_up     = len(batch) // 2
        self.card1        = None
        self.card2        = None
        self.input_locked = False
        self.on_batch_done(batch)

    def put_card(self, card):
        if self.input_locked:
            return

        if self.card1 is None:
            self.card1 = card
            self._on_select_first(card)
            return

        self.card2        = card
        self.input_locked = True
        self._on_select_second(card)
        self.on_move()
        self._check_match()

    def _on_select_first(self, card):
        pass

    def _on_select_second(self, card):
        pass

    def _check_match(self):
        raise NotImplementedError

    def _pair_ids_match(self):
        return self.card1.pair_id == self.card2.pair_id

    def _after_correct(self):
        self.card1        = None
        self.card2        = None
        self.pairs_up    -= 1
        self.input_locked = False

        if self.pairs_up == 0:
            QTimer.singleShot(500, self.load_batch)

    def _after_wrong(self, c1, c2, delay_ms, callback):
        self.card1 = None
        self.card2 = None
        QTimer.singleShot(delay_ms, lambda: callback(c1, c2))