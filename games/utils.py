import re
import os
import html
import json
import random
from aqt.qt import (QVBoxLayout, QLabel, QPushButton, QWidget, Qt)
from aqt.utils import qconnect
from aqt import mw

def load_config(*keys_and_defaults):
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    return {key: config.get(key, default) for key, default in keys_and_defaults}

def make_win_widget(moves: int, seconds: int, on_close) -> QWidget:
    win        = QWidget()
    win_layout = QVBoxLayout()
    win_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    title = QLabel("You Won!")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setStyleSheet("font-size: 48px; font-weight: bold; color: white;")

    stats = QLabel(f"Moves: {moves}   Time: {seconds}s")
    stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
    stats.setStyleSheet("font-size: 24px; color: #ccc;")

    close_btn = QPushButton("Close")
    close_btn.setStyleSheet("font-size: 18px; padding: 10px 40px; background: #4CAF50; color: white; border-radius: 8px;")
    close_btn.setFixedWidth(200)
    qconnect(close_btn.clicked, on_close)

    win_layout.addWidget(title)
    win_layout.addWidget(stats)
    win_layout.addSpacing(20)
    win_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    win.setLayout(win_layout)
    return win

def prepare_field(field: str) -> str:
    media_dir = mw.col.media.dir()
    srcs   = re.findall(r'<img[^>]*\ssrc="([^"]+)"', field)
    local  = [s for s in srcs if not s.startswith('http')]
    remote = [s for s in srcs if s.startswith('http')]
    chosen = local[0] if local else (remote[0] if remote else None)

    if chosen:
        field = re.sub(r'<[^>]+>', '', field).strip()
        field += f'<img src="{os.path.join(media_dir, chosen)}" width="180" height="130">' if not chosen.startswith('http') else ''
    else:
        field = re.sub(r'<[^>]+>', '', field).strip()

    field = re.sub(r'\[sound:[^\]]+\]', '', field).strip()
    field = html.unescape(field)
    return field

def load_pairs(deck_name: str, count: int) -> list:
    card_ids = mw.col.find_cards(f'deck:"{deck_name}"')
    if len(card_ids) < count:
        count = len(card_ids)
    selected = random.sample(card_ids, count)
    pairs    = []
    for card_id in selected:
        card  = mw.col.get_card(card_id)
        note  = card.note()
        front = prepare_field(note.fields[0])
        back  = prepare_field(note.fields[1])
        if front and back:
            pairs.append((front, back))
    return pairs