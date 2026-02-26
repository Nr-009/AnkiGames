from aqt.qt import (QDialog, QVBoxLayout, QHBoxLayout,
                    QLabel, QRadioButton, QSpinBox, QPushButton)
from aqt.utils import qconnect
from aqt import mw

class GameSelector(QDialog):
    def __init__(self, deckName: str):
        super().__init__(mw)
        self.deckName                   = deckName
        self.chosen_mode                = None
        self.numberOfCardsPerMemoryGrid = 16    # default 8 pairs
        self.loadUI()

    def loadUI(self):
        self.setWindowTitle("AnkiGames")

        mainLayout = QVBoxLayout()

        # deck name
        mainLayout.addWidget(QLabel(f"<b>{self.deckName}</b>"))

        # mode selection
        mainLayout.addWidget(QLabel("Select game:"))
        self.radioMemory = QRadioButton("Memory Flip")
        self.radioLine   = QRadioButton("Line Match")
        self.radioMemory.setChecked(True)
        mainLayout.addWidget(self.radioMemory)
        mainLayout.addWidget(self.radioLine)

        # pair count
        mainLayout.addWidget(QLabel("Cards per grid:"))
        self.spin = QSpinBox()
        self.spin.setMinimum(4)
        self.spin.setMaximum(32)
        self.spin.setSingleStep(2)   # always even so pairs stay together
        self.spin.setValue(16)
        mainLayout.addWidget(self.spin)

        # buttons
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
        self.numberOfCardsPerMemoryGrid = self.spin.value()
        self.accept()
