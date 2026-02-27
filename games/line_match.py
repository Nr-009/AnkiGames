import random
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTimer,
    QPushButton, QWidget, Qt, QPainter, QPen, QColor, QPoint
)
from aqt.utils import qconnect
from aqt import mw
from .utils import load_config, load_pairs, make_win_widget
from .base_state import BaseState

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

    def get_center(self, canvas) -> QPoint:
        global_point = self.mapToGlobal(self.rect().center())
        return canvas.mapFromGlobal(global_point)

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

    def flash_red(self, p1, p2):
        self.red_line = (p1, p2)
        self.update()
        QTimer.singleShot(800, self._clear_red)

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

        painter.setPen(QPen(QColor("#4aff4a"), 3))
        for p1, p2 in self.green_lines:
            painter.drawLine(p1, p2)

        if self.red_line:
            painter.setPen(QPen(QColor("#ff4a4a"), 3))
            painter.drawLine(self.red_line[0], self.red_line[1])

        painter.end()

class LineState(BaseState):
    def __init__(self, cards, cards_per_batch, on_batch_done, on_game_done, on_move, on_correct, on_wrong):
        super().__init__(
            cards           = cards,
            cards_per_batch = cards_per_batch,
            on_batch_done   = on_batch_done,
            on_game_done    = on_game_done,
            on_move         = on_move,
        )
        self.on_correct = on_correct
        self.on_wrong   = on_wrong

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

        super().put_card(label)

    def _on_select_first(self, card):
        card.set_selected()

    def _on_select_second(self, card):
        card.set_selected()

    def _check_match(self):
        if self._pair_ids_match():
            self.card1.set_matched()
            self.card2.set_matched()
            self.on_correct(self.card1, self.card2)
            self._after_correct()
        else:
            self.on_wrong(self.card1, self.card2)
            cfg   = load_config(("line_wrong_ms", 800))
            delay = cfg["line_wrong_ms"]
            self._after_wrong(self.card1, self.card2, delay, self._reset_after_wrong)

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

        cfg             = load_config(("numberOfPairs", 4))
        number_of_pairs = cfg["numberOfPairs"]
        pairs           = load_pairs(deck_name, count=999)
        all_labels      = self._pairs_to_labels(pairs)

        self._load_ui()

        self.state = LineState(
            cards           = all_labels,
            cards_per_batch = number_of_pairs * 2,
            on_batch_done   = self._build_columns,
            on_game_done    = self._finish,
            on_move         = self._count_move,
            on_correct      = self._on_correct,
            on_wrong        = self._on_wrong,
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
        self.moves   = 0
        self.clock   = QTimer()
        self.clock.setInterval(1000)
        qconnect(self.clock.timeout, self._tick)
        self.clock.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'canvas'):
            self.canvas.setGeometry(self.rect())

    def _build_columns(self, batch):
        for col in [self.left_col, self.right_col]:
            while col.count():
                item = col.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        self.canvas.clear_all()

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
        self.canvas.flash_red(p1, p2)

    def _count_move(self):
        self.moves += 1
        self.moves_label.setText(f"Moves: {self.moves}")

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

        win = make_win_widget(self.moves, self.seconds, self.accept)
        self.game_area_layout.addWidget(win)