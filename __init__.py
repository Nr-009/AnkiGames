# __init__.py

from aqt import gui_hooks, mw
from aqt.utils import qconnect
from aqt.qt import QDialog
from .ui.game_selector import GameSelector
from .games.memory_flip import MemoryFlipGame

def launch_game(deck_id):
    deck     = mw.col.decks.get(deck_id)
    deckName = deck["name"]

    selector = GameSelector(deckName)
    result   = selector.exec()

    if result == QDialog.DialogCode.Accepted:
        if selector.chosen_mode == "memory_flip":
            game = MemoryFlipGame(deckName, selector.numberOfCardsPerMemoryGrid)
            game.exec()

def add_game_option(menu, deck_id):
    action = menu.addAction("Play as Game")
    qconnect(action.triggered, lambda: launch_game(deck_id))

gui_hooks.deck_browser_will_show_options_menu.append(add_game_option)