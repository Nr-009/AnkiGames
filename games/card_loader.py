# games/card_loader.py

import re
import os
import html
import random
from aqt import mw

def prepare_field(field: str) -> str:
    media_dir = mw.col.media.dir()
    
    srcs = re.findall(r'<img[^>]*\ssrc="([^"]+)"', field)
    
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