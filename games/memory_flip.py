import random
from dataclasses import dataclass
from aqt.qt import (QDialog, QGridLayout, QVBoxLayout,
                    QHBoxLayout, QLabel, QTimer, QSizePolicy, Qt, QPushButton, QWidget)
from aqt.utils import qconnect
from aqt import mw
from .utils import load_config, load_pairs, make_win_widget
from .base_state import BaseState

@dataclass
class Tile:
    text: str
    pair_id: int
    is_front: bool
    is_flipped: bool = False
    is_Matched: bool = False

class TileButton(QLabel):
    def __init__(self, tile: Tile, putCard):
        super().__init__()
        self.tile    = tile
        self.putCard = putCard
        self.pair_id = tile.pair_id
        self.setMinimumSize(200, 150)
        self.setMaximumSize(400, 300)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.set_facedown()

    def mousePressEvent(self, event):
        if not self.tile.is_Matched:
            self.putCard(self)

    def set_facedown(self):
        self.tile.is_flipped = False
        self.setText("?")
        self.setStyleSheet("background: #607D8B; color: white; font-size: 24px; font-weight: bold; border-radius: 8px;")

    def set_flipped(self):
        self.tile.is_flipped = True
        self.setText(self.tile.text)
        self.setStyleSheet("background: #2196F3; color: white; font-size: 18px; border-radius: 8px;")

    def set_matched(self):
        self.tile.is_Matched = True
        self.tile.is_flipped = True
        self.setText(self.tile.text)
        self.setStyleSheet("background: #4CAF50; color: white; font-size: 18px; border-radius: 8px;")

    def set_wrong(self):
        self.setStyleSheet("background: #F44336; color: white; font-size: 18px; border-radius: 8px;")

class State(BaseState):
    def __init__(self, cards, numberOfCardsPerMemoryGrid, onBatchDone, onGameDone, onMove):
        super().__init__(
            cards           = cards,
            cards_per_batch = numberOfCardsPerMemoryGrid,
            on_batch_done   = onBatchDone,
            on_game_done    = onGameDone,
            on_move         = onMove,
        )

    def put_card(self, tileBtn):
        if self.input_locked:
            return
        if tileBtn.tile.is_flipped:
            return
        super().put_card(tileBtn)

    def _on_select_first(self, card):
        card.set_flipped()

    def _on_select_second(self, card):
        card.set_flipped()

    def _check_match(self):
        if self._pair_ids_match():
            self.card1.set_matched()
            self.card2.set_matched()
            self._after_correct()
        else:
            self.card1.set_wrong()
            self.card2.set_wrong()
            cfg   = load_config(("flip_delay_ms", 800))
            delay = cfg["flip_delay_ms"]
            self._after_wrong(self.card1, self.card2, delay, self._flip_back)

    def _flip_back(self, c1, c2):
        c1.set_facedown()
        c2.set_facedown()
        self.input_locked = False

class MemoryFlipGame(QDialog):
    def __init__(self, deckName: str):
        super().__init__(mw)
        self.deckName = deckName
        cfg           = load_config(("rows", 4), ("cols", 4))
        self.rows     = cfg["rows"]
        self.cols     = cfg["cols"]
        self.numberOfCardsPerMemoryGrid = self.rows * self.cols
        self.setWindowTitle("Memory Flip")
        self.showMaximized()

        pairs       = load_pairs(deckName, count=999)
        tileButtons = self._pairs_to_tile_buttons(pairs)

        self._load_ui()

        self.state = State(
            cards                      = tileButtons,
            numberOfCardsPerMemoryGrid = self.numberOfCardsPerMemoryGrid,
            onBatchDone                = self._build_grid,
            onGameDone                 = self._finish,
            onMove                     = self._count_move,
        )

        self.state.load_batch()

    def _pairs_to_tile_buttons(self, pairs):
        tiles = []
        for i, (front, back) in enumerate(pairs):
            tiles.append(TileButton(Tile(text=front, pair_id=i, is_front=True),  putCard=None))
            tiles.append(TileButton(Tile(text=back,  pair_id=i, is_front=False), putCard=None))
        return tiles

    def _load_ui(self):
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.setSpacing(10)

        top = QHBoxLayout()

        backBtn = QPushButton("← Back")
        backBtn.setStyleSheet("font-size: 14px; color: white; background: #455A64; border-radius: 6px; padding: 4px 10px;")
        qconnect(backBtn.clicked, self._go_back)
        top.addWidget(backBtn)

        self.deckLabel  = QLabel(f"<b>{self.deckName}</b>")
        self.movesLabel = QLabel("Moves: 0")
        self.timeLabel  = QLabel("Time: 0s")

        for label in [self.deckLabel, self.movesLabel, self.timeLabel]:
            label.setStyleSheet("font-size: 16px; color: white;")

        top.addWidget(self.deckLabel)
        top.addStretch()
        top.addWidget(self.movesLabel)
        top.addWidget(self.timeLabel)
        self.mainLayout.addLayout(top)

        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(10)
        self.mainLayout.addLayout(self.gridLayout, 1)
        self.setLayout(self.mainLayout)

        self.seconds = 0
        self.moves   = 0
        self.clock   = QTimer()
        self.clock.setInterval(1000)
        qconnect(self.clock.timeout, self._tick)
        self.clock.start()

    def _go_back(self):
        self.clock.stop()
        self.reject()

    def _build_grid(self, batch):
        while self.gridLayout.count():
            item = self.gridLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        random.shuffle(batch)

        for btn in batch:
            btn.putCard = self.state.put_card
            btn.set_facedown()

        i = 0
        for x in range(self.rows):
            for y in range(self.cols):
                if i < len(batch):
                    self.gridLayout.addWidget(batch[i], x, y)
                    i += 1

    def _count_move(self):
        self.moves += 1
        self.movesLabel.setText(f"Moves: {self.moves}")

    def _tick(self):
        self.seconds += 1
        self.timeLabel.setText(f"Time: {self.seconds}s")

    def _finish(self):
        self.clock.stop()

        while self.gridLayout.count():
            item = self.gridLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        win = make_win_widget(self.moves, self.seconds, self.accept)
        self.gridLayout.addWidget(win, 0, 0)