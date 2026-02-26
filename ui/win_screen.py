# ui/win_screen.py

from aqt.qt import (QDialog, QVBoxLayout, QHBoxLayout,
                    QLabel, QPushButton)
from aqt.utils import qconnect
from aqt import mw

class WinScreen(QDialog):
    def __init__(self, deckName: str, moves: int, seconds: int):
        super().__init__(mw)
        self.deckName = deckName
        self.moves    = moves
        self.seconds  = seconds
        self.loadUI()

    def loadUI(self):
        self.setWindowTitle("AnkiGames 🎮")

        mainLayout = QVBoxLayout()

        # deck name
        mainLayout.addWidget(QLabel(f"<b>{self.deckName}</b>"))

        # win message
        mainLayout.addWidget(QLabel("<h2> You won!</h2>"))

        # stats
        mainLayout.addWidget(QLabel(f"Moves: {self.moves}"))
        mainLayout.addWidget(QLabel(f"Time: {self.seconds}s"))

        # close button
        btnLayout = QHBoxLayout()
        closeBtn  = QPushButton("Close")
        qconnect(closeBtn.clicked, self.accept)
        btnLayout.addWidget(closeBtn)
        mainLayout.addLayout(btnLayout)

        self.setLayout(mainLayout)