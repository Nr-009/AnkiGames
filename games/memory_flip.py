# games/memory_flip.py

import random
from dataclasses import dataclass
from aqt.qt import (QDialog, QGridLayout, QVBoxLayout,
                    QHBoxLayout, QLabel, QTimer, QSizePolicy, Qt, QPushButton, QWidget)
from aqt.utils import qconnect
from aqt import mw
from .card_loader import load_pairs


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
        self.setMinimumSize(200, 150)
        self.setMaximumSize(400, 300)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.set_facedown()

    def mousePressEvent(self, event):
        if not self.tile.is_Matched:
            self.putCard(self)

    def set_facedown(self):
        self.tile.is_flipped = False
        self.setText("?")
        self.setStyleSheet("""
            background: #607D8B;
            color: white;
            font-size: 24px;
            font-weight: bold;
            border-radius: 8px;
        """)

    def set_flipped(self):
        self.tile.is_flipped = True
        self.setText(self.tile.text)
        self.setStyleSheet("""
            background: #2196F3;
            color: white;
            font-size: 18px;
            border-radius: 8px;
        """)

    def set_matched(self):
        self.tile.is_Matched = True
        self.tile.is_flipped = True
        self.setText(self.tile.text)
        self.setStyleSheet("""
            background: #4CAF50;
            color: white;
            font-size: 18px;
            border-radius: 8px;
        """)

    def set_wrong(self):
        self.setStyleSheet("""
            background: #F44336;
            color: white;
            font-size: 18px;
            border-radius: 8px;
        """)

class State:
    def __init__(self, cards, numberOfCardsPerMemoryGrid, onBatchDone, onGameDone, onMove):
        self.cards                      = cards
        self.numberOfCardsPerMemoryGrid = numberOfCardsPerMemoryGrid
        self.numberOfCardsUp            = numberOfCardsPerMemoryGrid // 2
        self.onBatchDone                = onBatchDone
        self.onGameDone                 = onGameDone
        self.onMove                     = onMove
        self.card1                      = None
        self.card2                      = None
        self.inputLocked                = False
        self.batchIndex                 = 0

    def loadCards(self):
        if self.batchIndex >= len(self.cards):
            self.onGameDone()
            return

        batch                = self.cards[self.batchIndex:self.batchIndex + self.numberOfCardsPerMemoryGrid]
        self.batchIndex     += self.numberOfCardsPerMemoryGrid
        self.numberOfCardsUp = len(batch) // 2
        self.card1           = None
        self.card2           = None
        self.inputLocked     = False
        self.onBatchDone(batch)

    def putCard(self, tileBtn):
        if self.inputLocked:
            return
        if tileBtn.tile.is_flipped:
            return

        if self.card1 is None:
            self.card1 = tileBtn
            tileBtn.set_flipped()
            return

        if self.card2 is None:
            self.card2       = tileBtn
            self.inputLocked = True
            tileBtn.set_flipped()
            self.onMove()
            self.checkMatch()

    def checkMatch(self):
        if self.card1.tile.pair_id == self.card2.tile.pair_id:
            self.card1.set_matched()
            self.card2.set_matched()
            self.card1            = None
            self.card2            = None
            self.numberOfCardsUp -= 1
            self.inputLocked      = False

            if self.numberOfCardsUp == 0:
                QTimer.singleShot(500, self.loadCards)
        else:
            self.card1.set_wrong()
            self.card2.set_wrong()
            c1, c2       = self.card1, self.card2
            self.card1   = None
            self.card2   = None
            QTimer.singleShot(800, lambda: self.flipBack(c1, c2))

    def flipBack(self, c1, c2):
        c1.set_facedown()
        c2.set_facedown()
        self.inputLocked = False

class MemoryFlipGame(QDialog):
    def __init__(self, deckName: str, numberOfCardsPerMemoryGrid: int):
        super().__init__(mw)
        self.deckName                   = deckName
        self.numberOfCardsPerMemoryGrid = numberOfCardsPerMemoryGrid
        self.setWindowTitle("Memory Flip")
        self.showMaximized()

        pairs       = load_pairs(deckName, count=999)
        tileButtons = self.pairsToTileButtons(pairs)

        self.loadUI()

        self.state = State(
            cards                      = tileButtons,
            numberOfCardsPerMemoryGrid = numberOfCardsPerMemoryGrid,
            onBatchDone                = self.buildGrid,
            onGameDone                 = self.finish,
            onMove                     = self.countMove
        )

        self.state.loadCards()

    def pairsToTileButtons(self, pairs):
        tiles = []
        for i, (front, back) in enumerate(pairs):
            tiles.append(TileButton(Tile(text=front, pair_id=i, is_front=True),  putCard=None))
            tiles.append(TileButton(Tile(text=back,  pair_id=i, is_front=False), putCard=None))
        return tiles

    def loadUI(self):
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.setSpacing(10)

        top = QHBoxLayout()

        backBtn = QPushButton("← Back")
        backBtn.setStyleSheet("font-size: 14px; color: white; background: #455A64; border-radius: 6px; padding: 4px 10px;")
        qconnect(backBtn.clicked, self.goBack)
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
        qconnect(self.clock.timeout, self.tick)
        self.clock.start()

    def goBack(self):
        self.clock.stop()
        self.reject()

    def buildGrid(self, batch):
        while self.gridLayout.count():
            item = self.gridLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        random.shuffle(batch)

        for btn in batch:
            btn.putCard = self.state.putCard
            btn.set_facedown()

        cols = 4
        for idx, btn in enumerate(batch):
            row = idx // cols
            col = idx % cols
            self.gridLayout.addWidget(btn, row, col)

    def countMove(self):
        self.moves += 1
        self.movesLabel.setText(f"Moves: {self.moves}")

    def tick(self):
        self.seconds += 1
        self.timeLabel.setText(f"Time: {self.seconds}s")

    def finish(self):
        self.clock.stop()

        while self.gridLayout.count():
            item = self.gridLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        winWidget = QWidget()
        winLayout = QVBoxLayout()
        winLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("You Won!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 48px; font-weight: bold; color: white;")

        stats = QLabel(f"Moves: {self.moves}   Time: {self.seconds}s")
        stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats.setStyleSheet("font-size: 24px; color: #ccc;")

        closeBtn = QPushButton("Close")
        closeBtn.setStyleSheet("font-size: 18px; padding: 10px 40px; background: #4CAF50; color: white; border-radius: 8px;")
        closeBtn.setFixedWidth(200)
        qconnect(closeBtn.clicked, self.accept)

        winLayout.addWidget(title)
        winLayout.addWidget(stats)
        winLayout.addSpacing(20)
        winLayout.addWidget(closeBtn, alignment=Qt.AlignmentFlag.AlignCenter)

        winWidget.setLayout(winLayout)
        self.gridLayout.addWidget(winWidget, 0, 0)