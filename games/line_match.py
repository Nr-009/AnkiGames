import json
import os
import random
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTimer,
    QPushButton, QWidget, Qt, QPainter, QPen, QColor, QPoint
)
from aqt.utils import qconnect
from aqt import mw
from .utils import load_pairs


def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    return {
        "numberOfPairs": config.get("numberOfPairs", 4),
        "line_wrong_ms": config.get("line_wrong_ms", 800),
    }


class LineLabel(QLabel):
    def __init__(self, text: str, pair_id: int, on_click):
        super().__init__()
        self.pair_id    = pair_id
        self.is_matched = False
        self.on_click   = on_click
        self.side       = None

        self.setText(text)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(150, 60)
        self.setMaximumSize(300, 120)
        self._apply_style("default")

    def mousePressEvent(self, event):
        if not self.is_matched and self.on_click:
            self.on_click(self)

    def get_center(self, relative_to) -> QPoint:
        global_point = self.mapToGlobal(self.rect().center())
        return relative_to.mapFromGlobal(global_point)

    def set_selected(self):
        self._apply_style("selected")

    def set_matched(self):
        self.is_matched = True
        self._apply_style("matched")

    def deselect(self):
        self._apply_style("default")

    def _apply_style(self, state: str):
        styles = {
            "default":  "background-color: #2b2b2b; color: white; border: 2px solid #555; border-radius: 6px; padding: 8px;",
            "selected": "background-color: #1a4a7a; color: white; border: 2px solid #4a9eff; border-radius: 6px; padding: 8px;",
            "matched":  "background-color: #1a4a1a; color: white; border: 2px solid #4aff4a; border-radius: 6px; padding: 8px;",
        }
        self.setStyleSheet(styles[state])


class LineCanvas(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setStyleSheet("background: transparent;")
        self.green_lines = []
        self.red_line    = None

    def add_green(self, p1, p2):
        self.green_lines.append((p1, p2))
        self.update()

    def flash_red(self, p1, p2, wrong_ms=800):
        self.red_line = (p1, p2)
        self.update()
        QTimer.singleShot(wrong_ms, self._clear_red)

    def _clear_red(self):
        self.red_line = None
        self.update()

    def clear_all(self):
        self.green_lines = []
        self.red_line    = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor("#4aff4a"), 3)
        painter.setPen(pen)
        for p1, p2 in self.green_lines:
            painter.drawLine(p1, p2)

        if self.red_line:
            pen = QPen(QColor("#ff4a4a"), 3)
            painter.setPen(pen)
            painter.drawLine(self.red_line[0], self.red_line[1])

        painter.end()


class LineState:
    def __init__(self, cards, cards_per_batch, on_batch_done, on_game_done, on_move, on_correct, on_wrong, wrong_ms=800):
        self.cards           = cards
        self.cards_per_batch = cards_per_batch
        self.on_batch_done   = on_batch_done
        self.on_game_done    = on_game_done
        self.on_move         = on_move
        self.on_correct      = on_correct
        self.on_wrong        = on_wrong
        self.card1           = None
        self.card2           = None
        self.input_locked    = False
        self.batch_index     = 0
        self.pairs_up        = 0
        self.wrong_ms        = wrong_ms
        self.moves           = 0
        self.correct_moves   = 0

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

    def put_card(self, label):
        if self.input_locked:
            return

        if self.card1 is None:
            self.card1 = label
            label.set_selected()
            return

        if label.side == self.card1.side:
            self.card1.deselect()
            self.card1 = label
            label.set_selected()
            return

        self.card2        = label
        self.input_locked = True
        label.set_selected()
        self.moves += 1
        self.on_move()
        self._check_match()

    def _check_match(self):
        if self.card1.pair_id == self.card2.pair_id:
            self.card1.set_matched()
            self.card2.set_matched()
            self.on_correct(self.card1, self.card2)
            self.correct_moves += 1
            self.card1        = None
            self.card2        = None
            self.pairs_up    -= 1
            self.input_locked = False

            if self.pairs_up == 0:
                QTimer.singleShot(500, self.load_batch)
        else:
            c1, c2     = self.card1, self.card2
            self.card1 = None
            self.card2 = None
            self.on_wrong(c1, c2)
            QTimer.singleShot(self.wrong_ms, lambda: self._reset_after_wrong(c1, c2))

    def _reset_after_wrong(self, c1, c2):
        c1.deselect()
        c2.deselect()
        self.input_locked = False


class LineMatchGame(QDialog):
    def __init__(self, deck_name: str):
        super().__init__(mw)
        self.deck_name = deck_name
        self.setWindowTitle("Line Match")
        self.showMaximized()

        cfg             = load_config()
        number_of_pairs = cfg["numberOfPairs"]
        wrong_ms        = cfg["line_wrong_ms"]

        pairs      = load_pairs(deck_name)
        all_labels = self._pairs_to_labels(pairs)

        self._load_ui()

        self.wrong_ms = wrong_ms
        self.state = LineState(
            cards           = all_labels,
            cards_per_batch = number_of_pairs * 2,
            on_batch_done   = self._build_columns,
            on_game_done    = self._finish,
            on_move         = self._count_move,
            on_correct      = self._on_correct,
            on_wrong        = self._on_wrong,
            wrong_ms        = wrong_ms,
        )

        self.state.load_batch()

    def _pairs_to_labels(self, pairs):
        labels = []
        for i, (front, back) in enumerate(pairs):
            left       = LineLabel(text=front, pair_id=i, on_click=None)
            right      = LineLabel(text=back,  pair_id=i, on_click=None)
            left.side  = "left"
            right.side = "right"
            labels.append(left)
            labels.append(right)
        return labels

    def _load_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(10)

        top = QHBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet("font-size: 14px; color: white; background: #455A64; border-radius: 6px; padding: 4px 10px;")
        qconnect(back_btn.clicked, self._go_back)
        top.addWidget(back_btn)

        self.deck_label  = QLabel(f"<b>{self.deck_name}</b>")
        self.moves_label = QLabel("Moves: 0")
        self.time_label  = QLabel("Time: 0s")

        for lbl in [self.deck_label, self.moves_label, self.time_label]:
            lbl.setStyleSheet("font-size: 16px; color: white;")

        top.addWidget(self.deck_label)
        top.addStretch()
        top.addWidget(self.moves_label)
        top.addWidget(self.time_label)
        self.main_layout.addLayout(top)

        self.game_area = QWidget()
        self.game_area.setStyleSheet("background: transparent;")
        self.game_area_layout = QHBoxLayout(self.game_area)
        self.game_area_layout.setContentsMargins(40, 10, 40, 10)
        self.game_area_layout.setSpacing(80)

        self.left_col  = QVBoxLayout()
        self.right_col = QVBoxLayout()
        self.left_col.setSpacing(12)
        self.right_col.setSpacing(12)

        self.game_area_layout.addLayout(self.left_col)
        self.game_area_layout.addLayout(self.right_col)

        self.main_layout.addWidget(self.game_area, 1)
        self.setLayout(self.main_layout)

        self.canvas = LineCanvas(self)
        self.canvas.raise_()
        self.canvas.show()

        self.seconds = 0
        self.clock   = QTimer()
        self.clock.setInterval(1000)
        qconnect(self.clock.timeout, self._tick)
        self.clock.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "canvas"):
            self.canvas.setGeometry(self.rect())

    def _build_columns(self, batch):
        for col in [self.left_col, self.right_col]:
            while col.count():
                item = col.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        self.canvas.clear_all()
        self.canvas.raise_()

        lefts  = batch[0::2]
        rights = batch[1::2]

        random.shuffle(lefts)
        random.shuffle(rights)

        for lbl in lefts:
            lbl.on_click = self.state.put_card
            self.left_col.addWidget(lbl)

        for lbl in rights:
            lbl.on_click = self.state.put_card
            self.right_col.addWidget(lbl)

        self.left_col.addStretch()
        self.right_col.addStretch()

    def _on_correct(self, c1, c2):
        p1 = c1.get_center(self.canvas)
        p2 = c2.get_center(self.canvas)
        self.canvas.add_green(p1, p2)

    def _on_wrong(self, c1, c2):
        p1 = c1.get_center(self.canvas)
        p2 = c2.get_center(self.canvas)
        self.canvas.flash_red(p1, p2, self.wrong_ms)

    def _count_move(self):
        self.moves_label.setText(f"Moves: {self.state.moves}")

    def _tick(self):
        self.seconds += 1
        self.time_label.setText(f"Time: {self.seconds}s")

    def _go_back(self):
        self.clock.stop()
        self.reject()

    def _finish(self):
        self.clock.stop()

        for col in [self.left_col, self.right_col]:
            while col.count():
                item = col.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        self.canvas.clear_all()

        win        = QWidget()
        win_layout = QVBoxLayout()
        win_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("You Won!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 48px; font-weight: bold; color: white;")

        accuracy = int((self.state.correct_moves / self.state.moves) * 100) if self.state.moves > 0 else 100

        stats = QLabel(f"Moves: {self.state.moves}   Accuracy: {accuracy}%   Time: {self.seconds}s")
        stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats.setStyleSheet("font-size: 24px; color: #ccc;")

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("font-size: 18px; padding: 10px 40px; background: #4CAF50; color: white; border-radius: 8px;")
        close_btn.setFixedWidth(200)
        qconnect(close_btn.clicked, self.accept)

        win_layout.addWidget(title)
        win_layout.addWidget(stats)
        win_layout.addSpacing(20)
        win_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        win.setLayout(win_layout)

        self.game_area_layout.addWidget(win)