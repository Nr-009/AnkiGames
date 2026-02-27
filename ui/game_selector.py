from aqt.qt import (QDialog, QVBoxLayout, QHBoxLayout,
                    QLabel, QRadioButton, QPushButton)
from aqt.utils import qconnect, showWarning
from aqt import mw
from ..games.utils import check_deck_has_cards


class GameSelector(QDialog):
    def __init__(self, deck_name: str):
        super().__init__(mw)
        self.deck_name   = deck_name
        self.chosen_mode = None
        self._load_ui()

    def _load_ui(self):
        self.setWindowTitle("AnkiGames")

        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel(f"<b>{self.deck_name}</b>"))
        main_layout.addWidget(QLabel("Select game:"))

        self.radio_memory = QRadioButton("Memory Flip")
        self.radio_line   = QRadioButton("Line Match")
        self.radio_memory.setChecked(True)

        main_layout.addWidget(self.radio_memory)
        main_layout.addWidget(self.radio_line)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        play_btn   = QPushButton("Play!")

        qconnect(cancel_btn.clicked, self.reject)
        qconnect(play_btn.clicked,   self._on_play)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(play_btn)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def _on_play(self):
        if not check_deck_has_cards(self.deck_name):
            showWarning(f'No cards found in deck "{self.deck_name}".\nIf you have useReviewQueue enabled, there may be no cards due today.')
            return

        self.chosen_mode = "memory_flip" if self.radio_memory.isChecked() else "line_match"
        self.accept()