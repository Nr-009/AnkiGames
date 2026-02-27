import re
import os
import html
import json
import random
from aqt import mw


def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    return config.get("useReviewQueue", False)


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
    use_review_queue = load_config()

    query    = f'deck:"{deck_name}" is:due' if use_review_queue else f'deck:"{deck_name}"'
    card_ids = mw.col.find_cards(query)

    random.shuffle(card_ids)
    pairs = []

    for card_id in card_ids:
        card  = mw.col.get_card(card_id)
        note  = card.note()
        front = prepare_field(note.fields[0])
        back  = prepare_field(note.fields[1])
        if front and back:
            pairs.append((front, back))

    return pairs