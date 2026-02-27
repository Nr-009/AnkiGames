import re
import os
import html
import json
import random
from aqt.qt import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, Qt)
from aqt.utils import qconnect
from aqt import mw


def load_config(*keys_and_defaults):
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    return {key: config.get(key, default) for key, default in keys_and_defaults}


def make_win_widget(moves: int, seconds: int, accuracy: int, on_close, on_play_again) -> QWidget:
    win        = QWidget()
    win_layout = QVBoxLayout()
    win_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    title = QLabel("You Won!")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setStyleSheet("font-size: 48px; font-weight: bold; color: white;")

    stats = QLabel(f"Moves: {moves}   Accuracy: {accuracy}%   Time: {seconds}s")
    stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
    stats.setStyleSheet("font-size: 24px; color: #ccc;")

    again_btn = QPushButton("Play Again")
    again_btn.setStyleSheet("font-size: 18px; padding: 10px 40px; background: #4CAF50; color: white; border-radius: 8px;")
    again_btn.setFixedWidth(200)
    qconnect(again_btn.clicked, on_play_again)

    close_btn = QPushButton("Close")
    close_btn.setStyleSheet("font-size: 18px; padding: 10px 40px; background: #455A64; color: white; border-radius: 8px;")
    close_btn.setFixedWidth(200)
    qconnect(close_btn.clicked, on_close)

    btn_row = QHBoxLayout()
    btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
    btn_row.setSpacing(20)
    btn_row.addWidget(again_btn)
    btn_row.addWidget(close_btn)

    win_layout.addWidget(title)
    win_layout.addWidget(stats)
    win_layout.addSpacing(20)
    win_layout.addLayout(btn_row)
    win.setLayout(win_layout)
    return win


def prepare_field(field: str) -> str:
    media_dir = mw.col.media.dir()
    srcs   = re.findall(r'<img[^>]*\ssrc="([^"]+)"', field)
    local  = [s for s in srcs if not s.startswith('http')]
    remote = [s for s in srcs if s.startswith('http')]
    chosen = local[0] if local else (remote[0] if remote else None)

    if chosen:
        field  = re.sub(r'<[^>]+>', '', field).strip()
        field += f'<img src="{os.path.join(media_dir, chosen)}" width="180" height="130">' if not chosen.startswith('http') else ''
    else:
        field = re.sub(r'<[^>]+>', '', field).strip()

    field = re.sub(r'\[sound:[^\]]+\]', '', field).strip()
    field = html.unescape(field)
    return field


def load_pairs(deck_name: str) -> list:
    config           = load_config(("useReviewQueue", False), ("maxCards", None))
    use_review_queue = config["useReviewQueue"]
    max_cards        = config["maxCards"]

    query    = f'deck:"{deck_name}" is:due' if use_review_queue else f'deck:"{deck_name}"'
    card_ids = mw.col.find_cards(query)
    random.shuffle(card_ids)

    if max_cards is not None:
        card_ids = card_ids[:max_cards]

    pairs = []
    for card_id in card_ids:
        card  = mw.col.get_card(card_id)
        note  = card.note()
        front = prepare_field(note.fields[0])
        back  = prepare_field(note.fields[1])
        if front and back:
            pairs.append((front, back))
    return pairs


def check_deck_has_cards(deck_name: str) -> bool:
    config           = load_config(("useReviewQueue", False))
    use_review_queue = config["useReviewQueue"]
    query    = f'deck:"{deck_name}" is:due' if use_review_queue else f'deck:"{deck_name}"'
    card_ids = mw.col.find_cards(query)
    return len(card_ids) > 0