from aqt.qt import (QDialog, QVBoxLayout, QHBoxLayout,
                    QLabel, QRadioButton, QSpinBox, QPushButton)
from aqt.utils import qconnect
from aqt import mw

class GameSelector(QDialog):
    def __init__(self, deckName: str):
        super().__init__(mw)
        self.deckName                   = deckName
        self.chosen_mode                = None
        self.numberOfCardsPerMemoryGrid = 16   
        self.loadUI()

    def loadUI(self):
        self.setWindowTitle("AnkiGames")

        mainLayout = QVBoxLayout()

        mainLayout.addWidget(QLabel(f"<b>{self.deckName}</b>"))


        mainLayout.addWidget(QLabel("Select game:"))
        self.radioMemory = QRadioButton("Memory Flip")
        self.radioLine   = QRadioButton("Line Match")
        self.radioMemory.setChecked(True)
        mainLayout.addWidget(self.radioMemory)
        mainLayout.addWidget(self.radioLine)

        btnLayout  = QHBoxLayout()
        cancelBtn  = QPushButton("Cancel")
        playBtn    = QPushButton("Play!")
        qconnect(cancelBtn.clicked, self.reject)
        qconnect(playBtn.clicked,   self.onPlay)
        btnLayout.addWidget(cancelBtn)
        btnLayout.addWidget(playBtn)
        mainLayout.addLayout(btnLayout)

        self.setLayout(mainLayout)

    def onPlay(self):
        self.chosen_mode                = "memory_flip" if self.radioMemory.isChecked() else "line_match"
        self.accept()
