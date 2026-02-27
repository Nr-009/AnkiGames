import json
import os
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QSpinBox, QPushButton, Qt
)
from aqt.utils import qconnect, showInfo
from aqt import mw


CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


def read_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def write_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__(mw)
        self.setWindowTitle("AnkiGames Settings")
        self.setMinimumWidth(320)
        self._load_ui()

    def _load_ui(self):
        cfg = read_config()

        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(10)

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(2, 10)
        self.rows_spin.setValue(cfg.get("rows", 4))

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(2, 10)
        self.cols_spin.setValue(cfg.get("cols", 4))

        self.pairs_spin = QSpinBox()
        self.pairs_spin.setRange(2, 20)
        self.pairs_spin.setValue(cfg.get("numberOfPairs", 4))

        self.flip_delay_spin = QSpinBox()
        self.flip_delay_spin.setRange(200, 3000)
        self.flip_delay_spin.setSingleStep(100)
        self.flip_delay_spin.setSuffix(" ms")
        self.flip_delay_spin.setValue(cfg.get("flip_delay_ms", 800))

        self.line_wrong_spin = QSpinBox()
        self.line_wrong_spin.setRange(200, 3000)
        self.line_wrong_spin.setSingleStep(100)
        self.line_wrong_spin.setSuffix(" ms")
        self.line_wrong_spin.setValue(cfg.get("line_wrong_ms", 800))

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff4a4a; font-size: 13px;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form.addRow("Memory Flip rows:", self.rows_spin)
        form.addRow("Memory Flip cols:", self.cols_spin)
        form.addRow("Line Match pairs:", self.pairs_spin)
        form.addRow("Flip delay (wrong):", self.flip_delay_spin)
        form.addRow("Red line duration:", self.line_wrong_spin)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        save_btn   = QPushButton("Save")
        save_btn.setStyleSheet("background: #4CAF50; color: white; padding: 4px 16px; border-radius: 4px;")
        qconnect(cancel_btn.clicked, self.reject)
        qconnect(save_btn.clicked, self._save)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        main_layout.addLayout(form)
        main_layout.addWidget(self.error_label)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def _save(self):
        rows = self.rows_spin.value()
        cols = self.cols_spin.value()

        if (rows * cols) % 2 != 0:
            self.error_label.setText(f"rows × cols must be even ({rows} × {cols} = {rows * cols})")
            return

        self.error_label.setText("")

        write_config({
            "rows":          rows,
            "cols":          cols,
            "numberOfPairs": self.pairs_spin.value(),
            "flip_delay_ms": self.flip_delay_spin.value(),
            "line_wrong_ms": self.line_wrong_spin.value(),
        })

        self.accept()


def open_settings():
    dialog = SettingsDialog()
    dialog.exec()